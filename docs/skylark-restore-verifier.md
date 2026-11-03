# C-004: Skylark restore verification

Approved within the source and isolated-test evidence below. SLY-001 and SLY-002 are resolved;
no remaining shipping blocker was found in the reviewed change. This is the independent review
of the isolated `fix-skylark-restore` worktree based on `e7728d2`. The final engine hash is
`a37c96169d153a4f1b14eb90a276ae6996e6f421088806138ac3c4afebcf81a1`.

The final change adds Skylark's summon entry, recovers an existing matching shell window, and
uses shell-app identity when separating floating windows from dialogs. README explains old
recording support and returning an existing Skylark window from another workspace.

Scope: inspect launcher identity and restore gates, then run isolated fixtures for tiled and
floating old records, existing windows, unknown shell windows and placeholders. This verifier
does not operate live windows or calendars, change settings, install, restart or publish. The
pre-existing main-checkout AGENTS.md change is outside this review and is left untouched.

## Confirmed findings

### SLY-001 — resolved: an already-open Skylark on another desk could not be restored

In the initial patch, `engine/ws-layout:918–923` recorded every existing matching address, then accepted only addresses
outside that set. The new command uses the correct idempotent shell summon, which leaves an
already-open window open. The source contract is confirmed in `/usr/share/omarchy/shell/shell.qml`
(`summon`, line 1155) and Skylark's `ui/App.qml` (`open`, line 35; fixed window title, line 141).

An isolated probe presented a mapped Skylark at address `0xexisting` on desk 2 and asked
`open_window` to restore desk 4. The actual predicate rejected that same window, the helper
returned None, and exactly one summon command was recorded. Its configured wait is 30 seconds;
the fixture did not spend that time waiting or execute the command. A real idempotent summon
cannot satisfy the new-address requirement when this window is already open elsewhere.

This was inherited new-window machinery exposed by adding another singleton shell app. The
correction recognizes a mapped, non-placeholder window belonging to the known summon and
passes its exact address to `place_new`, without launching or summoning it again. Eight
independent cases used the actual placement function with Skylark/Magpie and both starting and
requested floating states. Each moved only the matching window and made no Popen call.
Additional checks confirm unmapped windows and placeholders are not reused, ordinary apps and
unknown shell commands retain the new-window path, and `open_apps=false` blocks the operation.

### SLY-002 — resolved: a floating Skylark was omitted beside another tiled shell app

In the initial patch, `engine/ws-layout:547–551` excluded floating windows using tiled window classes. A tiled Magpie
and floating Skylark share `org.quickshell`, so `floating_on(4)` returned an empty list in an
isolated two-window probe. `take_snapshot` consumes this list at line 674, omitting Skylark.
The same class-only filtering appeared in `desk_model` at lines 1808–1810.

The correction adds `app_identity` using the existing summon-title-or-class rule and applies it
to both filters, the cull and recorded counts. Six independent ordered combinations of Skylark,
Magpie and Holodeck exercised actual snapshot, desk-model and restore functions. Each retained
the separate floating app, marked both recorded windows open, reported no extra window, and
restored without a launch, close or move. Four checks preserve same-app dialog exclusion for
the three shell identities and an ordinary app. This verifier did not change application code.

## Initial checks

- `tests/test_ws_layout.py`: 18 tests passed, exit 0.
- `tests/test_reptile_features.py`: 44 tests passed, exit 0.
- Both suites ran with private HOME/TMPDIR and bytecode writes disabled, in addition to their
  own mocked desktop access and private configuration fixtures.
- The two direct reproductions above ran only with private configuration and mocked client,
  placement and subprocess operations. No compositor, shell summon or calendar operation ran.

Before the corrections, a separate 23-case private restore probe checked tiled/floating old
records, current-launcher precedence over a stale saved command, existing local windows,
restore/open/automatic/on-visit/floating gates, unknown shell placeholders, failed summons and
record preservation. These initial results are not claimed as final-code reruns.

## Final checks and limits

- The corrected source passed 21 layout tests and 44 feature tests, each with exit 0 and a
  private HOME/TMPDIR. These replace the earlier suite counts rather than adding to them.
- The 23 independent correction/boundary scenarios described above passed, exit 0. They used
  actual `place_new`, `take_snapshot`, `desk_model` and `restore` functions with private files
  and a mutable in-memory compositor fixture; subprocess and desktop dispatch were intercepted.
- A further 17 final-code old-record/gate scenarios passed, exit 0. Tiled and floating records
  with null, absent or stale launch commands use the current Skylark summon. Master restore,
  automatic, on-visit, reopen and floating gates prevent their relevant actions. Turning
  placeholders off does not prevent the known Skylark launcher. Every recording stayed byte-for-byte
  unchanged, and none of these known-app cases requested a placeholder.
- The shell source's summon path sets open state; it does not use toggle. Skylark's manifest
  declares id `skylark`, and its App.qml declares the `Skylark` title and an `open` method that
  sets `opened=true`. This is source-contract evidence; no live summon or calendar operation ran.
- The final README matches the tested missing-window and existing-window behavior. Diff
  whitespace checks passed. No QML/UI implementation changed, so Qt/rendering suites were not
  run for this patch. No performance improvement is claimed.

The existing policy that a placeholder counts as the recorded window is retained. An already
present stand-in is not automatically replaced merely because a launcher becomes available;
the old-record checks cover missing real windows, not automatic stand-in replacement. Unknown
shell windows do not acquire Skylark's launcher or identity.

At the source-review boundary, live installation, a real shell summon and the actual Messaging
layout remained the owner's delivery-verification responsibility; that pass did not assert that
any machine was already running the change. Only this report and private temporary fixtures
were written by the verifier; no live window, setting, calendar, installer or service was changed.

