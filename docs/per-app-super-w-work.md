# C-002 follow-up: per-app SUPER+W

Dave asked: “Id like the hide quick apps with super w to be per quick app instead of global.”
This extends C-002. The queued rollout completed after unlock; final live checks are recorded below.

Implementation was isolated from Enterprise's ship-sync in
`/home/anotherdave/.local/state/barbarian/per-app-super-w`, branch `per-app-super-w`.
The reviewed source was committed as `9521d30`, fast-forwarded into the main clone and pushed.
The worktree's automatic deployment hook was bypassed for that commit, then the normal installer
and ship-sync services were run from main. The only installed Git hook is post-commit deployment;
no validation hook was skipped. No companion files are added;
the automatic caller protocol and its two restoration gates remain compatible.

- Each Quick app card gets a native Hide with SUPER+W switch, saved immediately.
- Existing apps inherit their current global choice; explicit per-app choices take precedence.
  New apps start with hiding on. The app's own summon/hide shortcut is unchanged.
- The global Features/Caboodle switch is retired. Its owned manifest moves to Trash; legacy
  settings remain available only to migrate old app records.
- Strict booleans, shared locking, binding rollback and exact app updates preserve other choices.
- The UI preserves drafts and focused rows, serializes list reads and writes, and shows pending,
  error and parent-off states. The native Toggle retains its two-child row structure.

Independent verifier: `/root/feature_verifier`; report `docs/per-app-super-w-verifier.md`.
The isolated source/tests, operated private native panel, mixed app behavior and skill check report
were completed before commit/push/install. The original watcher was stopped while the follow-up
changed the expected QML, then rearmed against the final reviewed source. Voyager's plugin rollout
remained owned by setup-portable; no locked plugin write or forced restart was used.

## Verified result

Independent review resolved stale list replies, missing parent-off explanations and inability to
disable Quick apps with a damaged app list. The inherited keyboard catcher was also corrected so
Tab on Quick apps reaches the first switch. All 132 Python tests, 46 existing Qt checks and 13
focused current-handler Qt checks passed. The independent report distinguishes its 119-case engine
matrix, concurrent process probes, source/screenshot review and the owner's operated native checks.

The native panel was operated with Tab and repeated Space, private JSON assertions, a failed
desktop save and retry, a retained unsaved CTRL+slash draft, paused choices and focus scrolling
at 600×600 logical pixels with 1.5× scaling. Both dark and coherent light palettes were viewed.
Direct close-or-hide calls closed the private off app and hid the on app while retaining its PID;
the app toggle restored the same window. Virtual global-key injection did not trigger the nested
compositor's bindings, so hardware SUPER+W dispatch is not claimed by that probe. The generated
binding routes to the tested close handler. No live choices or live windows changed during tests.

The nested desktop was stopped after verification. Its compositor PID 1403881, Quickshell PIDs
1423790 and 1509728, editor PID 1612711 and terminal PID 1612726 are gone. The validated runtime
folder moved to Trash. Enterprise's main shell PID 457406 was left running.

P-006 is updated in place with per-app screenshots and the full 96-check review:
http://100.124.40.42:3012/peacock/barbarian/P-006. The HTML was checked at 1440 and 430 pixels wide
with all details open: no horizontal overflow or broken images. Its working builder remains under
the ignored docs/artifacts/reptile-features directory.

## Queued delivery history

Enterprise locked again while tests ran. Its normal installer queued the three changed files;
barbarian-install-pending.service is active. Installed quick-app, reptile_features.py and QML are
still the previous versions. Its saved feature choices, including hide_on_close=false, were read
and left untouched; existing app choices must therefore migrate as off unless explicitly set.

DS9 has source-matching engines and Reptile.qml, with a new main shell PID 2357128. Voyager has
source-matching engines, but its QML is still 90a23896… in shell PID 791702; that is the initial
feature-control build, not this per-app follow-up. Its locked plugin update remains owned by
setup-portable and portable-selfheal.timer. Both ship-sync services completed with exit 0, and
Enterprise independently confirmed the new engine/module hashes and compatible restore gates.

