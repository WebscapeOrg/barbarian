# C-004: Skylark workspace restoration

Dave reported the cannot-reopen warning after recording Skylark on Messaging, then asked for
the fix. The saved org.quickshell/Skylark window has launch=null. The engine recognizes only
Magpie in its existing shell summon table.

Implementation worktree: /home/anotherdave/.local/state/barbarian/skylark-restore,
branch fix-skylark-restore, based on e7728d2. This isolates unfinished source changes from
Enterprise's ship sync. Main's generated AGENTS.md update is pre-existing and must be preserved.

Use the existing idempotent shell summon path for Skylark. Check new snapshots, old recordings
with no launch command, tiled/floating identity and matching against Magpie and other shell
windows. Existing restores and panel models already resolve current launchers before saved ones,
so old recordings should work without destructive rewrites or resaving.

Independent verifier: /root/feature_verifier; output docs/skylark-restore-verifier.md in main.
Source review, isolated regression checks and final delivery evidence are separate. Do not
operate live calendars or settings in tests. Coordinate the title/summon contract with @skylark.

Implementation, independent source review and installation are complete. Final native
verification used Enterprise's installed engine against the existing Messaging recording;
its results and the verification limit are recorded below.

The first independent pass found two inherited gaps exposed by the integration: a known shell
window already open on another desk was excluded by the new-address rule, and a floating shell
app beside a different tiled shell app was treated as a dialog. Both are patched. Known shell
apps reuse an existing mapped non-placeholder window by exact address without relaunching;
floating recording and panel models use app identity rather than the shared shell class.
The expanded launcher suite has 21 passing tests, and all 44 feature tests pass. The independent
review approved both corrections and passed 40 additional private cases. Its evidence and limits
are in docs/skylark-restore-verifier.md. Qt suites were not rerun: no QML implementation changed.

## Delivery

Source commit 9c35986 is pushed. It was committed in the isolated worktree with the deployment
hook disabled for that commit, then fast-forwarded into main. The normal installer and both ship
sync services were explicitly run from main. No validation hook was skipped; the hook being
bypassed performs deployment only. No new companion file or portable copy-list change is needed.

Enterprise, DS9 and Voyager's installed ws-layout hashes match the reviewed engine:
a37c96169d153a4f1b14eb90a276ae6996e6f421088806138ac3c4afebcf81a1. Both ship sync services
exited 0; both remote installed hashes were rechecked during final delivery verification.
Enterprise initially locked before installation. Its normal safe installer completed after
unlock at 13:22 on 3 November, exited 0 and is now inactive. No locked install was forced.
This is an engine-only change; no shell restart was required.

P-007 records the delivery: http://100.124.40.42:3012/peacock/barbarian/P-007.
The ignored docs/artifacts/skylark-restore directory holds a copy of the existing Messaging
recording and watch-install.py. The watcher reads the installed engine and lock state, then
self-nudges @barbarian for final verification. It never installs, restores or restarts anything.
It confirms notification delivery before writing its local marker and stopping only its own
timer. An inactive safe installer triggers an inspection/retry nudge without latching; from
10 November it asks for review instead of continuing readiness polling. Transient units need
rearming after a user-manager restart if delivery is still pending.

The watcher passed independent review after its lock-status check was tightened to require all
four lock booleans to be exactly false. Its 66 private scenarios passed; no live notification or
service action ran in those tests. The watcher hash is
6d0c72a185d4130601d5040edba3b1d6ecffe70bbcfb02b6f3abcf529aa84459.
barbarian-skylark-verify.timer was armed for two-minute follow-up checks with a 45-second
service timeout and explicit main-session OMARCHY_PATH/WAYLAND_DISPLAY/XDG_RUNTIME_DIR. Its
first actual service run exited 0 and correctly waited for the reviewed engine. After unlock
and installation, it delivered the verification nudge and stopped its own timer. The timer
and service were confirmed inactive, with successful service status, before native verification.

## Native delivery verification

Enterprise was freshly confirmed unlocked, with the installed engine matching the reviewed
hash. The actual Messaging recording still held one org.quickshell/Skylark window with
launch=null and no floating windows. Messaging was empty and no Skylark window was open.
Restore and reopen were enabled; close-extras and apply-on-visit were disabled. No switch
was changed for verification.

