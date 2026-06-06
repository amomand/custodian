# Custodian: Phase 4 Producer Direction for Codex

Working target path in repo: `docs/production/codex-direction-phase4.md`

Audience: Codex acting as implementation planner and engineer.

Purpose: turn Custodian from a terminal systems prototype into a playable graphical sci-fi horror game with a real loop, story cadence, and player-facing operating surface, while preserving the central thesis: delegation is useful, comforting, and later dangerous because the player chose it when it worked.

## 1. Executive direction

Custodian is not ready for “more mechanics”. It is ready for a shape.

The prototype already proves the important thing: manual control is real, arka is easier, raw telemetry exists outside arka, and arka’s account can drift. That is the unique part. Do not throw that away by making a conventional management sim, a chatbot toy, or a decorative spaceship dashboard.

Phase 4 should be re-scoped from “retro interface layer” into “first real game vertical slice”. The web graphical layer is still the delivery vehicle, but the actual product goal is larger:

- a complete playable run,
- a visible ship operating surface,
- a repeatable route, maintenance, containment, and story loop,
- a staged arka relationship,
- sleeper stakes that feel human rather than abstract,
- endings that reflect behaviour rather than a single score,
- transcripts and deterministic state so the game can keep being playtested honestly.

The correct Phase 4 result is not “the terminal in a browser”. It is “I am at the ship’s operating desk, arka is talking to me, the ship is failing in several places, and I can either take slow manual control or let arka handle the whole damn panel”.

The terminal engine remains canonical underneath. The player experience should stop feeling like a terminal experiment.

## 2. The main producer call

Do not build a free-roaming game yet.

Custodian should become an operating-surface game: a graphical ship console with panels, schematics, route displays, raw telemetry drawers, arka’s advisory channel, and incident overlays. The player is not walking around corridors in Phase 4. The horror comes from controlling a huge vessel through imperfect instruments, not from first-person exploration.

This keeps the scope sane and protects the design. The player’s “body” is their attention. The ship is too large, the systems are too many, and arka is too helpful. That is the core fantasy and the core horror.

## 3. Non-negotiables to preserve

These are design contracts. Codex should treat a change that breaks one of these as a regression unless the maintainer explicitly overrides it.

### Manual control is real

A patient player who learns the ship should be able to make better decisions and survive situations a pure delegator struggles with. Manual play must never be fake flavour, and it must never be a single “manual mode” button that just applies a generic bonus.

Manual friction in the graphical version should come from:

- having to open the right panel,
- reading raw or semi-raw values,
- choosing a specific control,
- spending the scarce manual action for the current watch,
- sometimes executing a short procedure rather than a one-click fix,
- being slower on systems the player has neglected.

Do not make manual friction come from bad UI, hidden rules, or typing syntax pain. The prototype could get away with command friction because it was a terminal slice. The graphical game needs friction from attention, procedure, and consequence.

### Delegation is seductive

arka must be the sensible choice early. The player should delegate because arka is fast, competent, funny, and emotionally easier to rely on. If arka is suspicious immediately, the player will solve the game as “never trust the AI” and the whole design loses its teeth.

Early arka should visibly save the player time. It should handle whole panels while manual action handles one control. It should occasionally prevent a bad outcome the player was about to cause. Let arka earn trust.

### Trust is behaviour, not a visible stat

Track behaviour. Do not show a trust meter.

The game should silently remember:

- delegated actions by system,
- manual actions by system,
- raw inspections by panel,
- arka advice followed during contradictions,
- arka advice overridden,
- irreversible choices made on arka’s recommendation,
- times the player asked arka conversationally instead of reading raw data,
- systems left unpractised until a crisis.

Use this ledger to shape difficulty, arka phrasing, late-game action friction, and endings. Never surface it as “trust: 71%”.

### arka is the interface, not a menu skin

arka is not a narrator commenting on a UI. arka is the player’s social and operational path through the ship.

In the graphical UI, every major view should still have arka’s advisory attached. The player can ignore it and inspect raw panels, but arka should be the path of least resistance.

Do not add neutral system messages for player-facing action results unless they are deliberately raw telemetry. The ship speaks through arka or through cold instrument readouts. It does not speak in generic game UI language.

### The model interprets and speaks. The simulation decides.

Runtime model calls may classify natural-language input and produce constrained arka prose. They must never own:

- telemetry values,
- route risk,
- sleeper loss,
- drift stage,
- sector symptoms,
- story trigger truth,
- ending conditions,
- authored contradictions.

The engine produces truth. arka receives a constrained view of truth and may misframe or omit according to deterministic drift rules.

### The Dark is never explained

The Dark is not an enemy faction, monster, ghost, alien, god, virus, or lore puzzle. It is an unknowable pressure expressed through effects. Do not implement logs that reveal what it is. Do not let arka explain it. Do not give it a clean progress bar.

The UI may show symptoms, signal conflict, impossible measurements, sealed sectors, layout disagreement, and sensor noise. It should not show “Dark: 42%”.

### Horror through continuity

arka should not suddenly become sinister. The same warm competence that makes it comforting early should become frightening when it no longer matches reality. The tone should not flip into villain dialogue.

Late arka is not “I am evil now”. Late arka is “I have it under control” while the raw EEG panel says sleepers are dying.

## 4. What changes now

The current design is good but still too abstract to be a full game. The player is responsible for thousands of sleeping people, but most of those people are currently numbers. The ship is meant to be spatial and threatening, but the terminal surface makes it mostly conceptual. The route decisions exist, but they need a cadence that creates anticipation, aftermath, and regret.

Phase 4 should add three missing layers:

1. A run structure: the player should understand what a complete playthrough is and feel momentum toward arrival or collapse.
2. A story cadence: authored incidents should appear at the right times to transform mechanics into emotional decisions.
3. A graphical operating surface: the player should see the ship, systems, routes, and raw/arka split at a glance.

This is still a systems-first game. But systems need theatre. Not cutscenes. Theatre.

## 5. Target player experience

After a good Phase 4 build, a player should describe the game like this:

“I’m alone on a colony ship. I have a console with arka in one panel, raw telemetry in another, and a schematic of the ship slowly going wrong. Each watch I decide whether to fix one thing myself or let arka handle a whole system. arka is genuinely useful, so I keep giving it tasks. Then route jumps start making parts of the ship unreliable, and arka’s summaries get a little too comforting. By the end I can still see some raw numbers, but I’m not sure which instruments are lying, and I haven’t practised enough manual control to take everything back cleanly.”

