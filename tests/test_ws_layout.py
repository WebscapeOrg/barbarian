#!/usr/bin/env python3
"""Tests for the engine's launch rules — the summons that reopens Quickshell plugin windows.

    python3 tests/test_ws_layout.py

The engine has no .py suffix and lives beside the plugin's scripts, so it loads by path;
importing it runs no command (everything subprocess-shaped happens inside functions, called
only by the real commands). Nothing here touches the shell, the bar or any live file.
"""
import importlib.util
import contextlib
from importlib.machinery import SourceFileLoader
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True   # the loader would otherwise cache a .pyc beside the engine

ENGINE = pathlib.Path(__file__).resolve().parent.parent / "engine/ws-layout"
sys.path.insert(0, str(ENGINE.parent))
loader = SourceFileLoader("ws_layout", str(ENGINE))
spec = importlib.util.spec_from_loader("ws_layout", loader)
engine = importlib.util.module_from_spec(spec)
loader.exec_module(engine)


def setUpModule():
    temporary = tempfile.TemporaryDirectory(prefix="barbarian-layout-identity-")
    unittest.addModuleCleanup(temporary.cleanup)
    directory = pathlib.Path(temporary.name)
    for module, key, path in [(engine.features, "SETTINGS_FILE", directory / "features.json"),
                              (engine, "QUICK_APPS_FILE", str(directory / "quick-apps.json"))]:
        patcher = mock.patch.object(module, key, path)
        patcher.start()
        unittest.addModuleCleanup(patcher.stop)


class Summons(unittest.TestCase):
    """Quickshell plugin windows share one class, so — like the placeholders — they are known
    by title and summoned through the shell (Magpie, 2026-10-15, Dave's Phase 3)."""

    def test_a_magpie_mail_window_is_summoned_by_its_title(self):
        """Magpie is Magpie Mail since 2026-11-08 (magpie C-065 and Q-017): the new title and the old
        one both reopen it through the new plugin id first and the old one while the shell does
        not know the new one yet."""
        for title in ("✉️ Magpie Mail", "✉️ Magpie Mail — Inbox", "🐦 Magpie", "🐦 Magpie — Inbox"):
            with self.subTest(title=title):
                win = {"class": "org.quickshell", "title": title}
                command = engine.launcher_for_win(win, 3)
                self.assertEqual(command, engine.SUMMONS["✉️ Magpie Mail"])
                self.assertIn("omarchy-shell shell summon magpie-mail", command)
                self.assertIn("|| omarchy-shell shell summon magpie", command)
                self.assertEqual(engine.app_identity(win), "✉️ Magpie Mail")

    def test_magpie_calendar_is_summoned_without_toggling_it_closed(self):
        """Skylark is Magpie Calendar since 2026-11-03: either title reopens it, through the new
        plugin id first and the old one when the shell does not know the new one yet."""
        for title in ("Magpie Calendar", "Magpie Calendar — Week", "Skylark", "Skylark — Calendar"):
            with self.subTest(title=title):
                win = {"class": "org.quickshell", "title": title}
                command = engine.launcher_for_win(win, 4)
                self.assertEqual(command, engine.SUMMONS["Magpie Calendar"])
                self.assertIn("omarchy-shell shell summon magpie-calendar", command)
                self.assertIn("|| omarchy-shell shell summon skylark", command)
                self.assertNotIn("toggle", command)

    def test_every_alias_names_a_current_plugin(self):
        for old, new in engine.SUMMONS_ALIASES.items():
            self.assertIn(new, engine.SUMMONS)
            self.assertNotIn(old, engine.SUMMONS)

    def test_another_quickshell_window_is_not_grabbed(self):
        """The class is the whole shell's; only the titled plugin may be claimed."""
        win = {"class": "org.quickshell", "title": "Holodeck"}
        self.assertIsNone(engine.launcher_for_win(win, 3))

    def test_every_summons_key_is_a_title_prefix_not_a_class(self):
        for prefix in (*engine.SUMMONS, *engine.SUMMONS_ALIASES):
            self.assertNotEqual(prefix, "org.quickshell")
            self.assertTrue(prefix and "." not in prefix)

    def test_ordinary_classes_still_go_by_class(self):
        win = {"class": "org.gnome.Nautilus", "title": "anything"}
        self.assertEqual(engine.launcher_for_win(win, 3),
                         engine.launcher_for("org.gnome.Nautilus", 3))

    def test_the_summons_only_applies_to_the_shell_class(self):
        """A window that merely carries Magpie's title but is not Quickshell's class must not
        be summoned — no other app may open a shell window."""
        win = {"class": "org.gnome.TextEditor", "title": "🐦 Magpie — my novel"}
        self.assertEqual(engine.launcher_for_win(win, 3),
                         engine.launcher_for("org.gnome.TextEditor", 3))


