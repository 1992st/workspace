const state = {
  model: null,
  quality: null,
  files: [],
  fileTree: null,
  relatedFilePaths: new Set(),
  rootHandle: null,
  fallbackFiles: [],
  currentFile: null,
  selectedFlowId: null,
  selectedCapabilityId: null,
  dirtyFiles: new Map(),
  sectionMap: new Map(),
  support: typeof window.showDirectoryPicker === "function" && window.isSecureContext,
};

const elements = {
  title: document.getElementById("skill-title"),
  subtitle: document.getElementById("skill-subtitle"),
  modeStatus: document.getElementById("mode-status"),
  supportStatus: document.getElementById("support-status"),
  editStatus: document.getElementById("edit-status"),
  overview: document.getElementById("section-overview"),
  overviewHeading: document.getElementById("overview-heading"),
  overviewResponsibility: document.getElementById("overview-responsibility"),
  overviewUse: document.getElementById("overview-use"),
  overviewBoundaries: document.getElementById("overview-boundaries"),
  overviewOutputs: document.getElementById("overview-outputs"),
  triggerHeading: document.getElementById("trigger-heading"),
  triggerChips: document.getElementById("trigger-chips"),
  pickBtn: document.getElementById("pick-directory-btn"),
  pickFilesBtn: document.getElementById("pick-files-btn"),
  fileInput: document.getElementById("file-picker-input"),
  reloadBtn: document.getElementById("reload-btn"),
  capabilitySection: document.getElementById("section-capability-map"),
  capabilityHeading: document.getElementById("capability-heading"),
  capabilityNav: document.getElementById("capability-nav"),
  fileTreeSection: document.getElementById("section-file-tree"),
  fileTreeHeading: document.getElementById("file-tree-heading"),
  fileTree: document.getElementById("file-tree"),
  flowSection: document.getElementById("section-flow-timeline"),
  flowHeading: document.getElementById("flow-heading"),
  flowNav: document.getElementById("flow-nav"),
  nestedSection: document.getElementById("section-nested-skills"),
  nestedHeading: document.getElementById("nested-heading"),
  nestedList: document.getElementById("nested-list"),
  qualitySection: document.getElementById("section-quality-findings"),
  qualityHeading: document.getElementById("quality-heading"),
  qualityList: document.getElementById("quality-list"),
  issueSection: document.getElementById("section-issue-book"),
  issueHeading: document.getElementById("issue-heading"),
  issueFeedbackList: document.getElementById("issue-feedback-list"),
  capabilityCardsSection: document.getElementById("section-capability-cards"),
  capabilityCards: document.getElementById("capability-cards"),
  capabilitySummarySection: document.getElementById("section-capability-summary"),
  capabilitySummary: document.getElementById("capability-summary"),
  flowCanvasSection: document.getElementById("section-flow-canvas"),
  flowCanvas: document.getElementById("flow-canvas"),
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
  state.fileTree = buildFileTree(state.files);
  state.sectionMap = new Map((model.sections || []).map((section) => [section.type, section]));
  state.selectedCapabilityId = getCapabilities()[0]?.id || null;
  state.selectedFlowId = model.flows?.[0]?.id || null;
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
  applySectionLayout();
  renderOverview();
  renderCapabilities();
  renderFileTree();
  renderNestedSkills();
  renderFlows();
  renderQuality();
  renderIssueFeedback();
  updateEditStatus();
  if (state.currentFile) renderFile(state.currentFile);
}

function getCapabilities() {
  return state.model.capabilities || state.model.features || [];
}

function getCapabilityFindings(capability) {
  const findings = state.quality?.findings || [];
  const linkedPaths = new Set(collectFeatureFiles(capability));
  const linkedFlowIds = new Set(capability.flows || []);
  const riskyCodes = new Set([
    "declared-capability-without-workflow",
    "trigger-surface-exceeds-workflow-surface",
    "feature-flow-collision",
    "phase-like-capability",
  ]);

  return findings.filter((finding) => {
    if (!riskyCodes.has(finding.code)) return false;
    const path = finding.path || "";
    if (path === "viewer-flow-spec.json") return true;
    if (path === "SKILL.md" && (capability.trigger_groups || capability.triggers || []).length) return true;
    if (linkedPaths.has(path)) return true;
    return [...linkedFlowIds].some((flowId) => finding.message?.includes(flowId));
  });
}

