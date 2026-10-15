#!/usr/bin/env python3
"""Tests for the engine's launch rules — the summons that reopens Quickshell plugin windows.

    python3 tests/test_ws_layout.py

The engine has no .py suffix and lives beside the plugin's scripts, so it loads by path;
importing it runs no command (everything subprocess-shaped happens inside functions, called
only by the real commands). Nothing here touches the shell, the bar or any live file.
"""
import importlib.util
from importlib.machinery import SourceFileLoader
import pathlib
import sys
import unittest

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


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    unittest.main()
