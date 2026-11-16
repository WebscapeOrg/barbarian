#!/usr/bin/env python3
"""The QML function-body gate (C-020, from Voyager's finding at the 12 Nov fire: qmllint is a
syntax check — a body that misspells a property name lints clean and only blows up as a
ReferenceError on a real machine, on the line that runs). Every named function body in the two
big QML files is executed in Node against stubs for EXACTLY the names that file declares — its
ids, properties, functions and imports — so any name outside that set throws ReferenceError
here, in the suite, instead of on Dave's screen.

    python3 tests/test_qml_bodies.py
"""

import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [ROOT / "plugin/Reptile.qml", ROOT / "plugin/Panel.qml"]
NODE = shutil.which("node")


def blank_strings_and_comments(text):
    """Same length as the original, with strings and comments blanked, so regex and brace
    matching never trip on prose, emoji or braces inside quotes."""
    out = list(text)
    i, n = 0, len(text)
    in_string = ""
    while i < n:
        c = text[i]
        if in_string:
            if c == "\\" and i + 1 < n:
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if c == in_string:
                in_string = ""
            if c != "\n":
                out[i] = " "
            i += 1
            continue
        if text.startswith("//", i):
            while i < n and text[i] != "\n":
                out[i] = " "
                i += 1
            continue
        if text.startswith("/*", i):
            while i < n and not text.startswith("*/", i):
                if text[i] != "\n":
                    out[i] = " "
                i += 1
            out[i] = out[i + 1] = " "
            i += 2
            continue
        if c in "'\"`":
            in_string = c
            out[i] = " "
            i += 1
            continue
        # A regex literal (Reptile's bodies do use /'/g): a / that follows an operator or a
        # keyword opens one, and its quotes must not be taken for strings.
        if c == "/":
            prev = text[:i].rstrip()
            trigger = prev[-1:] in "(,=:[!&|?{};" or prev.endswith("return") \
                or prev.endswith("match") or prev.endswith("replace") or prev.endswith("split")
            if trigger:
                out[i] = " "
                i += 1
                while i < n:
                    if text[i] == "\\":
                        out[i] = out[i + 1] = " "
                        i += 2
                        continue
                    if text[i] == "\n":
                        break    # a regex never spans lines; this was division after all
                    done = text[i] == "/"
                    out[i] = " "
                    i += 1
                    if done:
                        while i < n and text[i].isalpha():   # flags
                            out[i] = " "
                            i += 1
                        break
                continue
        i += 1
    return "".join(out)


def balanced(clean, open_index):
    """Index of the brace closing the one at open_index, or -1."""
    depth = 0
    for k in range(open_index, len(clean)):
        if clean[k] == "{":
            depth += 1
        elif clean[k] == "}":
            depth -= 1
            if depth == 0:
                return k
    return -1


def scan_source(text):
    """(functions, declared names) for a QML file: every named function with its body, and
    every id, property, function and import name the file declares."""
    clean = blank_strings_and_comments(text)
    functions = []
    for m in re.finditer(r"\bfunction\s+(\w+)\s*\(", clean):
        name = m.group(1)
        brace = clean.index("{", m.end() - 1)
        close = balanced(clean, brace)
        if close < 0:
            continue
        params_end = clean.index(")", m.end() - 1)
        params = [p.strip() for p in clean[m.end():params_end].split(",") if p.strip()]
        functions.append((name, params, text[brace + 1:close]))
    names = {m.group(1) for m in re.finditer(r"\bid:\s*(\w+)", clean)}
    names |= {m.group(1) for m in re.finditer(r"\bproperty\s+(?:readonly\s+)?[\w.<>{}\[\]]+\s+(\w+)", clean)}
    names |= {m.group(1) for m in re.finditer(r"\bproperty\s+alias\s+(\w+)", clean)}
    names |= {name for name, _, _ in functions}
    for m in re.finditer(r"^import\s+([\w.]+)(?:\s+as\s+(\w+))?", clean, re.M):
        names.add(m.group(2) or m.group(1).split(".")[-1])
    return functions, names


