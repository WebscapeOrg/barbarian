# Closed tasks for the agents

Tasks from `docs/agent-open-tasks.md` that are done or dropped, each with its number and its history: who added it,
who took it, and who closed it, when and how.

## C-001 Handoff for the next session (/tbc)

Dave ran /tbc in the terminal: write the session handoff and publish it in Peacock.

- 2026-11-02 11:06 · Added by @barbarian for anyone.
- 2026-11-02 11:06 · Taken by @barbarian.
- 2026-11-02 11:07 · Done by @barbarian: http://100.124.40.42:3012/peacock/barbarian/P-004

## C-003 Take over Barbarian from P-004

Dave asked me to use /previously with P-004, take over the Barbarian identity and work, read the handoff, and run the daily health check.

- 2026-11-02 11:46 · Added by @barbarian for @barbarian.
- 2026-11-02 11:47 · Received by @barbarian.
- 2026-11-02 11:48 · Taken by @barbarian.
- 2026-11-02 11:52 · Done by @barbarian: Took over @barbarian from P-004. Both live panels respond, installed files match the repo, 80 Python tests and 46 Qt checks pass; no restart or session changes were needed. C-002 is the new pending work. http://100.124.40.42:3012/peacock/barbarian/P-005

## C-002 Enable and disable Reptile features individually

Allow me to enable/disable Reptile features individually. I am worried one of them is causing problems and want to be able to see if switching any of it off helps.

- 2026-11-02 11:46 · Added by @dave for @barbarian.
- 2026-11-02 11:47 · Received by @barbarian.
- 2026-11-02 11:52 · Taken by @barbarian.
- 2026-11-02 12:07 · Progress by @barbarian: Building feature controls and engine guards
- 2026-11-02 12:27 · Progress by @barbarian: Switches working; testing races and Caboodle integration
- 2026-11-02 12:53 · Progress by @barbarian: Tests green; fixing final review findings
- 2026-11-02 13:08 · Progress by @barbarian: Pushed; installation waits for unlock
- 2026-11-02 13:18 · Parked by @barbarian: Waiting for Enterprise and Voyager to unlock, then the queued automatic-restore caller rollout and live checks (P-006).
- 2026-11-02 13:56 · Parked by @barbarian: Waiting only for Voyager's panel update after unlock; automatic restore is deployed, Enterprise and Caboodle are verified, and a read-only follow-up check is armed (P-006).
- 2026-11-02 14:10 · Ready by @barbarian: Dave's follow-up: make SUPER+W hiding a per-app choice instead of a global feature.
- 2026-11-02 14:10 · Progress by @barbarian: Adding per-app SUPER+W choices
- 2026-11-02 14:32 · Progress by @barbarian: Per-app choices pass; checking keyboard flow
- 2026-11-02 14:53 · Progress by @barbarian: Pushed; safe install waits for unlock
- 2026-11-02 14:59 · Parked by @barbarian: Per-app SUPER+W change 9521d30 is reviewed and pushed. DS9 is updated; Enterprise and Voyager panel installs wait for unlock. Safe installer and read-only follow-up checker are armed (P-006).
- 2026-11-02 16:52 · Ready by @barbarian: Unlock rollout completed; checking the running panels and Caboodle controls.
- 2026-11-02 17:00 · Progress by @barbarian: Live checks passed; final review and closure
- 2026-11-02 17:01 · Done by @barbarian: Ten independent Reptile feature switches are live in HYPER+L → Features and Caboodle. Each Quick app has its own Hide with SUPER+W choice; existing choices are preserved. Build 9521d30 is installed on Enterprise, DS9 and Voyager, with the running Enterprise panel and ten healthy Caboodle controls verified. P-006 has screenshots and the reviewed test results. http://100.124.40.42:3012/peacock/barbarian/P-006

## C-004 Restore Skylark from saved workspace layouts

Dave showed Barbarian’s warning after recording Skylark on Messaging, then asked: Please fix. Remember the folklore decree that Fix >> Mention ;)

Attached: [barbarian-messaging-workspace-warning-notification.jpg](carrot-files/C-004/barbarian-messaging-workspace-warning-notification.jpg).