The follow-up watcher is docs/artifacts/reptile-features/watch-voyager.py, unit pair
barbarian-voyager-verify.timer/service. It now reads both Enterprise and Voyager and expects QML
d1676b6141488ccb1ec3c3a8f3b357832fab5ad5e9e7bea5d736e1fedb354fa9, with fresh main shell PIDs
relative to 457406 and 791702. It nudges @barbarian after both match; installed bytes/new PID only
trigger final native checks and never close the task automatically. Its delivered-notification
marker is written only after hobnob confirms the nudge. The units are transient, so recreate them
after a user-manager restart if the task is still pending. If Enterprise remains old and the
installer is no longer active, it nudges the session to inspect and retry the normal safe installer.
It never writes, installs or restarts app files/processes. From 9 November it stops remote polling
and asks the session to inspect the parked work instead.

The transient unit pair was recreated and armed after review with a 60-second service timeout.
Its first real run exited 0 and correctly observed the previous QML on Enterprise/Voyager with
PIDs 457406/791702. The timer was active for two-minute checks, and the Enterprise installer
was independently read as active afterwards. The verifier's 27 readiness cases and six additional
inactive-installer cases used private subprocess stubs; its approval does not assert live loading.

## Final live verification

The watcher delivered readiness after both pending installs completed. On 2 November, the installed
QML, quick-app and shared-module hashes were read again on Enterprise, DS9 and Voyager. All match
source commit 9521d30. The observed main shell processes are Enterprise PID 3170160, started at
16:26; DS9 PID 2357128; and Voyager PID 1221374, started at 16:50. Enterprise and Voyager were
unlocked. The installer and completion timer units have disappeared after finishing; the delivered
watcher marker exists. No installation or restart was needed during this final verification.
Installed ws-layout features commands also succeeded on all three machines, each returning ten
strict boolean feature values and no hide_on_close feature. Enterprise's restoration gates remain
false/false and both ships' remain true/true; their different saved choices were kept.

Enterprise's actual running Quick apps and Features tabs were opened, selected with Ctrl+Tab and
closed with Escape. The four live app cards each show Hide with SUPER+W off. The installed engine's
read-only list also normalizes all four as false, preserving Dave's previous global false value.
No live switch, app shortcut, window action or layout action was activated. JSON hashes before
and after native inspection were identical:

- features.json: 7400eacfae4854dd1d86bff04ca0e3a85c3c0bec647f9017e1063005968ade22
- quick-apps.json: 75ccc4b2fce4773a084e6a0b34fe3de3493e7adc7b65dafad16f519c207888b5

The live Caboodle settings.json returned ten Reptile records, each with a boolean state and
problem=null, and no reptile-hide-on-close record. Isolated browser contexts read the actual
Settings page at 1440 and 430 pixels wide: ten enabled, labeled switch controls with matching
states, no global hiding control, no horizontal overflow and no JavaScript errors. No form was
submitted. Equal columns and Quick apps remain on; the other eight feature choices remain off.

Evidence under the ignored docs/artifacts/reptile-features directory: cropped live Enterprise
Quick apps/Features panel images, live-caboodle-430.png and live-caboodle-1440.png, and
live-caboodle-verification.json. P-006 is updated in place. Ship delivery checks read installed
files and fresh processes; the final operated native panel check was on Enterprise. The app source
did not change during delivery verification, so its already-passing source suites were not repeated.
The regenerated report was previewed at 1440 and 430 pixels wide with every review section open:
seven images loaded, none were broken, and neither viewport overflowed horizontally. P-006's served
HTML was fetched and matched the final local artifact byte for byte.

The independent verifier approved final delivery after its own current file/process, settings-hash
and live Caboodle reads, plus screenshot/report inspection. Its addendum records the owner-operated
native checks separately. C-002 is closed with P-006; no delivery work remains pending.
