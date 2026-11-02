# C-002 follow-up: per-app Super+W verification

Independent verifier: `/root/feature_verifier`. Implementation owner: `/root`.
Review target: `/home/anotherdave/.local/state/barbarian/per-app-super-w`, branch
`per-app-super-w`, based on `a61f17f`. Approved within the reviewed source, isolated tests
and rendered evidence. S-001 through S-003 are resolved; no shipping blocker remains.
Live installation and verification remain the implementation owner's work.

Dave asked: “Id like the hide quick apps with super w to be per quick app instead of global.”

## Scope and boundaries

Review the change from the global hide-on-close preference to a choice on each quick app:
migration of existing choices, strict saved values, prefix matching, generated shortcuts,
transaction rollback, feature combinations, removal of the global control/manifest,
and the new control's focus, draft retention and error feedback.

The verifier may write this report and private test fixtures only. No app source edits, live
settings changes, compositor actions, installs, restarts, notifications or deployment are
authorized for this pass. The implementation owner retains delivery and task ownership.

## Baseline

The original engine routes Super+W through `close-or-hide` only when the global choice and
Quick apps are enabled. Its close handler chooses the first matching prefix in list order.
The original Quick apps tab has a single global footer toggle. Per-app behavior therefore
requires checking both the action and the generated shortcut, as well as the stored value.

## Findings

### S-001 — resolved: an older app-list result could reverse the displayed switch

The initial patch at `plugin/Reptile.qml:997` started an app-list load without coordinating
it with the new per-app mutation. `listProc` assigned both `qa.model` and `qa.closeChoices`
when its output arrived (initial patch line 1247), while `closeProc` independently updated
the saved choice (initial patch line 1276). A later list response could overwrite that
successful result and rebuild the focused card. Reopening the panel or changing tabs
started this read while existing cards remained usable.

An isolated two-thread probe of the actual current Python engine paused `cmd_list` after
it read the app list, saved `false` with `cmd_hide_on_close`, then allowed the list to
finish. The saved file and mutation response were both `false`; the later list response
was `true`. The probe exited 0. The initial QML assignment accepted that stale value.
No real compositor operation ran: the generator's desktop command was mocked and every
path was private.

The implementation now disables mutations while a list read runs and defers new reads
while a close-choice save runs. It drains deferred reads afterwards. Per-app booleans are
kept outside the Repeater model, and a refresh replaces that model only when other row
data changed. An offscreen fixture extracted the actual revised functions/exit handlers
and passed seven behavioral checks plus setup/cleanup, exit 0. This verifies both ordering
directions, duplicate activation prevention, stale-read avoidance, delegate/focus/draft
retention, failed saves, malformed acknowledgements and failed reads.

### S-002 — resolved: the paused parent setting was no longer explained

The initial row at `plugin/Reptile.qml:1458` said “Hide with SUPER+W” and “Off closes this app
normally” even when the Quick apps feature was off. The old footer's explanation of that
state had been removed. The engine correctly closed normally while Quick apps was off, so
an on per-app switch described behavior that was paused. This was a feedback defect, not a backend
failure; the disabled-engine cases in the independent Lua matrix behaved correctly.

The revised description explicitly says when Quick apps is paused in Features, or when its
status is unavailable. The saved per-app value remains editable. Source verification passed;
the independently viewed native paused-state screenshot shows the explanation beneath
each app's switch.

### S-003 — resolved: a damaged app list prevented disabling Quick apps

The new strict `read_list()` correctly rejected invalid per-app booleans, but `generate()`
initially read that list before checking whether Quick apps was disabled
(`engine/quick-app:220`). Disabling the parent feature therefore failed on data that was
not needed to remove its bindings. This regressed the diagnostic off switch: the previous
reader treated damaged data as an empty list.

An isolated actual-engine probe started with Quick apps on and a private app record with
`hide_on_close: "false"`. `set_feature("quick_apps", False)` called the mocked hidden-window
recovery once, failed generation, failed shortcut rollback, and left the feature on.
The error said the saved choice was restored but shortcuts could not be restored. The
probe exited 0; no real desktop action ran and the damaged app file was preserved.

The generator now reads the enabled setting first and skips app-list parsing while off.
Independent actual-engine retests passed for three damaged-file variants: invalid per-app
boolean, malformed JSON and a non-object root. Disabling succeeded, revealed hidden windows
through the mocked recovery operation, removed overrides and retained false. Re-enabling
refused the damage, rolled back to false and left both the damaged file and disabled
bindings intact. Probe exit 0; the updated 44-test feature suite also passed.

## Native keyboard correction

