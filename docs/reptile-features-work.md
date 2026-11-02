# C-002: individual Reptile features

Dave wants to disable Reptile behaviors independently while investigating desktop problems. The
takeover is published as P-005; C-002 is the active task. No cause of the desktop problems has
been established.

## Implementation

- Add persistent feature settings shared by the QML panel and both Python engines. Existing
  behavior stays enabled by default; saved layouts and quick-app choices are preserved.
- Expose a Features tab using Omarchy's native Toggle rows. Keep settings reachable with
  features disabled, and make errors, pending saves, keyboard focus and off states explicit.
- Cover manual and automatic restoration, apply-on-visit, reopening missing apps, closing extra
  windows, floating layouts, placeholders, progress messages, equal columns, quick-app shortcuts
  and hiding quick apps on close. The existing hide-on-close preference remains authoritative
  during migration.
- Ask Enterprise to tag its two boot restoration calls with --automatic. Do not change those
  scripts behind its agent. Coordinate rollout after the compatible engine is installed.
- Keep disabled quick-app windows recoverable. Feature changes must not close real windows or
  throw away recordings. Re-enabling must not replay queued desk edits unexpectedly.

## Verification and delivery

- Baseline: 80 Python tests and 46 Qt checks pass. The engine emits an unclosed-file warning;
  fix the affected reads while touching it.
- Add isolated behavioral tests for persistence, disabled entry points, restoration subsets,
  shortcut generation, failure rollback and re-enabling. Run existing suites directly and read
  exit codes.
- Render and operate the tab in an isolated nested compositor, including keyboard controls,
  narrow height/width, off/error states and reopening. Record the invoked usability skills'
  complete check-by-check results in the final Peacock report.
- Required independent hostile verifier: `/root/feature_verifier`, started on the initial
  implementation. Output: `docs/reptile-features-verifier.md`. Send the final diff for a second
  read once tests and Caboodle integration are complete; resolve findings before shipping.
- Commit, push, install through the existing safe installer, and verify the running QML is new.
  The source-change post-commit hook deploys; park it for any intermediate source commit.
- Publish the report with screenshots, close C-002 and verify the final live state.

## Current state

Shared settings, engine guards and the Features tab are implemented and independently approved. The native
Toggle contract is a two-child row (text column plus visual switch), caller-owned checked value,
and whole-row activation. Reuse it intact and add accessible checked state at the call site.
The GitHub redirect was verified and origin now points to WebscapeOrg/barbarian.

## Coordination

Enterprise agreed to add --automatic to boot-apps.sh and portable-boot-restore.sh, with deployment
held until the new engine is installed and synced to the ships. Caboodle has been asked about
registering these same settings through its switch manifests; no second store is planned.

Isolated compositor: tests/nested/nested, signature
efb50993780079460b0cbed1363e2166a2de1d9f_1793621549_1778625535, wayland-2, work directory
/run/user/1000/barbarian-nested. Record its PIDs before cleanup; do not kill by a process pattern.

The isolated desktop was stopped after verification: nested Hyprland PID 3373862 and Quickshell
PID 3973652 are gone, and the validated runtime folder was moved to a unique Trash directory.
Earlier test Quickshell PIDs 3435469, 3712420 and 3783207 were stopped by their exact PID too.
The source-watching harness reloads and closes its panel after QML edits; reopen before operating it.

The independent verifier approved V-001 through V-007. The seven Python engine/installer suites
passed 112 tests, the new harness suite passed 6 tests, and the existing Qt drag suites passed
46 checks. Additional independent probes covered races, cross-process locking, shortcut rollback,
44 installed-helper operations, first-time settings-file creation, focus scrolling and cleanup.
See docs/reptile-features-verifier.md for the exact evidence boundary.

Native operation covered Ctrl+Tab, Tab, Space, scrolling at 600×600 logical pixels with 1.5×
desktop scaling, both palette branches, a long Quick apps list, hidden-window recovery, invalid
settings, a failed save and recovery, pending edit clearing and placeholder removal. Only private
test settings/windows changed. Native AT-SPI exposed the test application but no descendants;
screen-reader operation is not claimed. The control roles/actions are present in source.

