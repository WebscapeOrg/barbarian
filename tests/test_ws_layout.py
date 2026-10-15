#!/usr/bin/env python3
"""Tests for the engine's launch rules — the summons that reopens Quickshell plugin windows.

    python3 tests/test_ws_layout.py

The engine has no .py suffix and lives beside the plugin's scripts, so it loads by path;
importing it runs no command (everything subprocess-shaped happens inside functions, called
only by the real commands). Nothing here touches the shell, the bar or any live file.
"""
import importlib.util
from importlib.machinery import SourceFileLoader
import os
import pathlib
import sys
import unittest
from unittest import mock

sys.dont_write_bytecode = True   # the loader would otherwise cache a .pyc beside the engine

ENGINE = pathlib.Path(__file__).resolve().parent.parent / "engine/ws-layout"
loader = SourceFileLoader("ws_layout", str(ENGINE))
spec = importlib.util.spec_from_loader("ws_layout", loader)
engine = importlib.util.module_from_spec(spec)
loader.exec_module(engine)


class Summons(unittest.TestCase):
    """Quickshell plugin windows share one class, so — like the placeholders — they are known
    by title and summoned through the shell (Magpie, 2026-10-15, Dave's Phase 3)."""

    def test_a_magpie_window_is_summoned_by_its_title(self):
        win = {"class": "org.quickshell", "title": "🐦 Magpie — Inbox"}
        self.assertEqual(engine.launcher_for_win(win, 3),
                         "omarchy-shell shell summon magpie '{}'")

    def test_another_quickshell_window_is_not_grabbed(self):
        """The class is the whole shell's; only the titled plugin may be claimed."""
        win = {"class": "org.quickshell", "title": "Holodeck"}
        self.assertIsNone(engine.launcher_for_win(win, 3))

    def test_every_summons_key_is_a_title_prefix_not_a_class(self):
        for prefix in engine.SUMMONS:
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
        for recorded, actual in [("🐦 Magpie", "Holodeck"), ("Holodeck", "🐦 Magpie")]:
            with self.subTest(recorded=recorded, actual=actual):
                self.assertEqual(engine.assign([{"win": self.win(recorded)}],
                                               [self.win(actual)]), {})

    def test_floating_shell_windows_never_fill_another_plugin_recording(self):
        for recorded, actual in [("🐦 Magpie", "Holodeck"), ("Holodeck", "🐦 Magpie")]:
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

    def test_ordinary_app_titles_may_change(self):
        recorded = self.win("Old tab", klass="google-chrome")
        actual = self.win("New tab", "0x2", klass="google-chrome")
        self.assertEqual(engine.assign([{"win": recorded}], [actual]), {0: actual})
        self.assertEqual(engine.match_floats([recorded], [actual]), {0: actual})

    def test_the_cull_keeps_the_recorded_plugin_and_closes_the_stranger(self):
        """close_extras buckets by identity: with Magpie recorded and a stray second shell
        window on the desk, the stranger goes and Magpie stays."""
        magpie = self.win("🐦 Magpie — Inbox", "0xkeep")
        stray = self.win("Holodeck", "0xclose")
        closed = []
        with mock.patch.object(engine, "on_ws", return_value=[magpie, stray]), \
             mock.patch.object(engine, "dispatch", side_effect=lambda cmd: closed.append(cmd)), \
             mock.patch.object(engine, "wait_until", return_value=True):
            engine.close_extras(4, {"🐦 Magpie": 1})
        self.assertEqual(len(closed), 1)
        self.assertIn("0xclose", closed[0])
        self.assertNotIn("0xkeep", closed[0])

    def test_the_cull_closes_a_placeholder_before_the_real_window(self):
        """Within one identity the placeholder still goes first — the recorded window keeps
        its place (the original placeholder-removal rule, unchanged)."""
        placeholder = dict(self.win("🐦 Magpie — Inbox", "0xph"), placeholder="ab12cd")
        real = self.win("🐦 Magpie — Inbox", "0xreal")
        closed = []
        with mock.patch.object(engine, "on_ws", return_value=[placeholder, real]), \
             mock.patch.object(engine, "dispatch", side_effect=lambda cmd: closed.append(cmd)), \
             mock.patch.object(engine, "wait_until", return_value=True):
            engine.close_extras(4, {"🐦 Magpie": 1})
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


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    unittest.main()
