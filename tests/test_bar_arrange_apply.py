#!/usr/bin/env python3
"""Tests for plugin/bin/bar-arrange-apply — the one thing that writes the bar's layout.

    python3 tests/test_bar_arrange_apply.py

Each test runs the real script with HOME pointing at a throwaway folder, so nothing touches the
running bar.
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "plugin/bin/bar-arrange-apply"

STOCK = {"bar": {"layout": {
    "left": [{"id": "omarchy.menu"}, {"id": "omarchy.workspaces"}],
    "center": [],
    "right": [{"id": "omarchy.clock", "format": "ddd d MMM HH:mm"}, {"id": "omarchy.power"},
              {"id": "atlas.arrange"}],
}}}


class Apply(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        (self.home / ".config/omarchy").mkdir(parents=True)
        self.shell = self.home / ".config/omarchy/shell.json"
        self.hidden = self.home / ".config/omarchy/bar-hidden.json"
        self.write(STOCK)

    def write(self, layout, hidden=None):
        self.shell.write_text(json.dumps(layout, indent=2) + "\n")
        self.hidden.write_text(json.dumps(hidden or {"left": [], "center": [], "right": []}) + "\n")

    def run_apply(self, *args):
        result = subprocess.run([str(SCRIPT), *args], capture_output=True, text=True,
                                env={**os.environ, "HOME": str(self.home)})
        return result

    def layout(self):
        return json.loads(self.shell.read_text())["bar"]["layout"]

    def ids(self, lane):
        return [entry["id"] for entry in self.layout()[lane]]

    def parked(self):
        return json.loads(self.hidden.read_text())

    def config(self):
        return json.loads(self.shell.read_text())

    def install_manifest(self, wid, kinds):
        plugin = self.home / ".config/omarchy/plugins" / wid
        plugin.mkdir(parents=True)
        manifest = {"schemaVersion": 1, "id": wid, "name": wid, "version": "1.0.0",
                    "kinds": kinds, "entryPoints": {}}
        (plugin / "manifest.json").write_text(json.dumps(manifest) + "\n")

    def show_entry(self, entry, plugins=None):
        layout = copy.deepcopy(STOCK)
        layout["bar"]["layout"]["right"].insert(0, entry)
        if plugins is not None:
            layout["plugins"] = plugins
        self.write(layout)

    def test_a_strip_that_is_not_changing_lane_stays_where_it_stands(self):
        """A stock bar's menu button must not be pushed out of the corner by a desk change."""
        self.run_apply("R:omarchy.power", "R:omarchy.clock", "WS:omarchy.workspaces:left")
        self.assertEqual(self.ids("left"), ["omarchy.menu", "omarchy.workspaces"])
        self.assertEqual(self.ids("right")[:2], ["omarchy.power", "omarchy.clock"])

    def test_a_strip_changing_lane_leads_its_new_one(self):
        self.run_apply("R:omarchy.clock", "R:omarchy.power", "WS:omarchy.workspaces:center")
        self.assertEqual(self.ids("left"), ["omarchy.menu"])
        self.assertEqual(self.ids("center"), ["omarchy.workspaces"])

    def test_entries_travel_whole(self):
        self.run_apply("R:omarchy.power", "R:omarchy.clock", "WS:omarchy.workspaces:left")
        clock = [e for e in self.layout()["right"] if e["id"] == "omarchy.clock"][0]
        self.assertEqual(clock["format"], "ddd d MMM HH:mm")

    def test_hiding_parks_the_whole_entry_and_showing_brings_it_back(self):
        self.run_apply("R:omarchy.clock:hidden", "R:omarchy.power", "WS:omarchy.workspaces:left")
        self.assertNotIn("omarchy.clock", self.ids("right"))
        parked = self.parked()["right"]
        self.assertEqual(parked[0]["entry"]["format"], "ddd d MMM HH:mm")
        self.run_apply("R:omarchy.clock", "R:omarchy.power", "WS:omarchy.workspaces:left")
        self.assertEqual(self.ids("right")[:2], ["omarchy.clock", "omarchy.power"])
        self.assertEqual(self.parked()["right"], [])

    def test_hiding_a_service_panel_or_overlay_keeps_the_plugin_enabled(self):
        for kind in ("service", "panel", "overlay"):
            with self.subTest(kind=kind):
                wid = f"test.{kind}"
                entry = {"id": wid, "refreshIntervalSec": 120, "nested": {"keep": True}}
                self.show_entry(entry)
                self.install_manifest(wid, ["bar-widget", kind])
                result = self.run_apply(f"R:{wid}:hidden")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.config()["plugins"], [{"id": wid}])
                self.assertEqual(self.parked()["right"][0]["entry"], entry)

    def test_hiding_a_bar_only_widget_adds_no_plugin_entry(self):
        entry = {"id": "test.widget", "setting": "kept"}
        self.show_entry(entry)
        self.install_manifest(entry["id"], ["bar-widget"])
        result = self.run_apply("R:test.widget:hidden")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("plugins", self.config())

    def test_a_non_string_kind_member_does_not_hide_a_service_kind(self):
        entry = {"id": "test.service"}
        self.show_entry(entry)
        self.install_manifest(entry["id"], ["bar-widget", "service", None])
        result = self.run_apply("R:test.service:hidden")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.config()["plugins"], [{"id": "test.service"}])

    def test_a_manifest_omarchy_rejects_adds_no_plugin_entry(self):
        entry = {"id": "test.service"}
        self.show_entry(entry)
        self.install_manifest(entry["id"], ["bar-widget", "service"])
        manifest = self.home / ".config/omarchy/plugins/test.service/manifest.json"
        manifest.write_text(json.dumps({"id": "test.service", "kinds": ["service"]}) + "\n")
        result = self.run_apply("R:test.service:hidden")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("plugins", self.config())

    def test_a_numeric_manifest_id_matches_its_string_bar_entry(self):
        entry = {"id": "123"}
        self.show_entry(entry)
        self.install_manifest("123", ["bar-widget", "service"])
        manifest_path = self.home / ".config/omarchy/plugins/123/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["id"] = 123
        manifest_path.write_text(json.dumps(manifest) + "\n")
        result = self.run_apply("R:123:hidden")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.config()["plugins"], [{"id": "123"}])

    def test_a_boolean_schema_version_is_rejected(self):
        entry = {"id": "test.service"}
        self.show_entry(entry)
        self.install_manifest(entry["id"], ["bar-widget", "service"])
        manifest_path = self.home / ".config/omarchy/plugins/test.service/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["schemaVersion"] = True
        manifest_path.write_text(json.dumps(manifest) + "\n")
        result = self.run_apply("R:test.service:hidden")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("plugins", self.config())

    def test_an_existing_plugin_entry_is_preserved_without_a_duplicate(self):
        entry = {"id": "test.service", "setting": "bar copy"}
        existing = {"id": "test.service", "setting": "plugin copy"}
        self.show_entry(entry, plugins=[existing, {"id": "test.other"}])
        self.install_manifest(entry["id"], ["bar-widget", "service"])
        result = self.run_apply("R:test.service:hidden")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.config()["plugins"], [existing, {"id": "test.other"}])

    def test_reapplying_an_existing_hide_repairs_its_missing_plugin_entry(self):
        entry = {"id": "test.service", "setting": "kept"}
        self.write(STOCK, hidden={"left": [], "center": [],
                                  "right": [{"index": 0, "entry": entry}]})
        self.install_manifest(entry["id"], ["bar-widget", "service"])
        result = self.run_apply("R:test.service:hidden")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.config()["plugins"], [{"id": entry["id"]}])

    def test_deleting_a_hidden_service_removes_its_plugin_entry_too(self):
        entry = {"id": "test.service", "setting": "kept"}
        self.show_entry(entry)
        self.install_manifest(entry["id"], ["bar-widget", "service"])
        self.run_apply("R:test.service:hidden")
        self.assertEqual(self.config()["plugins"], [{"id": "test.service"}])
        result = self.run_apply("DEL:test.service")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.config()["plugins"], [])
        self.assertEqual(self.parked()["right"], [])

    def test_an_id_it_does_not_recognise_changes_nothing(self):
        before = self.shell.read_text()
        result = self.run_apply("R:omarchy.clock", "R:nobody.here")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.shell.read_text(), before)

    def test_uninstalling_takes_the_entry_out_of_its_lane(self):
        """DEL:<id> is the panel's uninstall: the entry goes, everything else keeps its place."""
        self.run_apply("R:omarchy.clock", "DEL:omarchy.power")
        self.assertEqual(self.ids("right"), ["omarchy.clock", "atlas.arrange"])

    def test_uninstalling_takes_a_parked_entry_out_of_the_sidecar(self):
        parked_only = {"bar": {"layout": {
            "left": [{"id": "omarchy.menu"}, {"id": "omarchy.workspaces"}],
            "center": [],
            "right": [{"id": "omarchy.clock", "format": "ddd d MMM HH:mm"},
                      {"id": "atlas.arrange"}],
        }}}
        self.write(parked_only, hidden={"left": [], "center": [],
                                        "right": [{"index": 1, "entry": {"id": "omarchy.power"}}]})
        self.run_apply("R:omarchy.clock", "DEL:omarchy.power")
        self.assertEqual(self.parked()["right"], [])
        self.assertEqual(self.ids("right"), ["omarchy.clock", "atlas.arrange"])

    def test_uninstalling_an_unknown_id_changes_nothing(self):
        before = self.shell.read_text()
        result = self.run_apply("R:omarchy.clock", "DEL:nobody.here")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.shell.read_text(), before)

    def test_a_second_writer_waits_for_the_first(self):
        """Another plugin's uninstaller may run while the panel writes: one at a time."""
        lock = self.home / ".config/omarchy/.bar-arrange-apply.lock"
        before = self.shell.read_text()
        holder = subprocess.Popen(["flock", str(lock), "sleep", "3"])
        try:
            for _ in range(50):
                if lock.exists():
                    break
                subprocess.run(["sleep", "0.05"])
            result = subprocess.run(["timeout", "1", str(SCRIPT), "R:omarchy.clock:hidden"],
                                    capture_output=True, text=True,
                                    env={**os.environ, "HOME": str(self.home)})
        finally:
            holder.kill()
            holder.wait()
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertEqual(self.shell.read_text(), before)
        self.run_apply("R:omarchy.clock:hidden")
        self.assertNotIn("omarchy.clock", self.ids("right"))

    def test_the_panel_never_drops_an_entry_it_does_not_list(self):
        """Barbarian's own widget is never listed; it must keep its place at the lane's end."""
        self.run_apply("R:omarchy.power", "R:omarchy.clock", "WS:omarchy.workspaces:left")
        self.assertIn("atlas.arrange", self.ids("right"))


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    unittest.main()