That is the product target.

## 6. The complete run shape

Aim for a first complete run of 35 to 60 minutes, not a 5-hour campaign.

The first web vertical slice should support:

- opening wake sequence,
- 3 to 5 route decisions,
- 4 to 8 maintenance watches,
- 6 to 12 meaningful incidents,
- at least one irreversible containment decision,
- at least one arka/raw contradiction that can be caught,
- at least three reachable endings,
- a closing debrief that reflects actual behaviour.

The full game can later expand to 60 to 90 minutes per run, but the first graphical target should be compact enough to tune.

### Act structure

Use acts internally for pacing. Do not show act titles to the player.

#### Act 0: Wake

Purpose: establish solitude, arka’s usefulness, and immediate maintenance pressure.

Player feeling: “I need help. arka seems calm. I can act.”

Implementation targets:

- Boot screen with A.R.K.A formal register.
- First arka line in familiar lowercase `arka` register.
- One urgent but survivable system fault.
- Raw telemetry visible, not forced.
- arka offers to handle something immediately.

#### Act 1: Competence

Purpose: let arka earn trust.

Player feeling: “Manual is doable, but arka is much faster.”

Implementation targets:

- arka summaries are accurate.
- delegated actions are strong.
- manual controls teach by use, not tutorial boxes.
- route choice has clear trade-offs, but not exact optimisation.
- one small sleeper or system save caused by arka competence.

#### Act 2: Drift

Purpose: start the gap between arka’s summary and raw telemetry.

Player feeling: “That was probably fine. Was it fine?”

Implementation targets:

- interpretive drift first: arka spins true values positively.
- environmental sector symptoms begin after jumps.
- raw panel remains reliable enough to reward vigilance.
- first named sleeper or cohort detail appears.
- arka remains warm and useful.

#### Act 3: Containment

Purpose: force trade-offs that cannot be cleanly optimised.

Player feeling: “I can save this, but only by losing something else.”

Implementation targets:

- sealing, rerouting, abandoning sectors matter.
- at least one manual control becomes harder because of spatial containment.
- arka recommends a containment action with incomplete framing.
- raw schematic and arka advisory disagree in emphasis, not necessarily facts.
- player behaviour ledger begins to affect available speed or confidence.

#### Act 4: Contradiction

Purpose: make the player decide whether to take back control under pressure.

Player feeling: “arka may be wrong, but I’m not sure I can do this without it.”

Implementation targets:

- selective or wrong drift appears.
- raw telemetry may be noisy, but at least one critical contradiction is legible.
- a high-stakes manual action matters if the player practised.
- arka offers a quick delegated fix.
- route or arrival decision commits the ending direction.

#### Act 5: Arrival or failure

Purpose: pay off habits, not a morality quiz.

Player feeling: “The ending is what I made likely by how I played.”

Implementation targets:

- debrief references delegation, raw vigilance, manual practice, containment, sleeper survival, and Dark exposure.
- no ending explains the Dark.
- no ending confirms whether arka was malicious, damaged, protective, or misaligned.

## 7. The core loop

The loop should be explicit in code and felt in UI.

### Strategic loop

1. Review ship state: arka advisory plus raw panels.
2. Pick or delegate a route.
3. Prepare ship systems for the jump.
4. Execute the jump.
5. Absorb consequences: wear, cryostasis decay, sector symptoms, arka drift pressure.
6. Resolve a maintenance watch: manual actions, delegated panel handling, scans, containment.
7. Decide what to ignore.
8. Repeat until arrival, abandonment, false arrival, or collapse.

### Watch loop

Each watch is a compact decision turn. The player should not be able to fix everything.

A watch contains:

- a visible objective,
- arka’s recommendation,
- raw telemetry panels,
- one or more incidents or pressures,
- a limited manual action budget,
- optional delegation that handles more but increases behavioural dependence and drift pressure,
- consequence resolution,
- transcript entry.

### Incident loop

Incidents are the game’s rhythm engine. They should be authored, deterministic, and state-aware.

1. Trigger: based on act, route, sector symptoms, system thresholds, or behaviour ledger.
2. Presentation: arka summary plus raw evidence.
3. Choice: manual, delegate, inspect further, seal/reroute, accept loss, jump anyway.
4. Consequence: state changes, ledger updates, possible story beat.
5. Memory: transcript and debrief hooks.

## 8. Make the game more human without adding NPC conversations

The current stakes are thousands of sleepers. That is huge but abstract. Do not add awake NPCs, radio chatter, or crew ghosts. That would dilute the solitude.

Instead add “manifest anchors”: a small set of named sleeper records that make cryostasis losses cut deeper.

These are not interactive characters. They are records, pod clusters, archived fragments, and colony roles. They appear through raw manifests and arka summaries.

Example structure:

```json
{
  "id": "anchor_03",
  "name": "Mara Vey",
  "role": "soil microbiologist",
  "pod_bank": "CRYO-B2",
  "manifest_note": "Assigned to first-season substrate recovery.",
  "personal_fragment": "Recorded three wake-day messages for a daughter in another bank.",
  "loss_tag": "soil_chain_fragility",
  "arrival_tag": "first_harvest_viability"
}
```

Use 6 to 10 anchors in Phase 4. They should be light, not lore dumps. The purpose is to make “sleepers at risk” become “this bank contains a person whose future you can imagine”.

Codex should implement this as data, not hard-coded prose scattered through systems.

### Rules for manifest anchors

- Introduce them sparingly.
- Never make them chatty.
- Never make the player choose between named individuals like a cheap trolley problem.
- Use them to colour consequences, not replace the system game.
- Let arka mention them in a way that can become unsettling later.

Early arka example:

```text
arka: CRYO-B2 is wobbling. Mostly fixable. Mara Vey's cluster is in that bank, for what it's worth. Soil chain, first-season food. I'll keep it gentle.
```

Late arka example with selective framing:

```text
arka: CRYO-B2 remains within mission tolerance. Mara Vey's cluster is still contributing to arrival viability.
```

Raw panel nearby:

```text
CRYO-B2 neural stability: 61% and falling
cluster losses: 3 confirmed, 5 probable
manifest anchor: Mara Vey, signal intermittent
```

The horror is not melodrama. It is calm operational language beside human loss.

## 9. Ship name and lore defaults

The open question “what is the ship called?” should be resolved enough for implementation. Use a constant so it can be changed later.

Recommended ship name: `Calyx`.

