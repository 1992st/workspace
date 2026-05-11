const state = {
  model: null,
  quality: null,
  files: [],
  rootHandle: null,
  fallbackFiles: [],
  currentFile: null,
  selectedFlowId: null,
  dirtyFiles: new Map(),
  support: typeof window.showDirectoryPicker === "function" && window.isSecureContext,
};

const elements = {
  title: document.getElementById("skill-title"),
  subtitle: document.getElementById("skill-subtitle"),
  modeStatus: document.getElementById("mode-status"),
  supportStatus: document.getElementById("support-status"),
  editStatus: document.getElementById("edit-status"),
  overviewResponsibility: document.getElementById("overview-responsibility"),
  overviewUse: document.getElementById("overview-use"),
  overviewBoundaries: document.getElementById("overview-boundaries"),
  overviewOutputs: document.getElementById("overview-outputs"),
  pickBtn: document.getElementById("pick-directory-btn"),
  pickFilesBtn: document.getElementById("pick-files-btn"),
  fileInput: document.getElementById("file-picker-input"),
  reloadBtn: document.getElementById("reload-btn"),
  flowNav: document.getElementById("flow-nav"),
  flowCanvas: document.getElementById("flow-canvas"),
  qualityList: document.getElementById("quality-list"),
  detailTitle: document.getElementById("detail-title"),
  flowDetail: document.getElementById("flow-detail"),
  fileMeta: document.getElementById("file-meta"),
  editor: document.getElementById("editor"),
  preview: document.getElementById("preview"),
  resetBtn: document.getElementById("reset-btn"),
  saveBtn: document.getElementById("save-btn"),
  flowButtonTemplate: document.getElementById("flow-button-template"),
  stepTemplate: document.getElementById("step-template"),
  assetTemplate: document.getElementById("asset-template"),
};

boot();

async function boot() {
  elements.supportStatus.textContent = state.support ? "可启用本地编辑" : "仅浏览";
  bindEvents();
  await loadStaticData();
  renderAll();
}

function bindEvents() {
  elements.pickBtn.addEventListener("click", pickDirectory);
  elements.pickFilesBtn.addEventListener("click", () => elements.fileInput.click());
  elements.fileInput.addEventListener("change", pickFiles);
  elements.reloadBtn.addEventListener("click", reloadFiles);
  elements.editor.addEventListener("input", onEditorInput);
  elements.resetBtn.addEventListener("click", resetCurrentFile);
  elements.saveBtn.addEventListener("click", saveCurrentFile);
}

async function loadStaticData() {
  const model = readEmbeddedJson("skill-model-data") || await fetchJson("skill-model.json");
  const quality = readEmbeddedJson("quality-report-data") || await fetchJson("quality-report.json");
  state.model = model;
  state.quality = quality;
  state.files = model.files.map((file) => ({ ...file, content: file.content ?? null, handle: null, file: null }));
  state.selectedFlowId = model.flows[0]?.id || null;
  state.currentFile = state.files.find((file) => file.path === "SKILL.md") || state.files[0] || null;
}

