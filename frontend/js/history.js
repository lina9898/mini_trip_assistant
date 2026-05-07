document.addEventListener("DOMContentLoaded", async () => {
  const summaryEl = $("history-summary");
  const listEl = $("history-list");

  summaryEl.innerHTML = createLoadingSkeleton(2);
  listEl.innerHTML = `
    <div class="timeline-group">${createCardSkeleton()}</div>
    <div class="timeline-group">${createCardSkeleton()}</div>
  `;

  try {
    const result = await api.get("/api/trips");
    const groups = result.projects || [];
    const summary = result.summary || {};

    summaryEl.innerHTML = `
      <span class="tag">共 ${escapeHtml(summary.project_count ?? 0)} 个旅行项目</span>
      <span class="tag">共 ${escapeHtml(summary.snapshot_count ?? 0)} 个快照</span>
    `;

    if (!groups.length) {
      listEl.innerHTML = createEmptyState(
        "还没有历史项目",
        "先回到首页生成一个行程，历史快照就会出现在这里。"
      );
      return;
    }

    listEl.innerHTML = groups.map(renderProjectGroup).join("");

    listEl.querySelectorAll("button[data-path]").forEach((button) => {
      button.addEventListener("click", () => {
        goToDetail(button.dataset.path);
      });
    });
  } catch (error) {
    summaryEl.innerHTML = "";
    listEl.innerHTML = createErrorState(
      "历史项目读取失败",
      error.message || "暂时无法读取历史项目，请稍后再试。",
      '<a class="button secondary" href="/history">重新加载</a>'
    );
  }
});

function renderProjectGroup(group) {
  const travelDates = group.travel_dates || {};
  const snapshots = group.snapshots || [];

  return `
    <section class="timeline-group">
      <div class="timeline-group-head">
        <div>
          <h2>${escapeHtml(group.destination || "未知目的地")}</h2>
          <p>
            ${escapeHtml(travelDates.start_date || "未知日期")}
            至
            ${escapeHtml(travelDates.end_date || "未知日期")}
          </p>
        </div>
        <div class="timeline-group-meta">
          <span class="tag">最新版本 v${escapeHtml(group.latest_snapshot_version ?? 1)}</span>
          <span class="tag">${escapeHtml(group.snapshot_count ?? snapshots.length)} 个快照</span>
          <span class="tag">最近更新 ${escapeHtml(group.updated_at || "未知")}</span>
        </div>
      </div>
      <div class="timeline-list">
        ${snapshots.map((snapshot, index) => renderSnapshotItem(snapshot, index === snapshots.length - 1)).join("")}
      </div>
    </section>
  `;
}

function renderSnapshotItem(snapshot, isLatest) {
  return `
    <article class="timeline-item ${isLatest ? "latest" : ""}">
      <div class="timeline-dot"></div>
      <div class="timeline-card">
        <div class="section-head">
          <div>
            <h3>快照 v${escapeHtml(snapshot.snapshot_version ?? 1)}</h3>
            <div class="muted">
              创建于 ${escapeHtml(snapshot.created_at || "未知")} · 更新于 ${escapeHtml(snapshot.updated_at || snapshot.modified_time || "未知")}
            </div>
          </div>
          <div class="action-row">
            ${isLatest ? '<span class="pill clean">当前最新</span>' : ""}
            <button class="button secondary" data-path="${escapeHtml(snapshot.project_filepath || snapshot.filepath || "")}">查看详情</button>
          </div>
        </div>
        <div class="tag-row">
          <span class="tag">${escapeHtml(String(snapshot.days || "未知"))} 天</span>
          <span class="tag">${escapeHtml(String(snapshot.people || "未知"))} 人</span>
          <span class="tag">${snapshot.dirty ? "有未保存修改" : "已保存"}</span>
        </div>
        <div class="path-text">${escapeHtml(snapshot.project_filepath || snapshot.filepath || "")}</div>
      </div>
    </article>
  `;
}
