#!/usr/bin/env python3
"""Behavioral tests with private settings and mocked compositor access."""

import contextlib
import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ENGINE = Path(__file__).resolve().parent.parent / "engine"
sys.path.insert(0, str(ENGINE))
import reptile_features as features


def load(name, filename):
    loader = SourceFileLoader(name, str(ENGINE / filename))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


layout = load("layout_features_test", "ws-layout")
quick = load("quick_features_test", "quick-app")


class FeatureTest(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="barbarian-features-")
        self.addCleanup(self.scratch.cleanup)
        self.directory = Path(self.scratch.name)
        self.settings = self.directory / "features.json"
        self.apps = self.directory / "quick-apps.json"
        self.bindings = self.directory / "quick-apps.lua"
        for module, key, value in [
            (features, "SETTINGS_FILE", self.settings),
            (quick, "LIST_FILE", str(self.apps)),
            (quick, "GEN_FILE", str(self.bindings)),
            (layout, "SNAP_DIR", str(self.directory)),
        ]:
            patch = mock.patch.object(module, key, value)
            patch.start()
            self.addCleanup(patch.stop)
        self.app = {"name": "test", "label": "Test app", "key": "SUPER + comma",
                    "match": "test-app", "launch": "test-launcher"}
        self.apps.write_text(json.dumps({"hide_on_close": True, "apps": [self.app]}))

    def configure(self, **values):
        self.settings.write_text(json.dumps(values))

    def test_missing_settings_preserve_existing_behavior(self):
        self.assertTrue(all(features.read().values()))
        self.assertFalse(self.settings.exists())

    def test_legacy_hide_choice_survives_first_unrelated_change(self):
        self.apps.write_text(json.dumps({"hide_on_close": False, "apps": [self.app]}))
        self.assertFalse(quick.read_list()["apps"][0]["hide_on_close"])
        features.set_feature("columns", False)
        self.assertFalse(quick.read_list()["apps"][0]["hide_on_close"])
        self.assertEqual(json.loads(self.apps.read_text())["apps"], [self.app])

    def test_one_switch_preserves_all_others_and_unknown_future_settings(self):
        self.configure(open_apps=False, future_setting="retained")
        features.set_feature("columns", False)
        stored = json.loads(self.settings.read_text())
        self.assertEqual(stored["future_setting"], "retained")
        self.assertFalse(stored["open_apps"])
        self.assertFalse(stored["columns"])
        self.assertTrue(stored["restore_layouts"])

    def test_invalid_settings_disable_actions_and_cannot_be_silently_overwritten(self):
        for raw in ("broken json", "[]", '{"columns":"false"}'):
            with self.subTest(raw=raw):
                self.settings.write_text(raw)
                self.assertFalse(features.enabled("restore_layouts"))
                with self.assertRaises(features.SettingsError):
                    features.set_feature("columns", False)
                self.assertEqual(self.settings.read_text(), raw)

    def test_only_explicit_booleans_and_known_features_are_accepted(self):
        for key, value in [("columns", "false"), ("columns", 0), ("missing", False)]:
            with self.assertRaises(features.SettingsError):
                features.set_feature(key, value)
        self.assertFalse(self.settings.exists())

    def test_failed_atomic_write_leaves_the_previous_state(self):
        self.configure(columns=True)
        with mock.patch.object(features.os, "replace", side_effect=OSError("test write failure")):
            with self.assertRaises(OSError):
                features.set_feature("columns", False)
        self.assertTrue(features.read()["columns"])
        self.assertEqual(list(self.directory.glob(".features-*")), [])

    def test_failed_shortcut_update_rolls_back_the_choice_and_bindings(self):
        with mock.patch.object(features, "sync_shortcuts",
                               side_effect=[features.SettingsError("test reload failure"), None]) as sync:
            with self.assertRaisesRegex(features.SettingsError, "previous choice was kept"):
                features.set_feature("quick_apps", False)
        self.assertTrue(features.enabled("quick_apps"))
        self.assertEqual(sync.call_args_list, [mock.call(release_hidden=True), mock.call()])

    def test_failed_rollback_is_reported_without_claiming_the_shortcuts_are_restored(self):
        with mock.patch.object(features, "sync_shortcuts", side_effect=features.SettingsError("offline")):
            with self.assertRaisesRegex(features.SettingsError, "shortcuts could not be restored"):
                features.set_feature("quick_apps", False)
        self.assertTrue(features.enabled("quick_apps"))

    def test_repeated_choice_does_not_reload_or_reveal_windows(self):
        with mock.patch.object(features, "sync_shortcuts") as sync:
            features.set_feature("quick_apps", True)
        sync.assert_not_called()

    def test_disabling_quick_apps_reveals_hidden_windows_but_enabling_does_not(self):
        with mock.patch.object(features, "sync_shortcuts") as sync:
            features.set_feature("quick_apps", False)
            features.set_feature("quick_apps", True)
        self.assertEqual(sync.call_args_list, [mock.call(release_hidden=True), mock.call(release_hidden=False)])

    def test_disabled_quick_apps_generate_no_overrides_and_keep_the_app_list(self):
        self.configure(quick_apps=False)
        quick.generate(reload=False)
        self.assertNotIn("o.bind(", self.bindings.read_text())
        self.assertEqual(quick.read_list()["apps"], [{**self.app, "hide_on_close": True}])
        self.configure(quick_apps=True)
        quick.generate(reload=False)
        self.assertIn("Test app (quick app)", self.bindings.read_text())
        self.assertIn("SUPER + W", self.bindings.read_text())

    def test_legacy_hide_on_close_off_keeps_app_shortcuts_but_restores_normal_close_binding(self):
        self.configure(hide_on_close=False)
        quick.generate(reload=False)
        generated = self.bindings.read_text()
        self.assertIn("Test app (quick app)", generated)
        self.assertNotIn("close-or-hide", generated)
        self.assertNotIn("SUPER + ALT + W", generated)

    def test_disabled_quick_app_direct_call_never_launches_or_moves(self):
        self.configure(quick_apps=False)
        with mock.patch.object(quick, "hypr_eval") as execute, mock.patch.object(quick, "mark_fired") as fired:
            quick.cmd_toggle("test")
        execute.assert_not_called()
        fired.assert_not_called()

    def test_stale_close_binding_falls_back_to_normal_close(self):
        for values in ({"quick_apps": False}, {"hide_on_close": False}):
            self.configure(**values)
            with mock.patch.object(quick, "hypr_eval") as execute:
                quick.cmd_close_or_hide()
            execute.assert_called_once_with("hl.dispatch(hl.dsp.window.close())")

    def test_per_app_choices_override_both_legacy_global_locations(self):
        self.configure(hide_on_close=False)
        other = {**self.app, "name": "other", "match": "other-app", "hide_on_close": True}
        self.apps.write_text(json.dumps({"hide_on_close": True, "apps": [self.app, other]}))
        choices = quick.read_list()
        self.assertEqual([app["hide_on_close"] for app in choices["apps"]], [False, True])
        self.assertNotIn("hide_on_close", choices)
        self.assertNotIn("hide_on_close", features.read())
        self.assertNotIn("hide_on_close", features.DEFAULTS)
        self.assertNotIn("hide_on_close", json.loads(self.apps.read_text())["apps"][0])

    def test_explicit_app_choices_no_longer_depend_on_legacy_globals(self):
        self.configure(hide_on_close="damaged legacy choice")
        self.apps.write_text(json.dumps({"hide_on_close": "damaged", "apps": [{**self.app, "hide_on_close": False}]}))
        self.assertFalse(quick.read_list()["apps"][0]["hide_on_close"])
        self.assertTrue(features.enabled("restore_layouts"))

    def test_damaged_app_data_is_reported_without_disabling_unrelated_features(self):
        for raw in ('{broken', '{"apps":{}}', '{"apps":[{"hide_on_close":"false"}]}'):
            with self.subTest(raw=raw):
                self.apps.write_text(raw)
                self.assertTrue(features.enabled("restore_layouts"))
                with self.assertRaises(features.SettingsError):
                    quick.cmd_hide_on_close("test", "false")
                self.assertEqual(self.apps.read_text(), raw)

    def test_app_toggle_preserves_other_choices_and_metadata(self):
        other = {**self.app, "name": "other", "match": "other-app", "hide_on_close": False}
        self.apps.write_text(json.dumps({"future": "kept", "apps": [self.app, other]}))
        with mock.patch.object(quick, "desktop_command"), contextlib.redirect_stdout(io.StringIO()) as output:
            quick.cmd_hide_on_close("test", "false")
        saved = json.loads(self.apps.read_text())
        self.assertEqual(saved["future"], "kept")
        self.assertEqual(saved["apps"][1], other)
        self.assertFalse(saved["apps"][0]["hide_on_close"])
        self.assertEqual(json.loads(output.getvalue()), {"name": "test", "hide_on_close": False})
        self.assertNotIn("close-or-hide", self.bindings.read_text())
        self.assertIn("Test app (quick app)", self.bindings.read_text())

    def test_shortcut_edits_preserve_the_app_close_choice_and_new_apps_default_to_hide(self):
        self.apps.write_text(json.dumps({"hide_on_close": False, "apps": [self.app]}))
        updated = {**self.app, "key": "SUPER + period"}
        new = {**self.app, "name": "new", "key": "SUPER + slash", "match": "new-app"}
        with mock.patch.object(quick, "desktop_command"), mock.patch.object(quick, "live_binds", return_value={}):
            quick.cmd_set(json.dumps(updated))
            quick.cmd_set(json.dumps(new))
        saved = json.loads(self.apps.read_text())
        self.assertNotIn("hide_on_close", saved)
        self.assertEqual([app["hide_on_close"] for app in saved["apps"]], [False, True])

    def test_per_app_command_rejects_invalid_choices_and_missing_apps_without_writing(self):
        original = self.apps.read_text()
        for choice in ("1", "yes", "False", "", True):
            with self.assertRaises(features.SettingsError):
                quick.cmd_hide_on_close("test", choice)
        with self.assertRaises(features.SettingsError):
            quick.cmd_hide_on_close("missing", "true")
        with self.assertRaises(SystemExit):
            quick.cmd_set(json.dumps({**self.app, "hide_on_close": "false"}))
        self.assertEqual(self.apps.read_text(), original)

    def test_failed_per_app_binding_reload_restores_choices_and_generated_bindings(self):
        self.apps.write_text(json.dumps({"hide_on_close": False, "apps": [self.app]}))
        original = json.loads(self.apps.read_text())
        quick.generate(reload=False)
        old_bindings = self.bindings.read_text()
        with mock.patch.object(quick, "desktop_command", side_effect=[features.SettingsError("reload failed"), None]):
            with self.assertRaisesRegex(features.SettingsError, "previous choices were kept"):
                quick.cmd_hide_on_close("test", "true")
        self.assertEqual(json.loads(self.apps.read_text()), original)
        self.assertEqual(self.bindings.read_text(), old_bindings)

    def test_failed_per_app_binding_rollback_does_not_claim_success(self):
        self.apps.write_text(json.dumps({"hide_on_close": False, "apps": [self.app]}))
        with mock.patch.object(quick, "desktop_command", side_effect=features.SettingsError("desktop offline")):
            with self.assertRaisesRegex(features.SettingsError, "shortcuts could not be restored"):
                quick.cmd_hide_on_close("test", "true")
        self.assertFalse(quick.read_list()["apps"][0]["hide_on_close"])

    def test_per_app_choices_can_be_saved_while_quick_apps_is_paused(self):
        self.configure(quick_apps=False)
        with mock.patch.object(quick, "desktop_command"), contextlib.redirect_stdout(io.StringIO()):
            quick.cmd_hide_on_close("test", "false")
        self.assertFalse(quick.read_list()["apps"][0]["hide_on_close"])
        self.assertNotIn("o.bind(", self.bindings.read_text())

    def test_damaged_app_choices_can_be_disabled_and_cannot_be_reenabled_silently(self):
        quick.generate(reload=False)
        damaged = json.dumps({"apps": [{**self.app, "hide_on_close": "false"}]})
        self.apps.write_text(damaged)
        with mock.patch.object(features, "shortcut_engine", return_value=quick), \
             mock.patch.object(quick, "hypr_eval") as reveal, \
             mock.patch.object(quick, "desktop_command"):
            features.set_feature("quick_apps", False)
            self.assertFalse(features.enabled("quick_apps"))
            self.assertNotIn("o.bind(", self.bindings.read_text())
            reveal.assert_called_once()
            with self.assertRaisesRegex(features.SettingsError, "previous choice was kept"):
                features.set_feature("quick_apps", True)
        self.assertFalse(features.enabled("quick_apps"))
        self.assertEqual(self.apps.read_text(), damaged)
        self.assertNotIn("o.bind(", self.bindings.read_text())

    def test_only_the_first_or_last_hiding_choice_needs_to_change_close_bindings(self):
        other = {**self.app, "name": "other", "match": "other-app", "hide_on_close": True}
        self.apps.write_text(json.dumps({"apps": [{**self.app, "hide_on_close": True}, other]}))
        quick.generate(reload=False)
        with mock.patch.object(quick, "desktop_command") as desktop, contextlib.redirect_stdout(io.StringIO()):
            quick.cmd_hide_on_close("test", "false")
        desktop.assert_not_called()
        self.assertIn("close-or-hide", self.bindings.read_text())
        with mock.patch.object(quick, "desktop_command") as desktop, contextlib.redirect_stdout(io.StringIO()):
            quick.cmd_hide_on_close("other", "false")
        desktop.assert_called_once_with(["reload"])
        self.assertNotIn("close-or-hide", self.bindings.read_text())

    def run_close_lua(self, apps, klass, toggle=None):
        self.apps.write_text(json.dumps({"apps": apps}))
        with mock.patch.object(quick, "hypr_eval") as execute, mock.patch.object(quick, "mark_fired"):
            if toggle:
                quick.cmd_toggle(toggle)
            else:
                quick.cmd_close_or_hide()
        active = '{class=' + quick.lua_str(klass) + ',address="0x1"}'
        fixture = '''
hl = {
 get_active_window=function() return ACTIVE end,
 get_windows=function() return {ACTIVE} end,
 get_cursor_pos=function() return {x=3,y=4} end,
 dispatch=function(command) print(command) end,
 dsp={window={close=function() return "close" end,
              move=function(args) return args.workspace end},
      cursor={move=function() return "cursor" end}}
}
'''.replace('ACTIVE', active)
        result = subprocess.run(['lua', '-'], input=fixture + execute.call_args.args[0],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.splitlines()

    def test_super_w_honors_each_app_and_the_most_specific_window_match(self):
        broad = {**self.app, "hide_on_close": True}
        narrow = {**self.app, "name": "narrow", "match": "test-app-special", "hide_on_close": False}
        for apps, klass, expected in [
            ([broad, narrow], 'test-app-main', ['special:quick-test', 'cursor']),
            ([broad, narrow], 'test-app-special-page', ['close']),
            ([narrow, broad], 'test-app-special-page', ['close']),
            ([broad, narrow], 'ordinary-window', ['close']),
            ([{**broad, 'hide_on_close': False}, {**narrow, 'hide_on_close': True}],
             'test-app-special-page', ['special:quick-narrow', 'cursor']),
        ]:
            with self.subTest(klass=klass, apps=apps):
                self.assertEqual(self.run_close_lua(apps, klass), expected)

    def test_app_shortcut_still_hides_when_its_super_w_choice_is_off(self):
        app = {**self.app, "hide_on_close": False}
        self.assertEqual(self.run_close_lua([app], 'test-app-main', toggle='test'), ['special:quick-test', 'cursor'])

    def test_old_global_manifest_is_retired_to_trash_but_other_owners_are_kept(self):
        directory = self.directory / 'switches'
        directory.mkdir()
        retired = directory / 'reptile-hide-on-close.json'
        original = json.dumps({'id': 'reptile-hide-on-close', 'owner': '@barbarian'})
        retired.write_text(original)
        with mock.patch.object(features.Path, 'home', return_value=self.directory):
            features.install_manifests(directory)
            features.install_manifests(directory)
        self.assertFalse(retired.exists())
        archived = list((self.directory / '.local/share/Trash/files').glob('barbarian-switch-*/reptile-hide-on-close.json'))
        self.assertEqual(len(archived), 1)
        self.assertEqual(archived[0].read_text(), original)
        self.assertEqual(len(list(directory.glob('*.json'))), 10)
        unowned = json.dumps({'id': 'reptile-hide-on-close', 'owner': '@someone-else'})
        retired.write_text(unowned)
        with self.assertRaises(features.SettingsError):
            features.install_manifests(directory)
        self.assertEqual(retired.read_text(), unowned)

    def test_reload_failure_is_not_reported_as_success(self):
        failed = subprocess.CompletedProcess([], 1, "", "offline")
        with mock.patch.object(quick.subprocess, "run", return_value=failed):
            with self.assertRaises(features.SettingsError):
                quick.generate()

    def test_repair_reloads_even_when_the_generated_file_is_unchanged(self):
        quick.generate(reload=False)
        with mock.patch.object(quick, "desktop_command") as execute:
            quick.generate(force_reload=True)
        execute.assert_called_once_with(["reload"])

    def test_an_app_update_cannot_reinstate_shortcuts_after_disabling_them(self):
        read_started = threading.Event()
        release_read = threading.Event()
        failures = []
        original_read = quick.read_list

        def paused_read():
            data = original_read()
            if threading.current_thread().name == "older-app-update":
                read_started.set()
                if not release_read.wait(1):
                    raise RuntimeError("test barrier timed out")
            return data

        def run(function):
            try:
                function()
            except BaseException as error:
                failures.append(error)

        with mock.patch.object(quick, "read_list", side_effect=paused_read), \
             mock.patch.object(quick, "desktop_command"), mock.patch.object(quick, "release_hidden"), \
             mock.patch.object(features, "shortcut_engine", return_value=quick):
            older = threading.Thread(name="older-app-update", target=run, args=(quick.generate,))
            newer = threading.Thread(target=run, args=(lambda: features.set_feature("quick_apps", False),))
            older.start()
            self.assertTrue(read_started.wait(1))
            newer.start()
            release_read.set()
            older.join(2)
            newer.join(2)
        self.assertFalse(older.is_alive() or newer.is_alive())
        self.assertEqual(failures, [])
        self.assertFalse(features.enabled("quick_apps"))
        self.assertNotIn("o.bind(", self.bindings.read_text())

    def test_actual_generator_rolls_back_after_reload_failure(self):
        quick.generate(reload=False)
        original = self.bindings.read_text()
        with mock.patch.object(features, "shortcut_engine", return_value=quick), \
             mock.patch.object(quick, "release_hidden"), \
             mock.patch.object(quick, "desktop_command", side_effect=[features.SettingsError("offline"), None]):
            with self.assertRaisesRegex(features.SettingsError, "previous choice was kept"):
                features.set_feature("quick_apps", False)
        self.assertTrue(features.enabled("quick_apps"))
        self.assertEqual(self.bindings.read_text(), original)

    def test_manifest_commands_use_the_same_status_and_choices(self):
        features.install_manifests(self.directory / "switches")
        manifests = list((self.directory / "switches").glob("*.json"))
        self.assertEqual(len(manifests), len(features.FEATURES))
        self.configure(columns=False, restore_layouts=False)
        for path in manifests:
            manifest = json.loads(path.read_text())
            self.assertEqual(path.stem, manifest["id"])
            self.assertEqual(manifest["group"], "Reptile")
            self.assertEqual(manifest["status"][:2], ["reptile-feature", "status"])
            key = manifest["status"][2]
            state = features.status(key)
            self.assertEqual(state["id"], manifest["id"])
            self.assertEqual(state["on"], features.enabled(key))
        self.assertIn("Paused", features.status("automatic_restore")["summary"])

    def test_two_processes_preserve_each_others_choices(self):
        isolated_home = self.directory / "home"
        isolated_home.mkdir()
        environment = dict(os.environ, HOME=str(isolated_home), PYTHONDONTWRITEBYTECODE="1")
        processes = [subprocess.Popen([sys.executable, str(ENGINE / "reptile-feature"), "off", key],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment)
                     for key in ("columns", "layout_messages")]
        for process in processes:
            out, error = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, error)
            self.assertFalse(json.loads(out)["on"])
        path = isolated_home / ".config/omarchy/workspace-layout/features.json"
        stored = json.loads(path.read_text())
        self.assertFalse(stored["columns"])
        self.assertFalse(stored["layout_messages"])
        self.assertTrue(stored["quick_apps"])

    def test_disabled_restore_never_reads_a_recording_or_touches_windows(self):
        self.configure(restore_layouts=False)
        with mock.patch.object(layout, "snap_path") as path, mock.patch.object(layout, "dispatch") as dispatch:
            self.assertEqual(layout.restore(1), 0)
        path.assert_not_called()
        dispatch.assert_not_called()

    def test_automatic_and_visit_switches_are_independent_of_manual_restore(self):
        for key, arguments in [("automatic_restore", {"automatic": True}), ("apply_on_visit", {"on_visit": True})]:
            self.configure(**{key: False})
            with mock.patch.object(layout, "snap_path") as path:
                self.assertEqual(layout.restore(1, **arguments), 0)
                path.assert_not_called()
            with mock.patch.object(layout, "snap_path", return_value=str(self.directory / "missing")) as path, \
                 mock.patch.object(layout, "card"), mock.patch.object(layout, "card_down"):
                self.assertEqual(layout.restore(1), 1)
                path.assert_called_once()

    def test_disabled_columns_does_not_query_or_move_windows(self):
        self.configure(columns=False)
        with mock.patch.object(layout, "tiled_on") as windows:
            self.assertEqual(layout.columns(1, 3), 0)
        windows.assert_not_called()

    def test_disabled_closing_skips_both_restore_culls(self):
        self.configure(close_extras=False)
        with mock.patch.object(layout, "on_ws") as windows, mock.patch.object(layout, "dispatch") as dispatch:
            self.assertEqual(layout.close_extras(1, {}), 0)
            self.assertEqual(layout.close_extras(1, {}), 0)
        windows.assert_not_called()
        dispatch.assert_not_called()

    def test_floating_off_protects_extra_floating_windows_from_the_cull(self):
        self.configure(floating_windows=False)
        floating = {"address": "0xf", "class": "test", "title": "test", "floating": True}
        tiled = {**floating, "address": "0xt", "floating": False}
        with mock.patch.object(layout, "on_ws", return_value=[floating, tiled]), \
             mock.patch.object(layout, "dispatch") as dispatch, mock.patch.object(layout, "wait_until"):
            self.assertEqual(layout.close_extras(1, {}), 1)
        self.assertIn("0xt", dispatch.call_args.args[0])

    def test_floating_off_never_launches_or_repositions(self):
        self.configure(floating_windows=False)
        with mock.patch.object(layout, "desk_geometry") as geometry:
            self.assertEqual(layout.restore_floats(1, [{"class": "test"}], mock.Mock()), ([], [], 0))
        geometry.assert_not_called()

    def test_disabled_opening_and_placeholders_do_not_launch_or_wait(self):
        self.configure(open_apps=False, placeholders=False)
        with mock.patch.object(layout.subprocess, "Popen") as launch, \
             mock.patch.object(layout, "reptile_ipc") as ipc, mock.patch.object(layout, "place_new") as wait:
            self.assertIsNone(layout.open_window("test", "test-command", 1))
            self.assertIsNone(layout.open_placeholder(1, {"class": "test"}))
        launch.assert_not_called()
        ipc.assert_not_called()
        wait.assert_not_called()

    def test_disabled_messages_do_not_call_the_shell(self):
        self.configure(layout_messages=False)
        with mock.patch.object(layout, "reptile_ipc") as ipc:
            layout.card("Progress", "Reason")
            layout.card_down()
        ipc.assert_not_called()

    def test_skipping_missing_apps_preserves_existing_window_tree(self):
        self.configure(open_apps=False, placeholders=False, close_extras=False)
        first = {"class": "test-first", "title": "First", "address": "0x1", "at": [0, 0]}
        second = {"class": "test-missing", "title": "Missing", "launch": "run-missing"}
        third = {"class": "test-third", "title": "Third", "address": "0x3", "at": [100, 0]}
        steps = [{"win": first, "after": None, "side": None, "share": None},
                 {"win": second, "after": 0, "side": "r", "share": .5},
                 {"win": third, "after": 1, "side": "d", "share": .5}]
        with mock.patch.object(layout, "tiled_on", return_value=[first, third]), \
             mock.patch.object(layout, "same_arrangement", return_value=True) as same, \
             mock.patch.object(layout, "size_gaps", return_value=[]), \
             mock.patch.object(layout, "rebuild") as rebuild:
            self.assertEqual(layout._restore(1, "Test", steps, [], "Test", mock.Mock()), 0)
        kept = same.call_args.args[1]
        self.assertEqual([s["win"]["class"] for s in kept], ["test-first", "test-third"])
        self.assertEqual(kept[1]["after"], 0)
        rebuild.assert_not_called()

    def test_command_error_has_nonzero_status_and_keeps_bad_file(self):
        self.settings.write_text("corrupt")
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(features.command(["columns", "false"]), 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("Could not read", err.getvalue())
        self.assertEqual(self.settings.read_text(), "corrupt")


if __name__ == "__main__":
    unittest.main()
