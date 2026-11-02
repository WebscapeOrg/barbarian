# C-002 independent hostile verification

Reviewer: `/root/feature_verifier`. Scope: the uncommitted Reptile switches, engine guards,
shortcut updates, QML controls and installer. App code is owned by the parent agent; this
review changes only this record. No live desktop mutation or service restart is permitted.

Final independent assessment: approved within the reviewed code/test scope. V-001 through
V-007 are resolved. The seven original Python suites and offscreen Qt suite passed, followed
by the new harness suite and focused UI/cleanup resolution probes. No remaining code blocker
was found in the final changes.
The parent's operated native UI checks, Enterprise automatic callers and live deployment
are separate evidence boundaries; this report does not claim the running desktop is updated.

## Confirmed findings

### V-001 — resolved: new tab and Retry buttons omitted native keyboard activation

- Evidence: the new `Button` delegates in `plugin/Reptile.qml`'s tab strip and the Features
  Retry button do not set `focusable`. `/usr/share/omarchy/shell/Ui/Button.qml` defaults
  `focusable` to false and uses it to gate `activeFocusOnTab`, Enter/Space handlers and
  visible focus styling.
- Effect: the advertised native controls cannot be reached or activated through normal
  Tab/Enter keyboard navigation. This also removes the keyboard recovery route after a
  settings load failure.
- Resolution requested: set `focusable: true` and operate the tab/error path with the keyboard.
- Resolution verified in source: tab and Retry buttons set `focusable: true`; Ctrl+Tab uses
  `Qt.ApplicationShortcut` across the panel window boundary. Both also expose accessibility
  press actions. The parent reports successful native Ctrl+Tab then Space operation; that
  operated result is the parent's evidence, not an independently repeated desktop test.

### V-002 — resolved: quick-app toggle failures were invisible on the Quick apps tab

- Evidence: the footer's new `Toggle` calls `root.setFeature("hide_on_close", ...)`.
  `featureSetProc` writes failures to `root.featureSaveError`, and the only visual consumer
  is the feedback row inside `featuresTab`, whose visibility requires `root.tab === 2`.
- Effect: while on Quick apps, a failed shortcut regeneration/reload leaves the switch unchanged
  without showing why. The previous `qa.run()` path displayed the returned error in `qa.note`.
- Resolution requested: surface the shared saving/error state on Quick apps too.
- Resolution verified in source: Quick apps now displays the shared pending/error state,
  and errors have the accessibility AlertMessage role. Failure rendering belongs to the
  parent's operated pass.

### V-003 — resolved: concurrent app-list generation could reinstate disabled shortcuts

- Evidence: `quick-app:197–255` reads the feature at the beginning of `generate()`, then writes
  its resulting Lua later. Only `reptile_features.set_feature()` takes `features.lock`; the
  app-list operations and `generate()` do not. The `.tmp` path is shared too.
- Isolated reproduction: loaded the engines through the new test fixture, with private
  settings and generated paths; intercepted the first generation at its `os.makedirs`
  boundary and completed `set_feature("quick_apps", False)` plus its generation before
  allowing the older generation to continue. All compositor operations were mocked.
- Result: the saved `quick_apps` value was false, while the final generated file still
  contained `o.bind(`. Both conditions were asserted and the probe exited 0.
- Effect: an app edit begun before an off action can restore the old shortcut overrides.
  The direct toggle command is guarded, so it will swallow the key instead of opening the app;
  the ordinary shortcut displaced by that quick app remains unavailable despite the off state.
- Resolution requested: serialize feature changes with app-list changes and binding generation
  across the whole read/write/reload operation; avoid locking a parent while a child waits for
  the same lock. Use unique temporary names for generated bindings.
- Resolution independently verified: generation, app-list mutations and feature changes
  now use a shared reentrant thread/process lock and unique atomic temporary writes.
  The two-thread race, separate-process contention and timeout/rollback probes below passed.

### V-004 — resolved: turning layout messages off still sent the completion IPC

