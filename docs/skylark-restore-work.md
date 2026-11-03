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

Next: implement and test in the worktree; independent hostile review; commit and fast-forward
main, install via the normal safe installer and sync ships; check actual installed engine and
the saved Messaging recording's restore; publish a small Peacock note and close C-004.

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

DS9 and Voyager's installed ws-layout hashes both match the reviewed engine:
a37c96169d153a4f1b14eb90a276ae6996e6f421088806138ac3c4afebcf81a1. Both sync services exited 0.
Enterprise locked before installation. Its installed engine is still
3fa13d9b070aaaa931523a64a7471e742ebb2ed065d32557680b6dfd14bed908, and the normal
barbarian-install-pending.service is active. It waits for unlock and will expire after six hours.
Do not force a locked install. This is an engine-only change; no shell restart is required.

P-007 records this pending state: http://100.124.40.42:3012/peacock/barbarian/P-007.
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
barbarian-skylark-verify.timer is armed for two-minute follow-up checks with a 45-second service
timeout and explicit main-session OMARCHY_PATH/WAYLAND_DISPLAY/XDG_RUNTIME_DIR. Its first actual
service run exited 0 and correctly printed that it was waiting for the reviewed engine; no
notification marker was written. The safe installer was still active afterwards.

Final verification remains pending: re-read the Messaging recording, clients and feature gates;
use the installed engine to restore the existing Skylark recording safely; verify one calendar
window and no duplicate on repeat, with saved settings and recording unchanged. Preserve other
windows and restore the original focused desk. Update P-007 in place, close C-004 and commit/push
the delivery record only after the actual installed behavior is verified.

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
| Mutation walkthrough | Snapshot regression checks saved launcher and warning removal; old-record regression checks restore without rewriting; final installed verification remains pending. |
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
