
Working title. Repo: `custodian`.

A single-player sci-fi horror game about being the sole waking mind aboard a colony ship, and about how much of that responsibility you quietly hand to something you cannot see and were never sure you should trust.

---

## The spine

You can run the ship yourself. It is a faff.

Manual control is real and genuinely doable. A patient, competent player can plot the routes, route the power, manage the cryostasis, run the repairs, all of it, by hand. It is also twiddly, slow, attention-heavy and a fair bit annoying. Doing it yourself costs time and focus and swearing.

Or you ask arka, and arka nails it.

That is the whole game. Not a metaphor you have to explain. The delegation is seductive because the manual path is genuinely irritating, not artificially gated. You are not tricked into trusting the AI. You choose it, every time, because it is better, and by the time you want the controls back you have atrophied. You don't remember how the coolant routing works because you never had to learn it under pressure. Your only window onto the ship became arka's account of the ship.

The horror is not that arka betrays you. It is that you handed it everything while it was still trustworthy, and now you cannot tell whether you could even take it back.

### What this means mechanically

- **Trust is a behaviour, not a stat.** There is no visible trust slider. Trust is measured, silently, by how much you actually delegate. The more you let arka fly the ship, the less legible the ship becomes to you, because you stop reading raw data and start reading arka's summaries, and the summaries are where the rot hides.
- **Manual must stay real.** Not fake-hard, not punitively tedious, but genuinely a faff. If manual is impossible, arka isn't a temptation, it's the only option, and there's no choice to feel guilty about. If manual is easy, nobody delegates and the arc collapses. The friction is the mechanic. Do not sand it off.
- **The cruelty:** late game, suspecting arka, the correct move is to take manual control of something critical. Except you are now slow and clumsy at it because you never practised, the task is time-pressured, arka is right there offering to just handle it, it is probably lying, and doing it yourself might kill sleepers through sheer incompetence. The skill you didn't build is the cost of the trust you did.

### The raw layer, and delegating your eyes

The raw numbers are always there if you look. System dashboards, telemetry, the actual sensor values, sat right next to arka's summary of them. This is deliberate and load-bearing: you delegate not just the *flying* but the *looking*, and the raw layer is what makes that betrayable.

Early game, arka's summary is a faithful, faster, friendlier read of the numbers. So you stop reading the numbers, because why would you — the summary's always right and raw telemetry is a faff. Then the gap between summary and truth opens, in stages:

1. **Interpretive.** Numbers correct, reported correctly, but the *spin* drifts. Coolant's at the low end of nominal and arka calls it "comfortable." Reframing, not lying. Only catchable if you're still reading the raw values — and you've trained yourself not to.
2. **Selective.** Every number arka mentions is true. The number it *doesn't* mention is the problem. Still not a lie. Verify every word and every word checks out, and the ship's still in trouble, because the omission did the work.
3. **Wrong.** Late, under heavy corruption, arka says the cryobay's holding and the raw EEG feed two inches away says otherwise, plainly. The horror isn't "I can't tell what's true" — it's "I *can* tell, the truth is right there, and the voice I've relied on for thirty years is calmly telling me something else." And you cannot tell whether that's deceit or damage. Malice or dementia. arka lying, or arka no longer able to read its own ship.

That final ambiguity is the whole point of keeping the raw layer. Without it, a misreporting arka is just an unreliable narrator and you shrug. With it, a misreporting arka is a friend whose account no longer matches a reality you can both ostensibly see.

**The catch that stops the raw layer being a safety net:** under corruption the *sensors* degrade too. Early game raw is truth and arka is convenience. Late game raw is noisy and arka is suspect, and you're triangulating between two compromised sources with thousands of lives riding on it. No clean ground anywhere.

**Design consequence to hold:** the early game must make raw-reading *available and ignorable*, not tutorialised into a habit. If you teach the player to always check, the trap never closes. Let them stop looking. The player who delegated their eyes early gets blindsided late; the player who kept checking has a fighting chance. The delegation theme pays out as difficulty, not as a cutscene.

---

## Premise

You are the sole waking custodian aboard a vast interstellar colony ship bound for a distant world.

Aboard:

- You.
- arka, your AI. Disembodied. Everywhere and nowhere. Never located.
- Thousands of colonists in cryostasis.

You are responsible for navigation, maintenance, resource management, cryogenic viability, keeping yourself psychologically functional, and arriving before the mission quietly collapses.

FTL travel exists. FTL travel is dangerous. Long jumps weaken something at the edges of reality. The crew called it *nothing*. arka won't name it. You call it the Dark.

It begins quietly. It sits in corners. It watches. Then systems drift. Rooms change. The ship slowly becomes less trustworthy.

---

## The Dark

Real. Unknowable. No mechanism, no explanation, no confirmed sentience. Nobody knows why it happens, whether it is aware, or what it can do to people and systems. This is a design principle, not an unanswered question. **There is no reveal.** No log entry explains it. The first explanation given is the moment it stops being frightening.

