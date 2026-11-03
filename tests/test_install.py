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
import time
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
        # Hyprland is running, as on every machine with a session, so a panel check that fails to
        # ask the session it found reads as busy, as it would for real.
        self.stub("pgrep", 'case "$*" in *quickshell*)'
                                 ' [ -f "$SHELL_ALIVE" ] && echo 1234 || exit 1 ;;'
                                 ' *"-x Hyprland"*) echo 4321 ;;'
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
        # A private runtime folder with one running "Hyprland" (a copy of sleep under that name,
        # which is what /proc/<pid>/comm shows), so the panel check never walks Dave's own
        # sessions in /run/user and the stub hyprctl is what answers.
        self.runtime = self.tmp / "run"
        self.runtime.mkdir()
        self.fake_hyprland = self.tmp / "Hyprland"
        shutil.copy("/usr/bin/sleep", self.fake_hyprland)
        self.sessions = []
        self.live_hyprland("main-session")

    def live_hyprland(self, signature):
        process = subprocess.Popen([str(self.fake_hyprland), "60"])
        self.sessions.append(process)
        folder = self.runtime / "hypr" / signature
        folder.mkdir(parents=True)
        (folder / "hyprland.lock").write_text(f"{process.pid}\nwayland-1\n")
        return folder

    def tearDown(self):
        for process in self.sessions:
            process.kill()
            process.wait()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def stub(self, name, body):
        path = self.bin / name
        path.write_text(STUB.format(body=body))
        path.chmod(0o755)

    def locked(self, yes):
        self.stub("omarchy-shell", f'echo \'{{"sessionLocked":{str(bool(yes)).lower()}}}\'')

    def run_install(self, *args, extra=None):
        env = {**(extra or {}), "HOME": str(self.home), "PATH": f"{self.bin}:{os.environ['PATH']}",
               "OMARCHY_PATH": str(self.bin),   # the scripts prepend "$OMARCHY_PATH/bin" — stubs must win
               "CALLS": str(self.calls), "COUNT": str(self.tmp / "count"),
               "SHELL_ALIVE": str(self.shell_alive),
               "BARBARIAN_UNINSTALL_SETTLE": "0",
               "XDG_RUNTIME_DIR": str(self.runtime)}
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
        blip's display-filter finding, the main machine's 'insufficient evidence' rule)."""
        self.stub("quickshell", "exit 1")          # never reaches the IPC; the marker stands
        result = self.run_install()
        self.assertIn("could not prove the shell was stopped", result.stdout)
        self.assertFalse((self.home / PLUGIN).exists())
        self.assertTrue(self.called("systemd-run"))

    def test_a_locked_run_writes_no_plugin_file_and_arms_the_waiter(self):
        self.locked(True)
        result = self.run_install()
        self.assertFalse((self.home / PLUGIN).exists())
        self.assertFalse((self.home / ".config/omarchy/workspace-backgrounds").exists())
        self.assertFalse(self.called("omarchy-restart-shell"))
        self.assertTrue(self.called("systemd-run"))
        self.assertIn("--when-unlocked", self.called("systemd-run")[0])
        self.assertIn("held back", result.stdout)

    def engines_out_of_date(self):
        """Everything installed, then the engines alone made older: an engine-only commit."""
        self.run_install()
        layout = self.home / ".config/omarchy/workspace-layout"
        engines = [layout / "ws-layout", layout / "quick-app", layout / "reptile_features.py",
                   self.home / ".local/bin/reptile-feature"]
        for engine in engines:
            engine.write_text("# an older engine\n")
        self.calls.write_text("")
        self.shell_alive.touch()       # the first run stopped the stub shell; a real one is back
        return engines

    def test_an_engine_only_change_goes_in_under_a_lock(self):
        """Nothing reloads the engines, so a locked night does not leave the machine on old ones."""
        engines = self.engines_out_of_date()
        self.locked(True)
        result = self.run_install()
        for engine in engines:
            self.assertNotEqual(engine.read_text(), "# an older engine\n", f"{engine}: {result.stdout}")
        self.assertFalse(self.called("systemd-run"))
        self.assertNotIn("held back", result.stdout)

    def test_the_engines_wait_with_a_panel_held_back_in_the_same_run(self):
        """An old panel must not drive a new engine."""
        engines = self.engines_out_of_date()
        (self.home / PLUGIN / "Panel.qml").write_text("// an older panel\n")
        self.locked(True)
        self.run_install()
        for engine in engines:
            self.assertEqual(engine.read_text(), "# an older engine\n", str(engine))
        self.assertTrue(self.called("systemd-run"))

    def test_the_layout_engines_wait_out_a_desk_renumber(self):
        engines = self.engines_out_of_date()
        self.stub("pgrep", 'case "$*" in *quickshell*)'
                           ' [ -f "$SHELL_ALIVE" ] && echo 1234 || exit 1 ;;'
                           ' *"-x Hyprland"*) echo 4321 ;;'
                           ' *ws-renumber*) echo 777 ;;'
                           ' *) exit 1 ;; esac')
        result = self.run_install()
        self.assertEqual(engines[0].read_text(), "# an older engine\n")
        self.assertTrue(self.called("systemd-run"), result.stdout)

    def test_the_switch_manifests_follow_the_installed_engine(self):
        """Held back with the engine, so no switch names a feature the engine does not know."""
        self.engines_out_of_date()
        switches = self.home / ".config/caboodle/switches"
        before = sorted(p.name for p in switches.glob("*")) if switches.exists() else []
        for manifest in switches.glob("*"):
            manifest.unlink()
        self.stub("pgrep", 'case "$*" in *quickshell*)'
                           ' [ -f "$SHELL_ALIVE" ] && echo 1234 || exit 1 ;;'
                           ' *"-x Hyprland"*) echo 4321 ;;'
                           ' *ws-renumber*) echo 777 ;;'
                           ' *) exit 1 ;; esac')
        self.run_install()
        self.assertEqual(sorted(p.name for p in switches.glob("*")), [])
        self.assertTrue(before, "the first install wrote no switch manifests to compare")

    def test_the_switch_manifests_go_in_with_the_engines_while_the_watcher_waits(self):
        """The watcher is held back under a lock, the engines are not, so the manifests follow them."""
        self.engines_out_of_date()
        (self.home / ".config/omarchy/workspace-backgrounds/per-workspace-wallpaper.sh").write_text(
            "# an older watcher\n")
        switches = self.home / ".config/caboodle/switches"
        for manifest in switches.glob("*"):
            manifest.unlink()
        self.locked(True)
        result = self.run_install()
        self.assertTrue(list(switches.glob("*")), result.stdout + result.stderr)
        self.assertIn("held back", result.stdout)

    def test_a_file_that_cannot_be_written_is_reported_not_skipped(self):
        engines = self.engines_out_of_date()
        bin_dir = self.home / ".local/bin"
        switches = self.home / ".config/caboodle/switches"
        for manifest in switches.glob("*"):
            manifest.unlink()
        bin_dir.chmod(0o555)
        try:
            result = self.run_install()
        finally:
            bin_dir.chmod(0o755)
        self.assertEqual(result.returncode, 1, result.stdout)
        report = result.stderr.split("could not write these files", 1)
        self.assertEqual(len(report), 2, result.stderr)
        self.assertIn(str(bin_dir / "reptile-feature"), report[1])
        self.assertNotIn(str(engines[0]), report[1])
        self.assertIn("installed the files it could write", result.stdout)
        self.assertEqual(engines[3].read_text(), "# an older engine\n")
        self.assertEqual(engines[0].read_text(), (ROOT / "engine/ws-layout").read_text())
        self.assertEqual(list(switches.glob("*")), [])
        self.assertFalse(self.called("systemd-run"))

    def test_a_write_that_fails_part_way_leaves_the_old_file_whole(self):
        """A full disk mid-copy must not leave a truncated engine where a working one was."""
        engines = self.engines_out_of_date()
        self.stub("install", 'case "$2" in */engine/ws-layout) head -c 100 "$2" > "$3"; exit 1 ;; esac\n'
                             'exec /usr/bin/install "$@"')
        result = self.run_install()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(engines[0].read_text(), "# an older engine\n")
        self.assertEqual([p.name for p in engines[0].parent.glob(".barbarian-install.*")], [])
        self.assertEqual(engines[1].read_text(), (ROOT / "engine/quick-app").read_text())

    def test_a_folder_where_a_file_belongs_is_reported(self):
        engines = self.engines_out_of_date()
        engines[3].unlink()
        engines[3].mkdir()
        result = self.run_install()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = result.stderr.split("could not write these files", 1)
        self.assertEqual(len(report), 2, result.stderr)
        self.assertIn(str(engines[3]), report[1])
        self.assertEqual(list(engines[3].iterdir()), [])
        self.assertEqual([p.name for p in engines[3].parent.glob(".barbarian-install.*")], [])

    def test_old_temp_files_are_cleared_and_folder_modes_kept(self):
        engines = self.engines_out_of_date()
        layout = engines[0].parent
        stale, fresh = layout / ".barbarian-install.AAAAAA", layout / ".barbarian-install.BBBBBB"
        stale.write_text("left by a killed run\n")
        fresh.write_text("another run's, still being written\n")
        hour_ago = time.time() - 3600
        os.utime(stale, (hour_ago, hour_ago))
        layout.chmod(0o700)
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(stale.exists())
        self.assertTrue(fresh.exists())
        self.assertEqual(layout.stat().st_mode & 0o777, 0o700)

    def test_the_panel_on_screen_counts_as_busy(self):
        self.stub("hyprctl", 'echo \'[{"namespace": "omarchy-keyboard-panel"}]\'')
        self.run_install()
        self.assertFalse((self.home / PLUGIN).exists())
        self.assertTrue(self.called("systemd-run"))

    def no_hyprland(self):
        for process in self.sessions:
            process.kill()
            process.wait()
        self.sessions = []
        self.stub("pgrep", 'case "$*" in *quickshell*)'
                           ' [ -f "$SHELL_ALIVE" ] && echo 1234 || exit 1 ;;'
                           ' *) exit 1 ;; esac')

    def test_a_session_that_cannot_be_asked_counts_as_a_panel_on_screen(self):
        """#7403: hyprctl failing or hanging for a running Hyprland is busy."""
        self.stub("hyprctl", 'echo "HYPRLAND_INSTANCE_SIGNATURE not set!" >&2; exit 1')
        result = self.run_install()
        self.assertNotIn("Panel.qml", self.installed(), result.stdout + result.stderr)
        self.assertTrue(self.called("systemd-run"))

    def test_a_hyprland_with_no_folder_to_ask_counts_as_a_panel_on_screen(self):
        for process in self.sessions:
            process.kill()
            process.wait()
        self.sessions = []                        # pgrep (setUp) still finds a Hyprland
        result = self.run_install()
        self.assertNotIn("Panel.qml", self.installed(), result.stdout + result.stderr)

    def test_every_live_session_is_asked_not_just_the_first(self):
        """A nested test session must not hide the panel open in Dave's own."""
        self.live_hyprland("zz-dave")
        self.stub("hyprctl", 'case "$HYPRLAND_INSTANCE_SIGNATURE" in'
                             ' zz-dave) echo \'[{"namespace": "omarchy-keyboard-panel"}]\' ;;'
                             ' *) echo "[]" ;; esac')
        result = self.run_install()
        self.assertNotIn("Panel.qml", self.installed(), result.stdout + result.stderr)

    def test_a_folder_left_by_a_session_that_ended_is_not_asked(self):
        """Its process id may since belong to something else, alive but not Hyprland."""
        stale = self.runtime / "hypr" / "ended"
        stale.mkdir(parents=True)
        (stale / "hyprland.lock").write_text(f"{os.getpid()}\nwayland-9\n")
        self.stub("hyprctl", '[ "$HYPRLAND_INSTANCE_SIGNATURE" = ended ] && exit 1; echo "[]"')
        result = self.run_install()
        self.assertIn("Panel.qml", self.installed(), result.stdout + result.stderr)

    def test_a_hung_hyprctl_counts_as_a_panel_on_screen(self):
        """Asked once, timed out once: a hang must not cost the timeout for every file."""
        import time
        self.stub("hyprctl", "exec sleep 30")
        started = time.monotonic()
        result = self.run_install()
        self.assertLess(time.monotonic() - started, 20, "the hang was waited out more than once")
        self.assertNotIn("Panel.qml", self.installed(), result.stdout + result.stderr)
        self.assertEqual(len(self.called("hyprctl")), 1)

    def test_the_nested_test_session_is_never_asked(self):
        """tests/nested/nested runs the panel from the repo; one left open must not hold installs."""
        self.live_hyprland("nested-session")
        (self.runtime / "barbarian-nested").mkdir()
        (self.runtime / "barbarian-nested/sig").write_text("nested-session\n")
        self.stub("hyprctl", 'case "$HYPRLAND_INSTANCE_SIGNATURE" in'
                             ' nested-session) echo \'[{"namespace": "omarchy-keyboard-panel"}]\' ;;'
                             ' *) echo "[]" ;; esac')
        result = self.run_install()
        self.assertIn("Panel.qml", self.installed(), result.stdout + result.stderr)

    def test_an_answer_that_is_not_hyprctls_json_counts_as_a_panel_on_screen(self):
        self.stub("hyprctl", 'echo "unknown request"')
        result = self.run_install()
        self.assertNotIn("Panel.qml", self.installed(), result.stdout + result.stderr)

    def test_a_waiter_asks_a_hung_session_again_on_its_next_poll(self):
        count = self.tmp / "hyprctl-count"
        self.stub("hyprctl", f'n=$(( $(cat "{count}" 2>/dev/null || echo 0) + 1 )); echo $n > "{count}"; '
                             '[ $n = 1 ] && exec sleep 30; echo "[]"')
        result = self.run_install("--when-unlocked", extra={"BARBARIAN_UNLOCK_POLL": "1",
                                                            "BARBARIAN_UNLOCK_GIVE_UP": "4"})
        self.assertIn("Panel.qml", self.installed(), result.stdout + result.stderr)

    def test_no_hyprland_at_all_means_no_panel(self):
        """A machine with no session over ssh installs rather than waiting forever."""
        self.no_hyprland()
        self.stub("hyprctl", 'echo "HYPRLAND_INSTANCE_SIGNATURE not set!" >&2; exit 1')
        result = self.run_install()
        self.assertIn("Panel.qml", self.installed(), result.stdout + result.stderr)

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
