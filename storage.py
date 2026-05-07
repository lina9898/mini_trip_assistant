# storage.py

import json
import os
from datetime import datetime

from evaluation_manager import ensure_evaluation_fields, init_evaluation, update_project_evaluation


SAVE_DIR = "saved_trips"


def ensure_save_dir():
    """
    确保保存行程的文件夹存在。
    """
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)


def current_time_string():
    """
    返回当前时间字符串。
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def current_timestamp():
    """
    返回适合文件名使用的时间戳。
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def safe_filename(text):
    """
    处理文件名中的特殊字符。
    """
    text = str(text)
    text = text.replace("/", "_")
    text = text.replace("\\", "_")
    text = text.replace(" ", "_")
    text = text.replace(":", "_")

    return text


def build_project_id():
    """
    生成项目 ID。
    """
    return f"trip_{current_timestamp()}"


def build_project_filename(project_data):
    """
    根据目的地和项目 ID 生成文件名。
    """
    trip_data = project_data.get("trip_data", {})
    destination = trip_data.get("destination", "未知目的地")
    project_id = project_data.get("project_id", build_project_id())

    return f"{safe_filename(destination)}_{project_id}.json"


def build_project_data(
    trip_data,
    budget=None,
    location_info=None,
    weather_info=None,
    poi_info=None,
    route_info=None,
    hotel_info=None,
    transport_info=None,
    event_info=None,
    opening_hours_info=None,
    image_info=None,
    tool_plan=None,
    execution_logs=None,
    memory=None,
    version_history=None,
    travel_dates=None,
    evaluation=None,
    project_id=None,
    created_at=None
):
    """
    构造完整旅行项目数据。
    """
    now = current_time_string()
    base_project_id = project_id or build_project_id()

    return {
        "project_id": base_project_id,
        "base_project_id": base_project_id,
        "snapshot_version": 1,
        "project_filepath": None,
        "dirty": True,
        "snapshot_saved_after_edit": False,
        "trip_data": trip_data or {},
        "travel_dates": travel_dates or {},
        "budget": budget or {},
        "location_info": location_info or {},
        "weather_info": weather_info or {},
        "poi_info": poi_info or {},
        "route_info": route_info or {},
        "hotel_info": hotel_info or {},
        "transport_info": transport_info or {},
        "event_info": event_info or {},
        "opening_hours_info": opening_hours_info or {},
        "image_info": image_info or {},
        "tool_plan": tool_plan or {},
        "execution_logs": execution_logs or [],
        "memory": memory or {
            "constraints": [],
            "avoid_places": [],
            "preferences": []
        },
        "version_history": version_history or [],
        "export_history": [],
        "evaluation": evaluation or init_evaluation(),
        "created_at": created_at or now,
        "updated_at": now
    }


def save_project(project_data):
    """
    保存完整旅行项目。

    保存策略：
    1. 首次保存：生成 v1
    2. 修改后第一次保存：生成新快照 v2 / v3 / ...
    3. 当前修改版本已经保存过：覆盖当前快照
    4. 未修改项目保存：覆盖当前快照
    """
    ensure_save_dir()

    project_data = ensure_snapshot_fields(project_data)

    project_filepath = project_data.get("project_filepath")
    dirty = project_data.get("dirty", True)
    snapshot_saved_after_edit = project_data.get("snapshot_saved_after_edit", False)

    if not project_filepath:
        project_data["snapshot_version"] = project_data.get("snapshot_version", 1) or 1
        return save_project_snapshot(project_data)

    if dirty and not snapshot_saved_after_edit:
        project_data["snapshot_version"] = project_data.get("snapshot_version", 1) + 1
        project_data["project_filepath"] = None
        return save_project_snapshot(project_data)

    return save_project_snapshot(project_data)


def build_snapshot_filename(project_data):
    """
    根据目的地、项目 ID 和快照版本号生成文件名。
    例如：上海_trip_20260428_001_v1.json
    """
    trip_data = project_data.get("trip_data", {})
    destination = trip_data.get("destination", "未知目的地")

    base_project_id = (
        project_data.get("base_project_id")
        or project_data.get("project_id")
        or build_project_id()
    )
    snapshot_version = project_data.get("snapshot_version", 1)

    return f"{safe_filename(destination)}_{base_project_id}_v{snapshot_version}.json"


def save_project_snapshot(project_data, update_timestamp=True):
    """
    保存当前项目快照。
    """
    ensure_save_dir()

    project_data = ensure_snapshot_fields(project_data)
    if update_timestamp:
        project_data["updated_at"] = current_time_string()

    filename = build_snapshot_filename(project_data)
    filepath = os.path.join(SAVE_DIR, filename)

    project_data["project_filepath"] = filepath
    project_data["dirty"] = False
    project_data["snapshot_saved_after_edit"] = True

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(project_data, file, ensure_ascii=False, indent=2)

    return filepath


