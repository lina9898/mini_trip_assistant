let currentProjectFilepath = "";
let currentProjectData = null;
let detailBusy = false;

document.addEventListener("DOMContentLoaded", async () => {
  currentProjectFilepath = qs("project_filepath") || "";

  $("back-home").addEventListener("click", () => {
    window.location.href = "/";
  });
  $("back-history").addEventListener("click", () => {
    window.location.href = "/history";
  });
  $("open-memory").addEventListener("click", openMemoryDrawer);
  $("close-memory").addEventListener("click", closeMemoryDrawer);
  $("drawer-backdrop").addEventListener("click", closeMemoryDrawer);

  $("edit-form").addEventListener("submit", submitEdit);
  $("restore-button").addEventListener("click", restorePreviousVersion);
  $("export-markdown").addEventListener("click", () => exportTrip("markdown"));
  $("export-html").addEventListener("click", () => exportTrip("html"));
  $("export-pdf").addEventListener("click", () => exportTrip("pdf"));
  $("adopt-button").addEventListener("click", adoptCurrentTrip);
  $("feedback-form").addEventListener("submit", submitFeedback);

  renderDetailSkeleton();
  await loadDetail();
});

function renderDetailSkeleton() {
  $("detail-title").textContent = "正在加载行程详情...";
  $("detail-subtitle").textContent = "";
  $("basic-info").innerHTML = createLoadingSkeleton(4);
  $("weather-budget").innerHTML = `<div class="grid two">${createCardSkeleton()}${createCardSkeleton()}</div>`;
  $("transport-info").innerHTML = createLoadingSkeleton(5);
  $("plan-list").innerHTML = `${createCardSkeleton()}${createCardSkeleton()}`;
  $("hotel-info").innerHTML = createLoadingSkeleton(4);
  $("opening-hours").innerHTML = createLoadingSkeleton(3);
  $("events-info").innerHTML = createLoadingSkeleton(4);
  $("export-history").innerHTML = createLoadingSkeleton(3);
  $("evaluation-metrics").innerHTML = createLoadingSkeleton(6);
  $("memory-text").textContent = "";
  $("version-history").innerHTML = createLoadingSkeleton(2);
}

async function loadDetail() {
  if (!currentProjectFilepath) {
    $("detail-title").textContent = "缺少项目路径";
    $("page-status").innerHTML = createErrorState(
      "无法读取项目详情",
      "缺少 project_filepath 参数，请从首页或历史项目页重新进入。",
      '<a class="button secondary" href="/">返回首页</a>'
    );
    $("page-status").hidden = false;
    return;
  }

  setStatus("page-status", "正在读取项目详情...");

  try {
    const result = await api.get(`/api/trips/detail?project_filepath=${encodeURIComponent(currentProjectFilepath)}`);
    currentProjectData = result.project_data;
    currentProjectFilepath = currentProjectData.project_filepath || currentProjectFilepath;
    renderDetail(currentProjectData);
    setStatus("page-status", "");
  } catch (error) {
    $("detail-title").textContent = "项目详情读取失败";
    $("detail-subtitle").textContent = currentProjectFilepath;
    $("page-status").innerHTML = createErrorState(
      "读取失败",
      error.message || "暂时无法读取项目详情。",
      '<button id="retry-detail" class="button secondary" type="button">重新加载</button>'
    );
    $("page-status").hidden = false;

    const retryButton = $("retry-detail");
    if (retryButton) {
      retryButton.addEventListener("click", async () => {
        renderDetailSkeleton();
        await loadDetail();
      });
    }
  }
}