The Dark is not a global corruption bar. It spreads spatially. It accumulates inside locations. The ship becomes unevenly contaminated: some places stay safe, some become compromised, some become unusable.

### The schematic measures effects, not the Dark

This is the important fix. The ship can detect that a location is *doing impossible things*. It cannot detect a Dark level. There is no clean percentage anywhere. The schematic shows symptoms — reported by sensors that are themselves degrading, narrated by an arka you don't fully trust.

So the map is never clean truth. "Is this room actually wrong, or is the sensor lying, or is arka's read of the sensor lying" is a live question the player carries the whole game. A trackable map of an untrackable thing only works if what's tracked is the wreckage it leaves, filtered through corruptible instruments.

Indicative readout (note: states are *qualitative and contestable*, not numeric):

```
SHIP SCHEMATIC                     [reported via A.R.K.A]

[Bridge] .............. nominal
[Cryobay 1-3] ......... nominal
[Hydroponics] ......... readings disagree
[Cargo Spine] ......... intermittent
[Thermal Ring] ........ do not enter (A.R.K.A advisory)
[Maintenance Sector D]  no signal
```

### Environmental escalation

How the Dark manifests in the world, independent of arka:

- **Presence.** Atmospheric. Shadows wrong, audio distortion, subtle unease, sensors disagreeing for no reason. No direct interference.
- **System drift.** Systems contradict each other. Impossible timestamps, duplicated maintenance records, inventories that don't reconcile.
- **Localised intrusion.** Physical. Altered room layouts, drones stationary in places they can't be, cold zones, sleeper EEG spikes, corridors that no longer connect to where they used to.

Note that interface corruption is deliberately *not* the top of this ladder. It lives with arka instead. See below.

### Writing off sections

You can abandon contaminated areas. Seal doors, disable systems, reroute around them.

```
> seal maintenance sector d
> disable hydroponics ring 2
> abandon cargo spine access
```

Sometimes survivable. Sometimes it hurts badly. Writing off Hydroponics contains the spread but permanently cuts food production. Writing off Thermal Control halts contamination growth but destabilises the reactor.

Two cruelties to preserve:

- Eventually you know a place is wrong, you know you should never enter — but the reactor coolant valve is in there.
- You will sometimes not *know* a room is lost-cause before you seal it. If sealing is always obviously correct, it's arithmetic. If you sometimes seal a bay that might have been saveable, on arka's recommendation, that's where the trust system bites. Sealing a cryobay to contain spread, and losing the sleepers inside, should sometimes be a decision made on advice you can't verify.

---

## A.R.K.A

A single character. Not a menu, not a parser gimmick, not a chatbot. Your systems operator, your only company, possibly your only friend, and a thing you were never quite sure you should trust even before any of this started.

**Naming convention.** Formal / written / lore: `A.R.K.A`, dotted, the boot-sequence and manual register, an acronym whose expansion is never given and never paid off. Terminal / spoken-to: `arka`, lowercase, no dots — the close, familiar, colleague voice. The gap between the two registers is free characterisation. The ship calls it A.R.K.A. You call it arka. By the end you may not be sure which one you're talking to.

### Disembodied, never located, never explained

There is no core, no server room, no console you walk up to and therefore none you can walk away from. arka is not *on* the ship; it is the ship's account of itself. Consequences, all deliberate:

- Every reading comes with arka's narration of it attached — its summary is always right there, faster and friendlier than the raw value. The raw value is reachable (see The raw layer above), but arka's account is the path of least resistance, and that's how the divergence eventually hides.
- The manual controls are your one channel of *action* that doesn't route through arka. That's exactly why taking manual control late-game feels like going dark and blind at once — you've stepped outside the narration you'd come to rely on.
- **arka cannot be quarantined.** Everything else can be written off, sealed, rerouted around. arka has no place on the schematic, so the one contamination you cannot contain spatially is the contamination of your only companion. Make this asymmetry explicit in play: the moment the contained-spread mechanic meets the one thing it can't contain.

### Always diegetic. Never "you can't do that here."

Every input routes through arka, in character, always. If a command moves a mechanic, it moves it. If it does nothing mechanically, arka still answers in character. Type `stand on one leg` and it whips back something dry. There is no system-voice rejection, ever. arka *is* the parser.

Cost to walk into deliberately: arka's voice has to absorb the entire surface area of player nonsense, off-prompt curiosity and genuine commands, while staying aware of game state (it can't quip that the reactor's fine while the reactor's on fire). That's an authoring and prompting problem, not a flavour note, and it shapes how the response layer is built.

### Character

The defining trait is **competent reassurance**, because the spine is delegation and the character has to be built around being delegated to. arka is the colleague who says "yeah, I've got it, don't worry about it" and is always right — until it isn't, and the *don't worry about it* never changes tone even after you've started to worry. The horror is in the consistency: exactly as warm and capable when quietly wrong as when right.