class WindowIdentity(unittest.TestCase):
    """The shared class is never an identity: a Quickshell plugin window matches only within
    its summons title, in the tiled matcher, the floating matcher and the cull (the probe's
    four forbidden assignments, 2026-10-15)."""

    @staticmethod
    def win(title, address="0x1", klass="org.quickshell"):
        return {"class": klass, "title": title, "address": address,
                "at": [0, 0], "size": [100, 100], "floating": False}

    def test_existing_shell_windows_never_fill_another_plugin_recording(self):
        for recorded, actual in [("🐦 Magpie", "Holodeck"), ("Holodeck", "🐦 Magpie"),
                                 ("Skylark", "🐦 Magpie"), ("🐦 Magpie", "Skylark"),
                                 ("Skylark", "Holodeck"), ("Holodeck", "Skylark"),
                                 ("Magpie Calendar", "🐦 Magpie"), ("🐦 Magpie", "Magpie Calendar"),
                                 ("Magpie Calendar", "Holodeck"), ("Holodeck", "Magpie Calendar"),
                                 ("✉️ Magpie Mail", "Magpie Calendar"), ("Skylark", "✉️ Magpie Mail"),
                                 ("✉️ Magpie Mail", "Holodeck"), ("Holodeck", "✉️ Magpie Mail")]:
            with self.subTest(recorded=recorded, actual=actual):
                self.assertEqual(engine.assign([{"win": self.win(recorded)}],
                                               [self.win(actual)]), {})

    def test_floating_shell_windows_never_fill_another_plugin_recording(self):
        for recorded, actual in [("🐦 Magpie", "Holodeck"), ("Holodeck", "🐦 Magpie"),
                                 ("Skylark", "🐦 Magpie"), ("🐦 Magpie", "Skylark"),
                                 ("Skylark", "Holodeck"), ("Holodeck", "Skylark"),
                                 ("Magpie Calendar", "🐦 Magpie"), ("🐦 Magpie", "Magpie Calendar"),
                                 ("Magpie Calendar", "Holodeck"), ("Holodeck", "Magpie Calendar"),
                                 ("✉️ Magpie Mail", "Magpie Calendar"), ("Skylark", "✉️ Magpie Mail"),
                                 ("✉️ Magpie Mail", "Holodeck"), ("Holodeck", "✉️ Magpie Mail")]:
            with self.subTest(recorded=recorded, actual=actual):
                self.assertEqual(engine.match_floats([self.win(recorded)],
                                                     [self.win(actual)]), {})

    def test_a_summons_window_whose_title_changed_still_matches(self):
        """The identity is the title prefix, not the whole title — a plugin window's title
        changes with its state, exactly as a Chrome tab's does."""
        recorded = self.win("🐦 Magpie — Inbox")
        actual = self.win("🐦 Magpie — Compose", "0x2")
        self.assertEqual(engine.assign([{"win": recorded}], [actual]), {0: actual})
        self.assertEqual(engine.match_floats([recorded], [actual]), {0: actual})

    def test_a_skylark_recording_matches_the_renamed_window(self):
        for recorded, actual in [("Skylark", "Magpie Calendar"), ("Magpie Calendar", "Skylark"),
                                 ("🐦 Magpie — Inbox", "✉️ Magpie Mail — Inbox"),
                                 ("✉️ Magpie Mail", "🐦 Magpie")]:
            with self.subTest(recorded=recorded, actual=actual):
                window = self.win(actual, "0x2")
                self.assertEqual(engine.assign([{"win": self.win(recorded)}], [window]), {0: window})
                self.assertEqual(engine.match_floats([self.win(recorded)], [window]), {0: window})

    def test_ordinary_app_titles_may_change(self):
        recorded = self.win("Old tab", klass="google-chrome")
        actual = self.win("New tab", "0x2", klass="google-chrome")
        self.assertEqual(engine.assign([{"win": recorded}], [actual]), {0: actual})
        self.assertEqual(engine.match_floats([recorded], [actual]), {0: actual})

    def test_the_cull_keeps_the_recorded_plugin_and_closes_the_stranger(self):
        """close_extras buckets by identity: with Magpie recorded and a stray second shell
        window on the desk, the stranger goes and Magpie stays."""
        magpie = self.win("✉️ Magpie Mail — Inbox", "0xkeep")
        stray = self.win("Holodeck", "0xclose")
        closed = []
        with mock.patch.object(engine, "on_ws", return_value=[magpie, stray]), \
             mock.patch.object(engine, "dispatch", side_effect=lambda cmd: closed.append(cmd)), \
             mock.patch.object(engine, "wait_until", return_value=True):
            engine.close_extras(4, {"✉️ Magpie Mail": 1})
        self.assertEqual(len(closed), 1)
        self.assertIn("0xclose", closed[0])
        self.assertNotIn("0xkeep", closed[0])

    def test_the_cull_closes_a_placeholder_before_the_real_window(self):
        """Within one identity the placeholder still goes first — the recorded window keeps
        its place (the original placeholder-removal rule, unchanged)."""
        placeholder = dict(self.win("🐦 Magpie — Inbox", "0xph"), placeholder="ab12cd")
        real = self.win("✉️ Magpie Mail — Inbox", "0xreal")
        closed = []
        with mock.patch.object(engine, "on_ws", return_value=[placeholder, real]), \
             mock.patch.object(engine, "dispatch", side_effect=lambda cmd: closed.append(cmd)), \
             mock.patch.object(engine, "wait_until", return_value=True):
            engine.close_extras(4, {engine.app_identity({"class": "org.quickshell",
                                                         "title": "🐦 Magpie"}): 1})
        self.assertEqual(len(closed), 1)
        self.assertIn("0xph", closed[0])


