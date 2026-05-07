const api = {
  async get(url) {
    const response = await fetch(url);
    const data = await parseJsonResponse(response);

    if (!response.ok) {
      throw new Error(resolveErrorMessage(data, "请求失败，请稍后再试。"));
    }

    return data;
  },

  async post(url, payload) {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    const data = await parseJsonResponse(response);

    if (!response.ok) {
      throw new Error(resolveErrorMessage(data, "请求失败，请稍后再试。"));
    }

    return data;
  },
};

async function parseJsonResponse(response) {
  try {
    return await response.json();
  } catch (_error) {
    return {};
  }
}

function resolveErrorMessage(data, fallback = "请求失败，请稍后再试。") {
  if (!data) return fallback;

  if (typeof data.detail === "string" && data.detail.trim()) {
    return data.detail;
  }

  if (typeof data.message === "string" && data.message.trim()) {
    return data.message;
  }

  if (Array.isArray(data.detail)) {
    return data.detail
      .map((item) => item.msg || item.message || JSON.stringify(item))
      .join("；");
  }

  return fallback;
}

function $(id) {
  return document.getElementById(id);
}

function qs(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function setStatus(targetId, message, type = "info") {
  const el = $(targetId);
  if (!el) return;

  el.className = `notice ${type === "error" ? "error" : type === "success" ? "success" : ""}`.trim();
  el.textContent = message || "";
  el.hidden = !message;
}

function setButtonBusy(button, busy, busyText = "处理中...") {
  if (!button) return;

  if (busy) {
    if (!button.dataset.originalText) {
      button.dataset.originalText = button.textContent;
    }
    button.disabled = true;
    button.textContent = busyText;
    button.classList.add("is-busy");
    return;
  }

  button.disabled = false;
  if (button.dataset.originalText) {
    button.textContent = button.dataset.originalText;
  }
  button.classList.remove("is-busy");
}

function createEmptyState(title, description, actionHtml = "") {
  return `
    <div class="empty-state">
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(description)}</p>
      ${actionHtml}
    </div>
  `;
}

function createErrorState(title, description, actionHtml = "") {
  return `
    <div class="empty-state error-state">
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(description)}</p>
      ${actionHtml}
    </div>
  `;
}

function createLoadingSkeleton(lines = 3) {
  return `
    <div class="skeleton-block">
      ${Array.from({ length: lines })
        .map(() => '<div class="skeleton-line"></div>')
        .join("")}
    </div>
  `;
}

function createCardSkeleton() {
  return `
    <div class="card skeleton-card">
      <div class="skeleton-line short"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line short"></div>
    </div>
  `;
}

function formatMoney(value) {
  if (value === null || value === undefined || value === "") {
    return "暂无";
  }
  return `${value} 元`;
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") {
    return "暂无";
  }
  return `${Math.round(Number(value) * 100)}%`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function riskClass(level) {
  if (level === "high") return "high";
  if (level === "medium") return "medium";
  if (level === "low") return "low";
  return "clean";
}

function buildExportDownloadUrl(filepath) {
  if (!filepath) {
    return null;
  }
  return `/${String(filepath).replaceAll("\\", "/")}`;
}

function goToDetail(projectFilepath) {
  window.location.href = `/trip-detail?project_filepath=${encodeURIComponent(projectFilepath)}`;
}
