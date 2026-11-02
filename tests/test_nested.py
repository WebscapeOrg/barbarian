#!/usr/bin/env python3
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest


HARNESS = Path(__file__).resolve().parent / "nested/nested"


class NestedIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="barbarian-nested-test-")
        self.addCleanup(self.temporary.cleanup)
        self.runtime = Path(self.temporary.name)
        self.work = self.runtime / "barbarian-nested"
        self.work.mkdir()
        self.trace = self.runtime / "dispatched"
        binaries = self.runtime / "bin"
        binaries.mkdir()
        for command in ("hyprctl", "qs", "wtype", "grim"):
            stub = binaries / command
            stub.write_text('#!/bin/sh\nprintf dispatched > "$NESTED_TEST_TRACE"\n')
            stub.chmod(0o755)
        self.environment = {**os.environ, "XDG_RUNTIME_DIR": str(self.runtime),
                            "HYPRLAND_INSTANCE_SIGNATURE": "main_instance",
                            "WAYLAND_DISPLAY": "wayland-1",
                            "NESTED_TEST_TRACE": str(self.trace),
                            "PATH": str(binaries) + os.pathsep + os.environ["PATH"]}

    def selectors(self, signature="test_instance", display="wayland-2"):
        (self.work / "sig").write_text(signature)
        (self.work / "display").write_text(display)

    def socket(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = socket.socket(socket.AF_UNIX)
        self.addCleanup(connection.close)
        connection.bind(str(path))

    def run_harness(self, *arguments):
        return subprocess.run([str(HARNESS), *arguments], env=self.environment,
                              capture_output=True, text=True, timeout=5)

    def assert_refused(self):
        for arguments in (("hypr", "reload"), ("ipc", "features"), ("key", "-k", "Escape"),
                          ("pointer", "move", "1", "1"), ("shot", str(self.runtime / "shot.png")),
                          ("engine", "reptile-feature", "off", "hide_on_close"), ("stop",)):
            with self.subTest(arguments=arguments):
                result = self.run_harness(*arguments)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse(self.trace.exists())

    def test_missing_selectors_never_dispatch(self):
        self.assert_refused()

    def test_empty_selectors_never_dispatch(self):
        self.selectors("", "")
        self.assert_refused()

    def test_missing_sockets_never_dispatch(self):
        self.selectors()
        self.assert_refused()

    def test_main_session_selectors_never_dispatch(self):
        self.selectors("main_instance", "wayland-1")
        self.socket(self.runtime / "hypr/main_instance/.socket.sock")
        self.socket(self.runtime / "wayland-1")
        self.assert_refused()

    def test_malformed_selectors_never_dispatch(self):
        self.selectors("../main_instance", "../wayland-1")
        self.assert_refused()

    def test_valid_isolated_session_dispatches(self):
        self.selectors()
        self.socket(self.runtime / "hypr/test_instance/.socket.sock")
        self.socket(self.runtime / "wayland-2")
        result = self.run_harness("hypr", "version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.trace.exists())


if __name__ == "__main__":
    unittest.main()