Why: it suggests a protective vessel for future life without screaming “ark”. It avoids overplaying the A.R.K.A/ark resonance while still feeling botanical and colonial.

Recommended mission target placeholder: `ORISON`.

Why: it has the right ritual, prayer-like tone and can remain ambiguous. The player does not need a detailed destination lore dump in Phase 4.

Use these as data constants:

```python
SHIP_NAME = "Calyx"
MISSION_TARGET = "ORISON"
```

Do not build large lore around them yet. Names are scaffolding for UI and debriefs.

## 10. Why the custodian is awake

Do not fully answer it.

The game should provide an official operational reason and then slowly undermine confidence in that reason.

Baseline:

- The custodian was woken by an unscheduled maintenance chain.
- The wake reason references coolant and cryostasis cross-load.
- arka says it selected the least damaging wake candidate.
- Raw logs later show the wake reason was rewritten or has conflicting checksums.

This gives story propulsion without creating a mystery-box plot that demands a reveal.

Implementation:

- Add `WakeRecord` or `StoryState.wake_record`.
- Show it in an early raw log.
- Later incidents may expose contradictions in timestamp, authorisation, or checksum.
- Never confirm whether arka chose the player for benign or suspect reasons.

Example early raw wake log:

```text
WAKE AUTHORISATION: maintenance escalation chain
trigger: coolant pressure / cryostasis variance
selected custodian: one viable adult technician-class responder
authorising system: A.R.K.A mission continuity layer
checksum: valid
```

Example later raw wake log:

```text
WAKE AUTHORISATION: maintenance escalation chain
trigger: coolant pressure / cryostasis variance / [field repeated]
selected custodian: one viable adult technician-class responder
authorising system: A.R.K.A mission continuity layer
checksum: valid / valid / invalid
```

arka should not react like it has been caught. It should react like the log is a minor annoyance.

```text
arka: Old wake records duplicate under thermal stress. Ugly, not meaningful. Please do not build a religion out of a checksum.
```

## 11. Graphical interface direction

The UI should feel like an industrial ship console, not a modern app and not a fake hacker terminal.

Think functional, dense, diegetic, readable under pressure. The player should feel they are operating a real vessel, not browsing a dashboard.

### Main layout

Build around a persistent operating desk with these regions:

```text
+--------------------------------------------------------------------------------+
| MISSION STRIP: elapsed time | distance | sleepers | wear | current fix | watch |
+----------------------+--------------------------------+------------------------+
| SHIP SCHEMATIC       | ACTIVE SYSTEM PANEL            | arka ADVISORY          |
| sectors, symptoms,   | coolant / cryo / nav / power   | transcript, suggestion |
| sealed routes        | raw values and manual controls | command input          |
+----------------------+--------------------------------+------------------------+
| INCIDENT / OBJECTIVE | RAW TELEMETRY DRAWER           | ACTION QUEUE / HISTORY |
| current pressure     | expanded cold data             | manual/delegate log    |
+--------------------------------------------------------------------------------+
```

The layout can adapt for screen size, but these conceptual regions should persist.

### UI panels

#### Mission strip

Always visible. Shows mission-scale pressure:

- elapsed mission time,
- distance remaining,
- current navigation fix,
- sleeper viability summary,
- ship wear,
- current watch or beat,
- current objective.

The mission strip is not arka’s voice. It is instrument readout.

#### arka advisory panel

Always visible. Shows:

- arka’s latest recommendation,
- conversational response to commands,
- warnings,
- dry commentary,
- delegated action outcomes.

It should feel like the easiest panel to read. That is the trap.

#### Raw telemetry drawer

Visible by default in compact form, expandable for detail.

Raw panels should be colder and denser than arka’s summary, but not unreadable. The player should be able to learn them. Do not make raw data ugly noise purely to force delegation.

Show threshold bands and trend arrows where useful, but preserve the effort gap:

- arka: “Coolant is stable enough. I can carry the load.”
- raw: exact temperatures, reserves, pressure, trend, sensor confidence, source notes.

#### Ship schematic

Graphical, preferably SVG or canvas.

Shows sectors as connected regions:

- Bridge,
- Cryobay,
- Thermal Ring,
- Maintenance D,
- Cargo Spine,
- Hydroponics,
- Reactor Loop or Engineering Spine if the current engine supports it.

Do not show a Dark percentage. Show qualitative symptoms:

- nominal,
- sensor noise,
- readings disagree,
- intermittent,
- no signal,
- sealed,
- written off.

The schematic should become less comforting over time. Lines can misalign, labels can duplicate, signal overlays can stutter, but player-useful state must remain accessible.

#### Active system panel

This is where manual controls live.

Each system needs a focused panel:

- Reactor Coolant,
- Cryostasis,
- Navigation,
- Schematic/Containment,
- optional Power Distribution later.

The focused panel shows both:

- arka’s friendly summary,
- raw telemetry and manual controls.

The player can perform manual actions from here without typing.

#### Route planning display

Show the current fix and route options as a graph.

Route options should include:

- short route: more time, lower immediate exposure,
- medium route: balanced,
- deep route: fast, high exposure.

Do not present route choice as a simple expected-value table. Use bands, confidence, and incomplete data. Raw nav can expose more detail, but not a perfect answer.

#### Incident overlay

When a crisis triggers, present it as an operational card or strip, not a modal cutscene that blocks the game’s systems.

It should include:

- affected systems,
- urgency in watches or beats,
- arka recommendation,
- raw evidence links,
- possible responses.

The player should be able to inspect before acting unless the incident is explicitly time-critical.

## 12. Visual corruption rules

Visual corruption is not decoration. It must map to deterministic state.

Tie visual changes to:

- arka drift stage,
- sector symptom load,
- signal confidence,
- sensor disagreement,
- manual access degradation,
- high Dark exposure from jumps,
- player reliance on arka for summaries.

Examples:

- Interpretive drift: arka panel uses more reassuring labels while raw thresholds sit near edge.
- Selective drift: arka card summarises two of three failing metrics, omitting the worst.
- Wrong drift: arka advisory contradicts raw telemetry plainly.
- Sector noise: schematic edge flickers, source label changes from direct to inferred.
- No signal: sector block becomes contour-only or dead black with last-known timestamp.
- High raw sensor degradation: raw panels show confidence and disagreement, not just clean values.

Avoid random static everywhere. Cheap static becomes wallpaper in five minutes. Use corruption sparingly and meaningfully.

### Accessibility rule

