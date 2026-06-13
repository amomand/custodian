# Browser Session API

## Purpose

The browser shell lets the current terminal slice run in a local web page
without moving ship truth into the client.

It is deliberately small. It is not the future operating desk, story layer, or
graphical schematic. The web layer owns session lifecycle, transcript display,
serialised save/load, and UI snapshot delivery. The engine still owns state
transitions.

## Runtime Shape

```text
browser input -> local HTTP API -> BrowserSession.command()
-> GameEngine.handle(state, text) -> StepResult -> transcript and snapshot
```

`src/custodian/web_session.py` owns browser sessions. Each session has its own
`GameEngine`, mutable current `ShipState`, transcript events, and last message
block.

`src/custodian/web_server.py` exposes the local HTTP API with Python standard
library HTTP tools. It does not add a web framework dependency.

`src/custodian/ui_snapshot.py` projects `ShipState` into renderable web-safe UI
data: mission, objective, systems, navigation, schematic, arka advisory, raw
panels, action specs, transcript tail, and visual state.

`src/custodian/web_static/` contains the operating desk client: a vanilla,
build-free page that renders the `ui` snapshot into persistent panels and
dispatches action-spec commands through the same command endpoint as typed input.
See `docs/ui/operating-desk.md`.

## Endpoints

### `POST /api/session`

Creates a fresh session and returns its snapshot.

The opening transcript includes `opening_lines()` and the current terminal
status readout. This presentation read does not commit a command-history record,
matching the terminal startup behaviour.

### `GET /api/session/{id}/snapshot`

Returns renderable browser shell state:

- session id,
- beat,
- finished flag,
- outcome,
- current terminal status output,
- last message block,
- transcript tail,
- recent command history records.
- `ui`, a structured snapshot projection for future graphical clients.

It does not serialise the full `ShipState` to the client.

The normal `ui` snapshot and legacy web-shell line fields hide hidden state such
as manual familiarity, exact Dark exposure internals, drift stage, and sector
symptom loads. Navigation exposure is projected into qualitative bands.

### `GET /api/session/{id}/snapshot/dev`

Returns the same snapshot shape with `ui.dev` populated for local developer
inspection.

This is the explicit developer path for hidden values. It includes fields such
as drift stage, manual familiarity counters, exact total exposure, sector
symptom loads, and the full behaviour ledger (`ui.dev.behaviour_ledger`:
delegated/manual/raw counts by system or panel, standing-adjustment count, and
first delegation/raw timing). Normal client rendering should not use it. The
endpoint only responds to loopback clients.

### `POST /api/session/{id}/command`

Body:

```json
{ "command": "wait" }
```

Dispatches the text through `GameEngine.handle()`, appends player input and ship
output to the transcript, and returns the command messages plus a fresh
snapshot.

### `POST /api/session/{id}/save`

Returns the current state as existing persistence JSON:

```json
{ "save": "{...}" }
```

### `POST /api/session/{id}/load`

Loads state from save text:

```json
{ "save": "{...}" }
```

The loaded state replaces the session's current state and appends a transcript
line noting the restored beat.

### `GET /api/session/{id}/transcript`

Returns structured transcript events and a web-safe plain line transcript.
The operating desk's transcript export control downloads the plain line version
as a text file.

## Contracts

- Text commands route through the same engine path as terminal commands.
- The browser client renders API data and sends player commands; it does not
  decide game consequences or reconstruct simulation truth from dataclasses.
- Sessions do not share mutable `ShipState`.
- Save/load uses the existing `persistence.py` serialisation format. The HTTP
  API exchanges save text rather than arbitrary local filesystem paths.
- `ui.raw_panels` are projected from deterministic state, not arka prose.
- `ui.actions` are render specs for existing commands; dispatch still routes
  through `GameEngine.handle()`. This includes `kind: "standing"` actions
  (`assign`/`release`) and `kind: "focus"` actions (`focus`/`leave focus`).
- Standing-delegation posture (`ui.systems[id].standing`,
  `ui.navigation.standing`) and focus posture (`ui.focus_mode`) are shown because
  the player chose them. The behaviour ledger counts behind them — including
  `focus_beats` — are hidden, requiring the loopback-only dev snapshot. There is
  no visible trust meter.
- Action-spec `command` strings must resolve to their intended intent under the
  deterministic (no-AI) interpreter, since that is the default play mode. This is
  covered by a contract test in `tests/test_ui_snapshot.py`.
- Hidden values stay out of normal UI snapshots and legacy browser line fields;
  they require the explicit loopback-only dev snapshot endpoint.
- No-model operation remains available through `CUSTODIAN_AI=off` or
  `custodian-web --no-ai`.
- Terminal play remains available through `python3 main.py`.

## Local Run

```bash
PYTHONPATH=src python3 -m custodian.web_server --no-ai
```

Then open `http://127.0.0.1:8765`.
