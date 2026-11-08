const state = {
  meta: null,
  view: "desk",
  jobId: null,
  ws: null,
  reports: {},
  activeSection: null,
};

const SECTIONS = [
  ["market_report", "Marché"],
  ["sentiment_report", "Sentiment"],
  ["news_report", "News"],
  ["fundamentals_report", "Fondamentaux"],
  ["investment_plan", "Recherche"],
  ["trader_investment_plan", "Trader"],
  ["final_trade_decision", "Portfolio"],
];

const TEAMS = [
  ["Analystes", ["Market Analyst", "Sentiment Analyst", "News Analyst", "Fundamentals Analyst"]],
  ["Recherche", ["Bull Researcher", "Bear Researcher", "Research Manager"]],
  ["Trading", ["Trader"]],
  ["Risque & PM", ["Aggressive Analyst", "Neutral Analyst", "Conservative Analyst", "Portfolio Manager"]],
];

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

function clock() {
  const now = new Date();
  $("#clock").textContent = now.toLocaleString("fr-CA", { hour12: false });
}

function show(view) {
  state.view = view;
  $$(".view").forEach((el) => el.classList.toggle("active", el.id === `view-${view}`));
  $$(".rail nav button").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === view));
  const titles = {
    desk: ["Desk", "Le même moteur que le CLI, en salle de marché."],
    analyze: ["Nouvelle analyse", "Composez une run comme au terminal."],
    warroom: ["Salle des marchés", "Les cinq équipes, en direct."],
    reports: ["Rapports", "L’archive des décisions."],
    backtest: ["Backtest", "Grille de tickers et de dates, scorée comme le CLI."],
    settings: ["Réglages", "Clés et modèles, dans le .env du projet."],
  };
  $("#kicker").textContent = titles[view][0];
  $("#headline").textContent = titles[view][1];
  if (view === "reports") loadArchive();
  if (view === "desk") refreshDesk();
}

function md(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h3>$1</h3>")
    .replace(/^# (.*)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/^(?:- |\* )(.*)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`)
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/\n/g, "<br>");
}

function pill(rating) {
  if (!rating) return `<span class="pill">—</span>`;
  const tone = { Buy: "up", Overweight: "up", Hold: "level", Underweight: "down", Sell: "down", REVIEW: "level" }[rating] || "level";
  return `<span class="pill ${tone}">${rating}</span>`;
}

function fillSelect(el, items, valueKey = "id", labelKey = "label") {
  el.innerHTML = items.map((item) => {
    if (typeof item === "string") return `<option value="${item}">${item}</option>`;
    return `<option value="${item[valueKey]}">${item[labelKey]}</option>`;
  }).join("");
}

function providerOf(id) {
  return state.meta.providers.find((p) => p.id === id);
}

function syncModels() {
  const form = $("#analyze-form");
  const provider = providerOf(form.llm_provider.value);
  if (!provider) return;
  const map = (mode) => provider.models[mode].map((m) => ({ id: m.value, label: m.label }));
  fillSelect(form.quick_think_llm, map("quick"));
  fillSelect(form.deep_think_llm, map("deep"));
  const pulled = state.meta.ollama_models || [];
  if (provider.id === "ollama" && pulled.length) {
    form.quick_think_llm.value = pulled[0];
    form.deep_think_llm.value = pulled[Math.min(1, pulled.length - 1)] || pulled[0];
  }
  toggleCustom();
}

function toggleCustom() {
  const form = $("#analyze-form");
  const custom = form.quick_think_llm.value === "custom" || form.deep_think_llm.value === "custom";
  form.querySelector(".custom-models").classList.toggle("hidden", !custom);
}

function populateForm() {
  const m = state.meta;
  const form = $("#analyze-form");
  form.date.value = m.today;
  fillSelect(form.output_language, m.languages);
  fillSelect(form.research_depth, m.depths);
  fillSelect(form.llm_provider, m.providers, "id", "label");
  form.output_language.value = m.defaults.output_language;
  form.llm_provider.value = m.defaults.llm_provider;
  $("#analyst-picks").innerHTML = m.analysts.map((a) => `
    <label><input type="checkbox" name="analysts" value="${a.id}" checked /> ${a.label}</label>
  `).join("");
  syncModels();
  const bt = $("#backtest-form");
  bt.end.value = m.today;
  const start = new Date(m.today);
  start.setDate(start.getDate() - 28);
  bt.start.value = start.toISOString().slice(0, 10);
}

