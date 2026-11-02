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