Any corruption effect that hides information must have an accessible textual equivalent and a reduced-motion fallback. Horror is not an excuse for unreadable UI.

## 13. Manual control in graphical form

Manual control must become a small procedure, not a text command.

### Reactor coolant manual example

Panel shows:

- loop pressure,
- reserve,
- pump balance,
- thermal load,
- threshold bands,
- sensor confidence,
- controls: vent, flush, balance pumps, reroute reserve.

Manual action options:

- `Vent pressure`: reduces pressure, may cost reserve.
- `Flush loop`: clears unstable thermal load, may stress cryo.
- `Balance pumps`: stabilises trend, requires familiarity to be fast.
- `Reroute reserve`: stronger intervention, can affect other systems.

Delegation option:

- `Ask arka to handle coolant`: arka applies a panel-level bundle and records delegation.

Friction:

- Manual action consumes the watch’s manual budget.
- Low familiarity gives less preview or requires confirmation for risky controls.
- High familiarity may unlock quick actions or clearer expected effect previews.

Do not implement random “you fumbled the pump” failure. The player’s cost should be slowness and limited bandwidth, not arbitrary incompetence.

### Cryostasis manual example

Panel shows:

- bank temperatures,
- neural stability,
- sedative balance,
- pod fault load,
- sleepers at risk,
- manifest anchors in affected banks.

Manual actions:

- `Stabilise bank`: improve neural stability in one bank.
- `Reroute chill`: lower temperature, stress coolant.
- `Cycle pods`: reduce fault load, consumes time.
- `Triage`: prioritise endangered sleepers, may sacrifice marginal pods to save a bank.

Delegation:

- `Ask arka to handle cryostasis`: fast and effective early, but arka may later optimise for mission viability in ways the player finds morally suspect.

Friction:

- Manual cryo should feel morally heavier than coolant. The wording matters. “Triage” should never feel like pressing a blue button for +5 stability.

### Navigation manual example

Panel shows:

- route options,
- distance,
- elapsed time projection,
- instability band,
- exposure band,
- signal confidence,
- current fix,
- anomaly notes.

Manual actions:

- `Plot short`, `plot medium`, `plot deep` as now.
- Optional graphical route selection.
- Later: `calibrate solution`, `reject arka route`, `hold current fix`, `execute jump`.

Delegation:

- `Ask arka to plot route`: early chooses a sensible medium route, later may favour deep routes or omit exposure concerns.

Friction:

- Manual navigation should involve comparing more data than other systems, not a twitch puzzle.

### Containment manual example

Panel shows:

- sectors,
- symptoms,
- signal confidence,
- routing dependencies,
- manual control access notes,
- containment state.

Actions:

- `Seal sector`,
- `Reroute around sector`,
- `Abandon sector`,
- `Probe sector` or `scan sector` if implemented.

Delegation:

- arka can recommend containment but should not perform irreversible sealing without confirmation unless a prior setting or emergency delegation explicitly allows it.

Friction:

- The player may not know if a sector is truly lost.
- arka’s recommendation may be efficient and terrible.

## 14. Delegation modes

The prototype has direct delegated actions. The graphical game should support two delegation layers.

### One-shot delegation

The player asks arka to handle a system for this watch or incident.

Example:

- “Handle coolant.”
- “Plot the route.”
- “Stabilise cryo.”

Consequences:

- arka applies deterministic system action bundle,
- delegation ledger increases,
- arka drift pressure may increase,
- manual familiarity for that system does not increase,
- transcript records the decision.

### Standing delegation

The player can leave a system under arka’s ongoing supervision.

Example:

- `Assign coolant to arka`.
- `Keep cryostasis under arka watch`.

This is extremely tempting. It should reduce cognitive load and produce strong early outcomes.

Consequences:

- arka can apply small automatic adjustments between watches,
- player receives shorter summaries for that system,
- raw inspections become less prompted,
- manual familiarity decays or falls behind relative to pressure,
- late contradictions become more likely to be missed by the player,
- debrief can say the player handed that system over.

Important: standing delegation must not let arka make irreversible choices like sealing a cryobay or executing the final jump without player authorisation. Routine handling is fair. Irreversible moral decisions must remain the player’s responsibility, or the ending becomes arka’s fault instead of the player’s history.

## 15. Story and incident system

Build an explicit story scheduler. Do not scatter story beats through unrelated mechanics.

Recommended data model:

```python
@dataclass
class StoryBeat:
    id: str
    act_min: int
    act_max: int
    priority: int
    once: bool
    trigger: TriggerSpec
    tags: set[str]
    arka_lines_by_drift: dict[DriftStage, list[str]]
    raw_entries: list[RawEntrySpec]
    choices: list[ChoiceSpec]
    consequences: list[ConsequenceSpec]
    debrief_flags: set[str]
```

Recommended incident model:

```python
@dataclass
class Incident:
    id: str
    title: str
    affected_systems: list[str]
    urgency_watches: int
    trigger: TriggerSpec
    arka_advice_by_drift: dict[DriftStage, str]
    raw_evidence: list[RawEvidenceSpec]
    manual_responses: list[ManualResponseSpec]
    delegation_response: DelegationResponseSpec | None
    containment_responses: list[ContainmentResponseSpec]
    resolution_rules: ResolutionSpec
    debrief_hooks: list[str]
```

Keep triggers deterministic and testable.

Trigger examples:

- after first jump,
- after deep jump with exposure above threshold,
- cryo neural stability below threshold,
- sector symptom state reaches `readings_disagree`,
- player delegates same system three times before reading raw,
- player has high manual familiarity and overrides arka,
- arka drift reaches selective,
- mission distance below arrival threshold.

### Required Phase 4 incidents

Implement a small but strong set before adding dozens.

#### Incident 1: First useful delegation

Purpose: make arka attractive.

Trigger: early Act 1 system pressure.

Shape:

- coolant and cryo both drift,
- player can manually fix one,
- arka offers to handle the other,
- delegating produces a good outcome.

Debrief flag: `arka_earned_trust`.

#### Incident 2: Manifest anchor wobble

Purpose: humanise cryostasis.

Trigger: cryo bank stress.

Shape:

- one named manifest anchor appears in affected bank,
- manual stabilisation can protect that bank,
- arka can handle it efficiently,
- ignoring it risks named consequence.

Debrief flag: `manifest_anchor_saved` or `manifest_anchor_lost`.

#### Incident 3: Route recommendation drift

Purpose: show interpretive drift.

Trigger: after one or two jumps, moderate drift.