The implementation owner found that the inherited panel Tab catcher opened the Add picker
instead of reaching the new switches. The correction adds `focusFirstControl()`, defers it
until an active list read finishes, exposes the first row's Toggle and focuses the clicked
Toggle. The verifier reread the exact patch and expanded the extracted-current-source Qt
fixture to 13 checks, all passing. New checks cover direct/deferred first-control focus,
empty-list picker fallback and the tab-change guard.

The owner reports native Tab+Space and repeated Space changed only the first app's saved
choice, verified against private JSON. That operation was performed by the owner; the
verifier independently inspected its source, Qt behavior and `per-app-keyboard.png`.

## Verification

- Isolated actual-engine read/save ordering probe: confirmed S-001, exit 0.
- Offscreen Qt focus probe: setting the focused Item's `enabled` false temporarily clears
  active focus, but re-enabling restores it when focus has not moved elsewhere. Three
  checks passed (including setup/cleanup), Qt exit 0. Disabling during the save is not by
  itself a confirmed focus defect.
- A separate private-engine matrix passed 119 cases, exit 0: 64 actual Lua close-action
  cases (both app choices, both list orders, Quick apps on/off, broad/narrow/unmatched/no
  active window), 16 binding combinations, 27 legacy/per-app precedence combinations,
  seven invalid saved values rejected without desktop calls or file changes, rollback of
  hide/set/remove after a reload failure, and edit/add defaults. The actual generated Lua
  ran in `lua` with a fake `hl` table; every file was private and desktop calls were mocked.
- The revised QML handler fixture initially passed nine Qt checks. After the native keyboard
  correction, the expanded fixture passed 13 checks (11 behavioral cases plus setup/cleanup),
  exit 0. It uses current source functions/handlers with fake process objects and a real Qt
  Repeater/focus model. It does not claim to operate the native full panel.
- Four concurrent real-process cases passed, exit 0, with a private HOME and executable
  `hyprctl` stub. Per-app false saves ran alongside Quick apps on/off changes, in both
  process launch orders. Both choices, unrelated feature values and generated bindings
  were correct afterwards.
- The initial damaged-list/parent-off probe confirmed S-003. Its final retest passed three
  damaged-file variants through disable and rejected re-enable, exit 0; see the finding above.
- All eight Python suites were run independently against this worktree, with actual exit
  codes read: `test_ws_layout.py` 14, `test_install.py` 18, `test_bar_arrange_apply.py` 9,
  `test_plugin_uninstall.py` 13, `test_ws_renumber.py` 17, `test_ws_bg.py` 11,
  `test_reptile_features.py` 44 and `test_nested.py` 6. Total: 132 tests, all exits 0.
  The feature suite was rerun after the final disabled-generation correction; the other
  seven suites predate that final two-line change, which the focused retests also cover.
- `QT_QPA_PLATFORM=offscreen /usr/lib/qt6/bin/qmltestrunner -input tests -o -,txt` passed
  46 checks, zero failures/skips/blacklisted, exit 0. These are the existing DeskRow/Reorder
  suites, not automation of the native new toggles.
- `git diff --check` passed, exit 0.
- The fixture isolation edits were reread and the affected feature (then 43), workspace
  layout (14) and nested harness (6) suites rerun successfully. These reruns are not
  additional unique tests in the total above.
- Independently viewed `docs/artifacts/reptile-features/per-app-native.png` and
  `per-app-focused.png`. The visible app headers, Toggle rows and neighboring cards have
  clear space, and both on/off switches retain the native two-child layout. The second
  image has an open app picker; its filename is not treated as keyboard-focus evidence.
- Independently viewed the owner's final `per-app-keyboard.png`, `per-app-error.png`,
  `per-app-draft.png`, `per-app-narrow-focused.png` and `per-app-paused.png` in the same
  artifact directory. The error wraps inside its app card without crowding its neighbors;
  the unsaved CTRL+slash draft remains visible; the paused explanation is readable; and
  the 600×600 logical, 1.5× screenshot shows Save inside the viewport after focus scrolling.
  The partial first-card clipping is the ordinary scrolled top edge, not lost content.
  The owner reports native failure injection/retry, draft retention and Tab scrolling;
  those operations are owner evidence, while the screenshot inspection is independent.
- Prior C-002 tests are recorded separately in `docs/reptile-features-verifier.md` and are
  not evidence for the new per-app behavior.

## Control review

The input-and-interaction and control-and-feedback skills are applied to the changed
control. The scope is the new per-app choice and its save/read cycle. Unchanged controls are
not claimed as fully re-audited.