Reviewed code is committed and pushed as dbb8384. The report is P-006:
http://100.124.40.42:3012/peacock/barbarian/P-006. Its 96 usability/visual checks and screenshots
are in a self-contained HTML artifact, previewed at 1440 and 430 pixels wide with no horizontal
overflow or broken images. The working report source is ignored under docs/artifacts/reptile-features.

Deployment state last verified during the rollout follow-up:

- Enterprise unlocked and its deferred installer completed. Installed engines and Reptile.qml
  match the reviewed source. Its main shell PID 457406 started at 13:31:44 after installation.
  The live Features tab loaded through the actual panel, and Ctrl+Tab selected it. The panel
  was closed afterwards; no live feature choices were changed. Caboodle's live settings JSON
  returns all 11 Reptile switches with boolean values and no problems.
- DS9 has matching Reptile.qml and engines; its new shell PID 1901295 started after installation.
- Voyager has matching engines and helper, but remains locked and still has the old panel in shell
  PID 2000. Its shell uses ~/omarchy, not /usr/share/omarchy. Enterprise's setup-portable owns
  plugin installation there; portable-selfheal.timer is active and retries every 15 minutes.
- Both ships returned valid features and desks JSON with their recorded Hyprland session context.
- The first ship sync omitted the new shared module from Enterprise's separate portable copy
  list. Enterprise repaired it in ec36d2c (v1.139.13); the corrected source and installed hashes
  were then checked. Future companion files must be coordinated before sync, not merely added
  to this repo's installer. Ship sync copies the working tree, including uncommitted edits.

Enterprise's automatic-caller changes are committed as 65fa254, b79cf94 and 477182e
(v1.139.18, v1.139.19 and v1.139.22).
The installed Enterprise boot-apps.sh and both ships' portable-boot-restore.sh match those sources.
Both callers check the shared restoration switches before network/session waits or window/focus
actions, and pass --automatic to every restore. A private copied-script probe found that the first
Enterprise gate ignored an engine failure after valid JSON output; Enterprise corrected it in
b79cf94. The independent verifier then found that a second JSON document could override an off
answer in the first; 477182e requires exactly one answer. All 30 copied-script cases now pass,
including on/off, invalid/missing settings, partial-output failure and all four two-document
orderings. Every disabled/error case made no network, window, focus or restore call.
The probe source is ignored under docs/artifacts/reptile-features/probe-callers.py. Live login
scripts were never executed for testing. An independent caller follow-up review is recorded in
docs/reptile-features-verifier.md.

The live Caboodle Settings page was also checked in isolated browser contexts at 1440 and 430
pixels wide. Both return 11 enabled, named Reptile switch controls, current boolean state and no
horizontal overflow. No live controls were activated. A damaged legacy quick-apps.json already
produces explicit engine stderr, which the Features panel displays as its load error; this was
confirmed with a private HOME. The legacy file is only read until hide_on_close migrates.

Dave then requested per-app SUPER+W hiding in place of the global choice. That reviewed follow-up
is pushed as 9521d30; its current delivery state and verification are in
docs/per-app-super-w-work.md and docs/per-app-super-w-verifier.md. The earlier 11-feature/global
control descriptions above record the initial rollout. The final catalog has ten feature switches
plus app-specific choices. Enterprise locked again, so both its follow-up and Voyager's new panel
still wait for safe installation. DS9 has the follow-up files and a fresh shell. Keep C-002 open,
preserve Dave's choices and use the follow-up work file as the current recovery plan.

A read-only follow-up timer is armed on Enterprise: barbarian-voyager-verify.timer, every two
minutes. Its script is docs/artifacts/reptile-features/watch-voyager.py. It reads Voyager's installed
QML hash and main shell PID. The per-app follow-up expands it to Enterprise too and updates the
expected hash and baseline PIDs; see the current recovery plan. It never installs or restarts
anything. Delivery must succeed before its local
.notified marker is written and its own timer stops. A matching hash/new PID triggers inspection;
it does not close the task. From 9 November it stops remote polling and asks the session to recheck
the parked work. The transient timer lasts for the current Enterprise user-manager lifetime;
re-arm it if the machine restarts before Voyager updates. The independent verifier approved the
watcher source; four private command-stub scenarios passed before arming it.