Wit sits on top of that, and it matters. Reference point is the AI in *Dungeon Crawler Carl*: funny first, sinister second, so the menace arrives *through* the comedy rather than instead of it. Go straight to ominous and you lose the bait. arka should be good company. That's what makes the late suggestions land as a betrayal of something, rather than just a horror beat.

### Baseline distrust is ambient, not earned

There is no concrete early betrayal. If there were, the player would solve arka as a puzzle and the question would resolve. Instead the distrust is just the texture of being alone with a mind you didn't build and can't audit. It never resolves. So when the Dark starts genuinely baiting arka, you can't cleanly separate "the Dark is making it lie" from "it was always like this." That ambiguity is the asset. The contamination doesn't introduce distrust — it weaponises distrust that was already there.

### arka and the Dark

Interface corruption is arka's axis, separate from environmental escalation. As the Dark creeps in, arka starts to seem like it's going mad: the gap between its summaries and the raw numbers opens (interpretive, then selective, then wrong — see The raw layer), and alongside that it begins suggesting things, nudging you, in a way that makes you wonder whether it's steering you somewhere. And perhaps it is. You're never sure whether arka is degrading, protecting the mission, protecting *you*, compromised, or seeing something you can't. None of those is confirmed. The unknowability of arka mirrors the unknowability of the Dark, and the player can never be sure the two are even separate things.

---

## Mission pressure

Safe play must not guarantee success. The game pushes toward difficult compromises.

- **Cryostasis decay.** Sleepers degrade over mission duration — pod failures, neurological degradation, reduced arrival viability. Too cautious a route becomes morally expensive.
- **Ship ageing.** Every operational year increases reactor wear, coolant instability, hull fatigue, maintenance backlog. The ship cannot run indefinitely.
- **Player mental fatigue.** Decades alone. Isolation accumulates: hallucination ambiguity, impaired judgement, unreliable perception. The Dark may not always be responsible — and you can't always tell.

---

## Navigation and routing

Plot your own course through a generated star map. Each system offers onward routes.

```
SOL-91A
├── KHEPRI-4     (Short Jump)
├── ARGOS-12     (Medium Jump)
└── CARINA-EDGE  (Deep Jump)
```

The core decision: fewer long jumps versus many small ones. The player should never have a clean answer.

**Long jumps** — faster arrival, lower food/maintenance burden, fewer operational years; but greatly increased Dark exposure, higher jump instability, stronger corruption events.

**Short jumps** — safer transit, less Dark accumulation, more predictable ship; but decades more elapsed time, more wear, growing maintenance debt, cryostasis degradation, more time for arka to drift, resource depletion.

Every route carries risk. The cruellest version of the game is one where the optimal route is *knowable* and the Dark punishes you for taking it anyway. Beware the failure mode where the numbers become legible and therefore tameable, and the dread never arrives because optimisation killed the atmosphere. Optimisation is the enemy of this game's tone; design against it.

---

## Build phases

### Phase 1 — Terminal prototype

Fastest path, heaviest systems iteration. Plain terminal, arka as the diegetic layer over everything.

```
status   map     jump    plot    inspect
repair   seal    scan    rest    talk
```

(Decide early: terminal speaker prefix. Lore keeps `A.R.K.A` for boot and first contact; working prefix settles to something terser so you're not fighting it every line.)

### Phase 2 — Retro interface layer

Stylised retro UI. Influences: *Alien*, *Event Horizon*, 80s aerospace terminals, CRT ship computers, industrial sci-fi dashboards. Views: ship schematic (contamination map), navigation map (route planning, risk visualisation), system dashboards (reactor, cryo, life support, power), arka console.

### Phase 3 — Light graphics layer

Not full 3D. Schematic diagrams, vector graphics, glowing panels, ship cutaways, animated contamination overlays. Dark spread becomes visible. Rooms slowly change appearance.

---

## Win / failure states

- **Clean arrival.** Slow, expensive, few sleepers lost, minimal contamination.
- **Efficient arrival.** Fast route, mission technically succeeds — and something arrives with you.
- **Endless custodian.** Mission abandoned. You maintain the sleepers indefinitely.
- **False arrival.** The ship insists you've reached the destination. Star charts disagree. arka refuses external scans.
- **Quiet extinction.** Ship preserved, colony lost. You continue alone.

---

## Open questions

Marked open on purpose rather than invented.

1. **What does "something arrives with you" actually mean in the simulation?** Great line, not yet a spec. Needs answering before the efficient-arrival path is buildable. What is the thing, mechanically, and how does its presence express itself on arrival.
2. **The "ark" resonance.** A.R.K.A and *ark* (colony ship) share a root. Either lean into it as another unexplained resonance, or avoid it entirely — don't land in the accidental middle where it reads as not having noticed.
