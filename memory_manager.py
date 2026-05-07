# memory_manager.py

import copy
from datetime import datetime


def current_time_string():
    """
    返回当前时间字符串。
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_memory_fields(project_data):
    """
    确保 project_data 中存在 memory 和 version_history 字段。
    """
    if "memory" not in project_data or not isinstance(project_data.get("memory"), dict):
        project_data["memory"] = {
            "constraints": [],
            "avoid_places": [],
            "preferences": []
        }

    if "constraints" not in project_data["memory"]:
        project_data["memory"]["constraints"] = []

    if "avoid_places" not in project_data["memory"]:
        project_data["memory"]["avoid_places"] = []

    if "preferences" not in project_data["memory"]:
        project_data["memory"]["preferences"] = []

    if "version_history" not in project_data or not isinstance(project_data.get("version_history"), list):
        project_data["version_history"] = []

    return project_data


def add_unique_item(items, value):
    """
    向列表中添加不重复内容。
    """
    value = str(value).strip()

    if not value:
        return items

    if value not in items:
        items.append(value)

    return items


def add_version(project_data, action, summary):
    """
    将当前 trip_data 保存为一个历史版本。
    """
    project_data = ensure_memory_fields(project_data)
    trip_data = project_data.get("trip_data", {})
    version_history = project_data["version_history"]
    next_version_id = len(version_history) + 1

    version = {
        "version_id": next_version_id,
        "action": action,
        "summary": summary,
        "trip_data": copy.deepcopy(trip_data),
        "created_at": current_time_string()
    }

    version_history.append(version)
    return project_data


def restore_previous_version(project_data):
    """
    恢复上一版行程。
    """
    project_data = ensure_memory_fields(project_data)
    version_history = project_data.get("version_history", [])

    if len(version_history) < 2:
        return project_data, {
            "success": False,
            "message": "当前没有可恢复的上一版。"
        }

    previous_version = version_history[-2]
    project_data["trip_data"] = copy.deepcopy(previous_version["trip_data"])

    project_data = add_version(
        project_data=project_data,
        action="restore_previous",
        summary=f"恢复到版本 {previous_version['version_id']}：{previous_version.get('summary', '')}"
    )

    return project_data, {
        "success": True,
        "message": f"已恢复到上一版：版本 {previous_version['version_id']}",
        "version": previous_version
    }


def add_constraint(project_data, constraint):
    """
    添加用户持续约束。
    """
    project_data = ensure_memory_fields(project_data)
    project_data["memory"]["constraints"] = add_unique_item(
        project_data["memory"]["constraints"],
        constraint
    )
    return project_data


def add_avoid_place(project_data, place):
    """
    添加用户明确不想去的地点。
    """
    project_data = ensure_memory_fields(project_data)
    project_data["memory"]["avoid_places"] = add_unique_item(
        project_data["memory"]["avoid_places"],
        place
    )
    return project_data


def add_preference(project_data, preference):
    """
    添加用户偏好。
    """
    project_data = ensure_memory_fields(project_data)
    project_data["memory"]["preferences"] = add_unique_item(
        project_data["memory"]["preferences"],
        preference
    )
    return project_data


def split_place_text(place_text):
    """
    将一段地点文本拆成多个地点。
    例如：外滩和南京路 -> ["外滩", "南京路"]
    """
    separators = ["、", "，", ",", "和", "与", "及", "以及"]
    places = [place_text]

    for separator in separators:
        new_places = []
        for item in places:
            new_places.extend(item.split(separator))
        places = new_places

    cleaned = []

    for place in places:
        place = place.strip()

        for tail in ["这些地方", "这几个地方", "附近", "一带"]:
            place = place.replace(tail, "").strip()

        if place and len(place) <= 12:
            cleaned.append(place)

    return cleaned


def clean_after_negative_keyword(text):
    """
    从否定关键词后的文本中截取可能的地点片段。
    """
    for separator in ["。", "！", "!", ".", "；", ";"]:
        if separator in text:
            text = text.split(separator, 1)[0].strip()

    for tail in ["换成", "改成", "安排", "推荐"]:
        if tail in text:
            text = text.split(tail, 1)[0].strip()

    return text.strip(" ，,、")


def extract_memory_from_edit_request(project_data, user_edit_request):
    """
    从用户修改要求中提取简单记忆。
    当前先用规则法，后续可以升级为 LLM 提取。
    """
    text = user_edit_request.strip()

    if not text:
        return project_data

    project_data = ensure_memory_fields(project_data)

    negative_keywords = ["不去", "不要去", "别去", "避开", "不要安排", "不想去"]

    for keyword in negative_keywords:
        if keyword in text:
            project_data = add_constraint(project_data, text)
            after_text = text.split(keyword, 1)[1].strip()
            after_text = clean_after_negative_keyword(after_text)

            for place in split_place_text(after_text):
                project_data = add_avoid_place(project_data, place)

            return project_data

    positive_keywords = ["喜欢", "想多安排", "偏好", "更想要"]

    for keyword in positive_keywords:
        if keyword in text:
            project_data = add_preference(project_data, text)
            return project_data

    if "轻松" in text or "不要太累" in text or "少走路" in text:
        project_data = add_constraint(project_data, text)

    return project_data


def get_memory_text(project_data):
    """
    将项目记忆整理成可放入 Prompt 的文本。
    """
    project_data = ensure_memory_fields(project_data)
    memory = project_data.get("memory", {})

    constraints = memory.get("constraints", [])
    avoid_places = memory.get("avoid_places", [])
    preferences = memory.get("preferences", [])

    lines = []

    lines.append("【用户持续约束】")
    if constraints:
        for item in constraints:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无")

    lines.append("")
    lines.append("【明确避免地点】")
    if avoid_places:
        for item in avoid_places:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无")

    lines.append("")
    lines.append("【用户偏好记忆】")
    if preferences:
        for item in preferences:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无")

    return "\n".join(lines)


def get_version_history_text(project_data):
    """
    将行程版本历史整理成文本。
    """
    project_data = ensure_memory_fields(project_data)
    version_history = project_data.get("version_history", [])

    lines = ["【行程版本历史】"]

    if not version_history:
        lines.append("- 暂无版本历史")
        return "\n".join(lines)

    for version in version_history:
        version_id = version.get("version_id")
        action = version.get("action", "")
        summary = version.get("summary", "")
        created_at = version.get("created_at", "")

        lines.append(f"- 版本 {version_id}｜{action}｜{summary}｜{created_at}")

    return "\n".join(lines)


def get_snapshot_status_text(project_data):
    """
    展示当前项目快照状态。
    """
    snapshot_version = project_data.get("snapshot_version", 1)
    dirty = project_data.get("dirty", False)
    project_filepath = project_data.get("project_filepath") or "尚未保存"
    dirty_text = "是" if dirty else "否"

    lines = [
        "【当前项目快照】",
        f"- 当前快照版本：v{snapshot_version}",
        f"- 是否有未保存修改：{dirty_text}",
        f"- 当前快照文件：{project_filepath}"
    ]

    return "\n".join(lines)


def print_memory(project_data):
    """
    打印当前项目记忆、快照状态和版本历史。
    """
    project_data = ensure_memory_fields(project_data)

    print()
    print("当前项目记忆")
    print("-" * 60)
    print(get_memory_text(project_data))

    print()
    print(get_snapshot_status_text(project_data))

    print()
    print(get_version_history_text(project_data))