async function refreshDesk() {
  const data = await fetch("/api/runs").then((r) => r.json());
  const live = data.live || [];
  const saved = data.saved || [];
  $("#live-list").innerHTML = live.length
    ? live.map((job) => `
        <div class="item" data-job="${job.id}">
          <span class="sym">${(job.request.ticker || job.request.tickers || job.kind).toString().toUpperCase()}</span>
          <span class="meta">${job.kind} · ${job.status} · ${job.created_at}</span>
          ${pill(job.result?.rating)}
        </div>`).join("")
    : `<p class="muted">Aucune run live.</p>`;
  $("#saved-list").innerHTML = saved.length
    ? saved.map((row) => `
        <div class="item" data-saved="${row.id}">
          <span class="sym">${row.ticker}</span>
          <span class="meta">${row.date} · ${row.updated_at || ""}</span>
          ${pill(row.rating)}
        </div>`).join("")
    : `<p class="muted">Pas encore de décisions enregistrées. Lancez une analyse.</p>`;
  $$("#live-list .item").forEach((el) => el.onclick = () => openJob(el.dataset.job));
  $$("#saved-list .item").forEach((el) => el.onclick = () => openSaved(el.dataset.saved));
}

async function loadQuote(ticker) {
  $("#quote-box").innerHTML = `<p class="muted">Chargement ${ticker}…</p>`;
  try {
    const q = await fetch(`/api/quote/${encodeURIComponent(ticker)}`).then(async (r) => {
      if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
      return r.json();
    });
    const chg = q.change == null ? "" : `${q.change >= 0 ? "+" : ""}${(q.change * 100).toFixed(2)}%`;
    const dir = q.change > 0 ? "up" : q.change < 0 ? "down" : "";
    $("#quote-box").innerHTML = `
      <div class="px">${q.last != null ? Number(q.last).toFixed(2) : "—"} <small>${q.currency || ""}</small></div>
      <div class="chg ${dir}">${q.ticker} · ${q.exchange || q.asset_type} · ${chg}</div>
    `;
  } catch (err) {
    $("#quote-box").innerHTML = `<p class="muted">${err.message}</p>`;
  }
}

function renderFirm(status = {}) {
  $("#firm").innerHTML = TEAMS.flatMap(([team, agents]) =>
    agents.map((name) => {
      const st = status[name] || "pending";
      return `<div class="agent ${st}"><div class="role">${team}</div><div class="name">${name}</div></div>`;
    })
  ).join("");
}

function renderReports() {
  const tabs = $("#report-tabs");
  const available = SECTIONS.filter(([key]) => state.reports[key]);
  if (!available.length) {
    tabs.innerHTML = "";
    $("#report-body").innerHTML = "<p class='muted'>Les notes arriveront au fil des agents.</p>";
    return;
  }
  if (!state.activeSection || !state.reports[state.activeSection]) {
    state.activeSection = available[available.length - 1][0];
  }
  tabs.innerHTML = available.map(([key, label]) =>
    `<button data-section="${key}" class="${key === state.activeSection ? "active" : ""}">${label}</button>`
  ).join("");
  $("#report-body").innerHTML = `<p>${md(state.reports[state.activeSection])}</p>`;
  $$("#report-tabs button").forEach((btn) => {
    btn.onclick = () => { state.activeSection = btn.dataset.section; renderReports(); };
  });
}

function appendLog(event) {
  const log = $("#message-log");
  if (event.type === "message") {
    const line = document.createElement("div");
    line.className = event.message_type || "";
    const text = (event.content || "").replace(/\s+/g, " ").slice(0, 500);
    line.textContent = `${event.timestamp || event.ts}  [${event.message_type}]  ${text}`;
    log.appendChild(line);
  } else if (event.type === "tool") {
    const line = document.createElement("div");
    line.className = "Tool";
    line.textContent = `${event.timestamp || event.ts}  [Tool]  ${event.name}`;
    log.appendChild(line);
  }
  log.scrollTop = log.scrollHeight;
}