- Evidence: `card()` checks `layout_messages`, but `card_down()` does not. `restore()`'s
  `say()` marks the card as shown even when `card()` returns immediately, so its finally
  block still calls `reptile_ipc("laid")`.
- Isolated reproduction: disabled layout messages, mocked the restore body and recorded IPC
  calls around `restore(1)`. The exact result was `[call('laid')]`; the probe exited 0.
- Effect: the switch hides the presentation but does not completely remove the message
  feature's shell IPC. That weakens its usefulness for isolating the source of a desktop fault.
- Resolution requested: suppress the completion IPC when the message feature is off too;
  the QML watcher already hides a previously visible card on an off transition.
- Resolution verified in source: `card_down()` now checks `layout_messages` before sending
  `laid`. The final feature regression suite exercises both `card()` and `card_down()`.

## Revised implementation checks

### UI/harness follow-up: V-005 — resolved: shortcut capture scrolled away from its recorder

- Evidence: `plugin/Reptile.qml:1116` focuses `captureArea`, declared as a zero-size Item
  near the start of QuickAppsTab at lines 1202–1204. The new focus listener at lines 2557–2568
  maps every focused descendant to a scroll position, including this invisible key sink.
- Effect: when the app list makes the Quick apps tab scroll, pressing the shortcut recorder
  moves focus to the invisible item at the top and scrolls the visible recorder/instructions
  away. The new scrolling behavior introduces this regression.
- Independent isolated Qt probe: focused a recorder at y=600 in a 180-high viewport, then
  its zero-size capture sink, using the same focus listener. `contentY` changed from 460 to 0
  and the recorder fell outside the viewport. All probe assertions passed; exit 0.
- Requested resolution: map capture focus to the visible shortcut recorder, while retaining
  descendant focus handling for actual controls.
- Independent resolution retest extracted the current `scrollTarget()` and focus listener
  directly from Reptile.qml into an offscreen Qt fixture. It verified capture preserves the
  recorder's position, capture begun while scrolled elsewhere reveals the recorder, ordinary
  controls still scroll into view, and outside focus leaves the scroll position unchanged.
  Qt reported 6 passes including setup/cleanup, zero failures; exit 0.

### UI/harness follow-up: V-006 — resolved: the engine harness dispatched without a nested target

- Evidence: `tests/nested/nested`'s `nested_env()` places reads of the saved signature and
  display inside `export` command substitutions. When those reads fail, `export` still
  returns success. The new `engine` action proceeds with both selectors empty.
- Independent isolated reproduction: ran `engine reptile-feature off hide_on_close` with a
  fresh private XDG_RUNTIME_DIR and a stub `hyprctl`. The command printed missing-session
  errors but exited 0; the stub recorded `reload` with an empty HYPRLAND_INSTANCE_SIGNATURE
  and empty WAYLAND_DISPLAY. No real compositor command ran.
- Effect: a test invoked before `nested start`, or after its state is removed, can reach a
  default compositor rather than refusing. This was an isolation blocker for the new harness.
- Requested resolution: read selectors separately, reject missing/empty selectors and absent
  sockets, and only then export them. No engine/pointer/IPC action should proceed without a
  verified nested target.
- Independent resolution retest exercised 10 invalid target fixtures: missing files, empty
  selectors, malformed selectors, either selector equal to the inherited main session and
  either required socket absent. Every case exited 1 before executing the engine and called
  no compositor stub. A valid private target with two bound Unix sockets exited 0 and called
  only the stub, with the correct private HOME and selectors. The probe script exited 0.

### UI/harness follow-up: V-007 — resolved: cleanup bypassed the validated target guard

- This is a pre-existing hazard in the same harness, found while checking V-006's coverage.
  `stop)` does not call `nested_env()`. An empty saved signature is accepted by its `cat` read,
  passed to `hyprctl dispatch hl.dsp.exit()`, and used as the runtime-directory suffix.