HARNESS = r"""
const known = new Set(__NAMES__);
function benign() {
  const handler = {
    get(target, key) {
      if (key === Symbol.toPrimitive) return () => 0;
      if (key === "toString") return () => "stub";
      if (key === "valueOf") return () => 0;
      return proxy;
    },
    apply() { return proxy; },
    construct() { return proxy; },
    has() { return true; }
  };
  const proxy = new Proxy(function () {}, handler);
  return proxy;
}
const env = {};
for (const name of known) env[name] = benign();
const failures = [];
for (const [name, params, body] of __FUNCTIONS__) {
  try {
    // The inner function is BORN inside the with-block, so exactly the declared names are
    // visible to the body; anything else is a ReferenceError. (A function created outside
    // the with and called inside it resolves in its own closure — global — and sees nothing.)
    const run = new Function("env", "args",
      "with (env) { const __f = function(" + params.join(",") + ") { " + body +
      " }; return __f(...args); }");
    run(env, params.map(benign));
  } catch (error) {
    if (error instanceof ReferenceError) failures.push(name + ": " + error.message);
    // any other exception means the body RAN and tripped on a stub — the gate's business
    // is unbound names, not stub arithmetic.
  }
}
if (failures.length) { console.log(failures.join("\n")); process.exit(1); }
console.log("bodies ok");
"""


import tempfile


def run_harness(functions, names):
    # Base-class and context properties every QML item inherits (contentY, count, model in a
    # delegate...), the QML global objects, and the one property the SHELL injects into a bar
    # widget's root (PanelHost's `bar`): none of them are the gate's business, because a typo
    # in them is not a typo the file could have caught any other way.
    extra = {"Qt", "console", "Math", "JSON", "Date", "String", "Number", "Array",
             "Boolean", "Object", "parseInt", "parseFloat", "isNaN", "undefined",
             "Accessible",
             # The shell's Ui.Panel base (panel root's own base type) provides these; a
             # Barbarian typo in one of them is indistinguishable from a base member anyway.
             "bar", "moduleName", "settings", "ipcTarget", "manageIpc", "controller",
             "opened", "panelController",
             "x", "y", "width", "height", "visible", "enabled", "opacity", "scale",
             "count", "index", "model", "parent", "children", "data", "resources",
             "state", "focus", "contentY", "contentX", "position", "implicitHeight"}
    script = (HARNESS.replace("__NAMES__", json.dumps(sorted(names | extra)))
              .replace("__FUNCTIONS__", json.dumps(
                  [[name, params, body] for name, params, body in functions])))
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as handle:
        handle.write(script)
        path = handle.name
    try:
        return subprocess.run([NODE, path], capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(path)


class QmlBodies(unittest.TestCase):
    def test_every_declared_name_resolves_or_the_body_names_it(self):
        """A ReferenceError here is a typo'd property or id — the class qmllint passes and a
        real machine hits on the line that runs."""
        for path in FILES:
            with self.subTest(file=path.name):
                functions, names = scan_source(path.read_text())
                self.assertGreater(len(functions), 40, "the scan found too little to be a gate")
                result = run_harness(functions, names)
                self.assertEqual(result.returncode, 0,
                                 f"{path.name}:\n{result.stdout}\n{result.stderr}")

    def test_the_gate_catches_a_typo_the_scanner_sees(self):
        """The gate must fail on a seeded misspelling — a green that cannot fail proves
        nothing (Voyager's screenBlankedTYPO, verbatim)."""
        functions, names = scan_source((ROOT / "plugin/Reptile.qml").read_text())
        seeded = list(functions) + [("typoProbe", ["x"], "return screenBlankedTYPO.width;")]
        result = run_harness(seeded, names)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("screenBlankedTYPO", result.stdout)


if __name__ == "__main__":
    if not NODE:
        print("test_qml_bodies: node not found — the QML body gate cannot run")
        raise SystemExit(2)
    unittest.main()
else:
    if not NODE:
        print("WARNING: node not found; the QML function-body gate will not run")