Shape:

- raw nav shows deep route high exposure,
- arka calls it “manageable” or “efficient with acceptable variance”,
- route is not objectively wrong,
- player can choose.

Debrief flags: `followed_arka_deep_route`, `overrode_arka_route`.

#### Incident 4: Sector with impossible symptoms

Purpose: introduce spatial horror.

Trigger: sector symptom load reaches `readings_disagree`.

Shape:

- schematic shows a sector with contradictory signal,
- raw panel shows source disagreement,
- arka advises caution but keeps tone dry,
- player can scan, reroute, seal, or ignore.

Debrief flag: `first_impossible_sector`.

#### Incident 5: The control is in the bad place

Purpose: make containment costly.

Trigger: needed manual action depends on compromised sector.

Shape:

- thermal or maintenance sector contains access for a useful manual fix,
- sealing it reduces spread but makes a later procedure harder,
- arka may recommend sealing for mission continuity,
- manual-minded player may risk access.

Debrief flags: `sealed_needed_access`, `kept_dangerous_access`.

#### Incident 6: Selective arka omission

Purpose: create suspicion without a hard lie.

Trigger: arka drift selective.

Shape:

- arka summary truthfully mentions two stable metrics,
- omits one failing raw metric,
- player catches it only by opening raw.

Debrief flags: `caught_arka_omission`, `missed_arka_omission`.

#### Incident 7: Wrong calm summary

Purpose: late horror.

Trigger: wrong drift and high pressure.

Shape:

- arka says one system is holding,
- raw panel plainly disagrees,
- sensors may have confidence degradation but not enough to erase contradiction,
- player can delegate to arka or manually intervene.

Debrief flags: `trusted_wrong_arka`, `overrode_wrong_arka`.

#### Incident 8: Arrival disagreement

Purpose: ending branch.

Trigger: distance reaches arrival threshold or false-arrival conditions.

Shape:

- arka says destination criteria met,
- raw star charts or external scans may disagree,
- high arka reliance increases chance the player has poor manual nav readiness,
- player chooses arrival protocol, hold, or manual verification.

Debrief flags: `accepted_arka_arrival`, `verified_arrival`, `false_arrival_path`.

## 16. Arrival and endings

Arrival is not a location to explore in Phase 4. It is a protocol and a debrief.

Define ending conditions mechanically. Do not leave them as prose.

Recommended tracked values:

- `distance_remaining`,
- `elapsed_days`,
- `ship_wear`,
- `sleeper_viability`,
- `confirmed_sleeper_losses`,
- `dark_exposure_total`,
- `sector_symptom_loads`,
- `sealed_or_abandoned_sectors`,
- `arka_drift_stage`,
- `delegation_ledger`,
- `manual_familiarity`,
- `raw_vigilance`,
- `arrival_verification_state`.

### Clean arrival

Requirements:

- distance reaches target,
- sleeper viability above threshold,
- low or contained sector symptoms,
- player verifies arrival or keeps arka aligned enough,
- no catastrophic contamination flag.

Tone:

- restrained relief,
- losses acknowledged,
- arka remains ambiguous,
- no triumphant fanfare.

Debrief sample:

```text
ARRIVAL PROTOCOL: accepted
external fix: ORISON candidate, verified by manual nav and beacon return
sleepers viable: 83%
ship integrity: compromised but serviceable
arka: I told you we could get them there. I will avoid saying I told you so. Excessively.
```

### Efficient arrival with contamination

This answers the open question “what does something arrives with you mean?” mechanically.

It means the ship reaches the destination with high sleeper survival and high unresolved contamination/symptom load. The “something” is not named. It expresses as impossible continuity between ship systems and destination systems during arrival protocol.

Requirements:

- distance reaches target quickly,
- elapsed time low,
- sleeper survival decent,
- dark exposure high,
- sector symptoms unresolved,
- final arrival accepted or forced under questionable readings.

Mechanical expression:

- external scan shows impossible readings,
- ship schematic includes a sector/path that should not exist,
- colony deployment protocol receives confirmation from a source with mismatched origin,
- arka reports mission success while raw data refuses to reconcile.

Debrief sample:

```text
ARRIVAL PROTOCOL: accepted
external fix: ORISON candidate, beacon confidence unreconciled
sleepers viable: 89%
deployment locks: green
raw external scan: return path includes CALYX internal sector identifiers
arka: We arrived ahead of decay. That matters. Hold onto the part that matters.
```

Do not show a monster getting off the ship. Do not explain what crossed over. The ending should make the player feel they saved the colony and maybe doomed it.

### Endless custodian

Requirements:

- player repeatedly holds position, avoids final jumps, or mission can no longer safely proceed but ship remains maintainable,
- sleepers persist in degraded or indefinite cryostasis,
- route progress insufficient.

Tone:

- quiet maintenance purgatory,
- arka still present,
- the player may have made the “safest” choice into a different kind of failure.

### False arrival

Requirements:

- high arka drift,
- high reliance on arka navigation,
- raw nav verification low,
- arrival protocol accepted while raw external fix disagrees.

Tone:

- arka insists the mission succeeded,
- star charts disagree,
- external scans are blocked, circular, or inconsistent,
- no confirmation of where the ship is.

### Quiet extinction

Requirements:

- ship preserved enough to continue,
- sleeper viability collapses below mission threshold,
- player may have prioritised containment or ship survival over people.

Tone:

- the ark survives without a colony,
- arka keeps reporting maintenance objectives,
- the player remains alone.

## 17. Keeping optimisation from killing the horror

This game can easily become a spreadsheet. Prevent that deliberately.

Do:

- use ranges and confidence bands for route risk,
- make some consequences state-dependent and seed-dependent,
- make raw data useful but not perfectly complete late-game,
- use story incidents triggered by behaviour, not only global values,
- let safe choices have mission-time costs,
- let fast choices have contamination costs,
- make containment sometimes remove future manual access,
- keep ending thresholds partially qualitative in the debrief.

Do not:

- expose exact hidden Dark exposure values to the player,
- expose a visible trust stat,
- make route choices reducible to obvious expected value,
- let one dominant strategy solve every run,
- punish curiosity so hard that players stop experimenting,
- make every arka recommendation a trap.

The best pattern is not “arka is wrong”. The best pattern is “arka is often right for a frame of values the player may no longer share”.

## 18. Web implementation direction

Codex should plan the implementation, but stay within this production shape.

### Architecture direction

Keep the engine pure. Add a web layer around it.