- Independent isolated reproduction used a private XDG_RUNTIME_DIR, an empty sig file and
  stubs for qs, hyprctl, sleep and rm. The harness exited 0. The log recorded the compositor
  exit request with an empty signature followed by `rm -rf <private-runtime>/hypr/`, removing
  the directory suffix entirely. The stubs performed no real exit or deletion.
- Effect: an invalid cleanup request can target the default compositor and the whole runtime
  socket tree. The safety check must precede cleanup mutations as well as test operations.
- Requested resolution: require the same validated isolated session before stopping anything,
  then retain and use its nonempty validated signature for exactly its own runtime directory.
- Resolution: stop now validates the target before any command, retains the validated
  signature, refuses to move files while its compositor socket still exists, and moves its
  two directories into a unique Trash directory instead of deleting them.
- Independent resolution probe used private HOME/runtime paths and stub commands. An empty
  signature exited 1 with no dispatch; a still-present socket exited 1 with all files kept;
  a simulated completed private compositor exited 0 and moved only its own work and runtime
  directories into private Trash. An unrelated runtime-directory sentinel survived every
  case. The probe script exited 0; no real compositor/process action ran.

### Previously completed checks

- V-001: the current code sets the new tab/Retry buttons `focusable: true` and gives Ctrl+Tab
  shortcuts `Qt.ApplicationShortcut` context. The parent reports that native nested Ctrl+Tab
  followed by Space changed and persisted the first feature. That operated result is the
  parent's evidence; this reviewer confirmed the source change.
- V-002: Quick apps now has a visible status/error text bound to the shared feature request.
  Source inspection confirms this fixes the missing feedback consumer; failure rendering is
  part of the parent's operated pass.
- V-003: independent retest used two real threads. An old generation was held after reading
  the app list while a second thread attempted to disable Quick apps. After release, both
  completed, the saved switch was off, and the generated file contained no overrides.
  The shared reentrant lock and unique temporary writes resolve the reproduced race.
- A separate-process contention probe held the file lock in the reviewer process, attempted a
  change from another Python process, and verified it failed with the explicit busy message
  without writing settings. After releasing the lock, the same command succeeded and preserved
  unrelated settings. This checks the interprocess half of the lock, not just its thread half.
- Injecting `TimeoutExpired` into both desktop calls restored the previous quick-app choice and
  reported that the shortcut rollback could not complete. No traceback or false successful
  rollback was observed.
- The initial feature suite passed 26 tests during review. The final independent run below
  supersedes that intermediate result and includes 30 feature tests.
- A private installer fixture installed all 11 Caboodle manifests and the executable helper.
  The actual installed helper then completed 44 off/status/on/status round trips with matching
  ids and boolean states. Desktop commands were confined to the fixture's stub PATH.

### Other UI/harness follow-up checks

- Inspected the 600×600 logical desktop screenshot `quick-tab-wrapped.png`. Cancel and Save
  now sit within their own row; the shortcut control and manual-entry action remain distinct
  and the form has visible spacing. No extra layout defect was confirmed in that image.
- The focused-descendant check uses the actual QQuickWindow rather than the outer bar object.
  It rejects focus outside QuickAppsTab. Native SearchableDropdown popups live in the window
  overlay, so their search/list focus is not incorrectly mapped into the scroller.
- Tab and Retry accessibility press actions call the same clicked signals as pointer and
  keyboard activation. Both retain focusable=true and their semantic roles.
- Read the current private panel log. It contained no Connections, TypeError or ReferenceError
  warning; its host-portal registration warning is unrelated to these changes. This was a
  read of the parent's running test log, not an independently launched native UI session.
- Read `tests/nested/reptile.qml`: its IPC methods act on its own Reptile instance and its
  theme method changes in-process colors. No extra filesystem write or service action was
  introduced by that probe. The new engine wrapper keeps HOME private, but V-006 shows that
  private HOME alone is not enough to guarantee a private compositor target.
- The adaptive pointer extents now round up before dispatch. Independently extracted and
  evaluated the current jq expression with a 3440×1440 output at scale 1.5: it returned integer
  extents 2294×960, which the pointer helper accepts. The probe exited 0.
