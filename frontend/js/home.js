document.addEventListener("DOMContentLoaded", () => {
  const form = $("trip-form");
  const generateButton = $("generate-button");
  const historyButton = $("history-button");

  historyButton.addEventListener("click", () => {
    window.location.href = "/history";
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = {
      origin: $("origin").value.trim(),
      destination: $("destination").value.trim(),
      start_date: $("start_date").value.trim(),
      days: Number($("days").value),
      people: Number($("people").value),
      preference: $("preference").value.trim(),
      pace: $("pace").value,
      budget_level: $("budget_level").value,
    };

    const validationMessage = validateGeneratePayload(payload);
    if (validationMessage) {
      setStatus("form-status", validationMessage, "error");
      return;
    }

    setButtonBusy(generateButton, true, "正在生成...");
    setStatus("form-status", "正在生成行程，这一步会调用多个工具和大模型，请稍等。");

    try {
      const result = await api.post("/api/trips/generate", payload);
      setStatus("form-status", "行程生成成功，正在进入详情页。", "success");
      goToDetail(result.project_filepath);
    } catch (error) {
      setStatus("form-status", error.message || "生成失败，请稍后再试。", "error");
    } finally {
      setButtonBusy(generateButton, false);
    }
  });
});

function validateGeneratePayload(payload) {
  if (!payload.origin) return "请填写出发地。";
  if (!payload.destination) return "请填写目的地。";
  if (!payload.start_date) return "请选择计划出行日期。";
  if (!payload.preference) return "请填写旅行偏好。";
  if (!payload.days || payload.days < 1) return "旅行天数至少为 1 天。";
  if (!payload.people || payload.people < 1) return "出行人数至少为 1 人。";
  return "";
}