function applySnapshot(event) {
  if (event.agent_status) renderFirm(event.agent_status);
  if (event.reports) {
    state.reports = { ...state.reports, ...event.reports };
    renderReports();
  }
  if (event.section && event.content) {
    state.reports[event.section] = event.content;
    state.activeSection = event.section;
    renderReports();
  }
  if (event.stats) {
    const s = event.stats;
    $("#war-stats").innerHTML = `
      <span>LLM ${s.llm_calls || 0}</span>
      <span>Outils ${s.tool_calls || 0}</span>
      <span>Tokens ${(s.tokens_in || 0) + (s.tokens_out || 0)}</span>
      <span>${event.elapsed_s != null ? event.elapsed_s + "s" : ""}</span>
    `;
  }
  if (event.rating) {
    $("#decision-strip").hidden = false;
    $("#decision-rating").textContent = event.rating;
    $("#decision-excerpt").textContent = (event.decision || "").replace(/\s+/g, " ").slice(0, 280);
  }
}

function connectJob(jobId) {
  if (state.ws) state.ws.close();
  state.jobId = jobId;
  state.reports = {};
  $("#message-log").textContent = "";
  $("#decision-strip").hidden = true;
  renderFirm();
  $("#war-kicker").textContent = `Run ${jobId}`;
  $("#live-chip").textContent = `Live · ${jobId}`;
  $("#live-chip").classList.add("live");
  show("warroom");
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/api/ws/runs/${jobId}`);
  state.ws = ws;
  ws.onmessage = (msg) => {
    const event = JSON.parse(msg.data);
    if (event.type === "ping") return;
    if (event.type === "run_started") {
      $("#war-title").textContent = `${event.ticker || ""}  ${event.date || ""}`;
    }
    appendLog(event);
    applySnapshot(event);
    if (event.type === "run_completed") {
      $("#live-chip").textContent = `Terminé · ${event.rating || jobId}`;
      $("#live-chip").classList.remove("live");
      applySnapshot(event);
    }
    if (event.type === "run_error") {
      $("#live-chip").textContent = "Erreur";
      $("#live-chip").classList.remove("live");
      appendLog({ type: "message", message_type: "System", content: event.error, ts: event.ts });
    }
  };
}

function openJob(jobId) {
  connectJob(jobId);
}

async function openSaved(id) {
  show("reports");
  const run = await fetch(`/api/runs/${encodeURIComponent(id)}`).then((r) => r.json());
  const result = run.result || run.snapshot || {};
  $("#report-open-title").textContent = `${result.ticker || ""} ${result.date || ""}`;
  if (result.html) {
    $("#report-frame").hidden = false;
    $("#report-fallback").hidden = true;
    $("#report-frame").src = `/api/reports/file?path=${encodeURIComponent(result.html)}`;
  } else {
    $("#report-frame").hidden = true;
    $("#report-fallback").hidden = false;
    const body = Object.entries(result.reports || {})
      .filter(([, v]) => typeof v === "string" && v.trim())
      .map(([k, v]) => `<h3>${k}</h3><p>${md(v)}</p>`)
      .join("");
    $("#report-fallback").innerHTML = body || "<p class='muted'>Pas de contenu.</p>";
  }
}

async function loadArchive() {
  const data = await fetch("/api/runs").then((r) => r.json());
  const rows = [...(data.live || []), ...(data.saved || [])];
  $("#report-list").innerHTML = rows.map((row) => {
    const id = row.id;
    const ticker = row.ticker || row.request?.ticker || row.kind;
    const date = row.date || row.created_at || "";
    return `<div class="item" data-saved="${id}">
      <span class="sym">${ticker}</span>
      <span class="meta">${date}</span>
      ${pill(row.rating || row.result?.rating)}
    </div>`;
  }).join("") || `<p class="muted">Aucun rapport.</p>`;
  $$("#report-list .item").forEach((el) => el.onclick = () => openSaved(el.dataset.saved));
}

async function startAnalysis(ev) {
  ev.preventDefault();
  const form = ev.target;
  const analysts = $$("#analyst-picks input:checked").map((el) => el.value);
  const provider = form.llm_provider.value;
  let quick = form.quick_think_llm.value;
  let deep = form.deep_think_llm.value;
  if (quick === "custom") quick = form.quick_custom.value.trim();
  if (deep === "custom") deep = form.deep_custom.value.trim();
  const payload = {
    ticker: form.ticker.value.trim(),
    date: form.date.value,
    analysts,
    research_depth: Number(form.research_depth.value),
    llm_provider: provider,
    quick_think_llm: quick,
    deep_think_llm: deep,
    output_language: form.output_language.value,
    checkpoint_enabled: form.checkpoint_enabled.checked,
  };
  const providerRow = providerOf(provider);
  if (providerRow?.backend_url) payload.backend_url = providerRow.backend_url;
  const cash = form.cash.value;
  const position = form.position.value.trim();
  if (cash || position) {
    payload.portfolio = { cash: cash ? Number(cash) : null, currency: form.currency.value || "USD", positions: [] };
    if (position) {
      const [ticker, qty, price] = position.split(",").map((s) => s.trim());
      payload.portfolio.positions.push({ ticker, quantity: Number(qty), average_price: price ? Number(price) : null });
    }
  }
  $("#analyze-status").textContent = "Démarrage du graphe…";
  const res = await fetch("/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const job = await res.json();
  if (!res.ok) {
    $("#analyze-status").textContent = job.detail || "Échec";
    return;
  }
  $("#analyze-status").textContent = "";
  connectJob(job.id);
}

async function startBacktest(ev) {
  ev.preventDefault();
  const form = ev.target;
  $("#backtest-out").textContent = "Sweep en cours…";
  const payload = {
    tickers: form.tickers.value,
    start: form.start.value,
    end: form.end.value,
    every: Number(form.every.value),
  };
  const analyze = $("#analyze-form");
  payload.llm_provider = analyze.llm_provider.value;
  payload.quick_think_llm = analyze.quick_think_llm.value;
  payload.deep_think_llm = analyze.deep_think_llm.value;
  const res = await fetch("/api/backtests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const job = await res.json();
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/api/ws/runs/${job.id}`);
  ws.onmessage = (msg) => {
    const event = JSON.parse(msg.data);
    if (event.type === "progress") {
      $("#backtest-out").textContent = `[${event.done}/${event.total}] ${event.ticker} ${event.date}`;
    }
    if (event.type === "run_completed") {
      $("#backtest-out").textContent = event.summary?.text || JSON.stringify(event, null, 2);
    }
    if (event.type === "run_error") {
      $("#backtest-out").textContent = event.error;
    }
  };
}