function applySectionLayout() {
  const titles = new Map((state.model.sections || []).map((section) => [section.type, section.title || ""]));
  toggleSection(elements.overview, hasSection("overview") || hasSection("trigger-list"));
  toggleSection(elements.capabilitySection, hasSection("feature-map"));
  toggleSection(elements.flowSection, hasSection("flow-timeline"));
  // The file tree is intentionally shown after the flow section in the sidebar.
  // Users should first understand ability grouping and execution order, then
  // use the tree as evidence navigation and file lookup.
  toggleSection(elements.fileTreeSection, hasSection("file-tree"));
  toggleSection(elements.nestedSection, hasSection("nested-skills"));
  toggleSection(elements.qualitySection, hasSection("quality-findings"));
  toggleSection(elements.issueSection, hasSection("issue-book") || hasSection("feedback"));
  toggleSection(elements.capabilityCardsSection, hasSection("feature-map"));
  toggleSection(elements.capabilitySummarySection, hasSection("feature-map"));
  toggleSection(elements.flowCanvasSection, hasSection("flow-timeline"));

  setHeading(elements.overviewHeading, titles.get("overview"), "Agent Overview");
  setHeading(elements.capabilityHeading, titles.get("feature-map"), "能力");
  setHeading(elements.fileTreeHeading, titles.get("file-tree"), "Skill Tree");
  setHeading(elements.flowHeading, titles.get("flow-timeline"), "流程");
  setHeading(elements.nestedHeading, titles.get("nested-skills"), "嵌套 Skill");
  setHeading(elements.qualityHeading, titles.get("quality-findings"), "质量检查");
  setHeading(elements.issueHeading, titles.get("issue-book") || titles.get("feedback"), "错题集 / 反馈");
  setHeading(elements.triggerHeading, titles.get("trigger-list"), "Trigger 词");
}

function hasSection(type) {
  return state.sectionMap.has(type);
}

function toggleSection(node, visible) {
  node.classList.toggle("is-hidden", !visible);
}

function setHeading(node, value, fallback) {
  node.textContent = value || fallback;
}

