# Save / Load And Command History

## Purpose

Phase 1D adds game spine: the ability to preserve a watch and replay how the
player got there. Two pieces:

- **Save/load** of the full `ShipState`.
- **Structured command history** recorded on the state itself.

These exist for the same reason the design does: the game is about player
habits, so we need to capture and restore the exact state those habits produced,
with a path to intentional seed fixtures once key story or mechanic moments settle.

## State Serialisation

`custodian.persistence` is pure and importable. It does not touch the engine.

- `state_to_dict` / `state_from_dict` convert `ShipState` (including the nested
  mission clock, reactor, cryostasis, crisis, the previous-telemetry snapshots
  used for trends, and command history) to and from plain dicts.
- `dumps` / `loads` are the JSON string forms.
- `save_state` / `load_state` read and write a file (default
  `saves/custodian-save.json`).

Saves carry a `version` field. Version 2 adds `MissionStatus`; version 1 saves
load with a default mission clock so Phase 1D local saves can still be opened.
Loading an unknown version raises `ValueError` rather than silently importing an
incompatible save. Round-trip equality is covered by `tests/test_persistence.py`.

## Command History

`ShipState.history` is a tuple of `CommandRecord` entries. Each record stores the
raw command text, interpreted action, optional target/operation, whether the
command advanced the watch, and the beat after handling. The engine records it
centrally in `GameEngine.handle`, so every player command is captured without
threading bookkeeping through each branch. Developer colon-commands (`:debug`,
`:save`, ...) are not recorded as play.

History travels with the save, so a restored watch carries its own provenance.

## Terminal Commands

Save/load are maintainer-facing and therefore colon-prefixed and non-diegetic,
consistent with `:debug` and `:metrics`. They are handled in the CLI layer so the
engine stays pure:

```
:save            write the current watch to saves/custodian-save.json
:save path.json  write to a specific path
:load            restore from saves/custodian-save.json
:load path.json  restore from a specific path
```

Seed saves for known story or mechanic moments should live as intentional
fixtures once their moments are stable. Ordinary local saves belong under
`saves/`, which is ignored by git.

## Boundaries

- The engine remains the only authority over state transitions. Persistence only
  serialises and deserialises; it never advances time.
- Keeping the engine pure preserves the Phase 4 path of wrapping the same engine
  in a web session API.
