"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const state = { csrf: "", user: null, model: null, authMode: "login", projects: [], output: "", installPrompt: null };

async function api(path, options = {}) {
  const headers = { ...(options.body ? { "Content-Type": "application/json" } : {}), ...(options.headers || {}) };
  if (!["GET", "HEAD"].includes((options.method || "GET").toUpperCase()) && state.csrf) headers["X-CSRF-Token"] = state.csrf;
  const response = await fetch(path, { credentials: "same-origin", ...options, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status}).`);
  if (payload.csrf_token) state.csrf = payload.csrf_token;
  return payload;
}

function showToast(message, isError = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.remove("hidden");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.add("hidden"), 3200);
}

function setNotice(element, message, isError = false) {
  element.textContent = message;
  element.classList.remove("hidden", "error");
  if (isError) element.classList.add("error");
}

function renderSession() {
  const signedIn = Boolean(state.user);
  $("#auth-view").classList.toggle("hidden", signedIn);
  $("#workspace-view").classList.toggle("hidden", !signedIn);
  $("#account-area").classList.toggle("hidden", !signedIn);
  if (!signedIn) return;
  $("#account-name").textContent = state.user.username;
  $("#admin-nav").classList.toggle("hidden", state.user.role !== "admin");
  const badge = $("#model-badge");
  badge.classList.toggle("ready", Boolean(state.model?.configured));
  badge.classList.toggle("offline", !state.model?.configured);
  const indicator = document.createElement("i");
  badge.replaceChildren(indicator, document.createTextNode(state.model?.configured ? "Model ready" : "Local mode"));
  const toggle = $("#use-model");
  toggle.disabled = !state.model?.configured;
  $("#model-detail").textContent = state.model?.configured
    ? `${state.model.provider} · ${state.model.model}`
    : (state.model?.hint || "No model is configured; use local analysis.");
}

function selectView(view) {
  if (view === "admin" && state.user?.role !== "admin") view = "assistant";
  $$(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  $("#assistant-panel").classList.toggle("hidden", view !== "assistant");
  $("#projects-panel").classList.toggle("hidden", view !== "projects");
  $("#admin-panel").classList.toggle("hidden", view !== "admin");
  $(".workspace-nav").classList.remove("mobile-open");
  $("#mobile-nav-toggle").setAttribute("aria-expanded", "false");
  if (view === "projects") loadProjects();
  if (view === "admin") loadAdmin();
}

function setAuthMode(mode) {
  state.authMode = mode;
  $$(".auth-tab").forEach((button) => button.classList.toggle("active", button.dataset.authMode === mode));
  $("#auth-title").textContent = mode === "login" ? "Welcome back" : "Create your account";
  $("#auth-description").textContent = mode === "login" ? "Sign in to open your workspace." : "Create an account to save private projects and snippets.";
  $("#auth-submit").textContent = mode === "login" ? "Sign in" : "Create account";
  $("#auth-password").setAttribute("autocomplete", mode === "login" ? "current-password" : "new-password");
  $("#password-hint").classList.toggle("hidden", mode !== "register");
  $("#auth-message").classList.add("hidden");
}

$("#auth-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("#auth-submit");
  button.disabled = true;
  button.textContent = "Please wait…";
  try {
    const payload = Object.fromEntries(new FormData(event.currentTarget));
    const result = await api(state.authMode === "login" ? "/api/login" : "/api/register", { method: "POST", body: JSON.stringify(payload) });
    state.user = result.user;
    renderSession();
    selectView("assistant");
  } catch (error) {
    setNotice($("#auth-message"), error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = state.authMode === "login" ? "Sign in" : "Create account";
  }
});

$("#logout-button").addEventListener("click", async () => {
  try { await api("/api/logout", { method: "POST", body: "{}" }); } catch (_) { /* clear local view even if the connection ended */ }
  state.user = null;
  renderSession();
  setAuthMode("login");
});

$(".auth-tabs").addEventListener("click", (event) => {
  const tab = event.target.closest("[data-auth-mode]");
  if (tab) setAuthMode(tab.dataset.authMode);
});

$("#prompt-input").addEventListener("input", (event) => {
  $("#char-count").textContent = `${event.target.value.length.toLocaleString()} / 20,000`;
});

$(".prompt-examples").addEventListener("click", (event) => {
  const button = event.target.closest("[data-prompt]");
  if (!button) return;
  $("#prompt-input").value = button.dataset.prompt;
  $("#char-count").textContent = `${button.dataset.prompt.length.toLocaleString()} / 20,000`;
  $("#prompt-input").focus();
});

$$('[data-action]').forEach((button) => button.addEventListener("click", async () => {
  const text = $("#prompt-input").value;
  if (!text.trim()) { showToast("Enter a prompt or paste Python code first.", true); $("#prompt-input").focus(); return; }
  const status = $("#assist-status");
  status.textContent = "Working on your request…";
  status.classList.remove("hidden", "error");
  $$("[data-action]").forEach((item) => item.disabled = true);
  try {
    const result = await api("/api/assist", { method: "POST", body: JSON.stringify({
      action: button.dataset.action, text, level: $("#explanation-level").value, use_model: $("#use-model").checked,
    }) });
    state.output = result.output;
    $("#result-title").textContent = ({ generate: "Generated example", review: "Code review", fix: "Suggested changes", error_explain: "Error explanation", program_explain: "Code explanation" })[button.dataset.action];
    $("#result-output").textContent = result.output;
    $("#result-mode").textContent = result.mode === "local" ? "Local rules" : `${result.provider} · ${result.model}`;
    $("#result-mode").classList.remove("hidden");
    $("#empty-result").classList.add("hidden");
    $("#result-content").classList.remove("hidden");
    const syntaxNote = $("#syntax-note");
    syntaxNote.classList.add("hidden");
    syntaxNote.classList.remove("bad");
    if (result.syntax_valid !== null && result.syntax_valid !== undefined) {
      syntaxNote.textContent = result.syntax_valid ? "Python parser accepted the generated syntax. This does not check behavior." : "Python parser found a syntax issue in this generated code. Review it before use.";
      syntaxNote.classList.remove("hidden");
      syntaxNote.classList.toggle("bad", !result.syntax_valid);
    }
    status.textContent = "Done. Review the result before using it.";
    if (result.usage?.input_tokens) status.textContent += ` Approx. ${result.usage.input_tokens} input tokens.`;
  } catch (error) {
    status.textContent = error.message;
    status.classList.add("error");
  } finally {
    $$("[data-action]").forEach((item) => item.disabled = false);
  }
}));

$("#copy-result").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(state.output); showToast("Copied to clipboard."); }
  catch (_) { showToast("Clipboard access was unavailable.", true); }
});

$("#download-result").addEventListener("click", () => {
  const blob = new Blob([state.output], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "pyguide-result.txt";
  link.click();
  URL.revokeObjectURL(link.href);
});

$("#save-result").addEventListener("click", async () => {
  if (!state.output) return;
  try {
    if (!state.projects.length) await loadProjects();
    const select = $("#snippet-project");
    select.replaceChildren();
    state.projects.forEach((project) => { const option = document.createElement("option"); option.value = project.id; option.textContent = project.name; select.append(option); });
    $("#save-message").classList.add("hidden");
    if (!state.projects.length) { showToast("Create a project first in My projects.", true); selectView("projects"); return; }
    $("#snippet-title").value = "";
    $("#save-dialog").showModal();
  } catch (error) { showToast(error.message, true); }
});

$("#close-save-dialog").addEventListener("click", () => $("#save-dialog").close());
$("#save-snippet-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const projectId = $("#snippet-project").value;
    await api(`/api/projects/${projectId}/snippets`, { method: "POST", body: JSON.stringify({ title: $("#snippet-title").value, code: state.output }) });
    $("#save-dialog").close();
    showToast("Snippet saved to your project.");
    loadProjects();
  } catch (error) { setNotice($("#save-message"), error.message, true); }
});

$(".workspace-nav").addEventListener("click", (event) => {
  const button = event.target.closest("[data-view]");
  if (button) selectView(button.dataset.view);
});
$("#mobile-nav-toggle").addEventListener("click", () => {
  const nav = $(".workspace-nav");
  const opened = nav.classList.toggle("mobile-open");
  $("#mobile-nav-toggle").setAttribute("aria-expanded", String(opened));
});

$("#project-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = $("#project-name");
  try {
    await api("/api/projects", { method: "POST", body: JSON.stringify({ name: input.value }) });
    input.value = "";
    showToast("Project created.");
    loadProjects();
  } catch (error) { showToast(error.message, true); }
});

async function loadProjects() {
  const list = $("#project-list");
  list.replaceChildren();
  try {
    const result = await api("/api/projects");
    state.projects = result.projects;
    if (!state.projects.length) { const empty = document.createElement("p"); empty.className = "empty-projects"; empty.textContent = "No projects yet. Create one above, then save snippets from the Assistant."; list.append(empty); return; }
    state.projects.forEach((project) => {
      const article = document.createElement("article"); article.className = "project-item";
      const header = document.createElement("div"); header.className = "project-item-header";
      const info = document.createElement("div");
      const title = document.createElement("h3"); title.textContent = project.name;
      const count = document.createElement("p"); count.className = "muted"; count.textContent = `${project.snippet_count} saved ${project.snippet_count === 1 ? "snippet" : "snippets"}`;
      info.append(title, count);
      const controls = document.createElement("div"); controls.className = "project-controls";
      const open = document.createElement("button"); open.type = "button"; open.className = "button button-quiet"; open.textContent = "View snippets";
      open.addEventListener("click", () => loadSnippets(project.id, article));
      const remove = document.createElement("button"); remove.type = "button"; remove.className = "button button-danger"; remove.textContent = "Delete";
      remove.addEventListener("click", async () => { if (!window.confirm(`Delete “${project.name}” and its saved snippets?`)) return; try { await api(`/api/projects/${project.id}`, { method: "DELETE" }); loadProjects(); } catch (error) { showToast(error.message, true); } });
      controls.append(open, remove); header.append(info, controls);
      const snippets = document.createElement("div"); snippets.className = "snippet-list";
      article.append(header, snippets); list.append(article);
    });
  } catch (error) { const message = document.createElement("p"); message.className = "notice error"; message.textContent = error.message; list.append(message); }
}

async function loadSnippets(projectId, container) {
  const list = $(".snippet-list", container); list.replaceChildren();
  try {
    const result = await api(`/api/projects/${projectId}/snippets`);
    if (!result.snippets.length) { const p = document.createElement("p"); p.className = "muted"; p.textContent = "No snippets saved yet."; list.append(p); return; }
    result.snippets.forEach((snippet) => {
      const item = document.createElement("details"); item.className = "snippet-item";
      const summary = document.createElement("summary"); summary.textContent = `${snippet.title} · saved ${snippet.created_at}`;
      const code = document.createElement("pre"); code.textContent = snippet.code;
      const remove = document.createElement("button"); remove.type = "button"; remove.className = "button button-danger"; remove.textContent = "Delete snippet";
      remove.addEventListener("click", async () => { try { await api(`/api/snippets/${snippet.id}`, { method: "DELETE" }); loadSnippets(projectId, container); loadProjects(); } catch (error) { showToast(error.message, true); } });
      item.append(summary, code, remove); list.append(item);
    });
  } catch (error) { showToast(error.message, true); }
}

function makeMetric(label, value, note) {
  const card = document.createElement("article"); card.className = "metric-card";
  const name = document.createElement("span"); name.className = "muted"; name.textContent = label;
  const number = document.createElement("strong"); number.textContent = Number(value || 0).toLocaleString();
  const detail = document.createElement("small"); detail.textContent = note;
  card.append(name, number, detail); return card;
}

async function loadAdmin() {
  const metrics = $("#admin-metrics"); const usersBox = $("#admin-users");
  metrics.replaceChildren(); usersBox.textContent = "Loading…";
  try {
    const data = await api("/api/admin/summary");
    metrics.append(makeMetric("Accounts", data.totals.users, "Registered users"), makeMetric("Projects", data.totals.projects, "User workspaces"), makeMetric("Saved snippets", data.totals.snippets, "Private user content"), makeMetric("Requests", data.totals.requests_7d, "Last 7 days"));
    renderAdminActivity(data.modes_7d, data.actions_7d);
    renderAdminUsers(data.users);
    await loadExamples();
  } catch (error) { usersBox.textContent = error.message; }
}

function renderAdminActivity(modes, actions) {
  const box = $("#admin-activity"); box.replaceChildren();
  const table = document.createElement("table");
  const head = document.createElement("thead"); head.innerHTML = "<tr><th>Type</th><th>Requests</th><th>Successful</th></tr>";
  const body = document.createElement("tbody");
  [...modes.map((item) => ({ name: item.mode, ...item })), ...actions.map((item) => ({ name: item.action, ...item }))].forEach((item) => {
    const row = document.createElement("tr");
    [item.name, item.requests, item.successes].forEach((value) => { const cell = document.createElement("td"); cell.textContent = String(value ?? 0); row.append(cell); });
    body.append(row);
  });
  if (!body.children.length) { const row = document.createElement("tr"); const cell = document.createElement("td"); cell.colSpan = 3; cell.textContent = "No requests in the last 7 days."; row.append(cell); body.append(row); }
  table.append(head, body); box.append(table);
}

function renderAdminUsers(users) {
  const box = $("#admin-users"); box.replaceChildren();
  const table = document.createElement("table");
  const head = document.createElement("thead"); head.innerHTML = "<tr><th>Username</th><th>Joined</th><th>Role</th></tr>";
  const body = document.createElement("tbody");
  users.forEach((user) => {
    const row = document.createElement("tr");
    const name = document.createElement("td"); name.textContent = user.username;
    const joined = document.createElement("td"); joined.textContent = user.created_at;
    const roleCell = document.createElement("td"); const select = document.createElement("select"); select.setAttribute("aria-label", `Role for ${user.username}`);
    ["user", "admin"].forEach((role) => { const option = document.createElement("option"); option.value = role; option.textContent = role; option.selected = role === user.role; select.append(option); });
    select.addEventListener("change", async () => { try { await api(`/api/admin/users/${user.id}/role`, { method: "PATCH", body: JSON.stringify({ role: select.value }) }); showToast("User role updated."); } catch (error) { showToast(error.message, true); select.value = user.role; } });
    roleCell.append(select); row.append(name, joined, roleCell); body.append(row);
  });
  table.append(head, body); box.append(table);
}

async function loadExamples() {
  const box = $("#example-list"); box.replaceChildren();
  try {
    const data = await api("/api/admin/examples");
    data.examples.forEach((example) => {
      const row = document.createElement("div"); row.className = "example-row";
      const text = document.createElement("div"); const title = document.createElement("strong"); title.textContent = example.title;
      const meta = document.createElement("small"); meta.textContent = `${example.keywords.join(", ")} · ${example.enabled ? "enabled" : "disabled"}`; text.append(title, meta);
      const actions = document.createElement("div"); actions.className = "project-controls";
      const edit = document.createElement("button"); edit.type = "button"; edit.className = "button button-quiet"; edit.textContent = "Edit"; edit.addEventListener("click", () => fillExampleForm(example));
      const toggle = document.createElement("button"); toggle.type = "button"; toggle.className = "button button-quiet"; toggle.textContent = example.enabled ? "Disable" : "Enable"; toggle.addEventListener("click", async () => { try { await api(`/api/admin/examples/${example.id}`, { method: "PUT", body: JSON.stringify({ ...example, enabled: !example.enabled }) }); loadExamples(); } catch (error) { showAdminError(error.message); } });
      const remove = document.createElement("button"); remove.type = "button"; remove.className = "button button-danger"; remove.textContent = "Delete"; remove.addEventListener("click", async () => { if (!window.confirm(`Delete “${example.title}”?`)) return; try { await api(`/api/admin/examples/${example.id}`, { method: "DELETE" }); loadExamples(); } catch (error) { showAdminError(error.message); } });
      actions.append(edit, toggle, remove); row.append(text, actions); box.append(row);
    });
  } catch (error) { showAdminError(error.message); }
}

function fillExampleForm(example) {
  $("#example-id").value = example.id;
  $("#example-title").value = example.title;
  $("#example-keywords").value = example.keywords.join(", ");
  $("#example-description").value = example.description;
  $("#example-code").value = example.code;
  $("#cancel-example-edit").classList.remove("hidden");
  $("#example-title").focus();
}

function resetExampleForm() {
  $("#example-form").reset(); $("#example-id").value = ""; $("#cancel-example-edit").classList.add("hidden");
}

function showAdminError(message) { setNotice($("#admin-status"), message, true); }

$("#cancel-example-edit").addEventListener("click", resetExampleForm);
$("#example-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = $("#example-id").value;
  const payload = { title: $("#example-title").value, keywords: $("#example-keywords").value, description: $("#example-description").value, code: $("#example-code").value, enabled: true };
  try {
    await api(id ? `/api/admin/examples/${id}` : "/api/admin/examples", { method: id ? "PUT" : "POST", body: JSON.stringify(payload) });
    resetExampleForm(); loadExamples(); showToast("Template saved.");
  } catch (error) { showAdminError(error.message); }
});

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault(); state.installPrompt = event; $("#install-button").classList.remove("hidden");
});
$("#install-button").addEventListener("click", async () => {
  if (!state.installPrompt) return;
  state.installPrompt.prompt();
  await state.installPrompt.userChoice;
  state.installPrompt = null;
  $("#install-button").classList.add("hidden");
});

async function start() {
  try {
    const session = await api("/api/session");
    state.csrf = session.csrf_token; state.user = session.user; state.model = session.model;
    renderSession();
  } catch (error) {
    renderSession();
    setNotice($("#auth-message"), `Could not connect to the app: ${error.message}`, true);
  }
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/static/service-worker.js").catch(() => {});
}

start();