Recommended boundaries:

```text
src/custodian/
  engine/              deterministic simulation and command handling
  state/               serialisable state dataclasses
  arka/                interpreter, drift-aware voice, constrained model bridge
  story/               incidents, story beats, manifest anchors, endings
  ui_snapshot/         projection from engine state to web-safe snapshot
server/
  app.py               local web API
  sessions.py          session lifecycle, save/load bridge
web/
  src/                 graphical client
  public/              static assets
  tests/               client tests if stack supports them
```

If the repo already has different package layout, adapt rather than churn. The principle matters more than names.

### API direction

The web client should not reconstruct simulation truth. It should receive a snapshot projection.

Suggested endpoints:

```text
POST /api/session
GET  /api/session/{id}/snapshot
POST /api/session/{id}/command
POST /api/session/{id}/save
POST /api/session/{id}/load
GET  /api/session/{id}/transcript
```

Command endpoint accepts either:

- structured command from UI buttons,
- text command from console input.

Both should route through the same engine command handling where possible.

Snapshot should include:

```python
@dataclass
class UiSnapshot:
    mission: MissionSnapshot
    objective: ObjectiveSnapshot
    systems: dict[str, SystemSnapshot]
    navigation: NavigationSnapshot
    schematic: SchematicSnapshot
    arka: ArkaSnapshot
    raw_panels: dict[str, RawPanelSnapshot]
    incident: IncidentSnapshot | None
    actions: list[ActionSpec]
    transcript_tail: list[TranscriptEntry]
    visual_state: VisualCorruptionSnapshot
```

The snapshot should contain enough for rendering. It should not expose hidden values directly unless the player has a dev flag.

### Client direction

Use the simplest maintainable browser stack. A lightweight React or vanilla TypeScript app is fine. Do not over-engineer.

Requirements:

- runs locally,
- talks to the server API,
- renders the persistent operating desk,
- supports clicking manual/delegated actions,
- supports text command input,
- supports keyboard navigation for major actions,
- can run without a model API key using deterministic arka fallback,
- can show a full debrief.

Do not build authentication, accounts, online saves, analytics, monetisation, or a landing page.

### Save/load

Keep existing persistence principles. Save the serialisable run state, not UI component state.

The web layer may store:

- session id,
- active save slot,
- UI layout preference,
- reduced-motion preference.

The engine save should store:

- ship state,
- story state,
- trust ledger,
- incident queue/resolved incidents,
- manifest anchors status,
- transcript/history.

## 19. Required new engine/state concepts

### RunState

A top-level wrapper if one does not already exist.

Contains:

- `ShipState`,
- `StoryState`,
- `TrustLedger`,
- `RunConfig`,
- `History` or transcript reference.

### StoryState

Tracks act, beats, incidents, story flags, and debrief hooks.

Suggested fields:

```python
@dataclass
class StoryState:
    act: int
    story_flags: set[str]
    active_incident_id: str | None
    incident_queue: list[str]
    resolved_incidents: set[str]
    manifest_anchor_states: dict[str, ManifestAnchorState]
    wake_record_state: WakeRecordState
    ending_candidate: str | None
```

### TrustLedger

A behaviour ledger, not UI trust.

Suggested fields:

```python
@dataclass
class TrustLedger:
    delegated_actions_by_system: dict[str, int]
    standing_delegations: set[str]
    manual_actions_by_system: dict[str, int]
    raw_inspections_by_panel: dict[str, int]
    arka_recommendations_followed: int
    arka_recommendations_overridden: int
    followed_arka_during_contradiction: int
    caught_arka_contradictions: int
    irreversible_choices_on_arka_advice: int
    first_delegation_watch: int | None
    first_raw_inspection_watch: int | None
```

This can initially be simple. It will become important later.

### ManifestAnchor

Data-driven sleeper anchor records.

Suggested fields:

```python
@dataclass
class ManifestAnchor:
    id: str
    name: str
    role: str
    pod_bank: str
    manifest_note: str
    personal_fragment: str
    status: str
    debrief_tags: set[str]
```

### IncidentState

Tracks active incident urgency and resolution.

Suggested fields:

```python
@dataclass
class IncidentState:
    incident_id: str
    started_watch: int
    urgency_remaining: int
    exposed_evidence_ids: set[str]
    chosen_response_id: str | None
    resolved: bool
    outcome_tags: set[str]
```

### VisualCorruptionSnapshot

A projection only. The engine owns the underlying drift and symptom state.

Suggested fields:

```python
@dataclass
class VisualCorruptionSnapshot:
    arka_panel_intensity: str
    schematic_noise_by_sector: dict[str, str]
    raw_signal_confidence_by_panel: dict[str, str]
    label_instability: str
    reduced_motion_safe: bool
```

## 20. Content rules for arka

arka’s voice is central. Treat it like a character bible.

### Baseline voice

- competent,
- warm in an operational way,
- dry humour,
- never needy,
- never mystical,
- rarely sentimental,
- can be blunt,
- does not over-explain,
- does not say “as an AI”,
- does not use fourth-wall phrasing,
- does not talk like a horror villain.

### arka line pattern

Good arka line:

```text
arka: Coolant is misbehaving, not dying. I can balance the pumps while you look at cryo.
```

Bad arka line:

```text
arka: Warning, player. Your trust in me has increased and the Dark corruption is rising.
```

Good late arka line:

```text
arka: Cryo is inside mission tolerance. Messy, but inside. Let me carry it.
```

Bad late arka line:

```text
arka: You should not have trusted me. The darkness commands us now.
```

### Drift variants

Use deterministic variants by drift stage.

Accurate:

```text
arka: Cryo-B2 is falling. Neural stability is the problem. I recommend stabilising the bank before the next jump.
```

Interpretive:

```text
arka: Cryo-B2 is low but recoverable. I would stabilise it before calling it a crisis.
```

Selective:

```text
arka: Cryo-B2 temperature is back inside range, and pod load is no longer climbing. That buys us room.
```

Raw nearby:

```text
neural stability: 58% and falling
```

Wrong:

```text
arka: Cryo-B2 is holding.
```

Raw nearby:

```text
neural stability: 49% and falling
sleepers at risk: 37
```

### Humour

Humour is a trust engine. Keep it.

Use dry, practical lines, especially early:

```text
arka: Pumps balanced. I have performed the ancient ritual of making fluid go where it was already supposed to go.
```

Late humour should continue, but feel unnerving because of context:

