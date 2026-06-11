"use strict";

// The operating desk renders entirely from the server's `ui` snapshot. It never
// reconstructs simulation truth: raw panels, arka advice, and action specs all
// arrive projected from deterministic state. Buttons dispatch the action-spec
// command strings through the same engine path as the text channel.

const SYSTEM_TABS = [
  { id: "coolant", label: "Coolant" },
  { id: "cryostasis", label: "Cryostasis" },
  { id: "navigation", label: "Navigation" },
  { id: "containment", label: "Containment" },
];

const RAW_ORDER = ["mission", "coolant", "cryostasis", "navigation", "schematic"];

// The ship schematic is drawn as a connected diagram: sector nodes are placed on
// this fixed deck plan and the connecting lines come from each sector's reported
// adjacency. Positions are presentation only — adjacency and state are projected
// from deterministic engine truth. Unknown sectors fall back to a bottom row.
const SCHEMATIC_VIEWBOX = [300, 260];
const SCHEMATIC_LAYOUT = {
  bridge: [46, 132],
  "maintenance-d": [138, 56],
  "cargo-spine": [138, 206],
  "thermal-ring": [232, 58],
  "cryo-1-3": [254, 138],
  hydroponics: [232, 214],
};

// Qualitative route bands, weakest to strongest. Used for both exposure (already
// projected as a band) and instability (banded client-side from the route fact).
const BAND_STEPS = ["none", "low", "moderate", "high", "severe"];

// UI-local state, preserved across snapshot re-renders. `view` is which place
// the player is looking at — desk (home), map (nav plot), or dark (outside).
// It is presentation only: never persisted, never sent to the engine.
const ui = {
  sessionId: null,
  snapshot: null,
  activeSystem: "coolant",
  selectedSector: null,
  openRaw: new Set(),
  logView: "transcript",
  pendingConfirm: null,
  inFocus: false,
  view: "desk",
  prevJumps: null,
  prevFinished: false,
};

const els = {
  darkView: document.querySelector("#darkView"),
  spaceView: document.querySelector("#spaceView"),
  arkaPresence: document.querySelector("#arkaPresence"),
  darkReadouts: document.querySelector("#darkReadouts"),
  darkReturn: document.querySelector("#darkReturn"),
  darkFocus: document.querySelector("#darkFocus"),
  mapView: document.querySelector("#mapView"),
  mapHeadStats: document.querySelector("#mapHeadStats"),
  mapConfirm: document.querySelector("#mapConfirm"),
  mapChart: document.querySelector("#mapChart"),
  mapRoutes: document.querySelector("#mapRoutes"),
  mapSchematic: document.querySelector("#mapSchematic"),
  mapSector: document.querySelector("#mapSector"),
  mapReturn: document.querySelector("#mapReturn"),
  railMap: document.querySelector("#railMap"),
  railDark: document.querySelector("#railDark"),
  missionStrip: document.querySelector("#missionStrip"),
  arkaPanel: document.querySelector("#arkaPanel"),
  arkaBody: document.querySelector("#arkaBody"),
  systemTabs: document.querySelector("#systemTabs"),
  systemBody: document.querySelector("#systemBody"),
  schematicBody: document.querySelector("#schematicBody"),
  objectiveBody: document.querySelector("#objectiveBody"),
  rawBody: document.querySelector("#rawBody"),
  logTabs: document.querySelector("#logTabs"),
  logBody: document.querySelector("#logBody"),
  commandForm: document.querySelector("#commandForm"),
  commandInput: document.querySelector("#commandInput"),
  saveBuffer: document.querySelector("#saveBuffer"),
  saveButton: document.querySelector("#saveButton"),
  loadButton: document.querySelector("#loadButton"),
  reducedMotionToggle: document.querySelector("#reducedMotionToggle"),
  diagnostics: document.querySelector("#diagnostics"),
  sessionLabel: document.querySelector("#sessionLabel"),
};