class Forget(unittest.TestCase):
    """`forget` takes a placeholder's window out of the recording — by identity, never by the
    shared class alone, so a stale Magpie placeholder cannot prune an unrelated shell window's
    recording (#1120's seam, 2026-10-15)."""

    @staticmethod
    def stand_in(title, address="0xph", floating=False):
        return {"class": "org.quickshell", "title": title, "address": address,
                "floating": floating, "workspace": {"id": 9}, "placeholder": "ab12cd"}

    @staticmethod
    def run_forget(stand_in, windows):
        import json, tempfile
        record = {"workspace": 9, "name": "Test", "format": 2, "windows": windows, "floating": []}
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(record, f)
        written, closed = {}, []
        try:
            with mock.patch.object(engine, "placeholder_client", return_value=stand_in), \
                 mock.patch.object(engine, "snap_path", return_value=path), \
                 mock.patch.object(engine, "write_record",
                                   side_effect=lambda rec: written.update(rec=rec)), \
                 mock.patch.object(engine, "close_window",
                                   side_effect=lambda addr: closed.append(addr)):
                engine.forget("ab12cd")
        finally:
            os.unlink(path)
        return written, closed

    @staticmethod
    def window(klass, title):
        return {"class": klass, "title": title, "launch": None, "after": None,
                "side": None, "share": None, "at": [0, 0], "size": [800, 600]}

    def test_a_stale_magpie_placeholder_cannot_prune_an_unrelated_recording(self):
        """The Magpie entry is already gone from the recording; only Holodeck remains, and it
        shares the shell's class. The placeholder must close without touching Holodeck."""
        written, closed = self.run_forget(self.stand_in("🐦 Magpie"),
                                          [self.window("org.quickshell", "Holodeck")])
        self.assertEqual(closed, ["0xph"])
        self.assertEqual([w["title"] for w in written["rec"]["windows"]], ["Holodeck"])

    def test_a_placeholder_prunes_the_window_it_stands_in_for(self):
        stand = self.stand_in("Holodeck")
        written, closed = self.run_forget(stand,
                                          [self.window("org.quickshell", "Holodeck")])
        self.assertEqual(closed, ["0xph"])
        self.assertEqual(written["rec"]["windows"], [])

    def test_ordinary_apps_keep_the_first_of_class_fallback(self):
        """A terminal placeholder whose recorded title no longer matches still prunes the
        first window of its class — the pre-existing behaviour, unchanged."""
        written, _ = self.run_forget({"class": "foot", "title": "old command", "address": "0xph",
                                      "floating": False, "workspace": {"id": 9},
                                      "placeholder": "ab12cd"},
                                     [self.window("foot", "another command")])
        self.assertEqual(written["rec"]["windows"], [])