function renderOverview() {
  const summary = state.model.analysis || state.model.summary || {};
  elements.overviewResponsibility.textContent = summary.responsibility || state.model.skill.description || "No responsibility summary provided.";
  renderList(elements.overviewUse, summary.when_to_use || []);
  renderList(elements.overviewBoundaries, [...(summary.when_not_to_use || []), ...(summary.boundaries || [])]);
  renderList(elements.overviewOutputs, summary.core_outputs || []);
  renderChips(elements.triggerChips, state.model.skill.triggers || []);
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

function renderChips(container, items) {
  container.innerHTML = "";
  for (const item of items || []) {
    const chip = document.createElement("span");
    chip.className = "text-chip";
    chip.textContent = item;
    container.appendChild(chip);
  }
  if (!container.children.length) {
    const chip = document.createElement("span");
    chip.className = "text-chip is-muted";
    chip.textContent = "未声明";
    container.appendChild(chip);
  }
}

function buildFileTree(files) {
  const root = { name: "", path: "", type: "directory", children: new Map(), file: null };
  for (const file of files) {
    const parts = file.path.split("/");
    let node = root;
    parts.forEach((part, index) => {
      const path = parts.slice(0, index + 1).join("/");
      if (!node.children.has(part)) {
        node.children.set(part, { name: part, path, type: "directory", children: new Map(), file: null });
      }
      node = node.children.get(part);
      if (index === parts.length - 1) {
        node.type = file.type;
        node.file = file;
      }
    });
  }
  return root;
}

function renderFileTree() {
  elements.fileTree.innerHTML = "";
  if (!state.fileTree || !hasSection("file-tree")) return;
  const tree = document.createElement("div");
  tree.className = "tree-root";
  for (const child of sortedTreeChildren(state.fileTree)) {
    tree.appendChild(renderTreeNode(child, 0));
  }
  elements.fileTree.appendChild(tree);
  highlightTreeFile(state.currentFile?.path || "");
}

function sortedTreeChildren(node) {
  return [...node.children.values()].sort((a, b) => {
    if (Boolean(a.file) !== Boolean(b.file)) return a.file ? 1 : -1;
    return a.name.localeCompare(b.name);
  });
}

function renderTreeNode(node, depth) {
  const wrapper = document.createElement("div");
  wrapper.className = "tree-node-wrap";
  const row = document.createElement("button");
  row.className = node.file ? `tree-node file kind-${node.type}` : "tree-node directory";
  row.dataset.path = node.path;
  row.style.setProperty("--depth", depth);
  row.innerHTML = node.file
    ? `<span class="tree-name">${escapeHtml(node.name)}</span><span class="tree-kind">${escapeHtml(node.type)}</span>`
    : `<span class="tree-name">▾ ${escapeHtml(node.name)}</span>`;
  if (node.file) {
    row.addEventListener("click", () => openFile(node.path));
  }
  wrapper.appendChild(row);
  for (const child of sortedTreeChildren(node)) {
    wrapper.appendChild(renderTreeNode(child, depth + 1));
  }
  return wrapper;
}

function highlightTreeFile(path) {
  for (const node of elements.fileTree.querySelectorAll(".tree-node")) {
    const nodePath = node.dataset.path;
    node.classList.toggle("is-current", Boolean(path && nodePath === path));
    node.classList.toggle("is-related", state.relatedFilePaths.has(nodePath) && nodePath !== path);
  }
}

function renderCapabilities() {
  elements.capabilityNav.innerHTML = "";
  elements.capabilityCards.innerHTML = "";
  if (!hasSection("feature-map")) return;

  // The capability layer is the stable ability taxonomy for the current skill.
  // It must stay summary-only so users can choose an ability domain first,
  // then drill into the ordered execution flow in the next panel.
  const capabilities = getCapabilities();
  for (const capability of capabilities) {
    const capabilityFindings = getCapabilityFindings(capability);
    const btn = document.createElement("button");
    btn.className = "flow-button";
    btn.textContent = capabilityFindings.length ? `${capability.title} · ${capabilityFindings.length} risk` : capability.title;
    if (capability.id === state.selectedCapabilityId) btn.classList.add("is-active");
    btn.addEventListener("click", () => {
      state.selectedCapabilityId = capability.id;
      state.selectedFlowId = capability.flows?.[0] || state.selectedFlowId;
      renderCapabilities();
      renderFlows();
    });
    elements.capabilityNav.appendChild(btn);

    const card = document.createElement("button");
    card.className = capability.id === state.selectedCapabilityId ? "feature-card is-active" : "feature-card";
    if (capabilityFindings.length) card.classList.add("has-risk");
    card.innerHTML = `
      <span class="feature-card-label">能力域</span>
      <strong>${escapeHtml(capability.title)}</strong>
      <p>${escapeHtml(capability.description || "")}</p>
      ${capabilityFindings.length ? `<div class="feature-risk-banner">Declared capability needs review · ${capabilityFindings.length} finding(s)</div>` : ""}
      <span class="feature-card-meta">${(capability.trigger_groups || capability.triggers || []).length} triggers · ${(capability.flows || []).length} flows · ${(capability.tuning_points || []).length} tuning</span>
    `;
    card.addEventListener("click", () => {
      state.selectedCapabilityId = capability.id;
      state.selectedFlowId = capability.flows?.[0] || state.selectedFlowId;
      renderCapabilities();
      renderFlows();
    });
    elements.capabilityCards.appendChild(card);
  }
  renderSelectedCapability();
}

function renderSelectedCapability() {
  elements.capabilitySummary.innerHTML = "";
  if (!hasSection("feature-map")) {
    return;
  }
  const capability = getCapabilities().find((item) => item.id === state.selectedCapabilityId);
  if (!capability) return;
  const capabilityFindings = getCapabilityFindings(capability);
  state.relatedFilePaths = new Set(collectFeatureFiles(capability));
  highlightTreeFile(state.currentFile?.path || "");

  const hero = document.createElement("section");
  hero.className = "capability-hero";
  hero.innerHTML = `
    <div class="capability-hero-label">Selected Capability</div>
    <h2>${escapeHtml(capability.title)}</h2>
    <p>${escapeHtml(capability.description || "")}</p>
    <div class="capability-guide-grid">
      ${renderInfoBlock("Capability Intent", capability.description || "")}
      ${renderBullets("Routing Surface", capability.trigger_groups || capability.triggers)}
      ${renderBullets("Flow Coverage", capability.flows || [])}
      ${renderBullets("Tuning Surface", (capability.tuning_points || []).map((item) => item.title))}
    </div>
    ${renderFindingBlock("Capability Risks", capabilityFindings)}
  `;
  elements.capabilitySummary.appendChild(hero);
  renderCapabilityOrientation(capability);
}

function renderMindmapNode(node, feature, index) {
  const wrapper = document.createElement("div");
  wrapper.className = `mindmap-branch kind-${node.type || "note"}`;
  const btn = document.createElement("button");
  btn.className = "mindmap-node";
  btn.innerHTML = `<em>${String(index)}</em><span>${escapeHtml(node.type || "note")}</span><strong>${escapeHtml(node.label)}</strong>`;
  btn.addEventListener("click", () => renderMindmapDetail(feature, node));
  wrapper.appendChild(btn);
  (node.children || []).forEach((child, childIndex) => {
    wrapper.appendChild(renderMindmapNode(child, feature, `${index}.${childIndex + 1}`));
  });
  return wrapper;
}

function renderBranchCard(type, title, description, files, feature) {
  const card = document.createElement("button");
  card.className = `branch-card kind-${type}`;
  card.innerHTML = `<span>${escapeHtml(type)}</span><strong>${escapeHtml(title)}</strong><p>${escapeHtml(description || "")}</p>`;
  card.addEventListener("click", () => renderMindmapDetail(feature, { label: title, type, description, files }));
  return card;
}

function collectFeatureFiles(feature) {
  const files = [...(feature.files || []), ...flattenTuningFiles(feature)];
  const visit = (nodes) => {
    for (const node of nodes || []) {
      files.push(...(node.files || []));
      visit(node.children || []);
    }
  };
  visit(feature.mindmap || []);
  return unique(files);
}

function renderCapabilityOrientation(feature) {
  // Capability orientation is intentionally different from flow rendering.
  // This pane explains what the selected ability unlocks and where to tune it
  // before the user dives into the ordered execution map.
  elements.detailTitle.textContent = feature.title;
  elements.flowDetail.innerHTML = `
    <div class="detail-card">
      <strong>Capability Role</strong>
      <p>${escapeHtml(feature.description || "")}</p>
    </div>
    ${renderBullets("Routing Surface", feature.trigger_groups || feature.triggers)}
    ${renderBullets("Flow Entry Points", feature.flows || [])}
    ${renderBullets("Primary Artifacts", feature.files || [])}
    ${renderBullets("Tuning Surface", (feature.tuning_points || []).map((item) => item.title))}
  `;
  const firstFile = unique([...(feature.files || []), ...flattenTuningFiles(feature)])[0];
  if (firstFile) openFile(firstFile, { preserveDetailTitle: true });
}

function renderMindmapDetail(feature, node) {
  elements.detailTitle.textContent = node.label;
  elements.flowDetail.innerHTML = `
    <div class="detail-card"><strong>${escapeHtml(node.type || "node")}</strong><p>${escapeHtml(node.description || "")}</p></div>
    ${renderBullets("Files", node.files || [])}
  `;
  const firstFile = (node.files || [])[0];
  if (firstFile) {
    openFile(firstFile, { preserveDetailTitle: true });
  } else {
    highlightTreeFile(state.currentFile?.path || "");
  }
}

function renderFlows() {
  elements.flowNav.innerHTML = "";
  elements.flowCanvas.innerHTML = "";
  if (!hasSection("flow-timeline")) return;

  // The flow layer is intentionally subordinate to the selected capability.
  // Users should never see the flow list as the primary classification axis
  // when the skill exposes multiple ability domains.
  const selectedCapability = getCapabilities().find((item) => item.id === state.selectedCapabilityId);
  const allowedFlows = selectedCapability?.flows?.length ? new Set(selectedCapability.flows) : null;
  for (const flow of state.model.flows || []) {
    if (allowedFlows && !allowedFlows.has(flow.id)) continue;
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
  const flow = (state.model.flows || []).find((item) => item.id === state.selectedFlowId);
  if (!flow) return;
  const selectedCapability = getCapabilities().find((item) => item.id === state.selectedCapabilityId);
  const capabilityFindings = selectedCapability ? getCapabilityFindings(selectedCapability) : [];

  // The flow hero introduces the selected execution route. It should summarize
  // entry conditions, outputs, risk, and tuning surface without duplicating the
  // capability guide block above.
  const hero = document.createElement("section");
  hero.className = "flow-hero";
  hero.innerHTML = `
    <div class="flow-hero-header">
      <div>
        ${selectedCapability ? `<div class="flow-context-chip">${escapeHtml(selectedCapability.title)}</div>` : ""}
        <h2>${escapeHtml(flow.title)}</h2>
        <p>${escapeHtml(flow.description || "")}</p>
      </div>
      <div class="flow-hero-callout">
        <strong>Flow Intent</strong>
        <p>${escapeHtml(flow.intent || "未声明")}</p>
      </div>
    </div>
    <div class="flow-hero-grid">
      ${renderInfoBlock("Entry Trigger", flow.trigger)}
      ${renderBullets("Inputs", flow.inputs)}
      ${renderBullets("Outputs", flow.outputs)}
      ${renderBullets("Decision Points", flow.decision_points)}
      ${renderBullets("Blockers", flow.blockers)}
      ${renderBullets("Tuning Surface", (flow.tuning_points || []).map((item) => item.title))}
    </div>
    ${selectedCapability ? renderFindingBlock("Capability-Level Risks", capabilityFindings) : ""}
  `;
  elements.flowCanvas.appendChild(hero);

  const track = document.createElement("div");
  track.className = "step-track";
  flow.steps.forEach((step, index) => {
    const node = elements.stepTemplate.content.firstElementChild.cloneNode(true);
    node.classList.add(`kind-${step.kind || "read"}`);
    node.querySelector(".step-index").textContent = String(index + 1).padStart(2, "0");
    node.querySelector(".step-kicker").textContent = describeStepKind(step.kind);
    if (index === flow.steps.length - 1) node.classList.add("is-last");
    node.querySelector(".step-title").textContent = step.title;
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

function renderFindingBlock(label, findings) {
  if (!findings?.length) return "";
  return `
    <div class="finding-block">
      <strong>${escapeHtml(label)}</strong>
      <ul>
        ${findings.map((finding) => `<li><span class="finding-code">${escapeHtml(finding.code || finding.severity || "finding")}</span>${escapeHtml(finding.message || "")}</li>`).join("")}
      </ul>
    </div>
  `;
}

function renderStepMeta(step) {
  const parts = [];
  if (step.kind) parts.push(renderTagRow("Node Type", [describeStepKind(step.kind)]));
  if (step.kind === "decide") parts.push(renderTagRow("Decision", ["branch", "gate", "route choice"]));
  if (step.kind === "verify") parts.push(renderTagRow("Verification", ["check", "validate", "confirm result"]));
  if (step.kind === "run") parts.push(renderTagRow("Execution", ["tool", "script", "command"]));
  if (step.evidence?.length) parts.push(renderBullets("Evidence", step.evidence));
  if (step.files?.length) parts.push(renderBullets("Artifacts", step.files));
  return parts.join("");
}

function describeStepKind(kind) {
  const labels = {
    read: "Read Context",
    decide: "Decision",
    edit: "Edit / Fill",
    run: "Run Tool",
    verify: "Verify",
    report: "Report",
  };
  return labels[kind] || "Node";
}

function renderTagRow(label, items) {
  if (!items?.length) return "";
  return `<div class="tag-block"><strong>${escapeHtml(label)}</strong><div class="tag-row">${items.map((item) => `<span class="inline-tag">${escapeHtml(item)}</span>`).join("")}</div></div>`;
}

function renderFlowDetail(flow, step) {
  elements.detailTitle.textContent = step ? step.title : flow.title;
  elements.flowDetail.innerHTML = `
    <div class="detail-card">
      <strong>Flow</strong>
      <p>${escapeHtml(flow.title)}</p>
    </div>
    ${renderInfoBlock("Intent", flow.intent)}
    ${renderBullets("Flow Tuning Points", (flow.tuning_points || []).map((item) => item.title))}
    ${renderBullets("Flow Blockers", flow.blockers || [])}
    ${step ? renderInfoBlock("Selected Step", `${describeStepKind(step.kind)} · ${step.description || ""}`) : ""}
    ${step?.files?.length ? renderBullets("Step Artifacts", step.files) : ""}
    ${step?.evidence?.length ? renderBullets("Step Evidence", step.evidence) : ""}
  `;
  const firstFile = unique([...(step?.evidence || []), ...(step?.files || []), ...flattenTuningFiles(flow)])[0];
  if (firstFile) openFile(firstFile, { preserveDetailTitle: true });
}

function renderQuality() {
  elements.qualityList.innerHTML = "";
  if (!hasSection("quality-findings")) return;

  const findings = state.quality?.findings || [];
  if (!findings.length) {
    const item = document.createElement("div");
    item.className = "quality-item";
    item.textContent = "No findings";
    elements.qualityList.appendChild(item);
    return;
  }
  const structuralCodes = new Set([
    "missing-skill-md",
    "missing-frontmatter",
    "missing-name",
    "missing-description",
    "name-format",
    "weak-description",
    "skill-md-long",
    "absolute-path",
    "private-value-risk",
    "excluded-artifact",
  ]);
  const usageRiskCodes = new Set([
    "declared-capability-without-workflow",
    "trigger-surface-exceeds-workflow-surface",
    "feature-flow-collision",
    "phase-like-capability",
    "feature-without-trigger",
    "unmapped-trigger",
  ]);

  const groups = [
    {
      title: "Usage Stability Findings",
      items: findings.filter((finding) => usageRiskCodes.has(finding.code)),
      className: "usage-risk-group",
    },
    {
      title: "Structural Findings",
      items: findings.filter((finding) => structuralCodes.has(finding.code)),
      className: "structural-group",
    },
    {
      title: "Other Findings",
      items: findings.filter((finding) => !usageRiskCodes.has(finding.code) && !structuralCodes.has(finding.code)),
      className: "other-group",
    },
  ];

  for (const group of groups) {
    if (!group.items.length) continue;
    const header = document.createElement("div");
    header.className = `quality-group-title ${group.className}`;
    header.textContent = group.title;
    elements.qualityList.appendChild(header);
    for (const finding of group.items.slice(0, 20)) {
      const item = document.createElement("div");
      item.className = `quality-item ${finding.severity}`;
      if (usageRiskCodes.has(finding.code)) item.classList.add("usage-risk");
      item.textContent = `${finding.severity}: ${finding.code ? `${finding.code} · ` : ""}${finding.message}${finding.path ? ` (${finding.path})` : ""}`;
      elements.qualityList.appendChild(item);
    }
  }
}

function renderNestedSkills() {
  elements.nestedList.innerHTML = "";
  if (!hasSection("nested-skills")) return;

  const items = state.model.nested_skills || [];
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "quality-item";
    empty.textContent = "无嵌套 skill";
    elements.nestedList.appendChild(empty);
    return;
  }
  for (const item of items) {
    const node = document.createElement("button");
    node.className = "nested-item";
    node.innerHTML = `<strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.source)} → ${escapeHtml(item.target)}</span><small>${escapeHtml(item.condition || item.role || "")}</small>`;
    node.addEventListener("click", () => {
      elements.detailTitle.textContent = item.name;
      elements.flowDetail.innerHTML = `${renderInfoBlock("Role", item.role)}${renderInfoBlock("Condition", item.condition)}${renderBullets("Files", item.files || [])}`;
      if (item.files?.[0]) openFile(item.files[0], { preserveDetailTitle: true });
    });
    elements.nestedList.appendChild(node);
  }
}

function renderIssueFeedback() {
  elements.issueFeedbackList.innerHTML = "";
  if (!hasSection("issue-book") && !hasSection("feedback")) return;

  const items = [...(state.model.issue_book || []), ...(state.model.feedback || [])];
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "quality-item";
    empty.textContent = "暂无错题或用户反馈";
    elements.issueFeedbackList.appendChild(empty);
    return;
  }
  for (const item of items) {
    const node = document.createElement("div");
    node.className = "quality-item";
    node.textContent = `${item.status || "open"}: ${item.title}${item.description ? ` - ${item.description}` : ""}`;
    elements.issueFeedbackList.appendChild(node);
  }
}

async function openFile(path, options = {}) {
  const file = state.files.find((item) => item.path === path);
  if (!file) return;
  if (file.content === null) file.content = await readFile(file);
  state.currentFile = file;
  renderFile(file, options);
  highlightTreeFile(file.path);
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
  elements.editStatus.textContent = state.dirtyFiles.size ? `${state.dirtyFiles.size} file(s) dirty` : "无未保存修改";
}

// All viewer labels and file content pass through this helper because the page
// mixes semantic spec data with embedded local file content. Escaping keeps the
// static viewer stable and prevents authored text from breaking the DOM.
function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