function renderDetail(projectData) {
  const trip = projectData.trip_data || {};
  const travelDates = projectData.travel_dates || trip.travel_dates || {};
  const weather = projectData.weather_info || {};
  const budget = projectData.budget || {};
  const transport = projectData.transport_info || {};
  const hotel = projectData.hotel_info || {};
  const opening = projectData.opening_hours_info || {};
  const eventInfo = projectData.event_info || {};
  const imageInfo = projectData.image_info || {};
  const exportHistory = projectData.export_history || [];
  const evaluation = projectData.evaluation || {};
  const dayImages = buildDayImageMap(imageInfo.day_images || []);

  $("detail-title").textContent = `${trip.destination || "未命名"} 行程详情`;
  $("detail-subtitle").textContent = currentProjectFilepath;
  $("current-filepath").textContent = currentProjectFilepath;
  $("latest-export-feedback").innerHTML = "";

  $("basic-info").innerHTML = `
    <div class="stats-grid">
      ${statCard("出发地", trip.origin || "未填写")}
      ${statCard("目的地", trip.destination || "未填写")}
      ${statCard("旅行天数", `${trip.days || travelDates.days || "未知"} 天`)}
      ${statCard("出行人数", `${trip.people || "未知"} 人`)}
    </div>
    <div class="tag-row">
      <span class="tag">出行：${escapeHtml(trip.start_date || travelDates.start_date || "未填写")} 至 ${escapeHtml(trip.end_date || travelDates.end_date || "未填写")}</span>
      <span class="tag">偏好：${escapeHtml(trip.preference || "未填写")}</span>
      <span class="tag">节奏：${escapeHtml(trip.pace || "未填写")}</span>
      <span class="tag">预算：${escapeHtml(trip.budget_level || "未填写")}</span>
      <span class="tag">快照：v${escapeHtml(projectData.snapshot_version || 1)}</span>
      <span class="tag">${projectData.dirty ? "有未保存修改" : "当前快照已保存"}</span>
    </div>
  `;

  $("weather-budget").innerHTML = `
    <div class="grid two">
      <div class="list-item">
        <h3>天气信息</h3>
        <p><strong>天气模式：</strong>${escapeHtml(weather.mode || "未知")}</p>
        <p><strong>天气摘要：</strong>${escapeHtml(trip.weather_summary || "暂无")}</p>
        <p><strong>天气适配：</strong>${escapeHtml(trip.weather_adjustment || "暂无")}</p>
      </div>
      <div class="list-item">
        <h3>预算信息</h3>
        <p><strong>总预算：</strong>${formatMoney(budget.total)}</p>
        <p><strong>住宿：</strong>${formatMoney(budget.hotel)}</p>
        <p><strong>餐饮：</strong>${formatMoney(budget.food)}</p>
        <p><strong>交通：</strong>${formatMoney(budget.transport)}</p>
        <p><strong>门票：</strong>${formatMoney(budget.ticket)}</p>
      </div>
    </div>
  `;

  const recommendation = transport.recommendation || {};
  const driving = transport.driving || {};
  const transit = transport.transit || {};
  $("transport-info").innerHTML = `
    <div class="list-item">
      <p><strong>推荐方式：</strong>${escapeHtml(recommendation.main_mode || "暂无")}</p>
      <p><strong>驾车距离：</strong>${escapeHtml(String(driving.distance_km ?? "未知"))} km</p>
      <p><strong>驾车耗时：</strong>${escapeHtml(String(driving.duration_hour ?? "未知"))} 小时</p>
      <p><strong>公共交通耗时：</strong>${escapeHtml(String(transit.duration_hour ?? "未知"))} 小时</p>
      <p><strong>第一天建议：</strong>${escapeHtml(recommendation.first_day_advice || trip.intercity_transport_advice || "暂无")}</p>
    </div>
  `;

  $("plan-list").innerHTML = (trip.plan || []).map((day) => {
    const images = dayImages[String(day.day)] || [];
    return `
      <div class="card inner-card">
        <div class="section-head">
          <div>
            <h3>第 ${escapeHtml(day.day || "")} 天</h3>
            <div class="muted">${escapeHtml(day.date || "")}</div>
          </div>
        </div>
        <div class="day-plan">
          <p><span class="day-label">上午</span>${escapeHtml(day.morning || "")}</p>
          <p><span class="day-label">下午</span>${escapeHtml(day.afternoon || "")}</p>
          <p><span class="day-label">晚上</span>${escapeHtml(day.evening || "")}</p>
          <p><span class="day-label">说明</span>${escapeHtml(day.note || "")}</p>
          <p><span class="day-label">推荐理由</span>${escapeHtml(day.reason || "")}</p>
        </div>
        ${renderImages(images)}
      </div>
    `;
  }).join("") || createEmptyState("暂无每日行程", "当前项目还没有生成具体的每日安排。");

  $("hotel-info").innerHTML = `
    <p><strong>住宿建议：</strong>${escapeHtml(trip.hotel_advice || "暂无")}</p>
    <p><strong>推荐区域：</strong>${escapeHtml(hotel.area_suggestion || "暂无")}</p>
    <div class="list">
      ${(hotel.hotel_candidates || []).slice(0, 5).map((item) => `
        <div class="list-item">
          <h3>${escapeHtml(item.name || "酒店候选")}</h3>
          <p><strong>平均距离：</strong>${escapeHtml(String(item.avg_distance_km ?? "暂无"))} km</p>
          <p><strong>最近景点：</strong>${escapeHtml(item.nearest_place || "暂无")}</p>
          <p><strong>推荐理由：</strong>${escapeHtml(item.reason || "暂无")}</p>
        </div>
      `).join("") || createEmptyState("暂无酒店候选", "当前项目还没有可展示的酒店选址建议。")}
    </div>
  `;

  $("opening-hours").innerHTML = renderOpeningSection(opening);
  $("events-info").innerHTML = renderEventSection(trip, eventInfo);
  $("export-history").innerHTML = renderExportHistory(exportHistory);
  renderEvaluationSection(evaluation);
  renderFeedbackSection(evaluation);
}

