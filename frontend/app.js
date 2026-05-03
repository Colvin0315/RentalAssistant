const state = {
  apiBase: "http://127.0.0.1:8000/api/v1",
  documentId: "",
  sessionId: "",
  documentStatus: "",
};

const $ = (id) => document.getElementById(id);

const ui = {
  apiBase: $("apiBase"),
  apiBasePreview: $("api-base-preview"),
  activeDocument: $("active-document"),
  connectionState: $("connectionState"),
  documentId: $("documentId"),
  documentStatus: $("documentStatus"),
  chunkCount: $("chunkCount"),
  fieldsPanel: $("fieldsPanel"),
  answerPanel: $("answerPanel"),
  citationsPanel: $("citationsPanel"),
  qaRiskPanel: $("qaRiskPanel"),
  riskPanel: $("riskPanel"),
  draftPanel: $("draftPanel"),
  evalPanel: $("evalPanel"),
  logsPanel: $("logsPanel"),
  sessionId: $("sessionId"),
  askBtn: $("askBtn"),
  parseBtn: $("parseBtn"),
  indexBtn: $("indexBtn"),
  riskBtn: $("riskBtn"),
  draftBtn: $("draftBtn"),
  evalBtn: $("evalBtn"),
  logsBtn: $("logsBtn"),
};

function setConnectionState(kind, text) {
  ui.connectionState.className = `status-pill ${kind}`;
  ui.connectionState.textContent = text;
}