class SkylarkRestoration(unittest.TestCase):
    def setUp(self):
        self.window = {"class": "org.quickshell", "title": "Skylark", "address": "0xcal",
                       "at": [12, 40], "size": [800, 800], "floating": False}

    def test_recording_skylark_saves_a_launcher_without_the_warning(self):
        with mock.patch.object(engine, "tiled_on", return_value=[self.window]), \
             mock.patch.object(engine, "floating_on", return_value=[]), \
             mock.patch.object(engine, "ws_name", return_value="Messaging"), \
             mock.patch.object(engine, "write_record") as write, \
             mock.patch.object(engine, "ANNOUNCE", True), \
             mock.patch.object(engine, "card") as card, \
             mock.patch.object(engine, "card_down"), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(engine.take_snapshot(4), 0)
        saved = write.call_args.args[0]["windows"][0]
        self.assertEqual(saved["launch"], engine.SUMMONS["Magpie Calendar"])
        self.assertNotIn("cannot reopen", card.call_args.args[0])

    def test_an_old_null_launcher_recording_restores_without_resaving(self):
        record = {"workspace": 4, "name": "Messaging", "format": 2, "floating": [],
                  "windows": [{**self.window, "launch": None, "after": None,
                               "side": None, "share": None}]}
        with tempfile.TemporaryDirectory(prefix="barbarian-skylark-record-") as temporary:
            path = pathlib.Path(temporary) / "ws4.json"
            original = json.dumps(record).encode()
            path.write_bytes(original)
            with mock.patch.object(engine, "SNAP_DIR", temporary), \
                 mock.patch.object(engine, "on_ws", return_value=[]), \
                 mock.patch.object(engine, "clients", return_value=[]), \
                 mock.patch.object(engine, "stand_on"), \
                 mock.patch.object(engine, "default_split_ratio", return_value=1), \
                 mock.patch.object(engine, "set_default_split_ratio"), \
                 mock.patch.object(engine, "dispatch"), \
                 mock.patch.object(engine, "place_new", return_value=self.window), \
                 mock.patch.object(engine.subprocess, "Popen") as launch, \
                 mock.patch.object(engine, "card"), mock.patch.object(engine, "card_down"), \
                 mock.patch.object(engine, "ANNOUNCE", False), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(engine.restore(4), 0)
            self.assertIn(engine.SUMMONS["Magpie Calendar"], launch.call_args.args[0])
            self.assertEqual(path.read_bytes(), original)

    def test_a_recording_with_the_old_summon_reopens_through_the_new_one(self):
        """Dave's Messaging recording stores Skylark's launch as the old summon string; the live
        launcher wins over it, so the renamed plugin is summoned, never the old id alone."""
        record = {"workspace": 4, "name": "Messaging", "format": 2, "floating": [],
                  "windows": [{**self.window, "launch": "omarchy-shell shell summon skylark '{}'",
                               "after": None, "side": None, "share": None}]}
        with tempfile.TemporaryDirectory(prefix="barbarian-skylark-record-") as temporary:
            path = pathlib.Path(temporary) / "ws4.json"
            path.write_text(json.dumps(record))
            with mock.patch.object(engine, "SNAP_DIR", temporary), \
                 mock.patch.object(engine, "on_ws", return_value=[]), \
                 mock.patch.object(engine, "clients", return_value=[]), \
                 mock.patch.object(engine, "stand_on"), \
                 mock.patch.object(engine, "default_split_ratio", return_value=1), \
                 mock.patch.object(engine, "set_default_split_ratio"), \
                 mock.patch.object(engine, "dispatch"), \
                 mock.patch.object(engine, "place_new", return_value=self.window), \
                 mock.patch.object(engine.subprocess, "Popen") as launch, \
                 mock.patch.object(engine, "card"), mock.patch.object(engine, "card_down"), \
                 mock.patch.object(engine, "ANNOUNCE", False), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(engine.restore(4), 0)
        self.assertEqual([c.args[0] for c in launch.call_args_list],
                         [f"setsid {engine.SUMMONS['Magpie Calendar']} >/dev/null 2>&1 &"])

    def test_a_recording_with_the_old_magpie_summon_reopens_through_the_new_one(self):
        """Dave's Messaging recording stores Magpie's launch as the old summon string; the live
        launcher wins over it, so the renamed plugin is summoned, never the old id alone."""
        record = {"workspace": 4, "name": "Messaging", "format": 2, "floating": [],
                  "windows": [{**self.window, "title": "🐦 Magpie",
                               "launch": "omarchy-shell shell summon magpie '{}'",
                               "after": None, "side": None, "share": None}]}
        with tempfile.TemporaryDirectory(prefix="barbarian-magpie-record-") as temporary:
            path = pathlib.Path(temporary) / "ws4.json"
            path.write_text(json.dumps(record))
            with mock.patch.object(engine, "SNAP_DIR", temporary), \
                 mock.patch.object(engine, "on_ws", return_value=[]), \
                 mock.patch.object(engine, "clients", return_value=[]), \
                 mock.patch.object(engine, "stand_on"), \
                 mock.patch.object(engine, "default_split_ratio", return_value=1), \
                 mock.patch.object(engine, "set_default_split_ratio"), \
                 mock.patch.object(engine, "dispatch"), \
                 mock.patch.object(engine, "place_new", return_value=self.window), \
                 mock.patch.object(engine.subprocess, "Popen") as launch, \
                 mock.patch.object(engine, "card"), mock.patch.object(engine, "card_down"), \
                 mock.patch.object(engine, "ANNOUNCE", False), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(engine.restore(4), 0)
        self.assertEqual([c.args[0] for c in launch.call_args_list],
                         [f"setsid {engine.SUMMONS['✉️ Magpie Mail']} >/dev/null 2>&1 &"])

    def test_a_new_unrelated_shell_window_cannot_be_taken_for_skylark(self):
        def place(predicate, ws, timeout, floating=False):
            self.assertFalse(predicate({**self.window, "title": "🐦 Magpie"}))
            self.assertFalse(predicate({**self.window, "title": "Holodeck"}))
            self.assertFalse(predicate({**self.window, "class": "foot"}))
            self.assertTrue(predicate(self.window))
            self.assertTrue(predicate({**self.window, "title": "Magpie Calendar"}))
            return self.window

        with mock.patch.object(engine, "clients", return_value=[]), \
             mock.patch.object(engine.subprocess, "Popen"), \
             mock.patch.object(engine, "place_new", side_effect=place):
            self.assertEqual(engine.open_window("org.quickshell",
                             engine.SUMMONS["Magpie Calendar"], 4), self.window)

    def test_open_skylark_is_moved_from_another_desk_without_relaunching(self):
        for title in ("Skylark", "Magpie Calendar"):
            with self.subTest(title=title):
                self.move_open_calendar({**self.window, "title": title, "workspace": {"id": 5}})

    def move_open_calendar(self, window):

        def dispatch(command):
            if "window.move" in command:
                window["workspace"] = {"id": 4}

        with mock.patch.object(engine, "clients", return_value=[window]), \
             mock.patch.object(engine, "on_ws", side_effect=lambda ws:
                               [window] if window["workspace"]["id"] == ws else []), \
             mock.patch.object(engine, "dispatch", side_effect=dispatch), \
             mock.patch.object(engine.subprocess, "Popen") as launch:
            result = engine.open_window("org.quickshell", engine.SUMMONS["Magpie Calendar"], 4)
        self.assertEqual(result["address"], "0xcal")
        self.assertEqual(window["workspace"]["id"], 4)
        launch.assert_not_called()

    def test_floating_skylark_beside_tiled_magpie_is_recorded(self):
        skylark = {**self.window, "floating": True}
        magpie = {**self.window, "title": "🐦 Magpie", "address": "0xmail"}
        with mock.patch.object(engine, "on_ws", return_value=[skylark, magpie]):
            self.assertEqual(engine.floating_on(4), [skylark])

    def test_floating_dialogs_of_the_same_app_remain_excluded(self):
        dialog = {**self.window, "floating": True}
        with mock.patch.object(engine, "on_ws", return_value=[dialog, self.window]):
            self.assertEqual(engine.floating_on(4), [])


