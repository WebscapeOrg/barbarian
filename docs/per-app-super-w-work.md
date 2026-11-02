# C-002 follow-up: per-app SUPER+W

Dave asked: “Id like the hide quick apps with super w to be per quick app instead of global.”
This extends the held C-002, which still waits for Voyager's unlocked panel rollout.

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
Check the isolated source/tests, operate the native panel and mixed app behavior in a private
nested compositor, publish screenshots and the skill check report, then commit/push/install.
Verify Enterprise's fresh shell and Caboodle's 10 remaining feature switches. Recheck the ships;
replace the paused Voyager watcher hash only after the final QML is ready. The old
`barbarian-voyager-verify.timer` is stopped during this follow-up to prevent an obsolete completion
signal. Do not restart or write Voyager's plugin while locked; setup-portable owns that update.

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

## Delivery still pending

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
PIDs 457406/791702. The timer remains active for two-minute checks, and the Enterprise installer
was independently read as active afterwards. The verifier's 27 readiness cases and six additional
inactive-installer cases used private subprocess stubs; its approval does not assert live loading.

After installation, verify the actual per-app panel and ten healthy Caboodle Reptile switches with
no global hiding switch. Recheck the ships, update P-006 and close C-002. Keep Dave's choices.
