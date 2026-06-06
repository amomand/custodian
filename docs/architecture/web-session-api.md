# Browser Session API

## Purpose

The browser shell lets the current terminal slice run in a local web page
without moving ship truth into the client.

It is deliberately small. It is not the future operating desk, UI snapshot
projection, story layer, or graphical schematic. The web layer owns session
lifecycle, transcript display, and serialised save/load. The engine still owns
state transitions.

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

`src/custodian/web_static/` contains the minimal static client.

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

It does not serialise the full `ShipState` to the client.

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

Returns structured transcript events and a plain line transcript.

## Contracts

- Text commands route through the same engine path as terminal commands.
- The browser client renders API data and sends player commands; it does not
  decide game consequences.
- Sessions do not share mutable `ShipState`.
- Save/load uses the existing `persistence.py` serialisation format. The HTTP
  API exchanges save text rather than arbitrary local filesystem paths.
- No-model operation remains available through `CUSTODIAN_AI=off` or
  `custodian-web --no-ai`.
- Terminal play remains available through `python3 main.py`.

## Local Run

```bash
PYTHONPATH=src python3 -m custodian.web_server --no-ai
```

Then open `http://127.0.0.1:8765`.