def ensure_snapshot_fields(project_data):
    """
    确保项目中存在快照保存相关字段。
    用于兼容旧版本项目文件。
    """
    if "base_project_id" not in project_data:
        project_data["base_project_id"] = project_data.get("project_id") or build_project_id()

    if "project_id" not in project_data:
        project_data["project_id"] = project_data["base_project_id"]

    if "snapshot_version" not in project_data:
        project_data["snapshot_version"] = 1

    if "project_filepath" not in project_data:
        project_data["project_filepath"] = None

    if "dirty" not in project_data:
        project_data["dirty"] = False

    if "snapshot_saved_after_edit" not in project_data:
        project_data["snapshot_saved_after_edit"] = True

    if "export_history" not in project_data:
        project_data["export_history"] = []

    return project_data


def mark_project_dirty(project_data):
    """
    标记项目存在未保存修改。
    """
    project_data = ensure_snapshot_fields(project_data)

    project_data["dirty"] = True
    project_data["snapshot_saved_after_edit"] = False
    project_data["updated_at"] = current_time_string()

    return project_data


def ensure_project_saved(project_data):
    """
    确保项目已经保存。

    导出前调用：
    - 如果项目未保存，生成 v1
    - 如果项目已修改，生成新快照
    - 如果项目未修改，覆盖当前快照
    """
    project_data = ensure_snapshot_fields(project_data)

    before_filepath = project_data.get("project_filepath")
    before_version = project_data.get("snapshot_version")
    dirty = project_data.get("dirty", True)

    filepath = save_project(project_data)

    filepath = project_data.get("project_filepath")
    after_version = project_data.get("snapshot_version")

    created_new_snapshot = (
        before_filepath != filepath
        or before_version != after_version
        or dirty
    )

    return filepath, created_new_snapshot


def record_export_history(project_data, export_type, filepath):
    """
    记录导出历史。

    注意：
    记录导出历史属于当前快照的元数据更新，
    不应该触发新的项目快照。
    """
    project_data = ensure_snapshot_fields(project_data)

    if "export_history" not in project_data or not isinstance(project_data.get("export_history"), list):
        project_data["export_history"] = []

    project_data["export_history"].append({
        "type": export_type,
        "filepath": filepath,
        "created_at": current_time_string(),
        "snapshot_version": project_data.get("snapshot_version")
    })

    project_data["dirty"] = True
    project_data["updated_at"] = current_time_string()

    return project_data


def build_saved_project_summary(data, filepath, filename, modified_time):
    """
    将项目数据整理为历史列表所需的摘要信息。
    """
    trip_data = data.get("trip_data", data if isinstance(data, dict) else {})
    travel_dates = data.get("travel_dates", {}) if isinstance(data, dict) else {}

    if not travel_dates and isinstance(trip_data, dict):
        travel_dates = trip_data.get("travel_dates", {}) or {}

    start_date = (
        travel_dates.get("start_date")
        or trip_data.get("start_date")
        or "未知"
    )
    end_date = (
        travel_dates.get("end_date")
        or trip_data.get("end_date")
        or "未知"
    )

    base_project_id = data.get("base_project_id") or data.get("project_id") or filename
    snapshot_version = data.get("snapshot_version", 1) or 1
    updated_at = data.get("updated_at", "未知")
    created_at = data.get("created_at", "未知")

    return {
        "filename": filename,
        "filepath": filepath,
        "project_filepath": filepath,
        "project_id": data.get("project_id", base_project_id),
        "base_project_id": base_project_id,
        "snapshot_version": snapshot_version,
        "dirty": data.get("dirty", False),
        "destination": trip_data.get("destination", "未知目的地"),
        "origin": trip_data.get("origin", "未填写"),
        "days": trip_data.get("days", travel_dates.get("days", "未知")),
        "people": trip_data.get("people", "未知"),
        "created_at": created_at,
        "updated_at": updated_at,
        "modified_time": modified_time,
        "travel_dates": {
            "start_date": start_date,
            "end_date": end_date,
            "days": travel_dates.get("days", trip_data.get("days"))
        }
    }


def list_saved_projects():
    """
    列出 saved_trips 文件夹下所有项目 JSON 文件。
    """
    ensure_save_dir()
    files = []

    for filename in os.listdir(SAVE_DIR):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(SAVE_DIR, filename)
        modified_time = datetime.fromtimestamp(
            os.path.getmtime(filepath)
        ).strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict) and "trip_data" in data:
                data = ensure_snapshot_fields(data)

            files.append(
                build_saved_project_summary(
                    data=data if isinstance(data, dict) else {},
                    filepath=filepath,
                    filename=filename,
                    modified_time=modified_time
                )
            )

        except Exception:
            files.append({
                "filename": filename,
                "filepath": filepath,
                "project_filepath": filepath,
                "project_id": filename,
                "base_project_id": filename,
                "snapshot_version": 1,
                "dirty": False,
                "destination": "读取失败",
                "origin": "未知",
                "days": "未知",
                "people": "未知",
                "created_at": "未知",
                "updated_at": "未知",
                "modified_time": modified_time,
                "travel_dates": {
                    "start_date": "未知",
                    "end_date": "未知",
                    "days": "未知"
                }
            })

    files.sort(key=lambda item: item["modified_time"], reverse=True)
    return files


