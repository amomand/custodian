# Operating Desk UI

## Purpose

The operating desk is the first real graphical ship console. It replaces the
browser status dump with persistent panels: a mission strip, arka advisory, an
active system panel, a ship schematic, an incident/objective strip, a raw
telemetry drawer, and a transcript/action log.

It is a thin client. It renders the `ui` snapshot projected by
`src/custodian/ui_snapshot.py` and dispatches commands through the same engine
path as the text channel. It never reconstructs simulation truth, decides
consequences, or reads hidden values.

The client lives in `src/custodian/web_static/` (`index.html`, `styles.css`,
`app.js`) and stays a dependency-free vanilla page with no build step.

## Regions

```text
+--------------------------------------------------------------------------------+
| MISSION STRIP: elapsed | distance | wear | cryo decay | sleepers | fix | watch |
+----------------------+--------------------------------+------------------------+
| SHIP SCHEMATIC       | ACTIVE SYSTEM PANEL            | arka ADVISORY          |
| sectors + symptoms   | coolant / cryo / nav / contain | advice + command input |
+----------------------+--------------------------------+------------------------+
| INCIDENT / OBJECTIVE | RAW TELEMETRY DRAWER           | TRANSCRIPT / ACTION LOG|
+--------------------------------------------------------------------------------+
```

On desktop the desk is locked to the viewport and individual panels scroll. Below
1100px it becomes a two-column scrolling stack; below 760px a single column with
arka and the command channel near the top.

- **Mission strip** is instrument readout, not arka's voice: elapsed time,
  distance, ship wear, cryo decay, sleepers lost / at risk, current fix, and the
  watch label. A finished run shows the outcome banner here.
- **arka advisory** is deliberately the easiest panel to read. It shows the
  current drift-aware summaries and the recent arka channel, with the command
  input pinned beneath it. That readability is the trap.
- **Active system panel** has four tabs — Coolant, Cryostasis, Navigation,
  Containment — each with arka's summary, raw metrics, and the manual / delegated
  controls for that system. The Navigation tab renders the current fix and the
  candidate routes as a branching route display: each branch leads with
  qualitative exposure / instability bands and keeps the exact route facts as a
  detail line, with plot and execute-jump per route.
- **Ship schematic** renders the sectors as a connected deck diagram: nodes sit
  on a fixed plan and the connecting edges come from each sector's reported
  adjacency. Node and edge styling follow reported state, signal confidence, and
  containment; selecting a node focuses the Containment tab. Every node keeps its
  textual state in its label and `aria-label`, so corruption never removes the
  readable version.
- **Incident / objective** shows the watch objective and any active incident.
- **Raw telemetry drawer** holds the five raw panels (mission, coolant,
  cryostasis, navigation, schematic) as expandable, source-labelled readouts.
- **Transcript / action log** toggles between the narrative transcript and the
  structured command history.

## Actions come from the snapshot

Every button is generated from a `ui.actions` action spec. The client groups them
by `kind` and `target`:

| kind         | placement                                            |
| ------------ | ---------------------------------------------------- |
| `manual`     | active system panel, by target system               |
| `delegate`   | active system panel, "Delegate" group               |
| `raw`        | active system panel, "Inspect" group                |
| `navigation` | Navigation tab (plot per route, execute jump)        |
| `containment`| Containment tab, by selected sector                  |
| `watch`      | objective panel ("Wait one beat")                    |

A button dispatches its action spec's `command` string. UI commands and typed
commands route through the same `GameEngine.handle()` path, so the action specs
must round-trip through the deterministic (no-AI) interpreter — see the contract
test in `tests/test_ui_snapshot.py`.

Disabled specs (`enabled: false`) render disabled with their `reason` as a
tooltip. Specs marked `requires_confirmation` (triage, seal, abandon, jump) open
an inline diegetic confirmation strip before dispatch; nothing irreversible fires
on a single click.

## Deliberate boundaries

- **No hidden values.** The desk only renders the normal snapshot. Trust, manual
  familiarity, drift stage, exact Dark exposure, and sector symptom loads never
  appear. Navigation exposure is shown only as a qualitative band, and there is
  no Dark meter.
- **Visual corruption maps to deterministic state, never to new truth.**
  `visual_state` drives the look only. Sector noise degrades schematic nodes and
  edges (`steady` / `thin` / `disagreeing` / `broken` / `isolated` / `blank`);
  drift sets the schematic's `label_instability` wobble and the arka panel's
  `arka_panel_intensity` atmosphere. The drift atmosphere is deliberately
  *deniable* — as arka's account rots its panel reads calmer, not noisier — so the
  player still catches drift by reading raw, not from a legible tell.
  `arka_panel_intensity` and `label_instability` are applied only as `data-*`
  hooks and must never be printed as text (that would leak the hidden drift
  stage); a snapshot test guards against the leak.
- **Corruption never hides essential information.** Every degraded sector keeps
  its reported state and signal confidence as text (node label and `aria-label`),
  and raw panels keep their confidence chips. All corruption motion is gated
  behind `prefers-reduced-motion` and the reduced-motion toggle, which leave the
  desk fully static and legible. No Dark percentage is ever shown.
- **arka cannot be contained.** The schematic exposes `arka_locus` ("no
  compartment...") and offers no seal/reroute/abandon control for arka.

## Keyboard and accessibility

- `1`–`4` switch the active system tab; arrow keys move within the tablist.
- `/` focuses the command channel; `.` waits one beat; `?` opens diagnostics;
  `Escape` cancels a pending confirmation or blurs the command input.
- All controls are native buttons/inputs, tab-navigable, with ARIA roles on the
  tablists and labelled landmarks per region.
- Schematic sectors are native buttons whose `aria-label` carries the full
  textual state; the connecting edge layer is decorative and `aria-hidden`.
- Route exposure and instability are shown as labelled bands with the band word
  (and exact percentage) as text, not pips or colour alone.
- Metric bands and signal confidence are shown as text, not colour alone.
- Motion is gated behind `prefers-reduced-motion`, with a manual "Reduced motion"
  toggle in the diagnostics footer.

## Save / load

The diagnostics footer carries the session image buffer and Save / Load buttons.
Save/load uses the existing persistence JSON via the web API; it stores engine
run state, not UI component state. UI-local state (active tab, selected sector,
expanded raw panels, log view) is held only in the client and is not persisted.

## Local run

```bash
PYTHONPATH=src python3 -m custodian.web_server --no-ai
```

Then open `http://127.0.0.1:8765`.