| Input-and-interaction check | Inspection, finding, action and resulting state |
| --- | --- |
| Error prevention | Native two-state Toggle; strict JSON booleans and exact CLI true/false. Invalid stored values are rejected without writes or desktop calls. S-001 read/save ordering was corrected and independently retested. |
| Error recognition/recovery | Save errors appear beside the affected app; failed saves retain choice, focus and draft. The extracted-handler fixture verifies failure and retry-ready state. |
| Standard controls and labels | Uses the native Toggle with keyboard Space/Enter/Return, tab focus and an accessible checkbox role/name/checked state/action. The accessible name includes the app label. The owner's initial native Tab defect was corrected; the verifier checked the new focus code, Qt fixture and native screenshots. No screen-reader operation is claimed. |
| Platform action conventions | A direct reversible switch fits the platform. No destructive default or confirmation was added; existing Cancel/Save order remains. |
| Reuse known information | The engine derives each existing app's value from its explicit value, then the previous feature-level setting, then old list-level setting, then true. All 27 precedence combinations passed without read-time rewrites. Editing a shortcut preserves its choice; new apps default true. |
| Reset/Clear hazards | No Reset/Clear control was added. The separate save process does not reset the existing add/edit draft; independent Qt checks confirm retention on success and failure. |
| Password inspection | Not applicable: this change contains no password input. No action needed. |
| Selection semantics | Each app has one independent boolean switch. Mixed values work, and the most-specific matching app determines Super+W behavior; the independent Lua matrix confirms it. |
| Keyboard-only check | Native source supports Tab/Space/Enter/Return. Independent Qt tests verify first-row focus and focus retention through save/refresh/failure. The owner operated Tab+Space and repeated Space with private JSON assertions; the verifier viewed its native screenshots, including focused Save after narrow-layout scrolling. |
| Vendored block contract | The native Toggle owns a two-child row: text column and visual switch. This change adds no children inside it and uses its caller-owned checked value. Source and rendered full/narrow layout preserve that contract with clear spacing. |

| Control-and-feedback check | Inspection, finding, action and resulting state |
| --- | --- |
| Visibility of status | Immediate Saving… text, disabled controls during mutation/read, returned saved value on success, per-app alert on failure. S-002 added paused/unavailable-parent explanations. |
| User control/freedom | The choice is reversible with the same switch; the panel retains Escape/close. Saving does not move or close windows, and the app shortcut remains available even with Super+W hiding off. No new confirmation or modal trap. |
| Error prevention | Save/read serialization and duplicate activation guard prevent overlapping changes. Strict booleans and known-app lookup reject invalid requests. Independently checked. |
| Error recognition/recovery | Backend distinguishes restored choices from failed shortcut rollback; UI names the affected app and preserves work. Current handler tests cover command failure and malformed success output without claiming a successful save. |
| Error severity/recovery cost | Turning hiding off intentionally permits normal close for that app; matching a broader prefix cannot override a more-specific off choice. The Lua matrix verifies this boundary. Failed hide/set/remove updates restore choices/bindings. S-003 restored the ability to disable Quick apps with a damaged app list; independent disable/re-enable retests pass. |
| Response thresholds | Feedback starts synchronously. Backend lock waits and desktop subprocesses are bounded; no performance claim is made. No artificial long operation or new unbounded wait was introduced. |
| Longer-operation feedback | Saving… and disabled activation prevent duplicate saves; panel exit remains available while the process finishes. A determinate progress bar would not describe this single bounded local action. |
| Browser Back/navigation | Not applicable: this is a native QML panel, not a browser flow. Existing tab/close navigation remains; deferred reads handle a tab revisit during saving. |
| Mutation feedback walk | Start: busy + Saving…. Finish: only validated response updates the boolean. Failure: app-specific error + previous state/draft. Exit: existing panel close. Extracted handlers cover save outcomes; the owner operated failure/retry and draft retention, and the verifier inspected the rendered results. |
| Vendored block contract | The two-child Toggle contract remains intact. Independent full/narrow screenshot inspection confirms spacing, switch placement, readable error wrapping and reachable Save. |

## Completion watcher follow-up

Reviewed the ignored `docs/artifacts/reptile-features/watch-voyager.py` after source commit
`9521d30`. No blocker remains in this watcher change.

- The expected hash matches the checked-out `plugin/Reptile.qml` exactly (`d1676b61…`).
  Both Enterprise and Voyager must return that hash and exactly one selected main shell
  whose PID differs from their recorded baselines, 457406 and 791702 respectively.
- Both hosts use the same read-only probe. It reads installed QML bytes and `/proc`
  command lines, rejects IPC clients, and selects only the main shell configuration paths.
  The local probe adds no app write, window action or shell restart.
- Independent private stubs passed all 27 scenarios, exit 0: all 16 combinations of the
  two hosts' hash/PID readiness, missing or duplicate main PIDs on either host, either
  probe failing, either probe returning malformed JSON, busy notification, a prior latch,
  and expiry. Only full readiness or expiry attempts the self-nudge; busy delivery leaves
  the latch absent. Confirmed delivery writes the private latch and stops only the named
  watcher timer. A latched rerun makes no probe or notification call.
