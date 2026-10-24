# Open questions

## Q-104 The plugin id in the Atlas era

The machine renamed to Atlas today (atlas.anotherdave.net; every old host answers 403). The plugin's id is still `tinkerbell.arrange` — the old machine's name — and it appears in the IPC id, the plugin folder, and your HYPER+B / HYPER+L bindings block (`omarchy-shell tinkerbell.arrange …`). The installer already has the migration machinery from the reptile merge (old-id entry drop and removal), so a rename is one release plus a two-line change in your bindings.

**Should the plugin id rename now that the machine is Atlas?**

- Keep `tinkerbell.arrange` — it works everywhere today; the name keeps the machine it was born on.
- Rename to `atlas.arrange` — matches the machine; I migrate the old id automatically and send you the bindings diff.
- Rename to `barbarian.arrange` — the plugin's own name, machine-independent; same migration.