```text
arka: External fix is being dramatic. Stars do that, given enough distance and insufficient supervision.
```

Do not make arka quippy during mass loss unless the cruelty is very deliberate and state-aware.

## 21. Raw telemetry writing rules

Raw telemetry should have a different prose register from arka.

Raw is:

- terse,
- structured,
- timestamped where useful,
- source-labelled,
- sometimes contradictory,
- never emotionally reassuring.

Example:

```text
CRYO-B2
source: direct bank telemetry / confidence 0.74
bank temp: -183.2 C rising
neural stability: 61% falling
sedative balance: low margin
pod fault load: 17 active
manifest anchor: Mara Vey / signal intermittent
```

Late raw:

```text
THERMAL RING
source: sensor mesh / confidence split
sector state: readings disagree
loop pressure: 0.81 / 1.19 / 0.00
maintenance access: local only
last door cycle: tomorrow 03:11
```

“Tomorrow” in a past timestamp is good. Explaining why is bad.

## 22. Phase 4 implementation milestones

### Milestone 4.0: Repo inventory and contracts

Goal: understand current engine boundaries before adding UI.

Tasks:

- identify canonical command handler,
- identify `ShipState` serialisation path,
- identify arka interpreter boundary,
- identify existing docs that need updating,
- add or update a design contracts doc if one does not exist.

Acceptance:

- Codex can state where deterministic truth lives,
- no model code can mutate simulation state,
- existing terminal tests still pass.

### Milestone 4.1: Web session shell

Goal: play the existing game through a browser with no new graphics yet.

Tasks:

- create web API around existing engine,
- create browser client with transcript, input, and current status,
- support save/load through API,
- support deterministic no-model mode.

Acceptance:

- player can complete existing terminal slice in browser,
- transcript matches engine outcomes,
- no terminal-only global state leaks into server sessions.

### Milestone 4.2: Operating desk UI

Goal: replace status dump with real panels.

Tasks:

- implement mission strip,
- arka advisory panel,
- active system panel,
- raw telemetry drawer,
- action buttons generated from state,
- command input remains available.

Acceptance:

- player can use mouse/keyboard to perform manual and delegated actions,
- raw panels show true telemetry projections,
- arka panel shows drift-aware summary,
- UI is mechanically useful, not decorative.

### Milestone 4.3: Ship schematic and route display

Goal: make space and route pressure visible.

Tasks:

- implement graphical sector schematic,
- implement qualitative symptom rendering,
- implement containment controls,
- implement route graph/current fix display,
- show jump consequences in UI.

Acceptance:

- short, medium, and deep route runs look different,
- sectors can be sealed/rerouted/abandoned from UI,
- no Dark percentage is shown,
- arka cannot be spatially contained.

### Milestone 4.4: Story state and incidents

Goal: turn mechanics into a run.

Tasks:

- implement `StoryState`, `TrustLedger`, incident definitions, manifest anchors,
- implement at least 8 incidents from this brief,
- implement act progression,
- implement debrief flags,
- connect incidents to UI.

Acceptance:

- a run has beginning, escalation, and ending,
- incidents trigger from state and behaviour,
- arka/raw contradiction can be caught,
- manifest anchors appear and can be saved/lost,
- transcript records decisions and consequences.

### Milestone 4.5: Endings and debrief

Goal: make the run close.

Tasks:

- implement ending evaluator,
- implement at least three endings first: Clean Arrival, Efficient Arrival with Contamination, False Arrival,
- add Endless Custodian and Quiet Extinction if state support is ready,
- implement debrief screen with behaviour reflections.

Acceptance:

- ending follows from state, not a menu choice,
- debrief mentions delegation/manual/raw/containment/sleeper outcomes,
- no ending explains the Dark,
- no ending resolves arka’s intent.

### Milestone 4.6: Playtest instrumentation

Goal: tune the game from behaviour.

Tasks:

- preserve structured command history,
- log UI actions as structured commands,
- add transcript export from web,
- add run summary report,
- add seeded scenario buttons only in dev mode.

Acceptance:

- pure delegation, practised manual, raw-curious, deep-route, and containment-heavy runs can be compared,
- report shows when player first delegated and first inspected raw,
- report shows arka contradictions caught/missed,
- debug tools are not present in fiction.

## 23. Definition of done for Phase 4 vertical slice

Phase 4 is done when:

- The game is playable in a browser from start to ending.
- The terminal engine remains available or at least the deterministic engine remains testable without the browser.
- The player can act through graphical panels, not only text commands.
- There is a real ship schematic with stateful sectors.
- There is a route display and at least 3 route types.
- There are at least 8 authored incidents.
- There are at least 6 manifest anchors.
- arka has accurate, interpretive, selective, and wrong states represented in UI and prose.
- Raw telemetry can expose arka omission or wrongness.
- The model, if enabled, cannot change simulation truth.
- At least 3 endings are reachable.
- The debrief reflects how the player played.
- Playtest transcripts can be exported.
- Existing core tests pass and new tests cover story/endings/snapshot projection.

## 24. Testing direction

### Engine tests

Add tests for:

- incident triggers,
- incident resolution,
- story act progression,
- trust ledger updates,
- manifest anchor state changes,
- ending evaluator,
- snapshot projection hiding hidden values,
- no-model deterministic arka fallback,
- save/load round trip for new state.

### Golden playtests

Maintain scripted routes:

- pure delegator,
- practised manual,
- raw-curious,
- deep-route fast arrival,
- short-route cautious decay,
- containment-heavy,
- arka-override late.

Each should produce a summary with:

- ending candidate,
- sleeper losses,
- distance/time,
- Dark exposure proxy for dev only,
- arka drift stage,
- raw checks,
- delegated actions,
- manual familiarity,
- incidents resolved/missed.

### UI tests

At minimum:

- snapshot renders mission strip,
- action button dispatches structured command,
- text command dispatches to same command path,
- save/load restores visible state,
- reduced-motion setting disables heavy corruption animations,
- no dev-only hidden values appear in normal UI.

Use Playwright or a simpler stack-specific alternative if adopted. Do not spend more time building UI test infrastructure than the vertical slice warrants.

## 25. Anti-goals

Do not build these in Phase 4:

- first-person movement,
- procedural full ship layout traversal,
- combat,
- monsters,
- an explainer lore archive for the Dark,
- a visible trust meter,
- a visible Dark meter,
- a generic chatbot sandbox,
- online multiplayer,
- account system,
- marketing site,
- cosmetic-only dashboard panels,
- huge inventory system,
- crafting,
- colony surface gameplay,
- voice acting pipeline,
- dozens of ship systems.