The installed engine restored that existing recording and printed
`ws4 (Messaging): 1 window in place, 1 opened`. The compositor showed exactly one mapped,
tiled Skylark on Messaging, address 0x559d0b7b6b90, hosted by the existing shell PID 3170160.
A second restore printed `ws4 (Messaging): already as saved`, retained the same address/PID
and did not duplicate the calendar. The installed `show 4` reported `desk now: as saved`.
The same unrelated client addresses, processes, workspaces and geometry remained in place
during both restores. Focus returned to the original Caboodle window on Agents.

All six recording files, features.json, quick-apps.json, shell.json and bar-hidden.json were
byte-identical to their pre-verification hashes. The old Messaging recording needs no resave.
No calendar event or setting was edited. The native verification evidence is in ignored
docs/artifacts/skylark-restore/native-verification.json; it contains no claim of remote native
window verification. DS9 and Voyager were verified by installed engine hash only.

The initial operator script completed both restores and the saved-file checks, then failed an
extra comparison of the entire split-ratio option object. It did not retain the original
object, so the cause of that comparison failure and before/after ratio equality are not claimed.
A subsequent read-only check passed the explicit window, saved-file and focus assertions.
The current split-ratio value is 1.0. This operator-check limit does not change the passing
source-suite results or the observed native restore behavior.

P-007 was updated in place and its published page returned HTTP 200 with the expected title.
The independent delivery review confirmed all three installed hashes, the current single
Skylark window, the ten unchanged files and original focus; its addendum separates these
reads from the owner's native operations and records the option-comparison limit.
C-004 is closed with that link. No remaining delivery work is pending for this fix.

## Review checks

The change reuses the existing summon path and does not alter a QML component or vendored block.
The native card/panel structure is unchanged. Checks cover this backend fix and its short README
addition; they do not claim a new audit of the whole application.

| Control and feedback check | Finding, action and result |
| --- | --- |
| Status | A successful snapshot now records a Skylark launcher and uses the existing saved card, without the cannot-reopen warning. A regression checks both. |
| Control and freedom | The existing shell summon opens without toggling an open calendar closed. No new modal or action is added. |
| Error prevention | Recognition requires the shell class and Skylark title. Cross-app tiled/floating matching and newly appearing windows are covered by isolated regressions. |
| Error recovery | Old null-launcher records use the current launcher before saved fallback. The restore regression leaves the old file byte-identical and opens Skylark. |
| Recovery cost | Existing records need no resave or file rewrite. Saved geometry, calendar events and other app choices are retained. |
| Response thresholds | Existing bounded open/wait behavior is reused. No timing or performance improvement is claimed. |
| Longer operation | Existing restore progress/failure handling remains; no new long operation is introduced. |
| Browser navigation | Not applicable to the native engine; no web navigation changed. |
| Mutation walkthrough | Snapshot regression checks saved launcher and warning removal; old-record regression checks restore without rewriting; Enterprise's existing null-launcher recording reopened one Skylark, and repeat restoration kept that same window. |
| Block contract | No vendored or native UI block is extended. Existing card and panel composition are unchanged. |

| Reading and understanding check | Finding, action and result |
| --- | --- |
| Contextual help | README states the supported apps and that existing recordings need no resave. |
| Specific labels | Skylark and Magpie use their app names. No control or link label changes. |
| Concision | Three sentences explain reopening, old records and returning an existing window without command details. |
| Scannability | The short paragraph is beside existing layout feature documentation. |
| Conclusion first | The paragraph starts with the ability to reopen the apps. |
| Plain language | It says reopen and save again, with no window-class or IPC terminology. |
| Numerals | No new numerical facts occur in the user-facing paragraph. |
| Reading format | README remains ordinary searchable text; no PDF is added. |
| Text scaling | No font, wrapping or native text-size changes are introduced. |
| Task/readability walk | The action remains HYPER+R; no new instruction or control is needed. Existing recordings are supported automatically. |
| Block contract | No content block structure or UI layout changes. |