- The watcher and embedded probe compile successfully. All subprocess calls in the
  behavioral fixture were stubbed; no live SSH, notification or service mutation ran.
  The real notification marker was absent when inspected. The user service and timer
  were not present at this review (`systemctl --user cat` exited 1), so this approval is
  for the watcher source, not evidence that its timer has been rearmed.
- Matching installed bytes and a different PID do not prove which QML is cached in the
  running process. The notification still requires final live panel verification and the
  ten Caboodle feature checks before C-002 closes. Deployment observations and the
  owner's native close/hide probe remain owner evidence, not this watcher's result.

The additional inactive-installer safeguard is also approved. The installer source confirms
the `barbarian-install-pending` unit name and its 21,600-second unlock limit. When Enterprise
still has old QML, the watcher only reads that service's active state and requests an agent
inspection/retry if it is inactive. The maintenance nudge neither writes the completion latch
nor stops the timer, and its message explicitly forbids forcing an install while locked.

Six further private stub scenarios passed, exit 0: inactive installer with delivered, busy or
failed maintenance nudge; active installer; both panels ready; and maintenance timeout.
Delivered maintenance continues to the remote read without latching. A timeout leaves the
latch absent for a later timer run. Ready panels still take the existing final-notification
and latch path. No real subprocess action ran. The maintenance path's bounded subprocess
waits total at most 50 seconds; the owner's planned 60-second service timeout was not live
verified by this reviewer.

## Final delivery review — 2 November 2026

Delivery is approved within the evidence below. No remaining source, installation-evidence or
report blocker was found. The app source, tests, installer and README have no difference from
reviewed commit `9521d30`; that comparison exited 0. Source suites were not repeated for this
read-only delivery pass.

Independent local and SSH reads found the same installed hashes on all three machines:

- Reptile.qml: `d1676b6141488ccb1ec3c3a8f3b357832fab5ad5e9e7bea5d736e1fedb354fa9`.
- quick-app: `aabaa047e3f6e46002db18848bc03cc7d2892e7a32f5e07bca5f7ed938db091c`.
- reptile_features.py: `0c8a8141a08ff29debfc0d7cd9c185373fb4eb04afcf7b29231857a67e2415f1`.

These match the reviewed repository files. Process-command-line reads selected one main shell
per machine, excluding IPC clients: Enterprise 3170160, DS9 2357128 and Voyager 1221374.
The Enterprise installer and watcher timer/service all returned `LoadState=not-found` and
`ActiveState=inactive`. These are fresh observations, not the previous watcher's readiness claim.

Enterprise's current saved hashes independently match the owner's recorded before/after values:
features.json is `7400eacfae4854dd1d86bff04ca0e3a85c3c0bec647f9017e1063005968ade22`, and
quick-apps.json is `75ccc4b2fce4773a084e6a0b34fe3de3493e7adc7b65dafad16f519c207888b5`.
This reviewer read the current files; the earlier baseline and operated inspection are owner
evidence. No live choice or window action was performed by this reviewer.

An independent GET of Caboodle's live `/settings.json` returned HTTP 200. Its ten Reptile records
match `live-caboodle-verification.json` exactly: every state is a strict boolean, every problem
is null, and no `reptile-hide-on-close` record exists. Equal columns and Quick apps are on; the
other eight are off. No settings mutation endpoint was called.

Independently inspected the owner's two live Enterprise panel images and both Caboodle images.
The Quick apps image shows four separate off choices for Claude, ChatGPT, Gemini and Apple
Music, with clear spacing and complete labels. The Features image shows the visible upper part
of its scrollable list. Both cropped Caboodle sections show ten labeled controls with the same
two on states as the API and no global hiding control. The owner operated Enterprise's tab and
Escape navigation and captured the actual web page at 1440 and 430 pixels; this reviewer did
not operate those controls or independently measure those browser viewports.

The final report builder and generated HTML correctly distinguish live Enterprise/Caboodle
images from isolated fixtures, the final feature-test rerun from the seven earlier suites, and
Enterprise's operated native check from the ships' installed-file/process checks. All seven
embedded images match their current files and have alternative text. The old pending-install
claims are absent. The report's syntax check and these content/image checks exited 0. The
owner's no-overflow/no-JavaScript-error browser checks are reported as owner evidence, not
inferred from the cropped screenshots.

Limits remain explicit: this verifier did not operate a live panel on any machine; final native
operation was the owner's Enterprise check. DS9/Voyager evidence establishes installed files
and main shell processes, not a remote native interaction test. The private handler operation
does not claim successful hardware SUPER+W dispatch, and no screen-reader success or
performance improvement is claimed. Apart from this report, this pass wrote no files and made
no notification, installation, restart, UI or settings mutation.
