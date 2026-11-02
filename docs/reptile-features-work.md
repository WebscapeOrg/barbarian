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

Deployment state last verified after the push:

- Enterprise is locked, still running its old shell (PID 3016). barbarian-install-pending.service
  is active and waits for unlock. Do not force a restart or write plugin files while locked.
- DS9 has matching Reptile.qml and engines; its new shell PID 1901295 started after installation.
- Voyager has matching engines and helper, but is locked and still has the old panel in shell
  PID 2000. Its shell uses ~/omarchy, not /usr/share/omarchy. Enterprise's setup-portable owns
  plugin installation there; portable-selfheal.timer is active and retries every 15 minutes.
- Both ships returned valid features and desks JSON with their recorded Hyprland session context.
- The first ship sync omitted the new shared module from Enterprise's separate portable copy
  list. Enterprise repaired it in ec36d2c (v1.139.13); the corrected source and installed hashes
  were then checked. Future companion files must be coordinated before sync, not merely added
  to this repo's installer. Ship sync copies the working tree, including uncommitted edits.

Remaining work is live Enterprise/Voyager verification and Enterprise's automatic-caller rollout.
Enterprise is preparing a persistent waiter for its tested caller patches, gated on all three
installed engines returning the new feature settings; it will message @barbarian when it completes.
Keep C-002 open until that boundary is resolved, verify Caboodle's 11 live Reptile rows, update
P-006 in place, then close the carrot. The feature store must retain Dave's existing choices.
