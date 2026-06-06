let sessionId = null;

const els = {
  sessionLabel: document.querySelector("#sessionLabel"),
  statusOutput: document.querySelector("#statusOutput"),
  transcriptOutput: document.querySelector("#transcriptOutput"),
  commandForm: document.querySelector("#commandForm"),
  commandInput: document.querySelector("#commandInput"),
  saveBuffer: document.querySelector("#saveBuffer"),
  saveButton: document.querySelector("#saveButton"),
  loadButton: document.querySelector("#loadButton"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "content-type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

async function createSession() {
  const snapshot = await api("/api/session", { method: "POST", body: "{}" });
  sessionId = snapshot.session_id;
  renderSnapshot(snapshot);
  els.commandInput.focus();
}

async function sendCommand(command) {
  if (!sessionId) return;
  const payload = JSON.stringify({ command });
  const data = await api(`/api/session/${sessionId}/command`, {
    method: "POST",
    body: payload,
  });
  renderSnapshot(data.snapshot);
}

async function saveSession() {
  if (!sessionId) return;
  const data = await api(`/api/session/${sessionId}/save`, {
    method: "POST",
    body: "{}",
  });
  els.saveBuffer.value = data.save;
  renderSnapshot(data.snapshot);
}

async function loadSession() {
  if (!sessionId || !els.saveBuffer.value.trim()) return;
  const data = await api(`/api/session/${sessionId}/load`, {
    method: "POST",
    body: JSON.stringify({ save: els.saveBuffer.value }),
  });
  renderSnapshot(data.snapshot);
}

function renderSnapshot(snapshot) {
  sessionId = snapshot.session_id;
  els.sessionLabel.textContent = `${snapshot.session_id.slice(0, 8)} / beat ${snapshot.turn}`;
  els.statusOutput.textContent = (snapshot.status || []).join("\n");
  els.transcriptOutput.replaceChildren(
    ...normaliseLines(snapshot.transcript_tail || []).map(renderLine),
  );
  els.transcriptOutput.scrollTop = els.transcriptOutput.scrollHeight;
}

function normaliseLines(lines) {
  if (!lines.length) return [""];
  return lines;
}

function renderLine(text) {
  const div = document.createElement("div");
  div.className = `line ${lineClass(text)}`;
  div.textContent = text || " ";
  return div;
}

function lineClass(text) {
  const lower = text.toLowerCase();
  if (text.startsWith(">")) return "input";
  if (text.startsWith("arka:")) return "arka";
  if (lower.startsWith("raw ") || lower.includes(" telemetry")) return "raw";
  if (
    lower.includes("critical") ||
    lower.includes("loss") ||
    lower.includes("failed") ||
    lower.includes("dying")
  ) {
    return "danger";
  }
  return "";
}

function showFault(error) {
  console.error(error);
  els.transcriptOutput.replaceChildren(
    renderLine("arka: Local channel fault. I still have the board; try again."),
  );
}

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

els.saveButton.addEventListener("click", async () => {
  try {
    await saveSession();
  } catch (error) {
    showFault(error);
  }
});

els.loadButton.addEventListener("click", async () => {
  try {
    await loadSession();
  } catch (error) {
    showFault(error);
  }
});

createSession().catch(showFault);
