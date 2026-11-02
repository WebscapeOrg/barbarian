"""Persistent Reptile switches, shared by the panel and both command-line engines."""

import fcntl
import functools
import importlib.util
from importlib.machinery import SourceFileLoader
from contextlib import contextmanager
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

DIRECTORY = Path.home() / ".config/omarchy/workspace-layout"
SETTINGS_FILE = DIRECTORY / "features.json"
QUICK_APPS_FILE = DIRECTORY / "quick-apps.json"

FEATURES = [
    {"key": "restore_layouts", "label": "Restore desk layouts", "group": "Desk layouts",
     "description": "Put windows back with HYPER+R, at login or after edits."},
    {"key": "automatic_restore", "label": "Restore at login", "group": "Desk layouts",
     "requires": "restore_layouts",
     "description": "Restore saved desks at login and during automatic recovery."},
    {"key": "apply_on_visit", "label": "Apply edits on desk visit", "group": "Desk layouts",
     "requires": "restore_layouts",
     "description": "Apply new layout edits the next time you visit that desk."},
    {"key": "open_apps", "label": "Reopen missing apps", "group": "Desk layouts",
     "requires": "restore_layouts",
     "description": "Launch missing apps when restoring a desk."},
    {"key": "close_extras", "label": "Close extra windows", "group": "Desk layouts",
     "requires": "restore_layouts",
     "description": "Close windows that are not in the saved layout during restore."},
    {"key": "floating_windows", "label": "Restore floating windows", "group": "Desk layouts",
     "requires": "restore_layouts",
     "description": "Open and position saved floating windows. Off leaves them alone."},
    {"key": "placeholders", "label": "Missing-window placeholders", "group": "Desk layouts",
     "description": "Show a replacement window when an app cannot reopen. Off removes placeholders."},
    {"key": "layout_messages", "label": "Layout messages", "group": "Desk layouts",
     "description": "Show progress and explanations while restoring a desk."},
    {"key": "columns", "label": "Equal columns", "group": "Desk layouts",
     "description": "Let HYPER+3 arrange the current windows side by side."},
    {"key": "quick_apps", "label": "Quick apps", "group": "Quick apps",
     "description": "Use app shortcuts and hide apps. Off brings hidden apps to this desk."},
    {"key": "hide_on_close", "label": "Hide quick apps on close", "group": "Quick apps",
     "requires": "quick_apps",
     "description": "SUPER+W hides quick apps. Off closes them normally."},
]
DEFAULTS = {feature["key"]: True for feature in FEATURES}
_thread_lock = threading.RLock()
_lock_held = False


class SettingsError(Exception):
    pass


def read_object(path):
    try:
        with open(path) as stream:
            value = json.load(stream)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        raise SettingsError(f"Could not read {path.name}: {error}") from error
    if not isinstance(value, dict):
        raise SettingsError(f"{path.name} must contain an object.")
    return value


def read():
    stored = read_object(SETTINGS_FILE)
    values = dict(DEFAULTS)
    if "hide_on_close" not in stored:
        legacy = read_object(QUICK_APPS_FILE).get("hide_on_close", True)
        if isinstance(legacy, bool):
            values["hide_on_close"] = legacy
    for key in DEFAULTS:
        if key not in stored:
            continue
        if not isinstance(stored[key], bool):
            raise SettingsError(f"The {key} setting must be on or off.")
        values[key] = stored[key]
    return values


def enabled(key):
    try:
        return read()[key]
    except SettingsError:
        return False


def atomic_write(path, body):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.stem + "-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write(values):
    atomic_write(SETTINGS_FILE, json.dumps(values, indent=2) + "\n")


@contextmanager
def settings_lock():
    global _lock_held
    if not _thread_lock.acquire(timeout=0.5):
        raise SettingsError("Another feature change is still saving. Try again in a moment.")
    try:
        if _lock_held:
            yield
            return
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE.with_suffix(".lock"), "a") as lock:
            deadline = time.monotonic() + 0.5
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise SettingsError("Another feature change is still saving. Try again in a moment.")
                    time.sleep(0.02)
            _lock_held = True
            try:
                yield
            finally:
                _lock_held = False
    finally:
        _thread_lock.release()


def synchronized(function):
    @functools.wraps(function)
    def call(*arguments, **keywords):
        with settings_lock():
            return function(*arguments, **keywords)
    return call


@functools.lru_cache(maxsize=1)
def shortcut_engine():
    loader = SourceFileLoader("_reptile_quick_app", str(Path(__file__).with_name("quick-app")))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def sync_shortcuts(release_hidden=False):
    engine = shortcut_engine()
    if release_hidden:
        engine.release_hidden()
    engine.generate(force_reload=True)


def set_feature(key, value):
    if key not in DEFAULTS or not isinstance(value, bool):
        raise SettingsError("Choose a known feature and an on or off value.")
    with settings_lock():
        previous = read()
        if previous[key] == value:
            return previous
        stored = read_object(SETTINGS_FILE)
        write({**stored, **previous, key: value})
        if key in ("quick_apps", "hide_on_close"):
            try:
                sync_shortcuts(release_hidden=key == "quick_apps" and not value)
            except (SettingsError, OSError) as error:
                write({**stored, **previous})
                try:
                    sync_shortcuts()
                except (SettingsError, OSError):
                    raise SettingsError(f"{error} The saved choice was restored, but shortcuts could not be restored. Try again.") from error
                raise SettingsError(f"{error} Your previous choice was kept.") from error
        return read()


def status(key):
    feature = next((item for item in FEATURES if item["key"] == key), None)
    if feature is None:
        raise SettingsError("Choose a known Reptile feature.")
    values = read()
    summary = feature["description"]
    requirement = feature.get("requires")
    if requirement and not values[requirement]:
        parent = next(item["label"] for item in FEATURES if item["key"] == requirement)
        summary += f" Paused while {parent} is off."
    return {"id": "reptile-" + key.replace("_", "-"), "on": values[key], "summary": summary}


def install_manifests(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for feature in FEATURES:
        key = feature["key"]
        identifier = "reptile-" + key.replace("_", "-")
        manifest = {"id": identifier, "title": feature["label"], "group": "Reptile",
                    "description": feature["description"], "owner": "@barbarian",
                    "docs": "https://github.com/WebscapeOrg/barbarian#reptile-features",
                    "status": ["reptile-feature", "status", key],
                    "on": ["reptile-feature", "on", key], "off": ["reptile-feature", "off", key]}
        body = json.dumps(manifest, indent=2) + "\n"
        path = directory / (identifier + ".json")
        if path.exists() and path.read_text() == body:
            continue
        atomic_write(path, body)


def command(arguments):
    try:
        if arguments:
            if len(arguments) != 2 or arguments[1] not in ("true", "false"):
                raise SettingsError("Use features [name true|false].")
            set_feature(arguments[0], arguments[1] == "true")
        print(json.dumps({"values": read(), "features": FEATURES}))
        return 0
    except (SettingsError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