- The light-theme probe now clears its in-process shellValues before assigning the base
  palette. The native Color singleton exposes that as an ordinary property with no persistence
  handler; the change adds no config write or service action.

## Isolated checks completed

- A standalone offscreen Quickshell probe started with `features.json` absent, then created it
  after the FileView watcher was running. It received `FEATURE_CHANGED`, reloaded the new JSON,
  and exited 0. The concern that first creation would not propagate to other panels is rejected.
- An installer fixture with `.config/caboodle/switches` deliberately occupied by a file confirmed
  that the shell is restarted even when manifest creation fails. The initial suspected stopped-shell
  failure is rejected. It initially exited 0 despite the manifest failure. The installer now
  reports the manifest failure and exits 1 after the shell recovery path. The final installer
  suite includes the failing-manifest fixture and passed all 18 tests.
- Inspected the parent's first rendered Features screenshot. The rows and their descriptions have
  clear whitespace; the fixed list viewport shows the first 8 of 11 features. That image alone
  does not establish keyboard scrolling or discoverability of the lower rows.
- Reviewed restore subsets, including tree projection when apps are not opened, disabled
  floating-window changes, manual/automatic/on-visit gates and preserved saved layouts.
  No further window-action defect was confirmed. The final Python suites exercise these
  decisions using private fixtures and mocked compositor calls.
- Reviewed the external automatic restore wrappers and identified their remaining final-focus
  action and misleading replay log when an engine call is skipped. The parent reports that
  Enterprise is adding an early off check before waits/window reads/focus, while retaining
  the engine's `--automatic` guard. Those scripts and their deployment are outside this repo;
  the parent must verify the integration before claiming complete automatic isolation.

## Final independent suite run

Each command ran directly, without piping away its exit status. All results were read after
completion. The Python total is 112 tests. Qt reported 46 passed, zero failed, zero skipped
and zero blacklisted.

| Command | Tests | Exit code |
| --- | ---: | ---: |
| `python3 tests/test_ws_layout.py` | 14 | 0 |
| `python3 tests/test_install.py` | 18 | 0 |
| `python3 tests/test_bar_arrange_apply.py` | 9 | 0 |
| `python3 tests/test_plugin_uninstall.py` | 13 | 0 |
| `python3 tests/test_ws_renumber.py` | 17 | 0 |
| `python3 tests/test_ws_bg.py` | 11 | 0 |
| `python3 tests/test_reptile_features.py` | 30 | 0 |
| `QT_QPA_PLATFORM=offscreen /usr/lib/qt6/bin/qmltestrunner -input tests -o -,txt` | 46 | 0 |

`git diff --check` also exited 0 after the code review. Qt used version 6.12.0. Its existing
DeskRow/Reorder suites verify drag-and-drop regressions; they do not automate the new native
Features tab. All tests and additional probes were isolated from Dave's live configuration,
desktop windows and services.

After the UI/harness follow-up, `python3 tests/test_nested.py` independently passed 6 tests,
exit 0. These include 35 refusal subcases across engine, pointer, key, screenshot, IPC, direct
compositor and cleanup actions, plus a valid private target. The cumulative Python total is
118 across eight suites; the original seven ran before the final UI-only edits.
The extracted current focus functions passed another 6 isolated Qt checks, and the cleanup
probe passed the three cases documented under V-007. `bash -n tests/nested/nested` and
`git diff --check` both exited 0 on the final revision.

## Evidence limits

V-001 through V-007 are resolved within the reviewed source and isolated checks. This reviewer
did not operate the parent's nested compositor, install the live build, restart the shell or
verify deployed automatic callers. The parent's final report must distinguish its operated
evidence from this independent source/test result. The 112-test Python run and 46-check Qt run
precede the UI-only follow-up; the new harness suite and focused resolution probes were run
after it. No unresolved blocker remains in the reviewed code. This approval does not assert
that the live shell or external automatic callers have been updated.
