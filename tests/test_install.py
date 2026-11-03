#!/usr/bin/env python3
"""Tests for install.sh's update mechanism — what it writes, and when it waits.

    python3 tests/test_install.py

Every run uses a throwaway HOME and a stub PATH, so the live plugin, the live shell and systemd
are never touched: `omarchy-shell` answers whatever the test says the lock is, and
`omarchy-restart-shell`, `systemd-run` and `systemctl` only write down that they were called.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "install.sh"
PLUGIN = ".config/omarchy/plugins/atlas.arrange"

STUB = """#!/usr/bin/env bash
echo "$(basename "$0") $*" >> "$CALLS"
{body}
"""


class Install(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.calls = self.tmp / "calls"
        self.calls.touch()
        # A shell to find, so the installer does not take "nothing running" for "nothing locked",
        # and no renumber in flight. Stubbed rather than run, so the tests never depend on — or
        # wait for — what happens to be running on the machine.
        self.stub("pgrep", 'case "$*" in *quickshell*)'
                                 ' [ -f "$SHELL_ALIVE" ] && echo 1234 || exit 1 ;;'
                                 ' *) exit 1 ;; esac')
        # The shell stub is a killable thing: the first kill lands (and takes the marker the
        # pgrep stub keys on), the second finds nothing — the shape the stop-first pass needs.
        # A test that overrides quickshell without touching the marker models a headless pane
        # whose kill cannot reach the IPC at all.
        self.stub("quickshell", 'if [ -f "$SHELL_ALIVE" ]; then rm -f "$SHELL_ALIVE"; exit 0; '
                                'else exit 1; fi')
        self.stub("omarchy-restart-shell", "exit 0")
        self.shell_alive = self.tmp / "shell-alive"
        self.shell_alive.touch()
        self.stub("systemd-run", "exit 0")
        # No waiter is armed yet: `is-active` on a unit that is not running exits 3.
        self.stub("systemctl", 'case "$*" in *is-active*) exit 3 ;; *) exit 0 ;; esac')
        self.stub("hyprctl", 'echo "[]"')          # no panel on screen
        self.locked(False)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def stub(self, name, body):
        path = self.bin / name
        path.write_text(STUB.format(body=body))
        path.chmod(0o755)

    def locked(self, yes):
        self.stub("omarchy-shell", f'echo \'{{"sessionLocked":{str(bool(yes)).lower()}}}\'')

    def run_install(self, *args):
        env = {"HOME": str(self.home), "PATH": f"{self.bin}:{os.environ['PATH']}",
               "OMARCHY_PATH": str(self.bin),   # the scripts prepend "$OMARCHY_PATH/bin" — stubs must win
               "CALLS": str(self.calls), "COUNT": str(self.tmp / "count"),
               "SHELL_ALIVE": str(self.shell_alive),
               "BARBARIAN_UNINSTALL_SETTLE": "0",
               "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR", "/tmp")}
        return subprocess.run([str(SCRIPT), *args], capture_output=True, text=True, env=env)

    def called(self, name):
        return [line for line in self.calls.read_text().splitlines() if line.startswith(name)]

    def installed(self):
        return sorted(p.name for p in (self.home / PLUGIN).rglob("*") if p.is_file())

    def test_the_old_reptile_plugin_is_migrated_away(self):
        """Q-102: entry out of both files, folder to the trash, all in the install run."""
        import json
        old = self.home / ".config/omarchy/plugins/tinkerbell.reptile"
        old.mkdir(parents=True)
        (old / "manifest.json").write_text("{}\n")
        shell = self.home / ".config/omarchy/shell.json"
        shell.write_text(json.dumps({"bar": {"layout": {
            "left": [], "center": [],
            "right": [{"id": "tinkerbell.reptile"}, {"id": "omarchy.clock"}]}}}) + "\n")
        hidden = self.home / ".config/omarchy/bar-hidden.json"
        hidden.write_text(json.dumps({"left": [], "center": [],
                                      "right": [{"index": 0, "entry": {"id": "tinkerbell.reptile"}}]}) + "\n")
        result = self.run_install()
        self.assertFalse(old.exists(), result.stdout + result.stderr)
        layout = json.loads(shell.read_text())["bar"]["layout"]
        self.assertEqual([e["id"] for e in layout["right"]], ["omarchy.clock"])
        self.assertEqual(json.loads(hidden.read_text())["right"], [])
        self.assertIn("went to the trash", result.stdout)

    def test_the_migration_reminds_while_the_keybind_still_names_the_old_id(self):
        (self.home / ".config/omarchy/plugins/tinkerbell.reptile").mkdir(parents=True)
        (self.home / ".config/omarchy/plugins/tinkerbell.reptile/manifest.json").write_text("{}\n")
        (self.home / ".config/hypr/bindings.lua").parent.mkdir(parents=True)
        (self.home / ".config/hypr/bindings.lua").write_text(
            'bind("HYPER+L", "omarchy-shell tinkerbell.reptile toggle")\n')
        result = self.run_install()
        self.assertIn("keybind reminder", result.stdout)
        self.assertIn("omarchy-shell atlas.arrange layouts", result.stdout)

    def test_the_old_arrange_id_is_migrated_in_place(self):
        """Q-104: the bar entry renames (the panel keeps its lane), the folder trashes."""
        old = self.home / ".config/omarchy/plugins/tinkerbell.arrange"
        old.mkdir(parents=True)
        (old / "manifest.json").write_text("{}\n")
        shell = self.home / ".config/omarchy/shell.json"
        shell.parent.mkdir(parents=True, exist_ok=True)
        shell.write_text(json.dumps({"bar": {"layout": {"right": [
            {"id": "tinkerbell.arrange"}, {"id": "omarchy.clock"}]}}}) + "\n")
        hidden = self.home / ".config/omarchy/bar-hidden.json"
        hidden.write_text(json.dumps({"left": [], "center": [],
                                      "right": [{"index": 0, "entry": {"id": "tinkerbell.arrange"}}]}) + "\n")
        result = self.run_install()
        self.assertFalse(old.exists(), result.stdout + result.stderr)
        layout = json.loads(shell.read_text())["bar"]["layout"]
        self.assertEqual([e["id"] for e in layout["right"]], ["atlas.arrange", "omarchy.clock"])
        self.assertEqual(json.loads(hidden.read_text())["right"],
                         [{"index": 0, "entry": {"id": "atlas.arrange"}}])
        self.assertIn("went to the trash", result.stdout)

    def write_bar(self, right, hidden):
        shell = self.home / ".config/omarchy/shell.json"
        shell.parent.mkdir(parents=True, exist_ok=True)
        shell.write_text(json.dumps({"bar": {"layout": {"left": [], "center": [],
                                                        "right": right}}}) + "\n")
        sidecar = self.home / ".config/omarchy/bar-hidden.json"
        sidecar.write_text(json.dumps(hidden) + "\n")
        return shell, sidecar

    def test_a_widget_hidden_under_an_old_name_takes_the_new_one(self):
        """#7371: Skylark became Magpie Calendar. Its hidden entry keeps its spot and settings,
        and the entry on the bar is left for the calendar's own installer to rename."""
        shell, sidecar = self.write_bar(
            [{"id": "skylark"}, {"id": "omarchy.clock"}],
            {"left": [], "center": [],
             "right": [{"index": 0, "entry": {"id": "crmne.omacal"}},
                       {"index": 3, "entry": {"id": "skylark", "colour": "blue"}}]})
        before = shell.read_text()
        result = self.run_install()
        self.assertEqual(json.loads(sidecar.read_text())["right"],
                         [{"index": 0, "entry": {"id": "crmne.omacal"}},
                          {"index": 3, "entry": {"id": "magpie-calendar", "colour": "blue"}}],
                         result.stdout + result.stderr)
        self.assertEqual(shell.read_text(), before)
        self.assertIn("now carries the new one", result.stdout)

    def test_an_old_name_already_hidden_under_its_new_one_is_a_twin(self):
        """The twin is found across lanes, whichever of the two comes first."""
        _, sidecar = self.write_bar(
            [{"id": "omarchy.clock"}],
            {"left": [{"index": 1, "entry": {"id": "skylark"}}], "center": [],
             "right": [{"index": 0, "entry": {"id": "magpie-calendar"}}]})
        result = self.run_install()
        self.assertEqual(json.loads(sidecar.read_text()),
                         {"left": [], "center": [],
                          "right": [{"index": 0, "entry": {"id": "magpie-calendar"}}]})
        self.assertIn("is now listed once", result.stdout)
        self.assertNotIn("now carries the new one", result.stdout)

    def test_two_entries_hidden_under_the_old_name_leave_one(self):
        _, sidecar = self.write_bar(
            [], {"left": [{"index": 0, "entry": {"id": "skylark"}}], "center": [],
                 "right": [{"index": 2, "entry": {"id": "skylark"}}]})
        self.run_install()
        self.assertEqual(json.loads(sidecar.read_text()),
                         {"left": [{"index": 0, "entry": {"id": "magpie-calendar"}}],
                          "center": [], "right": []})

    def test_the_rename_lands_while_the_screen_is_locked(self):
        """Only the panel reads the sidecar, so the lock is no reason to wait."""
        _, sidecar = self.write_bar([], {"right": [{"index": 0, "entry": {"id": "skylark"}}]})
        self.locked(True)
        self.run_install()
        self.assertEqual(json.loads(sidecar.read_text()),
                         {"right": [{"index": 0, "entry": {"id": "magpie-calendar"}}]})

    def test_the_rename_waits_for_the_panel_to_close(self):
        """An open panel holds the old id and would write it back when it closes, so nothing is
        written and the waiter is armed, even when every plugin file is already in."""
        self.run_install()
        self.calls.write_text("")
        _, sidecar = self.write_bar([], {"right": [{"index": 0, "entry": {"id": "skylark"}}]})
        before = sidecar.read_text()
        self.stub("hyprctl", 'echo \'[{"namespace": "omarchy-keyboard-panel"}]\'')
        result = self.run_install()
        self.assertEqual(sidecar.read_text(), before)
        self.assertTrue(self.called("systemd-run"), result.stdout + result.stderr)
        self.assertIn("waits for the panel to close", result.stdout)

    def test_a_sidecar_with_nothing_renamed_is_not_rewritten(self):
        _, sidecar = self.write_bar([], {"right": [{"index": 0, "entry": {"id": "crmne.omacal"}}]})
        before = sidecar.read_text()
        self.run_install()
        self.assertEqual(sidecar.read_text(), before)

    def test_no_sidecar_is_no_sidecar_afterwards(self):
        result = self.run_install()
        self.assertFalse((self.home / ".config/omarchy/bar-hidden.json").exists())
        self.assertNotIn("Traceback", result.stderr)

    def test_a_sidecar_in_another_shape_is_left_alone_and_the_install_goes_on(self):
        _, sidecar = self.write_bar([], ["not", "the", "shape"])
        before = sidecar.read_text()
        result = self.run_install()
        self.assertEqual(sidecar.read_text(), before)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("left as it is", result.stdout)
        self.assertIn("Panel.qml", self.installed())

    def test_the_arrange_migration_reminds_while_the_keybind_still_names_the_old_id(self):
        (self.home / ".config/omarchy/plugins/tinkerbell.arrange").mkdir(parents=True)
        (self.home / ".config/omarchy/plugins/tinkerbell.arrange/manifest.json").write_text("{}\n")
        (self.home / ".config/hypr/bindings.lua").parent.mkdir(parents=True)
        (self.home / ".config/hypr/bindings.lua").write_text(
            'bind("HYPER+B", "omarchy-shell tinkerbell.arrange toggle")\n')
        result = self.run_install()
        self.assertIn("keybind reminder", result.stdout)
        self.assertIn("omarchy-shell atlas.arrange", result.stdout)

    def test_no_ghost_ids_in_what_ships(self):
        """Q-101, Q-104: one identity — nothing that installs may name a retired id; only
        the installer itself (which removes them) and the docs may."""
        hits = []
        for retired in ("tinkerbell.reptile", "tinkerbell.arrange"):
            for folder in ("plugin", "engine", "hooks"):
                for path in (ROOT / folder).rglob("*"):
                    if path.is_file() and "__pycache__" in path.parts:
                        continue
                    if path.is_file() and retired in path.read_text(errors="ignore"):
                        hits.append(f"{retired}: {path.relative_to(ROOT)}")
        self.assertEqual(hits, [])

    def test_an_unlocked_run_installs_and_restarts_the_shell(self):
        result = self.run_install()
        self.assertIn("Panel.qml", self.installed())
        self.assertTrue(self.called("omarchy-restart-shell"), result.stdout + result.stderr)
        self.assertIn("the shell restarted", result.stdout)

    def test_a_plugin_write_stops_the_shell_before_it(self):
        """The write must fire no watcher reload: stop first, restart after (2026-10-07 ×3)."""
        result = self.run_install()
        self.assertTrue(self.called("quickshell"), result.stdout + result.stderr)
        self.assertIn("kill", self.called("quickshell")[0])
        self.assertTrue(self.called("omarchy-restart-shell"))

    def test_a_kill_that_proves_nothing_writes_nothing(self):
        """A headless pane's 'no kill landed, one still running' defers the whole run (2026-10-15:
        blip's display-filter finding, enterprise's 'insufficient evidence' rule)."""
        self.stub("quickshell", "exit 1")          # never reaches the IPC; the marker stands
        result = self.run_install()
        self.assertIn("could not prove the shell was stopped", result.stdout)
        self.assertFalse((self.home / PLUGIN).exists())
        self.assertTrue(self.called("systemd-run"))

    def test_a_locked_run_writes_nothing_and_arms_the_waiter(self):
        self.locked(True)
        result = self.run_install()
        self.assertFalse((self.home / PLUGIN).exists())
        self.assertFalse(self.called("omarchy-restart-shell"))
        self.assertTrue(self.called("systemd-run"))
        self.assertIn("--when-unlocked", self.called("systemd-run")[0])
        self.assertIn("held back", result.stdout)

    def test_the_panel_on_screen_counts_as_busy(self):
        self.stub("hyprctl", 'echo \'[{"namespace": "omarchy-keyboard-panel"}]\'')
        self.run_install()
        self.assertFalse((self.home / PLUGIN).exists())
        self.assertTrue(self.called("systemd-run"))

    def test_a_restart_owed_from_a_locked_run_happens_at_the_next_free_one(self):
        self.locked(True)
        self.run_install()
        self.locked(False)
        result = self.run_install()
        self.assertIn("Panel.qml", self.installed())
        self.assertTrue(self.called("omarchy-restart-shell"))
        # Installed and restarted: nothing is owed any more.
        self.assertFalse((self.home / ".local/state/omarchy/barbarian-restart-owed").exists())
        self.assertIn("the shell restarted", result.stdout)

    def test_a_second_run_changes_nothing_and_leaves_the_shell_alone(self):
        self.run_install()
        (self.calls).write_text("")
        result = self.run_install()
        self.assertFalse(self.called("omarchy-restart-shell"))
        self.assertFalse(self.called("quickshell"))
        self.assertNotIn("restart", result.stdout)

    def test_feature_switches_are_installed_without_changing_saved_choices(self):
        saved = self.home / ".config/omarchy/workspace-layout/features.json"
        saved.parent.mkdir(parents=True)
        saved.write_text('{"quick_apps":false}\n')
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(saved.read_text(), '{"quick_apps":false}\n')
        manifests = list((self.home / ".config/caboodle/switches").glob("reptile-*.json"))
        self.assertEqual(len(manifests), 10)
        self.assertTrue(os.access(self.home / ".local/bin/reptile-feature", os.X_OK))
        self.assertTrue((saved.parent / "reptile_features.py").exists())

    def test_switch_install_failure_is_reported_after_restarting_the_shell(self):
        conflict = self.home / ".config/caboodle/switches"
        conflict.parent.mkdir(parents=True)
        conflict.write_text("existing file")
        result = self.run_install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("switches could not be installed", result.stderr)
        self.assertTrue(self.called("omarchy-restart-shell"))
        self.assertEqual(conflict.read_text(), "existing file")

    def test_a_refused_restart_is_owed_rather_than_forgotten(self):
        self.stub("omarchy-restart-shell", "exit 1")     # what it does while the session is locked
        self.run_install()
        self.assertIn("Panel.qml", self.installed())
        self.assertTrue((self.home / ".local/state/omarchy/barbarian-restart-owed").exists())
        self.assertTrue(self.called("systemd-run"))

    def test_a_panel_file_in_before_the_screen_went_up_is_still_owed_its_restart(self):
        """The panel opens part way through: what went in first must not be left uncompiled."""
        self.stub("hyprctl", 'if [ -f "$HOME/.config/omarchy/plugins/atlas.arrange/Panel.qml" ]; '
                             'then echo \'[{"namespace": "omarchy-keyboard-panel"}]\'; '
                             'else echo "[]"; fi')
        result = self.run_install()
        stamp = self.home / ".local/state/omarchy/barbarian-restart-owed"
        self.assertIn("Panel.qml", self.installed())
        self.assertNotIn("ws-renumber", self.installed())    # the rest are waiting
        self.assertTrue(stamp.exists(), result.stdout)
        self.assertTrue(self.called("systemd-run"))
        # The waiter's own run finishes both halves of the job.
        self.stub("hyprctl", 'echo "[]"')
        self.run_install("--when-unlocked")
        self.assertIn("ws-renumber", self.installed())
        self.assertTrue(self.called("omarchy-restart-shell"))
        self.assertFalse(stamp.exists())

    def test_the_wallpaper_engine_unit_is_restarted_when_the_engine_changes(self):
        unit = self.home / ".config/systemd/user/some-wallpaper.service"
        unit.parent.mkdir(parents=True)
        unit.write_text("[Service]\nExecStart=%h/.config/omarchy/workspace-backgrounds/"
                        "per-workspace-wallpaper.sh\n")
        self.run_install()
        self.assertTrue([c for c in self.called("systemctl") if "try-restart" in c])

    def test_the_waiter_installs_once_the_screen_is_free(self):
        result = self.run_install("--when-unlocked")
        self.assertIn("Panel.qml", self.installed())
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    unittest.main()