## Completion-watcher review

The application source is now committed as `9c35986`; its engine still matches the approved
hash above. This follow-up reviews the ignored
`docs/artifacts/skylark-restore/watch-install.py`, separately from the app. The watcher reads
the installed engine and lock status and requests agent follow-up. It does not install,
restore, summon or restart the app. Installed hashes and rollout status supplied by the owner
are not independently reverified in this watcher-only pass.

### SLY-003 — resolved: incomplete lock status could latch false readiness

The initial watcher requires `sessionLocked` to be exactly false but only rejects the other
lock fields when they are exactly true. Four private stub cases supplied a partial
`{"sessionLocked": false}` object, a `locked: "true"` string, a `pending: 1` integer or a missing
`secure` field. Every case requested a readiness nudge, wrote the private notification marker
and requested its timer stop. The native lock source declares boolean `locked`, `pending`,
`sessionLocked` and `secure` fields at `plugins/lock/Service.qml:535–541`. The watcher should
require an object with all four fields exactly false before asserting the desktop is unlocked.

This is a confirmed failure to reject malformed readiness evidence, with a potential lost
follow-up after a premature latch. It does not itself change a desktop window or setting.
The reproducer used a copied source engine, temporary markers and an intercepted subprocess
function; no live notification or service command ran.

The correction requires a dictionary and all four fields exactly false. The final watcher
hash is `6d0c72a185d4130601d5040edba3b1d6ecffe70bbcfb02b6f3abcf529aa84459`.
It is approved within this source and private-test evidence. The reviewed application source,
tests and README have no diff from `9c35986`; the application suites were not rerun for this
separate watcher change.

The corrected watcher passed 66 private scenarios, exit 0. They cover each missing lock field,
boolean true and wrong-type values, non-object and malformed JSON, failed and timed-out reads,
old or absent engines, active and inactive installers, delivered/busy/cooldown/missing/failed
notifications, the deadline, an existing marker and failed timer stops. Every subprocess was
intercepted and checked against the exact command allowlist and configured timeout. Engine
files and notification markers were temporary fixtures; the main entry point's exception
handler was exercised. No live nudge, shell IPC or systemctl command ran.

The source uses only `lock status`, installer `is-active`, a nudge to `@barbarian` and stop of
its own timer. The native lock source establishes the four boolean fields, and hobnob's
`nudge_agent` implementation confirms that the matched delivery text belongs to its delivered
branch. Busy, cooldown and missing-terminal replies do not latch. An inactive-installer alert
does not latch or stop polling. Deadline notification requests manual inspection rather than
claiming successful installation. Delivery must be confirmed before the marker is written;
a failed stop retains the marker, so the next run retries only its own timer stop.

These tests do not arm or verify the systemd unit. The owner must supply the main desktop's
Omarchy path/display environment when arming it; `omarchy-shell` requires that path and uses
the display to select the shell. The lock read is only a sample: the returning agent must
check current lock state and feature gates again before any native operation. Missing files
or unreadable status retry without claiming readiness, and the deadline still requests manual
attention. The watcher neither proves native restore behavior nor closes the task itself.

## Final delivery evidence review

Delivery evidence is approved within the distinctions below. The independent read-only checks
on 3 November confirmed the reviewed engine installed on Enterprise, DS9 and Voyager. Each
installed `ws-layout` has SHA-256
`a37c96169d153a4f1b14eb90a276ae6996e6f421088806138ac3c4afebcf81a1`, equal to the source engine.
The application source, tests and README remain unchanged from `9c35986`; no source suite was
rerun for this delivery-only review. No additional application blocker was found.

The owner's retained `native-verification.json` records the installed engine restoring the
existing Messaging recording: the first result is `1 window in place, 1 opened`, and the second
is `already as saved`. Its `show 4` result is `desk now: as saved`. These are owner-operated
results, not restore commands rerun by this verifier. The original partial evidence is retained
as `native-verification-initial.json`.

Independent current reads corroborated the resulting state:

- The actual Messaging recording still contains one `org.quickshell` / `Skylark` entry with
  `launch: null`, and no floating entries. It is byte-identical to `messaging-before.json`.
- The main compositor reports exactly one mapped, tiled Skylark window on Messaging, at
  `0x559d0b7b6b90`, PID `3170160`. Both identifiers match the retained native result. That PID's
  command line is the main Omarchy Quickshell instance.
- The current workspace is Agents and the focused window is `0x559d09adb3d0`, matching the
  original desk/window recorded before the operation.
- All ten protected files match the owner's retained pre-operation hashes: six workspace
  recordings, features.json, quick-apps.json, shell.json and bar-hidden.json. The before hashes
  were captured by the owner; the matching current hashes were independently recalculated.

The owner reports that assertions comparing unrelated client addresses, PIDs, workspaces and
geometry passed during both restores. The original client snapshots were held only in memory,
so this verifier cannot independently reconstruct that comparison. The native JSON's boolean
claim is treated as an owner-executed assertion, not a retained before/after client trace.

The initial operator script failed a later comparison of the entire split-ratio `getoption`
object. The original option object was also held only in memory and is unavailable. The
independent current read is `float: 1.0` and `set: true`. Neither ratio equality nor a
metadata-only cause is established; the report and work document explicitly preserve this
limit. A failed comparison alone does not establish a source regression, and the split-ratio
helpers are unchanged in this patch. The successful reopening, retained null-launch recording,
current single window, protected-file hashes and returned focus have separate evidence.

This verifier ran no window dispatch, restore, summon, calendar action, installer, service
operation or notification. Native operation evidence is from Enterprise only; DS9 and Voyager
were checked by reading their installed engine hashes over SSH. Calendar records were not
opened or compared. Publication and task closure are outside this independent verification pass.