async function loadSettings() {
  const data = await fetch("/api/settings").then((r) => r.json());
  const form = $("#settings-form");
  Object.entries(data.trading).forEach(([name, value]) => {
    if (form[name]) form[name].value = value;
  });
  $("#key-fields").innerHTML = Object.entries(data.keys).map(([env, info]) => `
    <label>${env}
      <input name="${env}" placeholder="${info.present ? info.hint : "non définie"}" />
    </label>
  `).join("");
}

async function saveSettings(ev) {
  ev.preventDefault();
  const values = {};
  new FormData(ev.target).forEach((value, key) => {
    if (String(value).trim()) values[key] = String(value).trim();
  });
  const res = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ values }),
  });
  const data = await res.json();
  $("#settings-status").textContent = `Enregistré (${data.saved.length} champs)`;
}

function bind() {
  $$(".rail nav button").forEach((btn) => btn.onclick = () => show(btn.dataset.view));
  $$("[data-go]").forEach((btn) => btn.onclick = () => show(btn.dataset.go));
  $("#quote-form").onsubmit = (ev) => { ev.preventDefault(); loadQuote($("#quote-ticker").value); };
  $("#analyze-form").onsubmit = startAnalysis;
  $("#analyze-form").llm_provider.onchange = syncModels;
  $("#analyze-form").quick_think_llm.onchange = toggleCustom;
  $("#analyze-form").deep_think_llm.onchange = toggleCustom;
  $("#backtest-form").onsubmit = startBacktest;
  $("#settings-form").onsubmit = saveSettings;
}

async function boot() {
  clock();
  setInterval(clock, 1000);
  bind();
  renderFirm();
  state.meta = await fetch("/api/meta").then((r) => r.json());
  populateForm();
  await loadSettings();
  await refreshDesk();
  loadQuote("SPY");
}

boot();
