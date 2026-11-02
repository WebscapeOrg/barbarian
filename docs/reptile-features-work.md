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

Recorded active test processes: nested Hyprland PID 3373862 and Quickshell PID 3973652. Earlier
test Quickshell PIDs 3435469, 3712420 and 3783207 were stopped by their exact PID. The source-watching
harness reloads and closes its panel after QML edits; reopen before operating it.

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

Remaining delivery steps: commit and push the reviewed code; verify installation on Enterprise
and both ships; let Enterprise deploy its prepared automatic-caller patches after compatibility
is verified; publish the HTML report; close C-002 after the running system is verified. Enterprise
was locked at the last check and still running its old shell (PID 3016); use the installer waiter,
never a forced restart. The Enterprise agent has been asked to prepare a persistent integration
waiter too. Keep the task open until this deployment boundary is resolved.