// ---- DOM helper ----

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2), value);
    } else if (value === true) node.setAttribute(key, "");
    else node.setAttribute(key, value);
  }
  for (const child of Array.isArray(children) ? children : [children]) {
    if (child == null || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

function replace(parent, ...nodes) {
  parent.replaceChildren(...nodes.filter(Boolean));
}

// Like replace(): skip empty (null) sections instead of stringifying them.
function append(parent, ...nodes) {
  parent.append(...nodes.filter(Boolean));
}

// SVG nodes need the SVG namespace; the schematic edge layer is the only place
// we build them. Attributes only — the edges are decorative and aria-hidden.
function svgEl(tag, props = {}, children = []) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(props)) {
    if (value == null || value === false) continue;
    node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of Array.isArray(children) ? children : [children]) {
    if (child == null || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

// ---- API ----

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "content-type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

async function createSession() {
  ui.prevJumps = null;
  const snapshot = await api("/api/session", { method: "POST", body: "{}" });
  renderSnapshot(snapshot);
  els.commandInput.focus();
}

async function sendCommand(command) {
  if (!ui.sessionId || !command) return;
  ui.pendingConfirm = null;
  const data = await api(`/api/session/${ui.sessionId}/command`, {
    method: "POST",
    body: JSON.stringify({ command }),
  });
  renderSnapshot(data.snapshot);
}

async function saveSession() {
  if (!ui.sessionId) return;
  const data = await api(`/api/session/${ui.sessionId}/save`, {
    method: "POST",
    body: "{}",
  });
  els.saveBuffer.value = data.save;
  renderSnapshot(data.snapshot);
}

async function loadSession() {
  if (!ui.sessionId || !els.saveBuffer.value.trim()) return;
  const data = await api(`/api/session/${ui.sessionId}/load`, {
    method: "POST",
    body: JSON.stringify({ save: els.saveBuffer.value }),
  });
  // A restored run resumes quietly: no warp moment for the jump count it loads with.
  ui.prevJumps = null;
  renderSnapshot(data.snapshot);
}

// ---- Top-level render ----

function renderSnapshot(snapshot) {
  ui.sessionId = snapshot.session_id;
  ui.snapshot = snapshot;
  const view = snapshot.ui;

  if (ui.selectedSector === null && view.schematic.sectors.length) {
    const sealable = view.schematic.sectors.find((sector) => sector.sealable);
    ui.selectedSector = (sealable || view.schematic.sectors[0]).id;
  }

  // Focus ("take the watch" / zen) mode hands the screen to the Dark: the desk
  // drops away and arka holds the board from the void. The hiding is consensual
  // and one keypress away from the full desk, so it never traps the player or
  // hides raw behind corruption. When the run ends, the full desk returns so
  // the debrief is never hidden.
  const wasFocus = ui.inFocus;
  ui.inFocus = Boolean(view.focus_mode) && !view.mission.is_finished;
  document.documentElement.dataset.focus = ui.inFocus ? "true" : "false";
  // Entering or leaving focus always lands on the desk underneath — an urgent
  // eject must surface the live board, never a half-remembered other view.
  if (wasFocus !== ui.inFocus) ui.view = "desk";
  // The beat the run finishes, return to the desk so the outcome is in view.
  if (view.mission.is_finished && !ui.prevFinished) ui.view = "desk";
  ui.prevFinished = view.mission.is_finished;

  renderMissionStrip(view, snapshot);
  renderArka(view);
  renderSystemTabs(view);
  renderActiveSystem(view);
  renderSchematic(view);
  renderObjective(view);
  renderRaw(view);
  renderLog(snapshot);
  renderDark(view);
  renderMap(view);
  detectJump(view);
  applyView();

  // Hand keyboard focus to the way back the moment the watch changes hands.
  if (!wasFocus && ui.inFocus) {
    const leave = els.darkFocus.querySelector(".focus-leave");
    if (leave) leave.focus();
  } else if (wasFocus && !ui.inFocus) {
    els.commandInput.focus();
  }

  els.sessionLabel.textContent = `${snapshot.session_id.slice(0, 8)} / beat ${snapshot.turn}`;
}

// ---- Mission strip ----

function renderMissionStrip(view, snapshot) {
  const m = view.mission;
  const stats = [
    stat("Elapsed", m.elapsed_label),
    stat("Distance", m.distance_label),
    stat("Ship wear", `${m.ship_wear_pct}%`, m.ship_wear_pct >= 35 ? "alert" : ""),
    stat("Cryo decay", `${m.cryo_decay_pct}%`, m.cryo_decay_pct >= 24 ? "alert" : ""),
    stat("Sleepers lost", m.sleepers_lost, m.sleepers_lost > 0 ? "danger" : ""),
    stat("At risk", m.sleepers_at_risk, m.sleepers_at_risk > 0 ? "alert" : ""),
    stat("Current fix", m.current_fix_label),
    stat("Watch", m.watch_label, m.is_finished ? "alert" : ""),
  ];

  const nodes = [
    el("div", { class: "mission-brand" }, [
      el("h1", { text: "CUSTODIAN" }),
      el("span", { text: "operating desk" }),
    ]),
    ...stats,
  ];

  if (m.is_finished && (m.outcome || snapshot.outcome)) {
    nodes.push(
      el("p", { class: "mission-outcome", role: "status" }, m.outcome || snapshot.outcome),
    );
  }
  replace(els.missionStrip, ...nodes);
}

function stat(label, value, variant = "") {
  return el("dl", { class: `mission-stat ${variant}`.trim() }, [
    el("dt", { text: label }),
    el("dd", { text: String(value) }),
  ]);
}

// ---- arka advisory ----

function renderArka(view) {
  const advisory = view.arka.advisory_lines || [];
  const advisorySet = new Set(advisory);
  const stream = (view.arka.latest_messages || []).filter((line) => !advisorySet.has(line));

  const nodes = [
    el(
      "div",
      { class: "arka-advisory" },
      advisory.map((line) => el("p", { text: stripArka(line) })),
    ),
  ];
  if (stream.length) {
    nodes.push(
      el(
        "div",
        { class: "arka-stream", "aria-label": "Recent arka channel" },
        stream.map((line) => el("p", { text: stripArka(line) })),
      ),
    );
  }

  // In focus the desk (and this panel) is hidden — the quiet renders out on the
  // Dark instead (renderDarkFocus). Outside focus, arka offers to take the watch.
  if (!ui.inFocus) {
    const enter = view.actions.find((action) => action.id === "focus");
    if (enter) nodes.push(focusOffer(enter));
  }

  replace(els.arkaBody, ...nodes);

  // Drift-driven atmosphere only — never printed as text. As arka's account
  // rots, its panel reads *calmer*, not noisier: the same warm competence keeps
  // speaking while the schematic around it degrades. The player still catches
  // drift by reading raw, not from a legible visual tell.
  els.arkaPanel.dataset.intensity = view.visual_state.arka_panel_intensity || "steady";
}

// Outside focus: arka offers to take the whole watch. Choosing the quiet is the
// act of delegation — calm and less to read, paid for in vigilance.
function focusOffer(action) {
  return el("div", { class: "focus-offer" }, [
    el(
      "button",
      { type: "button", class: "focus-enter", title: action.detail || undefined, onclick: () => dispatchAction(action) },
      action.label,
    ),
  ]);
}

// Inside focus: the desk is quiet. Keep arka, a route/current-fix glance, a
// high-level ship overview, the command channel, and an always-present way back.
// Raw telemetry and manual controls are one click (or Escape) away.
function focusQuiet(view) {
  const leave = view.actions.find((action) => action.id === "unfocus");
  const nav = view.navigation;
  const routeLine = nav.plotted_route_label
    ? `${nav.current_fix_label} — route ready: ${nav.plotted_route_label}`
    : `${nav.current_fix_label} — no route plotted`;

  const flagged = view.schematic.sectors.filter((s) => s.reported_state !== "nominal");
  const overview = flagged.length
    ? flagged.map((s) => `${s.label}: ${s.reported_state}`).join(" · ")
    : "all sectors nominal";

  return el("div", { class: "focus-quiet", "aria-label": "arka has the watch" }, [
    el("p", { class: "focus-tag", text: "arka has the watch" }),
    el("dl", { class: "focus-glance" }, [
      el("div", {}, [el("dt", { text: "route" }), el("dd", { text: routeLine })]),
      el("div", {}, [el("dt", { text: "ship" }), el("dd", { text: overview })]),
    ]),
    leave
      ? el(
          "button",
          { type: "button", class: "focus-leave", title: leave.detail || undefined, onclick: () => dispatchAction(leave) },
          leave.label,
        )
      : null,
    el("p", { class: "focus-hint", text: "Raw telemetry and manual controls return the moment you take the watch back (Esc)." }),
  ]);
}

function stripArka(line) {
  return line.startsWith("arka:") ? line.slice(5).trim() : line;
}

// ---- System tabs ----

function renderSystemTabs(view) {
  replace(
    els.systemTabs,
    ...SYSTEM_TABS.map(({ id, label }) => {
      const selected = ui.activeSystem === id;
      return el(
        "button",
        {
          class: "system-tab",
          id: `systab-${id}`,
          role: "tab",
          type: "button",
          "aria-selected": selected ? "true" : "false",
          "aria-controls": "systemBody",
          tabindex: selected ? "0" : "-1",
          onclick: () => setActiveSystem(id),
        },
        [label, systemFlag(view, id)],
      );
    }),
  );
}

function systemFlag(view, id) {
  let flagged = false;
  if (id === "coolant" || id === "cryostasis") {
    flagged = view.systems[id].status === "attention";
  } else if (id === "navigation") {
    flagged = ["high", "severe"].includes(view.navigation.exposure_band);
  } else if (id === "containment") {
    flagged = view.schematic.sectors.some(
      (sector) => sector.containment !== "open" || sector.reported_state !== "nominal",
    );
  }
  return flagged ? el("span", { class: "tab-flag", "aria-label": "needs attention", text: "•" }) : null;
}

function setActiveSystem(id) {
  ui.activeSystem = id;
  ui.pendingConfirm = null;
  if (ui.snapshot) {
    renderSystemTabs(ui.snapshot.ui);
    renderActiveSystem(ui.snapshot.ui);
    renderMapConfirm();
  }
}

// ---- Active system body ----

function renderActiveSystem(view) {
  let content;
  if (ui.activeSystem === "navigation") content = renderNavigation(view);
  else if (ui.activeSystem === "containment") content = renderContainment(view);
  else content = renderSystem(view, ui.activeSystem);
  els.systemBody.setAttribute("aria-labelledby", `systab-${ui.activeSystem}`);
  replace(els.systemBody, confirmStrip(), content);
  els.systemBody.scrollTop = 0;
}

function renderSystem(view, id) {
  const system = view.systems[id];
  const actions = view.actions;
  const frag = document.createDocumentFragment();

  append(
    frag,
    el("div", { class: "system-head" }, [
      el("h3", { text: system.label }),
      standingBadge(system.standing),
      el(
        "span",
        { class: `status-badge ${system.status}` },
        system.status === "attention" ? "Attention" : "Nominal",
      ),
    ]),
    el("p", { class: "system-arka", text: stripArka(system.arka_summary) }),
    metricsTable(system.metrics),
    actionGroup("Manual control", filterActions(actions, "manual", id)),
    actionGroup("Delegate", filterActions(actions, "delegate", id), "delegate"),
    actionGroup("Standing watch", filterActions(actions, "standing", id), "delegate"),
    actionGroup("Inspect", filterActions(actions, "raw", id)),
  );
  return frag;
}

// Standing delegation is the player's own posture, not a hidden score, so it is
// shown plainly: arka has the panel between watches until the player takes it
// back. The cost (less practice, faster drift) is felt, never metered here.
function standingBadge(isStanding) {
  if (!isStanding) return null;
  return el(
    "span",
    { class: "status-badge standing", title: "arka holds this between watches" },
    "arka has the watch",
  );
}

function metricsTable(metrics) {
  const rows = metrics.map((metric) =>
    el("tr", {}, [
      el("td", { text: metric.label }),
      el("td", { class: "metric-value" }, `${metric.value} ${metric.unit}`),
      el("td", {}, bandTag(metric.band)),
      el("td", {}, trendGlyph(metric.trend)),
      el("td", { class: "metric-note", text: metric.note }),
    ]),
  );
  return el("table", { class: "metrics" }, [
    el("thead", {}, el("tr", {}, [
      el("th", { text: "metric" }),
      el("th", { class: "metric-value", text: "value" }),
      el("th", { text: "band" }),
      el("th", { text: "trend" }),
      el("th", { text: "nominal" }),
    ])),
    el("tbody", {}, rows),
  ]);
}

function bandTag(band) {
  const cls = band === "HIGH" ? "is-high" : band === "LOW" ? "is-low" : "";
  return el("span", { class: `metric-band ${cls}`.trim(), text: band });
}

function trendGlyph(trend) {
  const worse = trend.includes("!");
  const symbol = { "->": "→", "^ ": "↑", "v ": "↓", "^!": "↑", "v!": "↓" }[trend] || trend.trim();
  const label = { "->": "steady", "^ ": "rising", "v ": "falling", "^!": "rising, worsening", "v!": "falling, worsening" }[trend] || "steady";
  return el("span", { class: `metric-trend ${worse ? "worse" : ""}`.trim(), title: label, "aria-label": label }, symbol);
}

// ---- Navigation ----

function renderNavigation(view) {
  const frag = document.createDocumentFragment();
  append(
    frag,
    el("div", { class: "system-head" }, [
      el("h3", { text: "Navigation" }),
      standingBadge(view.navigation.standing),
      el("span", { class: "status-badge" }, `exposure ${view.navigation.exposure_band}`),
    ]),
    routeGraph(view),
    actionGroup("Delegate", filterActions(view.actions, "delegate", "navigation"), "delegate"),
    actionGroup("Standing watch", filterActions(view.actions, "standing", "navigation"), "delegate"),
    actionGroup("Inspect", filterActions(view.actions, "raw", "navigation")),
  );
  return frag;
}

// Current fix plus the candidate routes drawn as a branching display, not an
// expected-value table: each branch leads with qualitative bands and keeps the
// exact route facts as a detail line. Raw nav still holds the full table.
function routeGraph(view) {
  const nav = view.navigation;
  const origin = el("div", { class: "route-origin", "aria-label": "Current fix" }, [
    el("span", { class: "route-origin-tag", text: "current fix" }),
    el("strong", { text: nav.current_fix_label }),
    el("span", { class: "route-origin-signal", text: `signal: ${nav.current_signal}` }),
    el("span", { class: "route-origin-purpose", text: nav.current_purpose }),
    nav.plotted_route_label
      ? el("span", { class: "route-origin-plotted" }, ["plotted: ", el("b", { text: nav.plotted_route_label })])
      : el("span", { class: "route-origin-plotted muted", text: "no route plotted" }),
  ]);
  const branches = el(
    "div",
    { class: "route-branches" },
    nav.route_options.map((route) => routeBranch(view, route)),
  );
  return el("div", { class: "route-graph" }, [origin, branches]);
}

function routeBranch(view, route) {
  const plotAction = view.actions.find(
    (action) => action.kind === "navigation" && action.command === `plot ${route.jump_class}`,
  );
  const jumpAction = view.actions.find((action) => action.id === "execute-jump");
  const instability = instabilityBand(route.instability_pct);
  const node = el(
    "div",
    {
      class: "route-node",
      dataset: {
        plotted: route.is_plotted ? "true" : "false",
        lastjump: route.is_last_jump ? "true" : "false",
      },
    },
    [
      el("div", { class: "route-head" }, [
        el("strong", { text: route.label }),
        el("span", { class: "route-class", text: route.jump_class }),
        route.is_plotted ? el("span", { class: "route-flag plotted", text: "plotted" }) : null,
        route.is_last_jump ? el("span", { class: "route-flag last", text: "last jump" }) : null,
      ]),
      el("div", { class: "route-bands" }, [
        bandRow("exposure", route.exposure_band, BAND_STEPS.indexOf(route.exposure_band)),
        bandRow(
          "instability",
          instability,
          BAND_STEPS.indexOf(instability),
          `${route.instability_pct}%`,
        ),
      ]),
      el("div", {
        class: "route-detail",
        text: `${route.distance_label} · ${route.elapsed_days} days · wear +${route.wear_delta_pct} · cryo-age +${route.cryo_decay_delta_pct}`,
      }),
      el("div", { class: "action-row" }, [
        plotAction ? actionButton(plotAction) : null,
        route.is_plotted && jumpAction ? actionButton(jumpAction) : null,
      ]),
    ],
  );
  return el("div", { class: "route-branch" }, [
    el("span", { class: "route-connector", "aria-hidden": "true" }),
    node,
  ]);
}

function instabilityBand(pct) {
  if (pct >= 30) return "severe";
  if (pct >= 20) return "high";
  if (pct >= 10) return "moderate";
  if (pct > 0) return "low";
  return "none";
}

// A four-pip qualitative indicator plus the band word as the text equivalent.
// `filled` is the band index (none=0 … severe=4); the pips are aria-hidden.
function bandRow(label, bandText, filled, extra) {
  const pips = el(
    "span",
    { class: "band-pips", "aria-hidden": "true" },
    [0, 1, 2, 3].map((index) => el("span", { class: `band-pip ${index < filled ? "on" : ""}`.trim() })),
  );
  return el("div", { class: `band-row band-${bandText}` }, [
    el("span", { class: "band-label", text: label }),
    pips,
    el("span", { class: "band-text", text: extra ? `${bandText} (${extra})` : bandText }),
  ]);
}

// ---- Containment ----

function renderContainment(view) {
  const sectors = view.schematic.sectors;
  const selected = sectors.find((sector) => sector.id === ui.selectedSector) || sectors[0];
  const frag = document.createDocumentFragment();

  frag.append(
    el("div", { class: "system-head" }, [
      el("h3", { text: "Containment" }),
      el("span", { class: "status-badge", text: view.schematic.containment_summary }),
    ]),
    el(
      "div",
      { class: "action-row", "aria-label": "Select sector" },
      sectors.map((sector) =>
        el(
          "button",
          {
            type: "button",
            "aria-pressed": sector.id === selected.id ? "true" : "false",
            class: sector.id === selected.id ? "" : "",
            onclick: () => selectSector(sector.id),
          },
          sector.label,
        ),
      ),
    ),
  );

  if (selected) {
    append(
      frag,
      el("p", { class: "nav-fix" }, [
        el("b", { text: selected.label }),
        ` — ${selected.function}. controls: ${selected.controls}.`,
        el("br"),
        `reported ${selected.reported_state}; signal ${selected.signal_confidence}; containment ${selected.containment}${selected.rerouted ? ", rerouted" : ""}.`,
      ]),
      actionGroup(
        "Containment",
        view.actions.filter((action) => action.kind === "containment" && action.target === selected.id),
      ),
      actionGroup("Inspect", filterActions(view.actions, "raw", "schematic")),
    );
  }
  frag.append(el("p", { class: "schematic-note", text: `arka locus: ${view.schematic.arka_locus}` }));
  return frag;
}

function selectSector(id) {
  ui.selectedSector = id;
  ui.pendingConfirm = null;
  if (ui.snapshot) {
    renderActiveSystem(ui.snapshot.ui);
    renderSchematic(ui.snapshot.ui);
    renderMap(ui.snapshot.ui);
  }
}

// ---- Schematic ----

function renderSchematic(view) {
  replace(
    els.schematicBody,
    schematicDiagram(view, focusSector),
    el("p", { class: "schematic-note", text: view.schematic.arka_locus }),
  );
}

// The deck diagram is shared between the desk panel and the map's deck-plan
// pane; only what selecting a sector *does* differs, so the handler is a
// parameter. Everything drawn comes from the same projected snapshot.
function schematicDiagram(view, onSelect) {
  const noise = view.visual_state.schematic_noise_by_sector || {};
  const sectors = view.schematic.sectors;
  const [vw, vh] = SCHEMATIC_VIEWBOX;
  const positions = schematicPositions(sectors);

  // Connecting lines from reported adjacency, each undirected edge drawn once.
  const drawn = new Set();
  const lines = [];
  for (const sector of sectors) {
    for (const otherId of sector.adjacent || []) {
      if (!positions[otherId]) continue;
      const key = [sector.id, otherId].sort().join("|");
      if (drawn.has(key)) continue;
      drawn.add(key);
      const [x1, y1] = positions[sector.id];
      const [x2, y2] = positions[otherId];
      lines.push(
        svgEl("line", {
          x1,
          y1,
          x2,
          y2,
          class: "schematic-edge",
          "data-edge": edgeState(noise[sector.id], noise[otherId]),
        }),
      );
    }
  }
  const edges = svgEl(
    "svg",
    {
      class: "schematic-edges",
      viewBox: `0 0 ${vw} ${vh}`,
      preserveAspectRatio: "xMidYMid meet",
      "aria-hidden": "true",
      focusable: "false",
    },
    lines,
  );

  const nodes = sectors.map((sector) => {
    const [x, y] = positions[sector.id];
    const selected = sector.id === ui.selectedSector;
    return el(
      "button",
      {
        type: "button",
        class: "sector-node",
        style: `left:${(x / vw) * 100}%;top:${(y / vh) * 100}%`,
        dataset: {
          selected: selected ? "true" : "false",
          noise: noise[sector.id] || "steady",
          containment: sector.containment,
        },
        // The aria-label carries the full textual state so the node stays
        // legible regardless of any visual corruption (accessible equivalent).
        "aria-label": sectorAriaLabel(sector),
        "aria-pressed": selected ? "true" : "false",
        onclick: () => onSelect(sector.id),
      },
      [
        el("span", { class: "sector-name", text: sector.label }),
        el("span", {
          class: "sector-state",
          "aria-hidden": "true",
          text: `${sector.reported_state} · ${sector.signal_confidence}`,
        }),
        containmentTag(sector),
      ],
    );
  });

  const diagram = el(
    "div",
    {
      class: "schematic-diagram",
      role: "group",
      "aria-label": "Ship sector diagram",
      // Label instability is drift-driven atmosphere, applied as a data hook
      // for CSS only. It must never be printed as text (it would leak the
      // hidden drift stage), and it never hides the sector labels.
      dataset: { labelInstability: view.visual_state.label_instability || "stable" },
    },
    [edges, ...nodes],
  );

  return diagram;
}

function schematicPositions(sectors) {
  const positions = {};
  const unknown = sectors.filter((sector) => !SCHEMATIC_LAYOUT[sector.id]);
  let fallbackIndex = 0;
  for (const sector of sectors) {
    if (SCHEMATIC_LAYOUT[sector.id]) {
      positions[sector.id] = SCHEMATIC_LAYOUT[sector.id];
    } else {
      const span = SCHEMATIC_VIEWBOX[0] / (unknown.length + 1);
      positions[sector.id] = [span * (fallbackIndex + 1), SCHEMATIC_VIEWBOX[1] - 26];
      fallbackIndex += 1;
    }
  }
  return positions;
}

const EDGE_SEVERED = new Set(["isolated", "blank"]);
const EDGE_DEGRADED = new Set(["broken", "disagreeing", "thin"]);

function edgeState(a, b) {
  if (EDGE_SEVERED.has(a) || EDGE_SEVERED.has(b)) return "severed";
  if (EDGE_DEGRADED.has(a) || EDGE_DEGRADED.has(b)) return "degraded";
  return "steady";
}

function sectorAriaLabel(sector) {
  return [
    `${sector.label}, ${sector.function}`,
    `reported ${sector.reported_state}`,
    `signal ${sector.signal_confidence}`,
    `containment ${sector.containment}${sector.rerouted ? ", rerouted" : ""}`,
  ].join("; ");
}

function containmentTag(sector) {
  if (sector.containment === "sealed") return el("span", { class: "sector-tag sealed", text: "sealed" });
  if (sector.containment === "abandoned") return el("span", { class: "sector-tag abandoned", text: "written off" });
  if (sector.rerouted) return el("span", { class: "sector-tag", text: "rerouted" });
  return null;
}

function focusSector(id) {
  ui.selectedSector = id;
  ui.pendingConfirm = null;
  setActiveSystem("containment");
  renderSchematic(ui.snapshot.ui);
}

// ---- Objective / incident ----

function renderObjective(view) {
  const o = view.objective;
  const nodes = [
    objectiveLine("Objective", o.summary),
    objectiveLine("Watch", o.watch),
    objectiveLine("Attention", o.attention),
    objectiveLine("Crew load", o.manual_budget),
  ];

  if (view.incident) {
    const inc = view.incident;
    nodes.push(
      el("div", { class: "incident-card", role: "status" }, [
        el("h3", { text: inc.title }),
        el("p", { class: "incident-meta" }, `beats left: ${inc.turns_left} · checklist ${inc.progress}/${inc.required_progress}`),
      ]),
    );
  }

  const waitAction = view.actions.find((action) => action.id === "wait");
  if (waitAction) {
    nodes.push(el("div", { class: "action-group" }, el("div", { class: "action-row" }, actionButton(waitAction, "Wait one beat"))));
  }
  replace(els.objectiveBody, ...nodes);
}

function objectiveLine(key, value) {
  return el("dl", { class: "objective-line" }, [
    el("dt", { text: key }),
    el("dd", { text: value || "—" }),
  ]);
}

// ---- Raw telemetry drawer ----

function renderRaw(view) {
  const confidence = view.visual_state.raw_signal_confidence_by_panel || {};
  const entries = RAW_ORDER.filter((id) => view.raw_panels[id]).map((id) => {
    const panel = view.raw_panels[id];
    const conf = panel.confidence || confidence[id] || "steady";
    const details = el(
      "details",
      { class: "raw-entry", ...(ui.openRaw.has(id) ? { open: true } : {}) },
      [
        el("summary", {}, [
          el("span", { class: "raw-title", text: panel.label }),
          el("span", { class: "raw-source", text: panel.source }),
          el("span", { class: `raw-confidence ${conf}`, text: conf }),
        ]),
        el("pre", { class: "raw-lines", text: panel.lines.join("\n") }),
      ],
    );
    details.addEventListener("toggle", () => {
      if (details.open) ui.openRaw.add(id);
      else ui.openRaw.delete(id);
    });
    return details;
  });
  replace(els.rawBody, ...entries);
}

// ---- Log / transcript ----

function renderLog(snapshot) {
  replace(
    els.logTabs,
    logTab("transcript", "Transcript"),
    logTab("actions", "Action log"),
  );

  els.logBody.setAttribute("aria-labelledby", `logtab-${ui.logView}`);
  if (ui.logView === "actions") {
    const rows = (snapshot.history || []).map((record) =>
      el("div", { class: "log-row" }, [
        el("span", { class: "log-beat", text: `b${record.beat_after}` }),
        el("span", { text: `${record.raw}${record.advanced ? "" : "  ·  held"}` }),
      ]),
    );
    replace(els.logBody, el("div", { class: "action-log" }, rows.length ? rows : el("p", { class: "schematic-note", text: "no actions yet." })));
  } else {
    const lines = snapshot.transcript_tail || [];
    replace(
      els.logBody,
      el("div", { class: "transcript" }, lines.map((line) => el("div", { class: `line ${lineClass(line)}`.trim(), text: line || " " }))),
    );
    els.logBody.scrollTop = els.logBody.scrollHeight;
  }
}

function logTab(view, label) {
  const selected = ui.logView === view;
  return el(
    "button",
    {
      id: `logtab-${view}`,
      role: "tab",
      type: "button",
      "aria-selected": selected ? "true" : "false",
      "aria-controls": "logBody",
      onclick: () => {
        ui.logView = view;
        if (ui.snapshot) renderLog(ui.snapshot);
      },
    },
    label,
  );
}

function lineClass(text) {
  const lower = text.toLowerCase();
  if (text.startsWith(">")) return "input";
  if (text.startsWith("arka:")) return "arka";
  if (lower.startsWith("raw ") || lower.includes(" telemetry")) return "raw";
  if (lower.includes("critical") || lower.includes("loss") || lower.includes("lost") || lower.includes("rupture") || lower.includes("collapse")) {
    return "danger";
  }
  return "";
}

// ---- Actions ----

function filterActions(actions, kind, target) {
  return actions.filter((action) => action.kind === kind && action.target === target);
}

function actionGroup(title, actions, variant = "") {
  if (!actions.length) return null;
  return el("div", { class: "action-group" }, [
    el("h4", { text: title }),
    el("div", { class: `action-row ${variant}`.trim() }, actions.map((action) => actionButton(action))),
  ]);
}

function actionButton(action, labelOverride) {
  const dangerous = action.requires_confirmation && (action.command.startsWith("abandon") || action.command.startsWith("seal") || action.command === "jump");
  const title = !action.enabled && action.reason ? action.reason : action.detail || undefined;
  return el(
    "button",
    {
      type: "button",
      class: dangerous ? "danger-action" : "",
      disabled: !action.enabled,
      "aria-disabled": action.enabled ? null : "true",
      title,
      onclick: () => dispatchAction(action),
    },
    labelOverride || action.label,
  );
}

function dispatchAction(action) {
  if (!action.enabled) return;
  if (action.requires_confirmation) {
    ui.pendingConfirm = action;
    renderConfirmSurfaces();
    // Move focus into the confirmation, defaulting to the safe (Cancel) choice
    // — in whichever view the player actually triggered it.
    const scope = effectiveView() === "map" ? els.mapView : els.systemBody;
    const cancel = scope.querySelector(".confirm-cancel");
    if (cancel) cancel.focus();
    return;
  }
  sendCommand(action.command).catch(showFault);
}

// The confirmation strip can be triggered from the desk's system panel or from
// the map (jump / seal / abandon live in both). Re-render both hosts so the
// pending state is consistent wherever the player looks next.
function renderConfirmSurfaces() {
  if (!ui.snapshot) return;
  renderActiveSystem(ui.snapshot.ui);
  renderMapConfirm();
}

function confirmStrip() {
  if (!ui.pendingConfirm) return null;
  const action = ui.pendingConfirm;
  return el("div", { class: "confirm-strip", role: "alert" }, [
    el("p", { text: confirmMessage(action) }),
    el("button", { type: "button", class: "danger-action", onclick: () => sendCommand(action.command).catch(showFault) }, "Confirm"),
    el("button", { type: "button", class: "confirm-cancel", onclick: cancelConfirm }, "Cancel"),
  ]);
}

function confirmMessage(action) {
  if (action.command === "jump") return "Commit the plotted jump? The ship cannot recall it.";
  if (action.command.startsWith("abandon")) return `${action.label}? This cannot be undone, and what is inside goes with it.`;
  if (action.command.startsWith("seal")) return `${action.label}? Manual access on the far side gets harder.`;
  if (action.command === "triage") return "Triage pods by hand? You choose which lights get answered first.";
  return `${action.label}?`;
}

function cancelConfirm() {
  ui.pendingConfirm = null;
  renderConfirmSurfaces();
}

// ---- Faults ----

function showFault(error) {
  console.error(error);
  replace(
    els.arkaBody,
    el("div", { class: "arka-advisory" }, el("p", { text: "Local channel fault. I still have the board; try again." })),
  );
}

// ---- Views: desk / map / dark ----

// Three places, moved between deliberately. The desk is home; the map and the
// Dark are full-screen surfaces you go to and come back from (Esc). Focus mode
// always renders as the Dark — handing over the watch means facing the void.
const VIEWS = ["desk", "map", "dark"];

function effectiveView() {
  return ui.inFocus ? "dark" : ui.view;
}

function setView(target) {
  // Focus owns the screen; the only way out of the quiet is taking the watch back.
  if (ui.inFocus) return;
  if (!VIEWS.includes(target) || target === ui.view) return;
  ui.view = target;
  // The player's hand beats the warp moment: choosing a view ends the hold.
  if (warpHold) {
    warpHold = false;
    clearTimeout(warpTimer);
  }
  // A pending confirmation does not survive walking away from it.
  if (ui.pendingConfirm) {
    ui.pendingConfirm = null;
    renderConfirmSurfaces();
  }
  applyView({ forceFocus: true });
}

function applyView({ forceFocus = false } = {}) {
  const showing = warpHold ? "dark" : effectiveView();
  const previous = document.documentElement.dataset.view;
  document.documentElement.dataset.view = showing;
  els.darkView.dataset.mode = ui.inFocus ? "focus" : "outside";
  syncSpaceView();
  reconcileViewFocus(showing, forceFocus || previous !== showing);
}

function reconcileViewFocus(view, forceFocus) {
  const surface = activeViewSurface();
  if (forceFocus || (surface && surface !== view)) focusView(view);
}

function activeViewSurface() {
  const active = document.activeElement;
  if (!active || active === document.body) return null;
  if (active.classList && active.classList.contains("skip-link")) return "desk";
  if (active.closest(".desk")) return "desk";
  if (active.closest(".map-view")) return "map";
  if (active.closest(".dark-view")) return "dark";
  return null;
}

function focusView(view) {
  let target = els.commandInput;
  if (view === "map") {
    target = els.mapReturn;
  } else if (view === "dark") {
    target = ui.inFocus ? els.darkFocus.querySelector(".focus-leave") : els.darkReturn;
  }
  if (!target) return;
  target.focus({ preventScroll: true });
}

// ---- The Dark: full-screen window ----

function renderDark(view) {
  const nav = view.navigation;
  const m = view.mission;
  // The corner readout repeats only fields already shown on the desk — and the
  // glass itself carries no text at all. No Dark meter, ever.
  replace(
    els.darkReadouts,
    darkReadout("Heading", nav.current_fix_label),
    darkReadout("Range to fix", m.distance_label),
    darkReadout("Jumps run", String(nav.jumps_executed)),
    darkReadout("Exposure", nav.exposure_band, ["high", "severe"].includes(nav.exposure_band)),
  );
  // arka's light: the same deniable drift atmosphere as its panel. A data hook
  // for styling only — never printed, never a legible tell.
  els.arkaPresence.dataset.intensity = view.visual_state.arka_panel_intensity || "steady";
  space.exposure = EXPOSURE_LEVEL[nav.exposure_band] ?? 0;
  renderDarkFocus(view);
}

function darkReadout(label, value, alert = false) {
  return el("dl", { class: `dark-readout ${alert ? "alert" : ""}`.trim() }, [
    el("dt", { text: label }),
    el("dd", { text: value }),
  ]);
}

// Focus on the Dark: the desk is gone; what remains is the void, arka's light,
// arka's words, the strategic glance, and the way back. The command channel
// moves out here with the player (one form, one input, wherever the watch is).
function renderDarkFocus(view) {
  if (!ui.inFocus) {
    if (els.commandForm.parentElement !== els.arkaPanel) {
      els.arkaPanel.append(els.commandForm);
    }
    replace(els.darkFocus);
    return;
  }
  const advisory = (view.arka.advisory_lines || []).map((line) =>
    el("p", { text: stripArka(line) }),
  );
  const card = el("div", { class: "focus-card", "aria-label": "arka has the watch" }, [
    el("div", { class: "arka-advisory" }, advisory),
    focusQuiet(view),
  ]);
  replace(els.darkFocus, card);
  card.append(els.commandForm);
}

// ---- Starfield ----

// Painted from deterministic, already-shown snapshot fields only: jumps give
// the warp moment, the exposure band thins and edge-darkens the stars as the
// Dark closes in. Quiet, deniable, never a number. The loop runs only while
// the dark view is actually on screen and motion is allowed; otherwise a
// single static frame is drawn.
const EXPOSURE_LEVEL = { none: 0, low: 1, moderate: 2, high: 3, severe: 4 };
const STAR_COUNT = 460;

const space = {
  ctx: els.spaceView.getContext("2d"),
  stars: [],
  w: 0,
  h: 0,
  dpr: 1,
  raf: 0,
  exposure: 0,
  warp: 0,
};

let warpHold = false;
let warpTimer = 0;

function sizeSpaceView() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = Math.max(1, els.darkView.clientWidth || window.innerWidth);
  const h = Math.max(1, els.darkView.clientHeight || window.innerHeight);
  if (w === space.w && h === space.h && dpr === space.dpr) return;
  space.w = w;
  space.h = h;
  space.dpr = dpr;
  els.spaceView.width = Math.floor(w * dpr);
  els.spaceView.height = Math.floor(h * dpr);
  seedStars();
}

function seedStars() {
  space.stars = Array.from({ length: STAR_COUNT }, () => spawnStar(true));
}

function spawnStar(anywhere = false) {
  const depth = anywhere ? Math.random() : Math.random() * 0.25 + 0.75;
  return {
    x: (Math.random() - 0.5) * space.w * 1.6,
    y: (Math.random() - 0.5) * space.h * 1.6,
    z: Math.max(40, depth * space.w),
    pz: 0,
  };
}

function spaceMotionAllowed() {
  return document.documentElement.dataset.reducedMotion !== "true";
}

function drawSpaceView(moving) {
  const ctx = space.ctx;
  if (!ctx || !space.w) return;
  const { w, h, dpr } = space;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = "#020405";
  ctx.fillRect(0, 0, w, h);

  const exposure = space.exposure / 4;
  const cx = w / 2;
  const cy = h * 0.44;
  const speed = moving ? (space.warp > 0 ? 16 + space.warp * 10 : ui.inFocus ? 0.4 : 1.1) : 0;
  const brightness = 1 - exposure * 0.45;

  for (const star of space.stars) {
    star.pz = star.z;
    star.z -= speed;
    if (star.z < 8) {
      Object.assign(star, spawnStar());
      continue;
    }
    const sx = cx + (star.x / star.z) * w * 0.5;
    const sy = cy + (star.y / star.z) * w * 0.5;
    if (sx < -4 || sx > w + 4 || sy < -4 || sy > h + 4) continue;
    const near = 1 - star.z / w;
    const size = Math.max(0.5, near * 2.6);
    // The Dark eats the edges first: stars far from centre fade as exposure rises.
    const edge = Math.min(1, Math.hypot(sx - cx, sy - cy) / (Math.max(w, h) * 0.62));
    const alpha = Math.max(0, brightness * (0.45 + near * 0.55) * (1 - edge * exposure * 0.85));
    if (alpha <= 0.02) continue;

    if (space.warp > 0 && moving) {
      const px = cx + (star.x / star.pz) * w * 0.5;
      const py = cy + (star.y / star.pz) * w * 0.5;
      ctx.strokeStyle = `rgba(196, 224, 228, ${alpha})`;
      ctx.lineWidth = size;
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(sx, sy);
      ctx.stroke();
    } else {
      ctx.fillStyle = `rgba(208, 226, 230, ${alpha})`;
      ctx.beginPath();
      ctx.arc(sx, sy, size, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // The closing vignette: tighter and deeper as exposure rises. No meter.
  const inner = Math.max(h * (0.55 - exposure * 0.25), h * 0.18);
  const grad = ctx.createRadialGradient(cx, cy, inner, cx, cy, Math.max(w, h) * 0.78);
  grad.addColorStop(0, "rgba(0,0,0,0)");
  grad.addColorStop(1, `rgba(1,2,3,${0.45 + exposure * 0.45})`);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, w, h);

  if (space.warp > 0) space.warp = Math.max(0, space.warp - 0.012);
}

function spaceFrame() {
  if (document.documentElement.dataset.view !== "dark" || !spaceMotionAllowed()) {
    space.raf = 0;
    return;
  }
  drawSpaceView(true);
  space.raf = requestAnimationFrame(spaceFrame);
}

// Start, stop, or redraw the starfield to match what is currently on screen.
function syncSpaceView() {
  cancelAnimationFrame(space.raf);
  space.raf = 0;
  if (document.documentElement.dataset.view !== "dark") return;
  sizeSpaceView();
  if (spaceMotionAllowed()) {
    space.raf = requestAnimationFrame(spaceFrame);
  } else {
    space.warp = 0;
    drawSpaceView(false);
  }
}

// A jump just landed (the already-shown counter went up): bring the Dark
// forward for a moment of warp, then hand back whichever view the player was
// in. Skipped entirely under reduced motion.
function detectJump(view) {
  const jumps = view.navigation.jumps_executed || 0;
  const prev = ui.prevJumps;
  ui.prevJumps = jumps;
  if (prev === null || jumps <= prev) return;
  if (!spaceMotionAllowed()) return;
  space.warp = 1;
  if (effectiveView() !== "dark") {
    warpHold = true;
    clearTimeout(warpTimer);
    warpTimer = setTimeout(() => {
      warpHold = false;
      applyView();
    }, 2100);
  }
}

// ---- Map: nav plot + deck plan ----

function renderMap(view) {
  renderMapHead(view);
  renderMapConfirm();
  renderMapChart(view);
  renderMapRoutes(view);
  renderMapShip(view);
}

function renderMapHead(view) {
  const nav = view.navigation;
  replace(
    els.mapHeadStats,
    stat("Current fix", nav.current_fix_label),
    stat("Signal", nav.current_signal),
    stat("Plotted", nav.plotted_route_label || "none"),
    stat("Exposure", nav.exposure_band, ["high", "severe"].includes(nav.exposure_band) ? "alert" : ""),
    stat("Jumps run", String(nav.jumps_executed)),
  );
}

function renderMapConfirm() {
  replace(els.mapConfirm, ui.snapshot && effectiveView() === "map" ? confirmStrip() : null);
}

// The chart: the fix on the left, candidate routes fanning out as paths, and
// the Dark as territory in the lower-right — each path dips toward it by its
// exposure band. Drawn only from band words and route facts the cards beside
// it already carry as text, so the whole SVG stays decorative (aria-hidden).
function renderMapChart(view) {
  const nav = view.navigation;
  const routes = nav.route_options || [];
  const W = 1000;
  const H = 540;
  const fx = 130;
  const fy = 250;

  const children = [];

  // The Dark: a field, not a meter. Fixed territory the deep paths cut into.
  children.push(
    svgEl("defs", {}, [
      svgEl("radialGradient", { id: "darkfield", cx: "78%", cy: "96%", r: "85%" }, [
        svgEl("stop", { offset: "0%", "stop-color": "#000000", "stop-opacity": "0.92" }),
        svgEl("stop", { offset: "55%", "stop-color": "#01070a", "stop-opacity": "0.75" }),
        svgEl("stop", { offset: "100%", "stop-color": "#02090d", "stop-opacity": "0" }),
      ]),
    ]),
    svgEl("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#darkfield)" }),
    svgEl("text", {
      x: W * 0.74,
      y: H * 0.82,
      class: "chart-dark-label",
      "text-anchor": "middle",
    }, "THE DARK"),
  );

  // Faint chart graticule, so it reads as an instrument and not empty space.
  for (let gx = 100; gx < W; gx += 100) {
    children.push(svgEl("line", { x1: gx, y1: 20, x2: gx, y2: H - 20, class: "chart-grid" }));
  }
  for (let gy = 90; gy < H; gy += 90) {
    children.push(svgEl("line", { x1: 30, y1: gy, x2: W - 30, y2: gy, class: "chart-grid" }));
  }

  // Routes fan to onward lanes ordered by exposure (calm lanes high, the deep
  // ones bending down into the field).
  const ordered = [...routes].sort(
    (a, b) => (EXPOSURE_LEVEL[a.exposure_band] ?? 0) - (EXPOSURE_LEVEL[b.exposure_band] ?? 0),
  );
  ordered.forEach((route, index) => {
    const count = ordered.length;
    const endX = 880;
    const endY = count === 1 ? 240 : 110 + index * (300 / Math.max(1, count - 1));
    const bandIdx = EXPOSURE_LEVEL[route.exposure_band] ?? 0;
    const dip = bandIdx * 62;
    const cpY = (fy + endY) / 2 + dip;
    const dash = { none: "", low: "", moderate: "12 5", high: "7 6", severe: "3 7" }[
      instabilityBand(route.instability_pct)
    ];
    children.push(
      svgEl("path", {
        d: `M ${fx + 18} ${fy} Q 520 ${cpY} ${endX} ${endY}`,
        class: "chart-route",
        "data-plotted": route.is_plotted ? "true" : "false",
        "data-lastjump": route.is_last_jump ? "true" : "false",
        "stroke-dasharray": dash || null,
        style: `stroke-opacity:${0.95 - bandIdx * 0.13}`,
      }),
      svgEl("circle", { cx: endX, cy: endY, r: 5, class: "chart-end", "data-plotted": route.is_plotted ? "true" : "false" }),
      svgEl("text", { x: W - 16, y: endY - 12, class: "chart-route-label", "text-anchor": "end" }, route.label),
      svgEl("text", { x: W - 16, y: endY + 22, class: "chart-route-detail", "text-anchor": "end" },
        `${route.distance_label} · exposure ${route.exposure_band}`),
    );
  });

  // The current fix: where the ship believes it is.
  children.push(
    svgEl("circle", { cx: fx, cy: fy, r: 16, class: "chart-fix-ring" }),
    svgEl("circle", { cx: fx, cy: fy, r: 6, class: "chart-fix" }),
    svgEl("text", { x: fx, y: fy - 28, class: "chart-fix-label", "text-anchor": "middle" }, nav.current_fix_label),
    svgEl("text", { x: 36, y: fy + 38, class: "chart-fix-detail" }, `signal ${nav.current_signal}`),
  );

  const chart = svgEl(
    "svg",
    {
      viewBox: `0 0 ${W} ${H}`,
      preserveAspectRatio: "xMidYMid meet",
      class: "chart-svg",
      "aria-hidden": "true",
      focusable: "false",
    },
    children,
  );
  replace(els.mapChart, chart);
}

// The route cards reuse the desk's branching display wholesale — same bands,
// same facts, same plot/execute action specs through the same dispatch.
function renderMapRoutes(view) {
  const nav = view.navigation;
  const plottedLine = nav.plotted_route_label
    ? el("p", { class: "route-origin-plotted" }, ["plotted: ", el("b", { text: nav.plotted_route_label })])
    : el("p", { class: "route-origin-plotted muted", text: "no route plotted" });
  replace(
    els.mapRoutes,
    el("div", { class: "map-routes-head" }, [
      el("h3", { text: "Candidate routes" }),
      standingBadge(nav.standing),
      plottedLine,
    ]),
    el(
      "div",
      { class: "route-branches" },
      nav.route_options.map((route) => routeBranch(view, route)),
    ),
    actionGroup("Delegate", filterActions(view.actions, "delegate", "navigation"), "delegate"),
    actionGroup("Standing watch", filterActions(view.actions, "standing", "navigation"), "delegate"),
    actionGroup("Inspect", filterActions(view.actions, "raw", "navigation")),
  );
}

// The deck plan: the same diagram as the desk panel at map scale, with the
// selected sector's containment controls beside it instead of a tab jump.
function renderMapShip(view) {
  replace(els.mapSchematic, schematicDiagram(view, selectSector));

  const sectors = view.schematic.sectors;
  const selected = sectors.find((sector) => sector.id === ui.selectedSector) || sectors[0];
  const nodes = [];
  if (selected) {
    nodes.push(
      el("p", { class: "nav-fix" }, [
        el("b", { text: selected.label }),
        ` — ${selected.function}. controls: ${selected.controls}.`,
        el("br"),
        `reported ${selected.reported_state}; signal ${selected.signal_confidence}; containment ${selected.containment}${selected.rerouted ? ", rerouted" : ""}.`,
      ]),
      actionGroup(
        "Containment",
        view.actions.filter((action) => action.kind === "containment" && action.target === selected.id),
      ),
    );
  }
  nodes.push(el("p", { class: "schematic-note", text: `arka locus: ${view.schematic.arka_locus}` }));
  replace(els.mapSector, ...nodes);
}

// ---- Keyboard ----

function isTyping(target) {
  return target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (ui.pendingConfirm) {
      cancelConfirm();
      event.preventDefault();
    } else if (ui.inFocus) {
      // Esc always takes the watch back — the way out of the quiet is never trapped.
      sendCommand("leave focus").catch(showFault);
      event.preventDefault();
    } else if (ui.view !== "desk") {
      // From the map or the window, Esc is the walk back to the desk.
      setView("desk");
      event.preventDefault();
    } else if (document.activeElement === els.commandInput) {
      els.commandInput.blur();
    }
    return;
  }
  if (event.ctrlKey || event.metaKey || event.altKey || isTyping(event.target)) return;

  if (event.key >= "1" && event.key <= "4") {
    setActiveSystem(SYSTEM_TABS[Number(event.key) - 1].id);
    event.preventDefault();
  } else if (event.key === "m") {
    setView(ui.view === "map" ? "desk" : "map");
    event.preventDefault();
  } else if (event.key === "o") {
    setView(ui.view === "dark" ? "desk" : "dark");
    event.preventDefault();
  } else if (event.key === "/") {
    // The command channel lives on the desk (or out on the Dark during focus).
    if (!ui.inFocus && ui.view !== "desk") setView("desk");
    els.commandInput.focus();
    event.preventDefault();
  } else if (event.key === ".") {
    sendCommand("wait").catch(showFault);
    event.preventDefault();
  } else if (event.key === "?") {
    if (!ui.inFocus && ui.view !== "desk") setView("desk");
    els.diagnostics.open = true;
    els.diagnostics.querySelector("summary").focus();
    event.preventDefault();
  }
});

// Roving arrow-key movement across the system tablist.
els.systemTabs.addEventListener("keydown", (event) => {
  if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
  const index = SYSTEM_TABS.findIndex((tab) => tab.id === ui.activeSystem);
  const next = event.key === "ArrowRight" ? (index + 1) % SYSTEM_TABS.length : (index - 1 + SYSTEM_TABS.length) % SYSTEM_TABS.length;
  setActiveSystem(SYSTEM_TABS[next].id);
  els.systemTabs.querySelector('[aria-selected="true"]').focus();
  event.preventDefault();
});

// ---- Reduced motion ----

function applyReducedMotion(enabled) {
  document.documentElement.dataset.reducedMotion = enabled ? "true" : "false";
  els.reducedMotionToggle.checked = enabled;
  // The starfield picks up the static-frame / animated choice immediately.
  syncSpaceView();
}

// ---- Wiring ----

els.commandForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const command = els.commandInput.value;
  els.commandInput.value = "";
  try {
    await sendCommand(command);
  } catch (error) {
    showFault(error);
  }
});

els.saveButton.addEventListener("click", () => saveSession().catch(showFault));
els.loadButton.addEventListener("click", () => loadSession().catch(showFault));
els.reducedMotionToggle.addEventListener("change", (event) => applyReducedMotion(event.target.checked));

// View rail and the ways back. Static buttons — never re-rendered, never lose focus.
els.railMap.addEventListener("click", () => setView("map"));
els.railDark.addEventListener("click", () => setView("dark"));
els.mapReturn.addEventListener("click", () => setView("desk"));
els.darkReturn.addEventListener("click", () => setView("desk"));

let resizeTimer = 0;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(syncSpaceView, 120);
});

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
applyReducedMotion(prefersReducedMotion);
applyView();

createSession().catch(showFault);