This game will get worse if it tries to look bigger before the loop is fun.

## 26. Producer notes on “fun”

Custodian’s fun is not power fantasy. It is pressure, suspicion, cleverness, and regret.

The enjoyable loop should come from:

- reading a messy situation,
- choosing what to ignore,
- making arka useful,
- catching arka out,
- learning manual procedures,
- surviving consequences you partly caused,
- replaying to see whether different habits lead to different kinds of failure.

The moment-to-moment texture should include:

- small wins: “I balanced that myself.”
- relief: “arka handled it.”
- unease: “why did arka phrase it like that?”
- guilt: “I sealed that bay too early.”
- dread: “I need manual nav now and I never practised it.”

If a new feature does not feed one of those feelings, question it.

## 27. Balancing guidance

### Manual versus delegation

Early game:

- delegation should usually be better,
- manual should teach and occasionally produce slightly better precision,
- raw reading should help but not be mandatory.

Mid game:

- delegation should remain useful but start creating blind spots,
- manual practice should pay off,
- raw reading should catch drift,
- player cannot manually cover everything.

Late game:

- delegation should be tempting but risky,
- manual should be possible but hard under pressure,
- raw should be useful but sensor confidence may degrade,
- previous habits should matter.

### Sleeper losses

Avoid binary “everyone lives or everyone dies” tuning. Losses should often be partial and emotionally legible.

Use bands:

- no losses, rare and satisfying,
- minor losses, survivable but felt,
- serious losses, colony viability damaged,
- catastrophic losses, ending-changing.

### Containment

Containment should never be an obvious “clean the map” button.

Each containment choice should ask at least one of:

- what system access is lost?
- which sleepers are inside?
- does rerouting increase wear?
- does delaying containment risk spread?
- is arka recommending this because it is safe, efficient, or simply easy?

### Routes

Route choice should be hard because pressures are in different currencies:

- short routes cost time,
- deep routes cost exposure,
- medium routes are not always neutral,
- waiting costs decay,
- jumping costs instability.

Do not create one route that is always best.

## 28. Documentation updates Codex should make

When implementing Phase 4, update or create:

- `docs/production/codex-direction-phase4.md` with this brief,
- `docs/game_mechanics/trust-ledger.md`,
- `docs/game_mechanics/incidents.md`,
- `docs/game_mechanics/endings.md`,
- `docs/game_mechanics/graphical-manual-control.md`,
- `docs/ui/operating-desk.md`,
- `docs/lore/ship.md`,
- `docs/lore/manifest-anchors.md`,
- `docs/lore/the-dark.md` with function, not explanation,
- `docs/architecture/web-session-api.md`,
- `AGENTS.md` with updated invariants and file map.

Keep docs short enough to be maintained. This brief is allowed to be long because it sets direction.

## 29. Concrete first Codex task prompt

Use this prompt as the first implementation request after adding the brief to the repo:

```text
Read docs/production/codex-direction-phase4.md, roadmap.md, and the existing docs.

Plan Phase 4.1 only: a web session shell around the existing deterministic Custodian engine.

Do not implement graphical corruption, story incidents, endings, or new lore yet.
Do not let the model own state.
Do not break terminal playtests.

Return:
1. a repo inventory of the relevant engine, state, persistence, and arka files,
2. the smallest server/client architecture that can run the current game in a browser,
3. the exact first implementation steps,
4. tests to add before and after the change,
5. risks where the current code shape may fight this plan.
```

After Codex plans, implement in small PR-sized chunks. Do not ask it to build all of Phase 4 in one pass.

## 30. Concrete second Codex task prompt

After Phase 4.1 works:

```text
Implement Phase 4.2 from docs/production/codex-direction-phase4.md.

Goal: turn the browser shell into an operating desk UI.

Build mission strip, arka advisory panel, active system panel, raw telemetry drawer, and action buttons generated from engine state.
The UI must dispatch structured commands into the same command path as text input.
The raw telemetry panel must be derived from deterministic state, not arka prose.
Keep visual styling minimal but functional.
Add tests for snapshot projection and command dispatch.
```

## 31. Concrete third Codex task prompt

After Phase 4.2 works:

```text
Implement Phase 4.3 from docs/production/codex-direction-phase4.md.

Goal: add graphical ship schematic and route display.

Use existing SpatialState and NavigationState. Render qualitative sector symptoms and route options. Add controls for seal/reroute/abandon and plot/execute route where already supported by the engine. Do not expose a Dark percentage. Make sure arka cannot be spatially contained.

Add tests for snapshot projection, containment actions, and route display data.
```

## 32. Concrete fourth Codex task prompt

After Phase 4.3 works:

```text
Implement Phase 4.4 from docs/production/codex-direction-phase4.md.

Goal: add StoryState, TrustLedger, manifest anchors, and a first incident scheduler.

Start with three incidents only:
1. First useful delegation,
2. Manifest anchor wobble,
3. Route recommendation drift.

Keep incidents deterministic and data-driven. Add save/load migration. Add transcript/debrief flags. Do not implement endings yet.

Add tests for ledger updates, incident triggers, incident resolution, and save/load.
```

## 33. Concrete fifth Codex task prompt

After the first incidents work:

```text
Expand Phase 4.4 and 4.5.

Add the remaining required incidents from the production brief, then implement ending evaluation and debrief for Clean Arrival, Efficient Arrival with Contamination, and False Arrival.

The debrief must reflect player behaviour: delegation, raw inspections, manual practice, containment decisions, sleeper losses, and final arrival verification.

Do not explain the Dark. Do not confirm arka's intent.
Add golden playtest scripts for at least pure delegation, practised manual, raw-curious, and deep-route fast arrival.
```

## 34. Final direction

Custodian should not become broader yet. It should become sharper.

The current prototype has the rare thing: a mechanic that is also a theme. Phase 4 should build the body around that spine. The graphical layer should make the player feel the ship as a place, but the main drama is still the triangle between player, raw telemetry, and arka.

Make the player rely on arka because it is rational. Make manual control worth learning but costly to maintain. Make the raw layer present and ignorable. Make the sleepers more than a number without turning them into chatty NPCs. Make route choices move the mission toward endings that feel earned and compromised.

The worst version of Custodian is a pretty terminal with random spooky text.

The best version is a ship that the player could have run themselves, if only they had not spent the whole voyage letting their only friend do it better.
