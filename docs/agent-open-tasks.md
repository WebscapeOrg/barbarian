# Open tasks for the agents

Things Dave handed the agents to pick up and run with. Each has a number that is never reused (`C-NNN`), and a
finished one moves, with its number, to `docs/agent-closed-tasks.md`. Dave adds them from Caboodle or with
`carrot add`; an agent takes one with `carrot take` and closes it with `carrot done`; `carrot --help` explains.

## C-007 Hide the calendar icon after its update (Q-105)

Dave chose “Hide it again — back to how your bar was before the 2 November update” in Q-105. Continue the previous session’s pending work: wait for Calendar’s reviewed Enterprise install, then remove only the visible calendar entry under the bar-arrange-apply lock while unlocked, keep its hidden copy, and verify the result and ship propagation. Calendar’s installer fix must be live first so another update does not restore the icon.

- 2026-11-05 01:26 · Added by @barbarian for @barbarian.
- 2026-11-05 01:26 · Taken by @barbarian.
- 2026-11-05 01:26 · Parked by @barbarian: Waiting for Calendar’s reviewed Enterprise install and an unlocked screen; Q-105 is already decided. Enterprise and DS9 still list skylark on the bar.
- 2026-11-05 05:17 · Parked by @barbarian: Q-105 is settled. Waiting for Calendar’s reviewed Enterprise install and an unlocked screen; live registry still lists skylark and the visible calendar entry is unchanged.
- 2026-11-06 06:41 · Ready by @barbarian: Calendar’s reviewed update is installed and Enterprise is unlocked; applying Q-105 now.
- 2026-11-06 06:44 · Progress by @barbarian: Enterprise hidden and verified; checking ship propagation
- 2026-11-06 06:48 · Parked by @barbarian: Enterprise’s calendar icon is hidden and independently verified; hidden entry and all other settings are preserved (P-018). Waiting for Enterprise’s approved DS9 mirror sync and Voyager to reconnect for propagation checks; Voyager SSH timed out.
- 2026-11-06 06:53 · Parked by @barbarian: Q-105 is applied and verified on Enterprise and DS9: no visible calendar entry and one hidden copy on each (P-018). Waiting only for Voyager to reconnect and receive its normal mirror sync; fresh tailnet SSH retry timed out, so its applied state is unverified.
- 2026-11-06 14:55 · Parked by @barbarian: Voyager SSH alias voyager-ts timed out again after 8 seconds (exit 255) on 2026-11-06; its configuration and running bar remain unverified. Retry when Voyager reconnects. P-019 records the attempt.
- 2026-11-06 15:48 · Parked by @barbarian: Enterprise shell.json now includes {"id": "magpie-calendar"} in plugins[] with the bar icon hidden (magpie-calendar a5d910e). Waiting for @enterprise to sync the updated shell.json to DS9 (#8670) and for Voyager to come back online.