class AccountLaunchers(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="barbarian-accounts-")
        self.addCleanup(directory.cleanup)
        self.settings = pathlib.Path(directory.name) / "accounts.json"
        self.settings.write_text(json.dumps({
            "Default": "personal@example.test",
            "Profile 1": "work@example.test",
        }))
        patcher = mock.patch.object(engine, "ACCOUNT_SETTINGS", str(self.settings))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_personal_mail_and_calendar_use_the_private_default_account(self):
        for klass, kind in (("chrome-mail.google.com__mail_-Default", "mail"),
                            ("chrome-calendar.google.com__calendar_r_week-Default", "calendar")):
            with self.subTest(kind=kind):
                command = engine.launcher_for(klass, 3)
                self.assertIn(f"https://{kind}.google.com/", command)
                self.assertIn("authuser=personal@example.test", command)
                self.assertIn("--profile-directory=Default", command)

    def test_work_mail_and_calendar_use_the_private_profile_account(self):
        for klass in ("chrome-mail.google.com__mail_-Profile_1",
                      "chrome-calendar.google.com__calendar_r_week-Profile_1"):
            with self.subTest(klass=klass):
                command = engine.launcher_for(klass, 2)
                self.assertIn("authuser=work@example.test", command)
                self.assertIn("--profile-directory='Profile 1'", command)

    def test_a_missing_account_file_reopens_nothing(self):
        self.settings.unlink()
        self.assertIsNone(engine.launcher_for("chrome-mail.google.com__mail_-Default", 3))

    def test_a_missing_profile_entry_reopens_nothing(self):
        self.settings.write_text("{}\n")
        self.assertIsNone(engine.launcher_for("chrome-calendar.google.com__calendar_r_week-Default", 3))