def load_project(filepath):
    """
    读取完整旅行项目。
    兼容旧版本只保存 trip_data 的 JSON 文件。
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在：{filepath}")

    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)

    if "trip_data" in data:
        data = ensure_snapshot_fields(data)
        data = ensure_evaluation_fields(data)
        data["project_filepath"] = filepath
        data["dirty"] = False
        data["snapshot_saved_after_edit"] = True

        if "travel_dates" not in data:
            trip_data = data.get("trip_data", {})
            data["travel_dates"] = trip_data.get("travel_dates", {})
            if not data["travel_dates"] and trip_data.get("start_date"):
                data["travel_dates"] = {
                    "start_date": trip_data.get("start_date"),
                    "end_date": trip_data.get("end_date"),
                    "days": trip_data.get("days")
                }
        if "export_history" not in data:
            data["export_history"] = []
        if "poi_info" not in data:
            data["poi_info"] = {
                "tool_name": "poi_tool",
                "success": False,
                "error": "该项目未保存 POI 信息。",
                "pois": []
            }
        if "route_info" not in data:
            data["route_info"] = {
                "tool_name": "route_tool",
                "success": False,
                "error": "该项目未保存路线距离信息。",
                "routes": []
            }
        if "image_info" not in data:
            data["image_info"] = {
                "tool_name": "image_tool",
                "success": False,
                "error": "该项目未保存图片信息。",
                "photos": []
            }
        if "hotel_info" not in data:
            data["hotel_info"] = {
                "tool_name": "hotel_tool",
                "success": False,
                "error": "旧版项目未保存酒店选址信息。",
                "hotel_candidates": [],
                "reference_places": []
            }
        if "transport_info" not in data:
            data["transport_info"] = {
                "tool_name": "transport_tool",
                "success": False,
                "error": "旧版项目未保存城际交通信息。"
            }
        if "opening_hours_info" not in data:
            data["opening_hours_info"] = {
                "tool_name": "opening_hours_tool",
                "success": False,
                "error": "旧版项目未保存开放时间检查信息。",
                "checks": []
            }
        if "event_info" not in data:
            data["event_info"] = {
                "tool_name": "event_tool",
                "success": False,
                "error": "旧版项目未保存城市活动信息。",
                "events": []
            }
        if "memory" not in data or not isinstance(data.get("memory"), dict):
            data["memory"] = {
                "constraints": [],
                "avoid_places": [],
                "preferences": []
            }

        if "constraints" not in data["memory"]:
            data["memory"]["constraints"] = []

        if "avoid_places" not in data["memory"]:
            data["memory"]["avoid_places"] = []

        if "preferences" not in data["memory"]:
            data["memory"]["preferences"] = []

        if "version_history" not in data or not isinstance(data.get("version_history"), list):
            data["version_history"] = []
        data = update_project_evaluation(data)
        return data

    project_data = build_project_data(
        trip_data=data,
        budget={
            "tool_name": "budget_tool",
            "success": False,
            "error": "旧版行程文件未保存预算信息。"
        },
        location_info={
            "tool_name": "map_tool",
            "success": False,
            "error": "旧版行程文件未保存地图信息。"
        },
        weather_info={
            "tool_name": "weather_tool",
            "success": False,
            "error": "旧版行程文件未保存天气信息。"
        },
        poi_info={
            "tool_name": "poi_tool",
            "success": False,
            "error": "旧版行程文件未保存 POI 信息。",
            "pois": []
        },
        route_info={
            "tool_name": "route_tool",
            "success": False,
            "error": "旧版行程文件未保存路线距离信息。",
            "routes": []
        },
        hotel_info={
            "tool_name": "hotel_tool",
            "success": False,
            "error": "旧版行程文件未保存酒店选址信息。",
            "hotel_candidates": [],
            "reference_places": []
        },
        transport_info={
            "tool_name": "transport_tool",
            "success": False,
            "error": "旧版行程文件未保存城际交通信息。"
        },
        event_info={
            "tool_name": "event_tool",
            "success": False,
            "error": "旧版项目未保存城市活动信息。",
            "events": []
        },
        opening_hours_info={
            "tool_name": "opening_hours_tool",
            "success": False,
            "error": "旧版项目未保存开放时间检查信息。",
            "checks": []
        },
        image_info={
            "tool_name": "image_tool",
            "success": False,
            "error": "旧版行程文件未保存图片信息。",
            "photos": []
        },
        tool_plan={},
        execution_logs=[],
        travel_dates=data.get("travel_dates", {}),
        evaluation=init_evaluation()
    )

    project_data["project_filepath"] = filepath
    project_data["dirty"] = False
    project_data["snapshot_saved_after_edit"] = True
    project_data = update_project_evaluation(project_data)

    return project_data


def load_project_by_filepath(filepath):
    """
    根据文件路径读取项目。
    """
    return load_project(filepath)