function readEmbeddedJson(id) {
  const node = document.getElementById(id);
  if (!node?.textContent?.trim()) return null;
  return JSON.parse(node.textContent);
}

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Failed to load ${path}`);
  return response.json();
}

async function pickDirectory() {
  if (!state.support) {
    alert("当前浏览器不支持目录写回，请使用 Chrome 或 Edge。页面浏览不受影响。");
    return;
  }
  const dir = await window.showDirectoryPicker();
  state.rootHandle = dir;
  state.fallbackFiles = [];
  await attachHandlesFromDirectory(dir);
  elements.reloadBtn.disabled = false;
  renderAll();
}

async function pickFiles(event) {
  state.fallbackFiles = Array.from(event.target.files || []);
  state.rootHandle = null;
  attachFallbackFiles();
  elements.reloadBtn.disabled = false;
  renderAll();
}

async function reloadFiles() {
  if (state.rootHandle) {
    await attachHandlesFromDirectory(state.rootHandle);
  } else if (state.fallbackFiles.length) {
    attachFallbackFiles();
  }
  renderAll();
}

async function attachHandlesFromDirectory(dirHandle) {
  const handles = new Map();
  await walkDirectory(dirHandle, "", handles);
  state.files = state.model.files.map((file) => ({
    ...file,
    content: file.content ?? null,
    handle: handles.get(file.path) || null,
    file: null,
  }));
  refreshCurrentFile();
}

async function walkDirectory(dirHandle, currentPath, handles) {
  for await (const [name, handle] of dirHandle.entries()) {
    const nextPath = currentPath ? `${currentPath}/${name}` : name;
    if (handle.kind === "directory") {
      await walkDirectory(handle, nextPath, handles);
    } else {
      handles.set(nextPath, handle);
    }
  }
}

function attachFallbackFiles() {
  const files = new Map();
  for (const file of state.fallbackFiles) {
    const rel = normalizeFallbackPath(file.webkitRelativePath || file.name);
    files.set(rel, file);
  }
  state.files = state.model.files.map((item) => ({
    ...item,
    content: item.content ?? null,
    handle: null,
    file: files.get(item.path) || null,
  }));
  refreshCurrentFile();
}

function refreshCurrentFile() {
  const currentPath = state.currentFile?.path || "SKILL.md";
  state.currentFile = state.files.find((file) => file.path === currentPath) || state.files[0] || null;
}

function normalizeFallbackPath(path) {
  const parts = path.split("/");
  const skillName = state.model.skill.path.split("/").pop();
  const index = parts.indexOf(skillName);
  return index >= 0 ? parts.slice(index + 1).join("/") : path;
}

function renderAll() {
  elements.title.textContent = state.model.skill.name;
  elements.subtitle.textContent = state.model.skill.description || "No description";
  elements.modeStatus.textContent = state.model.skill.mode;
  renderOverview();
  renderFlows();
  renderQuality();
  updateEditStatus();
  if (state.currentFile) renderFile(state.currentFile);
}

function renderOverview() {
  const summary = state.model.summary || {};
  elements.overviewResponsibility.textContent = summary.responsibility || state.model.skill.description || "No responsibility summary provided.";
  renderList(elements.overviewUse, summary.when_to_use || []);
  renderList(elements.overviewBoundaries, [...(summary.when_not_to_use || []), ...(summary.boundaries || [])]);
  renderList(elements.overviewOutputs, summary.core_outputs || []);
}

function renderList(container, items) {
  container.innerHTML = "";
  if (!items.length) {
    const li = document.createElement("li");
    li.textContent = "未声明";
    container.appendChild(li);
    return;
  }
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    container.appendChild(li);
  }
}

function renderFlows() {
  elements.flowNav.innerHTML = "";
  for (const flow of state.model.flows) {
    const btn = elements.flowButtonTemplate.content.firstElementChild.cloneNode(true);
    const tuningCount = (flow.tuning_points || []).length;
    btn.textContent = tuningCount ? `${flow.title} · ${tuningCount} tuning` : flow.title;
    if (flow.id === state.selectedFlowId) btn.classList.add("is-active");
    btn.addEventListener("click", () => {
      state.selectedFlowId = flow.id;
      renderFlows();
    });
    elements.flowNav.appendChild(btn);
  }
  renderSelectedFlow();
}

function renderSelectedFlow() {
  const flow = state.model.flows.find((item) => item.id === state.selectedFlowId);
  if (!flow) return;
  elements.flowCanvas.innerHTML = "";

  const hero = document.createElement("section");
  hero.className = "flow-hero";
  hero.innerHTML = `
    <h2>${escapeHtml(flow.title)}</h2>
    <p>${escapeHtml(flow.description || "")}</p>
    ${renderInfoBlock("Intent", flow.intent)}
    ${renderInfoBlock("Trigger", flow.trigger)}
    ${renderBullets("Inputs", flow.inputs)}
    ${renderBullets("Outputs", flow.outputs)}
    ${renderBullets("Decision Points", flow.decision_points)}
    ${renderBullets("Blockers", flow.blockers)}
  `;
  elements.flowCanvas.appendChild(hero);

  const track = document.createElement("div");
  track.className = "step-track";
  flow.steps.forEach((step, index) => {
    const node = elements.stepTemplate.content.firstElementChild.cloneNode(true);
    node.classList.add(`kind-${step.kind || "read"}`);
    node.querySelector(".step-index").textContent = String(index + 1).padStart(2, "0");
    node.querySelector(".step-title").textContent = step.kind ? `${step.title} · ${step.kind}` : step.title;
    node.querySelector(".step-description").textContent = step.description || "";
    node.querySelector(".step-lists").innerHTML = renderStepMeta(step);
    const assets = node.querySelector(".step-assets");
    const linkedFiles = unique([...(step.evidence || []), ...(step.files || [])]);
    for (const path of linkedFiles) {
      const file = state.files.find((item) => item.path === path);
      if (!file) continue;
      const chip = elements.assetTemplate.content.firstElementChild.cloneNode(true);
      chip.classList.add(`kind-${file.type}`);
      chip.querySelector(".asset-kind").textContent = file.type;
      chip.querySelector(".asset-name").textContent = path.split("/").pop();
      chip.querySelector(".asset-path").textContent = path;
      chip.addEventListener("click", () => openFile(path));
      assets.appendChild(chip);
    }
    node.addEventListener("click", (event) => {
      if (event.target.closest(".asset-chip")) return;
      renderFlowDetail(flow, step);
    });
    track.appendChild(node);
  });
  elements.flowCanvas.appendChild(track);
  renderFlowDetail(flow, flow.steps[0] || null);
}

function renderInfoBlock(label, value) {
  if (!value) return "";
  return `<div class="info-block"><strong>${escapeHtml(label)}</strong><p>${escapeHtml(value)}</p></div>`;
}

function renderBullets(label, items) {
  if (!items?.length) return "";
  return `<div class="info-block"><strong>${escapeHtml(label)}</strong><ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>`;
}

function renderStepMeta(step) {
  const parts = [];
  if (step.evidence?.length) parts.push(renderBullets("Evidence", step.evidence));
  return parts.join("");
}

function renderFlowDetail(flow, step) {
  elements.detailTitle.textContent = step ? step.title : flow.title;
  elements.flowDetail.innerHTML = `
    <div class="detail-card">
      <strong>Flow</strong>
      <p>${escapeHtml(flow.title)}</p>
    </div>
    ${renderInfoBlock("Intent", flow.intent)}
    ${renderBullets("Tuning Points", (flow.tuning_points || []).map((item) => item.title))}
    ${renderBullets("Blockers", flow.blockers || [])}
    ${step ? renderInfoBlock("Selected Step", `${step.kind || "read"} · ${step.description || ""}`) : ""}
  `;
  const firstFile = unique([...(step?.evidence || []), ...(step?.files || []), ...flattenTuningFiles(flow)])[0];
  if (firstFile) openFile(firstFile, { preserveDetailTitle: true });
}

function renderQuality() {
  elements.qualityList.innerHTML = "";
  const findings = state.quality?.findings || [];
  if (!findings.length) {
    const item = document.createElement("div");
    item.className = "quality-item";
    item.textContent = "No findings";
    elements.qualityList.appendChild(item);
    return;
  }
  for (const finding of findings.slice(0, 12)) {
    const item = document.createElement("div");
    item.className = `quality-item ${finding.severity}`;
    item.textContent = `${finding.severity}: ${finding.message}${finding.path ? ` (${finding.path})` : ""}`;
    elements.qualityList.appendChild(item);
  }
}

async function openFile(path, options = {}) {
  const file = state.files.find((item) => item.path === path);
  if (!file) return;
  if (file.content === null) file.content = await readFile(file);
  state.currentFile = file;
  renderFile(file, options);
}

function flattenTuningFiles(flow) {
  return (flow.tuning_points || []).flatMap((item) => item.files || []);
}

function unique(items) {
  return [...new Set(items.filter(Boolean))];
}

async function readFile(file) {
  if (file.handle) return (await file.handle.getFile()).text();
  if (file.file) return file.file.text();
  return "";
}

function renderFile(file, options = {}) {
  if (!options.preserveDetailTitle) elements.detailTitle.textContent = "File";
  const canEdit = file.editable && Boolean(file.handle);
  const canRead = Boolean(file.handle || file.file || file.content !== null);
  elements.fileMeta.textContent = [
    `path: ${file.path}`,
    `type: ${file.type}`,
    `editable: ${canEdit ? "yes" : "no"}`,
    `content: ${canRead ? "available" : "not embedded"}`,
  ].join("\n");
  if (canEdit) {
    elements.preview.classList.add("is-hidden");
    elements.editor.classList.add("is-active");
    elements.editor.disabled = false;
    elements.editor.value = state.dirtyFiles.get(file.path) ?? file.content ?? "";
    elements.saveBtn.disabled = false;
    elements.resetBtn.disabled = false;
  } else {
    elements.preview.classList.remove("is-hidden");
    elements.editor.classList.remove("is-active");
    elements.editor.disabled = true;
    elements.preview.textContent = canRead
      ? (file.content || "")
      : "该文件内容未内嵌。若要查看最新本地内容，请点击“启用本地编辑”并选择对应 skill 目录。";
    elements.saveBtn.disabled = true;
    elements.resetBtn.disabled = true;
  }
}

function onEditorInput() {
  if (!state.currentFile) return;
  state.dirtyFiles.set(state.currentFile.path, elements.editor.value);
  updateEditStatus();
}

function resetCurrentFile() {
  if (!state.currentFile) return;
  state.dirtyFiles.delete(state.currentFile.path);
  renderFile(state.currentFile);
  updateEditStatus();
}

async function saveCurrentFile() {
  if (!state.currentFile?.handle) return;
  const content = state.dirtyFiles.get(state.currentFile.path);
  if (content === undefined) return;
  const writable = await state.currentFile.handle.createWritable();
  await writable.write(content);
  await writable.close();
  state.currentFile.content = content;
  state.dirtyFiles.delete(state.currentFile.path);
  renderFile(state.currentFile);
  updateEditStatus();
}

function updateEditStatus() {
  elements.editStatus.textContent = state.dirtyFiles.size
    ? `${state.dirtyFiles.size} file(s) dirty`
    : "无未保存修改";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