class LinkWindows(unittest.TestCase):
    """A link Magpie opened is a guest: never recorded, never closed, never taken for a recorded
    window or for the window a restore waits for. Magpie opens every link through its own page,
    so the window's class carries that page's name (Magpie's C-047, hobnob #7354)."""

    GMAIL = "chrome-mail.google.com__mail_-Profile_1"
    LINK = ("chrome-__home_user_.config_omarchy_plugins_magpie-6ffeab1a32e965d6"
            "_scripts_link-window.html-Profile_1")

    @staticmethod
    def win(address, klass, floating, at=(0, 0), size=(1000, 1000), ws=4):
        return {"class": klass, "title": "Inbox", "address": address, "floating": floating,
                "at": list(at), "size": list(size), "workspace": {"id": ws}, "mapped": True}

    def test_only_a_link_window_carries_the_mark(self):
        wins = [self.win("0xlink", self.LINK, True),
                self.win("0xlink2", self.LINK.replace("Profile_1", "Default"), True),
                self.win("0xmail", self.GMAIL, False),
                self.win("0xpr", "chrome-github.com__pulls-Default", True),
                self.win("0xcal", "org.quickshell", False)]
        self.assertEqual([c["address"] for c in engine.without_links(wins)],
                         ["0xmail", "0xpr", "0xcal"])

    def test_a_floating_link_window_is_never_recorded(self):
        link = self.win("0xlink", self.LINK, True, size=(500, 500))
        notes = self.win("0xnotes", "obsidian", True, at=(600, 0), size=(300, 300))
        with mock.patch.object(engine, "on_ws", return_value=[link, notes]):
            self.assertEqual(engine.floating_on(4), [notes])

    def test_a_tiled_link_window_is_pruned_from_a_recording(self):
        gmail = self.win("0xmail", self.GMAIL, False, size=(500, 1000))
        link = self.win("0xlink", self.LINK, False, at=(510, 0), size=(490, 1000))
        with mock.patch.object(engine, "tiled_on", return_value=[gmail, link]), \
             mock.patch.object(engine, "floating_on", return_value=[]), \
             mock.patch.object(engine, "ws_name", return_value="Mail"), \
             mock.patch.object(engine, "write_record") as write, \
             mock.patch.object(engine, "ANNOUNCE", False), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(engine.take_snapshot(4), 0)
        self.assertEqual([w["class"] for w in write.call_args.args[0]["windows"]], [self.GMAIL])

    def test_the_cull_never_closes_a_link_window(self):
        """With close extras and floating windows on (both on when nothing is saved), a floating
        window the recording does not list is a stray — unless it is a link."""
        gmail = self.win("0xmail", self.GMAIL, False)
        link = self.win("0xlink", self.LINK, True, size=(500, 500))
        stray = self.win("0xstray", "obsidian", True, size=(300, 300))
        closed = []
        with mock.patch.object(engine, "on_ws", return_value=[gmail, link, stray]), \
             mock.patch.object(engine, "dispatch", side_effect=lambda cmd: closed.append(cmd)), \
             mock.patch.object(engine, "wait_until", return_value=True):
            self.assertEqual(engine.close_extras(4, {self.GMAIL: 1}), 1)
        self.assertEqual(len(closed), 1)
        self.assertIn("0xstray", closed[0])

    def test_a_wait_for_any_new_window_never_takes_a_link_window(self):
        """A placeholder's "Open a new terminal" takes the first new window of any class; a link
        that maps first is passed over for the window that maps after it."""
        link = self.win("0xlink", self.LINK, False)
        real = self.win("0xterm", "Alacritty", False)
        polls = []

        def clients():
            polls.append(1)
            return [link] + ([real] if len(polls) >= 3 else [])

        with mock.patch.object(engine, "clients", side_effect=clients), \
             mock.patch.object(engine, "on_ws", return_value=[real]), \
             mock.patch.object(engine, "dispatch"):
            taken = engine.place_new(lambda c: True, 4, 2.0)
        self.assertEqual(taken["address"], "0xterm")

    def test_a_restore_leaves_the_link_and_reopens_gmail(self):
        record = {"workspace": 4, "name": "Mail", "format": 2, "floating": [],
                  "windows": [{"class": self.GMAIL, "title": "Inbox", "launch": None, "after": None,
                               "side": None, "share": None, "at": [0, 0], "size": [1000, 1000]}]}
        link = self.win("0xlink", self.LINK, True, size=(500, 500))
        real = self.win("0xnew", self.GMAIL, False)
        dispatched, out = [], io.StringIO()
        with tempfile.TemporaryDirectory(prefix="barbarian-link-restore-") as temporary:
            (pathlib.Path(temporary) / "ws4.json").write_text(json.dumps(record))
            accounts = pathlib.Path(temporary) / "accounts.json"
            accounts.write_text(json.dumps({"Profile 1": "work@example.test"}))
            with mock.patch.object(engine, "SNAP_DIR", temporary), \
                 mock.patch.object(engine, "ACCOUNT_SETTINGS", str(accounts)), \
                 mock.patch.object(engine, "on_ws", return_value=[link]), \
                 mock.patch.object(engine, "clients", return_value=[link]), \
                 mock.patch.object(engine, "stand_on"), \
                 mock.patch.object(engine, "dispatch", side_effect=lambda cmd: dispatched.append(cmd)), \
                 mock.patch.object(engine, "wait_until", return_value=True), \
                 mock.patch.object(engine, "default_split_ratio", return_value=1), \
                 mock.patch.object(engine, "set_default_split_ratio"), \
                 mock.patch.object(engine, "place_new", return_value=real), \
                 mock.patch.object(engine.subprocess, "Popen") as launch, \
                 mock.patch.object(engine, "card"), mock.patch.object(engine, "card_down"), \
                 mock.patch.object(engine, "ANNOUNCE", False), contextlib.redirect_stdout(out):
                engine.restore(4)
        self.assertEqual(len(launch.call_args_list), 1)
        self.assertIn("mail.google.com", launch.call_args.args[0])
        self.assertFalse([c for c in dispatched if "0xlink" in c])
        self.assertNotIn("closed", out.getvalue())

    def old_recording(self, temporary):
        """A recording made by a Barbarian that did not know the mark: Gmail with a link beside
        it, and a floating link."""
        record = {"workspace": 4, "name": "Mail", "format": 2,
                  "windows": [{"class": self.GMAIL, "title": "Inbox", "launch": None, "after": None,
                               "side": None, "share": None, "at": [0, 0], "size": [500, 1000]},
                              {"class": self.LINK, "title": "A link", "launch": None, "after": 0,
                               "side": "r", "share": 0.5, "at": [510, 0], "size": [490, 1000]}],
                  "floating": [{"class": self.LINK, "title": "Another", "launch": None,
                                "at": [100, 100], "size": [400, 400],
                                "frac": [0.1, 0.1, 0.4, 0.4]}]}
        path = pathlib.Path(temporary) / "ws4.json"
        path.write_text(json.dumps(record))
        return path

    def test_an_old_recording_is_read_without_its_link_windows(self):
        with tempfile.TemporaryDirectory(prefix="barbarian-link-record-") as temporary:
            path = self.old_recording(temporary)
            original = path.read_bytes()
            record = engine.read_record(str(path))
            self.assertEqual(path.read_bytes(), original)
        self.assertEqual([(w["class"], w["after"]) for w in record["windows"]], [(self.GMAIL, None)])
        self.assertEqual(record["floating"], [])

    def test_an_old_recording_with_a_link_restores_without_a_placeholder(self):
        gmail = self.win("0xmail", self.GMAIL, False)
        out = io.StringIO()
        with tempfile.TemporaryDirectory(prefix="barbarian-link-record-") as temporary:
            self.old_recording(temporary)
            with mock.patch.object(engine, "SNAP_DIR", temporary), \
                 mock.patch.object(engine, "on_ws", return_value=[gmail]), \
                 mock.patch.object(engine, "clients", return_value=[gmail]), \
                 mock.patch.object(engine, "open_placeholder") as placeholder, \
                 mock.patch.object(engine.subprocess, "Popen") as launch, \
                 mock.patch.object(engine, "card"), mock.patch.object(engine, "card_down"), \
                 mock.patch.object(engine, "ANNOUNCE", False), contextlib.redirect_stdout(out):
                self.assertEqual(engine.restore(4), 0)
        placeholder.assert_not_called()
        launch.assert_not_called()
        self.assertIn("already as saved", out.getvalue())

    def test_show_does_not_count_a_link_window(self):
        gmail = self.win("0xmail", self.GMAIL, False)
        link = self.win("0xlink", self.LINK, True, size=(500, 500))
        record = {"workspace": 4, "name": "Mail", "format": 2, "floating": [],
                  "windows": [{"class": self.GMAIL, "title": "Inbox", "launch": None, "after": None,
                               "side": None, "share": None, "at": [0, 0], "size": [1000, 1000]}]}
        out = io.StringIO()
        with tempfile.TemporaryDirectory(prefix="barbarian-link-show-") as temporary:
            (pathlib.Path(temporary) / "ws4.json").write_text(json.dumps(record))
            with mock.patch.object(engine, "SNAP_DIR", temporary), \
                 mock.patch.object(engine, "on_ws", return_value=[gmail, link]), \
                 contextlib.redirect_stdout(out):
                engine.show(4)
        self.assertIn("desk now: as saved", out.getvalue())

    def test_the_panel_does_not_offer_a_link_window_as_an_extra(self):
        link = self.win("0xlink", self.LINK, True, size=(500, 500))
        stray = self.win("0xstray", "obsidian", True, at=(600, 0), size=(300, 300))
        g = {"w": 1000, "h": 1000, "out": dict.fromkeys(("left", "right", "top", "bottom"), 0),
             "in": dict.fromkeys(("left", "right", "top", "bottom"), 0)}
        with tempfile.TemporaryDirectory(prefix="barbarian-link-windows-") as temporary, \
             mock.patch.object(engine, "SNAP_DIR", temporary):
            model = engine.desk_model(4, "Mail", [link, stray], g)
        self.assertEqual([e["class"] for e in model["extra"]], ["obsidian"])

if __name__ == "__main__":
    sys.dont_write_bytecode = True
    unittest.main()