function renderImages(images) {
  if (!images.length) {
    return "";
  }

  return `
    <div class="image-grid">
      ${images.map((item) => `
        <div class="image-card">
          <img src="${escapeHtml(item.image_url || "")}" alt="${escapeHtml(item.place_name || "地点图片")}">
          <div class="caption">
            <strong>${escapeHtml(item.place_name || "地点")}</strong>
            <div class="muted">${escapeHtml(item.description || "")}</div>
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

function renderOpeningSection(opening) {
  const checks = opening.checks || [];
  const riskItems = checks.filter((item) => item.risk_level === "high" || item.risk_level === "medium");

  if (!riskItems.length) {
    return createEmptyState("暂无明显风险", "目前没有发现高风险或需要确认的开放时间冲突。");
  }

  return `
    <div class="list">
      ${riskItems.map((item) => `
        <div class="list-item">
          <div class="section-head">
            <strong>第 ${escapeHtml(item.day || "")} 天 · ${escapeHtml(item.period || "")} · ${escapeHtml(item.place_name || "")}</strong>
            <span class="pill ${riskClass(item.risk_level)}">${escapeHtml(item.risk_level || "")}</span>
          </div>
          <div class="muted">${escapeHtml(item.message || "")}</div>
        </div>
      `).join("")}
    </div>
  `;
}

function renderEventSection(trip, eventInfo) {
  const events = eventInfo.events || [];
  const advice = trip.event_advice || eventInfo.summary?.suggestion || "暂未查询到可靠活动信息，建议出行前通过官方渠道确认。";

  if (!events.length) {
    return `
      <div class="notice">${escapeHtml(advice)}</div>
      <div class="muted" style="margin-top: 10px;">${escapeHtml(eventInfo.note || "")}</div>
    `;
  }

  return `
    <p>${escapeHtml(advice)}</p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>日期</th>
            <th>时间</th>
            <th>活动</th>
            <th>地点</th>
            <th>类型</th>
            <th>建议</th>
          </tr>
        </thead>
        <tbody>
          ${events.slice(0, 8).map((event) => `
            <tr>
              <td>${escapeHtml(event.date || "")}</td>
              <td>${escapeHtml(event.time || "")}</td>
              <td>${escapeHtml(event.name || "")}</td>
              <td>${escapeHtml(event.venue || "")}</td>
              <td>${escapeHtml(event.category || "")}</td>
              <td>${escapeHtml(event.recommendation || "")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderExportHistory(items) {
  if (!items.length) {
    return createEmptyState("还没有导出记录", "导出 Markdown、HTML 或 PDF 后，记录会显示在这里。");
  }

  return `
    <div class="list">
      ${items.slice().reverse().map((item, index) => {
        const downloadUrl = buildExportDownloadUrl(item.filepath);
        return `
          <div class="list-item">
            <div class="section-head">
              <strong>${escapeHtml(item.type || "").toUpperCase()}</strong>
              <div class="action-row">
                <span class="tag">v${escapeHtml(item.snapshot_version || "")}</span>
                ${index === 0 ? '<span class="pill clean">最新导出</span>' : ""}
              </div>
            </div>
            <div class="path-text">${escapeHtml(item.filepath || "")}</div>
            <div class="muted">${escapeHtml(item.created_at || "")}</div>
            <div class="action-row" style="margin-top: 10px;">
              ${
                downloadUrl
                  ? `<a class="button secondary" href="${escapeHtml(downloadUrl)}" target="_blank" rel="noopener noreferrer">下载文件</a>`
                  : '<span class="muted">仅显示文件路径</span>'
              }
            </div>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function renderEvaluationSection(evaluation) {
  const memoryCheck = evaluation.memory_check || {};
  const imageMatch = evaluation.image_match || {};
  const toolMetrics = evaluation.tool_metrics || {};
  const riskMetrics = evaluation.risk_metrics || {};

  $("evaluation-metrics").innerHTML = `
    <div class="metrics-grid">
      ${metricCard("修改次数", evaluation.edit_count ?? 0, "用户对初稿的二次调整次数")}
      ${metricCard("恢复次数", evaluation.restore_count ?? 0, "恢复上一版的使用次数")}
      ${metricCard("导出次数", evaluation.export_count ?? 0, "报告被导出的总次数")}
      ${metricCard("再次打开", evaluation.reopen_count ?? 0, "历史项目被重新打开的次数")}
      ${metricCard("是否采纳", evaluation.is_adopted ? "已采纳" : "未采纳", "最终是否认可这份行程")}
      ${metricCard("满意度", evaluation.satisfaction_score ? `${evaluation.satisfaction_score} / 5` : "暂无", "用户主动提交的评分")}
      ${metricCard("记忆命中率", formatPercent(memoryCheck.hit_rate), `命中 ${memoryCheck.hit_count ?? 0} / ${memoryCheck.total_constraints ?? 0}`)}
      ${metricCard("图片匹配率", formatPercent(imageMatch.accuracy), `匹配 ${imageMatch.matched_images ?? 0} / ${imageMatch.total_images ?? 0}`)}
      ${metricCard("工具成功率", formatPercent(toolMetrics.success_rate), `成功 ${toolMetrics.success_tools ?? 0} / ${toolMetrics.total_tools ?? 0}`)}
      ${metricCard("高风险提示", riskMetrics.opening_hours_high_risk ?? 0, "开放时间高风险地点数")}
      ${metricCard("路线较远", riskMetrics.route_faraway_count ?? 0, "路线工具识别出的较远地点数")}
      ${metricCard("生成耗时", evaluation.generation_duration ? `${evaluation.generation_duration} 秒` : "暂无", "从发起生成到项目构建完成")}
    </div>
    <div class="evaluation-note">
      <p><strong>导出类型：</strong>${(evaluation.export_types || []).length ? escapeHtml((evaluation.export_types || []).join("、").toUpperCase()) : "暂无"}</p>
      <p><strong>用户反馈：</strong>${escapeHtml(evaluation.user_feedback || "暂无")}</p>
    </div>
  `;
}

function renderFeedbackSection(evaluation) {
  const adopted = !!evaluation.is_adopted;
  const adoptButton = $("adopt-button");
  const scoreSelect = $("feedback-score");
  const feedbackText = $("feedback-text");

  adoptButton.disabled = adopted;
  adoptButton.textContent = adopted ? "已采纳此行程" : "采纳此行程";

  scoreSelect.value = evaluation.satisfaction_score ? String(evaluation.satisfaction_score) : "";
  feedbackText.value = evaluation.user_feedback || "";

  if (adopted) {
    setStatus("adoption-status", "用户已标记采纳这份行程。", "success");
  } else {
    setStatus("adoption-status", "");
  }
}

function buildDayImageMap(dayImages) {
  const map = {};
  dayImages.forEach((item) => {
    map[String(item.day)] = item.place_images || [];
  });
  return map;
}

function statCard(label, value) {
  return `
    <div class="stat">
      <div class="label">${escapeHtml(label)}</div>
      <div class="value">${escapeHtml(value)}</div>
    </div>
  `;
}

function metricCard(label, value, hint) {
  return `
    <div class="metric-card">
      <div class="metric-label">${escapeHtml(label)}</div>
      <div class="metric-value">${escapeHtml(value)}</div>
      <div class="metric-hint">${escapeHtml(hint || "")}</div>
    </div>
  `;
}

function setDetailBusy(busy, source = "") {
  detailBusy = busy;
  setButtonBusy($("restore-button"), busy, source === "restore" ? "正在恢复..." : "恢复上一版");
  setButtonBusy($("export-markdown"), busy, source === "export" ? "导出中..." : "导出 Markdown");
  setButtonBusy($("export-html"), busy, source === "export" ? "导出中..." : "导出 HTML");
  setButtonBusy($("export-pdf"), busy, source === "export" ? "导出中..." : "导出 PDF");
  setButtonBusy($("edit-submit"), busy, source === "edit" ? "提交中..." : "提交修改");
  setButtonBusy($("adopt-button"), busy, source === "adopt" ? "提交中..." : ($("adopt-button").disabled ? "已采纳此行程" : "采纳此行程"));
  setButtonBusy($("feedback-submit"), busy, source === "feedback" ? "提交中..." : "提交反馈");

  if (!busy && currentProjectData?.evaluation?.is_adopted) {
    $("adopt-button").disabled = true;
    $("adopt-button").textContent = "已采纳此行程";
  }
}

async function submitEdit(event) {
  event.preventDefault();
  if (detailBusy) return;

  const editRequest = $("edit-request").value.trim();
  if (!editRequest) {
    setStatus("action-status", "修改要求不能为空。", "error");
    return;
  }

  setDetailBusy(true, "edit");
  setStatus("action-status", "正在根据你的要求修改行程...");

  try {
    const result = await api.post("/api/trips/edit", {
      project_filepath: currentProjectFilepath,
      edit_request: editRequest,
    });
    currentProjectFilepath = result.project_filepath;
    currentProjectData = result.project_data;
    $("edit-request").value = "";
    renderDetail(currentProjectData);
    setStatus("action-status", result.message || "行程修改成功。", "success");
  } catch (error) {
    setStatus("action-status", error.message || "修改失败，请稍后再试。", "error");
  } finally {
    setDetailBusy(false);
  }
}

async function restorePreviousVersion() {
  if (detailBusy) return;

  setDetailBusy(true, "restore");
  setStatus("action-status", "正在恢复上一版行程...");

  try {
    const result = await api.post("/api/trips/restore", {
      project_filepath: currentProjectFilepath,
    });

    if (!result.success) {
      setStatus("action-status", result.message || "恢复失败。", "error");
      return;
    }

    currentProjectFilepath = result.project_filepath;
    currentProjectData = result.project_data;
    renderDetail(currentProjectData);
    setStatus("action-status", result.message || "已恢复上一版。", "success");
  } catch (error) {
    setStatus("action-status", error.message || "恢复失败，请稍后再试。", "error");
  } finally {
    setDetailBusy(false);
  }
}

async function exportTrip(exportType) {
  if (detailBusy) return;

  setDetailBusy(true, "export");
  setStatus("action-status", `正在导出 ${exportType.toUpperCase()} 文件...`);

  try {
    const result = await api.post("/api/trips/export", {
      project_filepath: currentProjectFilepath,
      export_type: exportType,
    });

    currentProjectData = result.project_data;
    renderDetail(currentProjectData);

    const downloadUrl = result.download_url;
    const message = downloadUrl
      ? `导出成功，已生成 ${exportType.toUpperCase()} 文件，可直接下载。`
      : `导出成功，文件路径：${result.export?.filepath || "未返回路径"}`;

    setStatus("action-status", message, "success");

    $("latest-export-feedback").innerHTML = `
      <div class="notice success">
        <strong>${escapeHtml(exportType.toUpperCase())} 导出完成</strong>
        <div style="margin-top: 6px;">${escapeHtml(result.export?.filepath || "未返回文件路径")}</div>
        ${
          downloadUrl
            ? `<div style="margin-top: 10px;"><a class="button secondary" href="${escapeHtml(downloadUrl)}" target="_blank" rel="noopener noreferrer">下载最新导出文件</a></div>`
            : ""
        }
      </div>
    `;
  } catch (error) {
    setStatus("action-status", error.message || "导出失败，请稍后再试。", "error");
    $("latest-export-feedback").innerHTML = "";
  } finally {
    setDetailBusy(false);
  }
}

async function adoptCurrentTrip() {
  if (detailBusy) return;

  setDetailBusy(true, "adopt");

  try {
    const result = await api.post("/api/trips/adopt", {
      project_filepath: currentProjectFilepath,
    });
    currentProjectData = result.project_data;
    renderDetail(currentProjectData);
    setStatus("feedback-status", result.message || "已采纳此行程。", "success");
  } catch (error) {
    setStatus("feedback-status", error.message || "采纳失败，请稍后再试。", "error");
  } finally {
    setDetailBusy(false);
  }
}

async function submitFeedback(event) {
  event.preventDefault();
  if (detailBusy) return;

  const scoreValue = $("feedback-score").value;
  const feedbackText = $("feedback-text").value.trim();

  if (!scoreValue && !feedbackText) {
    setStatus("feedback-status", "请至少填写评分或文字反馈。", "error");
    return;
  }

  setDetailBusy(true, "feedback");

  try {
    const result = await api.post("/api/trips/feedback", {
      project_filepath: currentProjectFilepath,
      score: scoreValue ? Number(scoreValue) : null,
      feedback: feedbackText,
    });
    currentProjectData = result.project_data;
    renderDetail(currentProjectData);
    setStatus("feedback-status", result.message || "反馈提交成功。", "success");
  } catch (error) {
    setStatus("feedback-status", error.message || "反馈提交失败，请稍后再试。", "error");
  } finally {
    setDetailBusy(false);
  }
}

async function openMemoryDrawer() {
  $("drawer-backdrop").classList.add("open");
  $("memory-drawer").classList.add("open");
  $("memory-text").textContent = "";
  $("version-history").innerHTML = createLoadingSkeleton(3);
  $("memory-error").hidden = true;
  $("memory-error").innerHTML = "";

  try {
    const result = await api.get(`/api/trips/memory?project_filepath=${encodeURIComponent(currentProjectFilepath)}`);
    $("memory-text").textContent = result.memory_text || "暂无记忆。";
    $("version-history").innerHTML = (result.version_history || []).map((item) => `
      <div class="list-item">
        <strong>版本 ${escapeHtml(item.version_id || "")}</strong>
        <div class="muted">${escapeHtml(item.action || "")} · ${escapeHtml(item.summary || "")}</div>
        <div class="muted">${escapeHtml(item.created_at || "")}</div>
      </div>
    `).join("") || createEmptyState("暂无版本历史", "当前项目还没有历史版本记录。");
  } catch (error) {
    $("memory-error").innerHTML = createErrorState(
      "记忆读取失败",
      error.message || "暂时无法读取当前记忆。"
    );
    $("memory-error").hidden = false;
    $("version-history").innerHTML = "";
  }
}

function closeMemoryDrawer() {
  $("drawer-backdrop").classList.remove("open");
  $("memory-drawer").classList.remove("open");
}