function setDocumentState(documentId, status) {
  state.documentId = documentId || "";
  state.documentStatus = status || "";
  ui.documentId.textContent = documentId || "-";
  ui.activeDocument.textContent = documentId || "未载入";
  ui.documentStatus.textContent = status || "未开始";

  const hasDoc = Boolean(state.documentId);
  ui.parseBtn.disabled = !hasDoc || state.documentStatus === "indexed";
  ui.indexBtn.disabled = state.documentStatus !== "parsed";
  ui.riskBtn.disabled = !hasDoc || !["parsed", "indexed"].includes(state.documentStatus);
  ui.draftBtn.disabled = !hasDoc || !["parsed", "indexed"].includes(state.documentStatus);
  ui.evalBtn.disabled = !hasDoc || !["parsed", "indexed"].includes(state.documentStatus);
  ui.askBtn.disabled = !hasDoc || state.documentStatus !== "indexed";
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${state.apiBase}${path}`, options);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = typeof payload === "string" ? payload : payload.detail || JSON.stringify(payload);
    throw new Error(message);
  }
  return payload;
}

function renderFields(fields) {
  const entries = Object.entries(fields || {});
  if (!entries.length) {
    ui.fieldsPanel.className = "tag-cloud empty";
    ui.fieldsPanel.textContent = "没有抽取到结构化字段。";
    return;
  }
  ui.fieldsPanel.className = "tag-cloud";
  ui.fieldsPanel.innerHTML = entries
    .map(([key, value]) => `<span class="pill"><strong>${escapeHtml(key)}</strong> ${escapeHtml(value)}</span>`)
    .join("");
}

function renderCitations(citations) {
  if (!citations?.length) {
    ui.citationsPanel.className = "list-box empty";
    ui.citationsPanel.textContent = "没有返回引用条款。";
    return;
  }
  ui.citationsPanel.className = "list-box";
  ui.citationsPanel.innerHTML = citations
    .map(
      (item) => `
        <article class="citation-card">
          <strong>${escapeHtml(item.chunk_id)}</strong>
          <p class="muted">${escapeHtml(item.text)}</p>
        </article>
      `,
    )
    .join("");
}

function formatAnswerSections(answer) {
  const iconMap = {
    "结论": "✅",
    "依据": "📎",
    "风险提醒": "⚠️",
    "建议": "📝",
  };
  const normalized = String(answer || "").replace(/\r\n/g, "\n").trim();
  const matches = [...normalized.matchAll(/^###\s*(.+)$/gm)];

  if (!matches.length) {
    return `<div class="answer-copy">${escapeHtml(normalized)}</div>`;
  }

  const sections = matches.map((match, index) => {
    const title = match[1].trim();
    const start = match.index + match[0].length;
    const end = index + 1 < matches.length ? matches[index + 1].index : normalized.length;
    const body = normalized.slice(start, end).trim();
    const icon = iconMap[title] || "📌";
    return `
      <section class="answer-section">
        <div class="answer-label">${icon} ${escapeHtml(title)}</div>
        <div class="answer-copy">${escapeHtml(body)}</div>
      </section>
    `;
  });

  return sections.join("");
}

function renderRiskFlags(target, risks, emptyText) {
  if (!risks?.length) {
    target.className = `${target.id === "riskPanel" ? "risk-stack" : "list-box"} empty`;
    target.textContent = emptyText;
    return;
  }
  const baseClass = target.id === "riskPanel" ? "risk-stack" : "list-box";
  target.className = baseClass;
  target.innerHTML = risks
    .map(
      (risk) => `
        <article class="risk-card">
          <div class="risk-title">
            <span>${escapeHtml(risk.title)}</span>
            <span class="severity ${escapeHtml(risk.severity)}">${escapeHtml(risk.severity)}</span>
          </div>
          ${risk.clause_id ? `<p class="muted">条款：${escapeHtml(risk.clause_id)}</p>` : ""}
          ${risk.explanation ? `<p>${escapeHtml(risk.explanation)}</p>` : ""}
        </article>
      `,
    )
    .join("");
}

function renderMetrics(metrics) {
  const entries = Object.entries(metrics || {});
  if (!entries.length) {
    ui.evalPanel.className = "metrics empty";
    ui.evalPanel.textContent = "没有可显示的评测指标。";
    return;
  }
  ui.evalPanel.className = "metrics";
  ui.evalPanel.innerHTML = entries
    .map(([key, value]) => `<span class="metric-pill">${escapeHtml(key)} : ${Number(value).toFixed(2)}</span>`)
    .join("");
}

function renderLogs(events) {
  if (!events?.length) {
    ui.logsPanel.className = "timeline empty";
    ui.logsPanel.textContent = "当前 session 暂无日志。";
    return;
  }
  ui.logsPanel.className = "timeline";
  ui.logsPanel.innerHTML = events
    .map(
      (event) => {
        const textValue = event?.data?.text;
        if (event.type === "answer" && typeof textValue === "string") {
          return `
            <article class="timeline-item">
              <strong>${escapeHtml(event.type)}</strong>
              <div class="log-text">${formatAnswerSections(textValue)}</div>
            </article>
          `;
        }
        return `
          <article class="timeline-item">
            <strong>${escapeHtml(event.type)}</strong>
            <pre>${escapeHtml(JSON.stringify(event.data, null, 2))}</pre>
          </article>
        `;
      },
    )
    .join("");
}

function setBusy(button, busyText) {
  const originalText = button.dataset.originalText || button.textContent;
  button.dataset.originalText = originalText;
  button.disabled = true;
  button.textContent = busyText;
  return () => {
    button.textContent = originalText;
    setDocumentState(state.documentId, ui.documentStatus.textContent);
    ui.logsBtn.disabled = !state.sessionId;
  };
}

ui.apiBase.addEventListener("input", (event) => {
  state.apiBase = event.target.value.trim().replace(/\/$/, "");
  ui.apiBasePreview.textContent = state.apiBase || "-";
});

$("pingBtn").addEventListener("click", async () => {
  state.apiBase = ui.apiBase.value.trim().replace(/\/$/, "");
  ui.apiBasePreview.textContent = state.apiBase || "-";
  setConnectionState("idle", "连接中");
  try {
    const root = state.apiBase.replace(/\/api\/v1$/, "");
    const response = await fetch(root);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    setConnectionState("ok", "连接成功");
  } catch (error) {
    setConnectionState("error", `连接失败: ${error.message}`);
  }
});

$("uploadForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = $("documentFile").files[0];
  if (!file) {
    alert("请先选择文件。");
    return;
  }
  const restore = setBusy(event.submitter, "上传中...");
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_type", $("documentType").value);
    const result = await apiFetch("/documents/upload", {
      method: "POST",
      body: formData,
    });
    setDocumentState(result.document_id, result.status);
    ui.chunkCount.textContent = "-";
    renderFields({});
    renderRiskFlags(ui.riskPanel, [], "点击“扫描风险”后，系统会把命中的风险条款列在这里。");
    ui.answerPanel.className = "answer-body empty";
    ui.answerPanel.textContent = "文档已上传，可以继续解析。";
    state.sessionId = "";
    ui.sessionId.textContent = "Session: -";
    ui.logsBtn.disabled = true;
  } catch (error) {
    alert(`上传失败：${error.message}`);
  } finally {
    restore();
  }
});

ui.parseBtn.addEventListener("click", async () => {
  const restore = setBusy(ui.parseBtn, "解析中...");
  try {
    const result = await apiFetch(`/documents/${state.documentId}/parse`, { method: "POST" });
    setDocumentState(result.document_id, result.status);
    ui.chunkCount.textContent = result.chunk_count;
    renderFields(result.fields);
  } catch (error) {
    alert(`解析失败：${error.message}`);
  } finally {
    restore();
  }
});

ui.indexBtn.addEventListener("click", async () => {
  const restore = setBusy(ui.indexBtn, "建索引中...");
  try {
    const result = await apiFetch(`/documents/${state.documentId}/index`, { method: "POST" });
    setDocumentState(result.document_id, result.status);
    ui.answerPanel.className = "answer-body empty";
    ui.answerPanel.textContent = "索引已建立，可以开始问答。";
  } catch (error) {
    alert(`建索引失败：${error.message}`);
  } finally {
    restore();
  }
});

$("qaForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const restore = setBusy(event.submitter, "分析中...");
  try {
    const result = await apiFetch("/qa/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document_id: state.documentId,
        question: $("questionInput").value.trim(),
      }),
    });
    ui.answerPanel.className = "answer-body";
    ui.answerPanel.innerHTML = formatAnswerSections(result.answer);
    renderCitations(result.citations);
    renderRiskFlags(ui.qaRiskPanel, result.risk_flags, "本次问答没有额外风险提示。");
    state.sessionId = result.session_id;
    ui.sessionId.textContent = `Session: ${result.session_id}`;
    ui.logsBtn.disabled = false;
  } catch (error) {
    alert(`问答失败：${error.message}`);
  } finally {
    restore();
  }
});

ui.riskBtn.addEventListener("click", async () => {
  const restore = setBusy(ui.riskBtn, "扫描中...");
  try {
    const result = await apiFetch("/risk/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: state.documentId }),
    });
    renderRiskFlags(ui.riskPanel, result.risks, "没有检测到显著风险。");
  } catch (error) {
    alert(`风险分析失败：${error.message}`);
  } finally {
    restore();
  }
});

$("draftForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const restore = setBusy(event.submitter, "生成中...");
  try {
    const result = await apiFetch("/drafts/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document_id: state.documentId,
        scenario: $("draftScenario").value,
        tone: $("draftTone").value,
      }),
    });
    ui.draftPanel.className = "note-card";
    ui.draftPanel.textContent = result.draft;
  } catch (error) {
    alert(`话术生成失败：${error.message}`);
  } finally {
    restore();
  }
});

$("evalForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const restore = setBusy(event.submitter, "评测中...");
  try {
    const result = await apiFetch("/eval/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dataset_name: $("datasetName").value.trim(),
        document_id: state.documentId,
      }),
    });
    renderMetrics(result.metrics);
  } catch (error) {
    alert(`评测失败：${error.message}`);
  } finally {
    restore();
  }
});

ui.logsBtn.addEventListener("click", async () => {
  const restore = setBusy(ui.logsBtn, "拉取中...");
  try {
    const result = await apiFetch(`/sessions/${state.sessionId}/logs`);
    renderLogs(result.events);
  } catch (error) {
    alert(`日志获取失败：${error.message}`);
  } finally {
    restore();
  }
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    $("questionInput").value = button.dataset.question;
  });
});

setDocumentState("", "");
renderFields({});
renderCitations([]);
renderRiskFlags(ui.qaRiskPanel, [], "问答阶段捕捉到的高风险提示会显示在这里。");
renderRiskFlags(ui.riskPanel, [], "点击“扫描风险”后，系统会把命中的风险条款列在这里。");
renderMetrics({});
renderLogs([]);
