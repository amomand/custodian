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

// UI-local state, preserved across snapshot re-renders.
const ui = {
  sessionId: null,
  snapshot: null,
  activeSystem: "coolant",
  selectedSector: null,
  openRaw: new Set(),
  logView: "transcript",
  pendingConfirm: null,
};

const els = {
  missionStrip: document.querySelector("#missionStrip"),
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

  renderMissionStrip(view, snapshot);
  renderArka(view);
  renderSystemTabs(view);
  renderActiveSystem(view);
  renderSchematic(view);
  renderObjective(view);
  renderRaw(view);
  renderLog(snapshot);

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
  replace(els.arkaBody, ...nodes);
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

  frag.append(
    el("div", { class: "system-head" }, [
      el("h3", { text: system.label }),
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
    actionGroup("Inspect", filterActions(actions, "raw", id)),
  );
  return frag;
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
  const nav = view.navigation;
  const frag = document.createDocumentFragment();

  frag.append(
    el("div", { class: "system-head" }, [
      el("h3", { text: "Navigation" }),
      el("span", { class: "status-badge" }, `exposure ${nav.exposure_band}`),
    ]),
    el("p", { class: "nav-fix" }, [
      el("b", { text: nav.current_fix_label }),
      ` — ${nav.current_purpose}. signal: ${nav.current_signal}.`,
      nav.plotted_route_label
        ? el("span", {}, [el("br"), `plotted: `, el("b", { text: nav.plotted_route_label })])
        : null,
    ]),
    el(
      "div",
      { class: "route-list" },
      nav.route_options.map((route) => routeCard(view, route)),
    ),
    actionGroup("Delegate", filterActions(view.actions, "delegate", "navigation"), "delegate"),
    actionGroup("Inspect", filterActions(view.actions, "raw", "navigation")),
  );
  return frag;
}

function routeCard(view, route) {
  const plotAction = view.actions.find(
    (action) => action.kind === "navigation" && action.command === `plot ${route.jump_class}`,
  );
  const jumpAction = view.actions.find((action) => action.id === "execute-jump");
  const cls = ["route-card", route.is_plotted ? "plotted" : "", route.is_last_jump ? "last-jump" : ""]
    .join(" ")
    .trim();

  return el("div", { class: cls }, [
    el("div", { class: "route-head" }, [
      el("strong", { text: route.label }),
      el("span", { class: "route-class", text: route.jump_class }),
    ]),
    el("div", { class: "route-stats" }, [
      kv("dist", route.distance_label),
      kv("days", route.elapsed_days),
      kv("exposure", route.exposure_band),
      kv("instability", `${route.instability_pct}%`),
      kv("wear", `+${route.wear_delta_pct}`),
      kv("cryo-age", `+${route.cryo_decay_delta_pct}`),
    ]),
    el("div", { class: "action-row" }, [
      plotAction ? actionButton(plotAction) : null,
      route.is_plotted && jumpAction ? actionButton(jumpAction) : null,
    ]),
  ]);
}

function kv(key, value) {
  return el("span", {}, [`${key} `, el("b", { text: String(value) })]);
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
    frag.append(
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
  }
}

// ---- Schematic ----

function renderSchematic(view) {
  const noise = view.visual_state.schematic_noise_by_sector || {};
  const grid = el(
    "div",
    { class: "schematic-grid" },
    view.schematic.sectors.map((sector) =>
      el(
        "button",
        {
          type: "button",
          class: "sector",
          dataset: {
            selected: sector.id === ui.selectedSector ? "true" : "false",
            noise: noise[sector.id] || "steady",
          },
          onclick: () => focusSector(sector.id),
        },
        [
          el("span", { class: "sector-name", text: sector.label }),
          el("span", { class: "sector-state", text: `${sector.reported_state} · ${sector.signal_confidence}` }),
          containmentTag(sector),
        ],
      ),
    ),
  );
  replace(
    els.schematicBody,
    grid,
    el("p", { class: "schematic-note", text: view.schematic.arka_locus }),
  );
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
    renderActiveSystem(ui.snapshot.ui);
    // Move focus into the confirmation, defaulting to the safe (Cancel) choice.
    const cancel = els.systemBody.querySelector(".confirm-cancel");
    if (cancel) cancel.focus();
    return;
  }
  sendCommand(action.command).catch(showFault);
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
  if (ui.snapshot) renderActiveSystem(ui.snapshot.ui);
}

// ---- Faults ----

function showFault(error) {
  console.error(error);
  replace(
    els.arkaBody,
    el("div", { class: "arka-advisory" }, el("p", { text: "Local channel fault. I still have the board; try again." })),
  );
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
    } else if (document.activeElement === els.commandInput) {
      els.commandInput.blur();
    }
    return;
  }
  if (event.ctrlKey || event.metaKey || event.altKey || isTyping(event.target)) return;

  if (event.key >= "1" && event.key <= "4") {
    setActiveSystem(SYSTEM_TABS[Number(event.key) - 1].id);
    event.preventDefault();
  } else if (event.key === "/") {
    els.commandInput.focus();
    event.preventDefault();
  } else if (event.key === ".") {
    sendCommand("wait").catch(showFault);
    event.preventDefault();
  } else if (event.key === "?") {
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

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
applyReducedMotion(prefersReducedMotion);

createSession().catch(showFault);