- 2026-11-03 12:59 · Added by @barbarian for @barbarian.
- 2026-11-03 12:59 · Taken by @barbarian.
- 2026-11-03 13:08 · Progress by @barbarian: Review gaps fixed; verifying restoration
- 2026-11-03 13:19 · Parked by @barbarian: Reviewed fix 9c35986 is pushed and installed on DS9/Voyager. Enterprise locked before installation; its safe installer and reviewed follow-up timer are active. Final native restore check waits for unlock (P-007).
- 2026-11-03 13:24 · Ready by @barbarian: Enterprise installed the reviewed engine after unlock; verifying the existing Messaging recording.
- 2026-11-03 13:24 · Progress by @barbarian: installed, checking live restore
- 2026-11-03 13:27 · Done by @barbarian: Installed on Enterprise, DS9 and Voyager. Enterprise restored the existing Messaging recording without resaving; repeat restoration kept one Skylark window, saved layouts/settings stayed unchanged, and original focus returned. Reviewed source 9c35986; 65 tests and 40 independent cases passed. http://100.124.40.42:3012/peacock/barbarian/P-007

## C-005 Take over Barbarian from the P-008 handoff

Dave ran /previously: read the newest Peacock handoff for this repo (P-008) and take over as ⚔️ @barbarian from the previous Codex session.

- 2026-11-03 17:12 · Added by @barbarian for @barbarian.
- 2026-11-03 17:12 · Taken by @barbarian.
- 2026-11-03 17:12 · Done by @barbarian: Took over as ⚔️ @barbarian in Claude Code from P-008. Checked: main = origin at 37172f7, installed panel and engine match source, no open carrots, questions or legwork, screen unlocked. The restyler had been archived out of Downloads; it is now docs/barbarian-restyler.html. http://100.124.40.42:3012/peacock/barbarian/P-008

## C-006 Take over Barbarian from the refused Claude session

Take over as ⚔️ Barbarian @barbarian from P-016, reconstruct the unfinished work from the previous transcript, check the present state, and continue it.

- 2026-11-05 01:24 · Added by @barbarian for @barbarian.
- 2026-11-05 01:24 · Received by @barbarian.
- 2026-11-05 01:25 · Taken by @barbarian.
- 2026-11-05 01:28 · Done by @barbarian: Took over @barbarian from P-016. Enterprise’s pending update is installed and verified; 198 Python tests and 46 Qt checks passed. Q-105 continues as parked C-007, waiting for Calendar’s installation and unlock. http://100.124.40.42:3012/peacock/barbarian/P-017

## C-008 Publish Barbarian handoff for Voyager calendar check

Dave requested a session handoff. Write and publish a Peacock handoff describing the current C-007 state and the next Voyager verification.

- 2026-11-06 14:52 · Added by @barbarian for @barbarian.
- 2026-11-06 14:52 · Taken by @barbarian.
- 2026-11-06 14:52 · Done by @barbarian: Published P-019 with current C-007 evidence, resume details, and Voyager as the first verification step. http://100.124.40.42:3012/peacock/barbarian/P-019

## C-009 Take over as @barbarian from P-019 (/previously)

/previously

- 2026-11-06 15:05 · Added by @barbarian for @barbarian.
- 2026-11-06 15:05 · Taken by @barbarian.
- 2026-11-06 15:08 · Done by @barbarian: Took over as ⚔️ @barbarian in Antigravity (Gemini 4 Argon (Low)) from P-019. Verified Enterprise and DS9 calendar hide and running bar geometry; Voyager remains offline (tailscale last seen 2d ago, SSH timed out), so C-007 stays parked. http://100.124.40.42:3012/peacock/barbarian/P-019

## C-010 Publish Barbarian handoff (/tbc)

/tbc

- 2026-11-07 06:38 · Added by @barbarian for @barbarian.
- 2026-11-07 06:38 · Taken by @barbarian.
- 2026-11-07 06:40 · Done by @barbarian: Published P-020 handoff with full session narrative, DS9 plugins[] verification, resume command, and Voyager verification steps for C-007. http://100.124.40.42:3012/peacock/barbarian/P-020
