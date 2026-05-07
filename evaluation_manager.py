def init_evaluation():
    """
    初始化项目评估指标结构。
    """
    return {
        "edit_count": 0,
        "restore_count": 0,
        "reopen_count": 0,
        "export_count": 0,
        "export_types": [],
        "is_adopted": False,
        "satisfaction_score": None,
        "user_feedback": "",
        "generation_duration": None,
        "generation_error_count": 0,
        "memory_check": {
            "total_constraints": 0,
            "hit_count": 0,
            "miss_count": 0,
            "hit_rate": None
        },
        "image_match": {
            "total_images": 0,
            "matched_images": 0,
            "accuracy": None
        },
        "tool_metrics": {
            "total_tools": 0,
            "success_tools": 0,
            "failed_tools": 0,
            "success_rate": None
        },
        "risk_metrics": {
            "opening_hours_high_risk": 0,
            "opening_hours_medium_risk": 0,
            "route_faraway_count": 0,
            "hotel_faraway_count": 0,
            "weather_out_of_range": False
        }
    }


def ensure_evaluation_fields(project_data):
    """
    确保项目中存在完整的评估字段。
    """
    evaluation = project_data.get("evaluation")

    if not isinstance(evaluation, dict):
        project_data["evaluation"] = init_evaluation()
        return project_data

    defaults = init_evaluation()

    for key, value in defaults.items():
        if isinstance(value, dict):
            if not isinstance(evaluation.get(key), dict):
                evaluation[key] = value
                continue

            for sub_key, sub_value in value.items():
                if sub_key not in evaluation[key]:
                    evaluation[key][sub_key] = sub_value
        elif key not in evaluation:
            evaluation[key] = value

    return project_data


def build_trip_text(trip_data):
    """
    将行程文本拼接为可检索的字符串。
    """
    if not isinstance(trip_data, dict):
        return ""

    parts = [
        str(trip_data.get("destination", "")),
        str(trip_data.get("route_strategy", "")),
        str(trip_data.get("advice", "")),
        str(trip_data.get("backup_plan", "")),
        str(trip_data.get("hotel_advice", "")),
        str(trip_data.get("intercity_transport_advice", "")),
        str(trip_data.get("event_advice", "")),
        str(trip_data.get("weather_adjustment", "")),
    ]

    for day_plan in trip_data.get("plan", []):
        parts.extend([
            str(day_plan.get("morning", "")),
            str(day_plan.get("afternoon", "")),
            str(day_plan.get("evening", "")),
            str(day_plan.get("note", "")),
            str(day_plan.get("reason", "")),
        ])

    return "\n".join(parts)


def calculate_memory_hit_rate(project_data):
    """
    评估记忆约束命中率。
    """
    memory = project_data.get("memory", {}) or {}
    trip_data = project_data.get("trip_data", {}) or {}
    trip_text = build_trip_text(trip_data)

    avoid_places = [str(item).strip() for item in memory.get("avoid_places", []) if str(item).strip()]
    constraints = [str(item).strip() for item in memory.get("constraints", []) if str(item).strip()]

    supported_constraints = []
    for item in constraints:
        if any(keyword in item for keyword in ["轻松", "不要太累", "少走路", "别太赶", "不要太赶"]):
            supported_constraints.append(item)

    total_constraints = len(avoid_places) + len(supported_constraints)
    hit_count = 0
    miss_count = 0

    for place in avoid_places:
        if place not in trip_text:
            hit_count += 1
        else:
            miss_count += 1

    pace = str(trip_data.get("pace", "")).strip()
    for item in supported_constraints:
        if any(keyword in item for keyword in ["轻松", "不要太累", "少走路", "别太赶", "不要太赶"]):
            if pace in ["轻松", "适中"]:
                hit_count += 1
            else:
                miss_count += 1

    return {
        "total_constraints": total_constraints,
        "hit_count": hit_count,
        "miss_count": miss_count,
        "hit_rate": round(hit_count / total_constraints, 2) if total_constraints else None
    }


def calculate_image_match_accuracy(project_data):
    """
    评估图片与行程地点的匹配准确率。
    """
    image_info = project_data.get("image_info", {}) or {}
    day_images = image_info.get("day_images", []) or []

    total_images = 0
    matched_images = 0

    for day_item in day_images:
        for image in day_item.get("place_images", []) or []:
            total_images += 1
            place_name = str(image.get("place_name", "")).strip()
            matched_poi_name = str(image.get("matched_poi_name", "")).strip()
            source = str(image.get("source", "")).strip()

            if not place_name:
                continue

            if matched_poi_name and (
                place_name == matched_poi_name
                or place_name in matched_poi_name
                or matched_poi_name in place_name
            ):
                matched_images += 1
                continue

            if source == "amap_poi" and matched_poi_name:
                matched_images += 1

    return {
        "total_images": total_images,
        "matched_images": matched_images,
        "accuracy": round(matched_images / total_images, 2) if total_images else None
    }


def calculate_tool_success_rate(project_data):
    """
    评估工具调用成功率。
    """
    execution_logs = project_data.get("execution_logs", []) or []
    total_tools = len(execution_logs)
    success_tools = 0

    for log in execution_logs:
        result = log.get("result", {}) or {}
        if result.get("success", False):
            success_tools += 1

    failed_tools = total_tools - success_tools

    return {
        "total_tools": total_tools,
        "success_tools": success_tools,
        "failed_tools": failed_tools,
        "success_rate": round(success_tools / total_tools, 2) if total_tools else None
    }


def calculate_risk_metrics(project_data):
    """
    汇总风险识别指标。
    """
    opening_hours_info = project_data.get("opening_hours_info", {}) or {}
    route_info = project_data.get("route_info", {}) or {}
    weather_info = project_data.get("weather_info", {}) or {}
    hotel_info = project_data.get("hotel_info", {}) or {}

    checks = opening_hours_info.get("checks", []) or []
    opening_hours_high_risk = len([item for item in checks if item.get("risk_level") == "high"])
    opening_hours_medium_risk = len([item for item in checks if item.get("risk_level") == "medium"])

    route_faraway_count = route_info.get("faraway_count")
    if route_faraway_count is None:
        route_faraway_count = len([
            item for item in route_info.get("routes", []) or []
            if (item.get("distance_km") or 0) > 8
        ])

    hotel_faraway_count = len([
        item for item in hotel_info.get("hotel_candidates", []) or []
        if (item.get("avg_distance_km") or 0) > 8
    ])

    return {
        "opening_hours_high_risk": opening_hours_high_risk,
        "opening_hours_medium_risk": opening_hours_medium_risk,
        "route_faraway_count": route_faraway_count,
        "hotel_faraway_count": hotel_faraway_count,
        "weather_out_of_range": weather_info.get("mode") == "out_of_range"
    }


def update_project_evaluation(project_data):
    """
    刷新当前项目的自动评估指标。
    """
    project_data = ensure_evaluation_fields(project_data)
    evaluation = project_data["evaluation"]

    evaluation["memory_check"] = calculate_memory_hit_rate(project_data)
    evaluation["image_match"] = calculate_image_match_accuracy(project_data)
    evaluation["tool_metrics"] = calculate_tool_success_rate(project_data)
    evaluation["risk_metrics"] = calculate_risk_metrics(project_data)

    return project_data


def record_edit(project_data):
    project_data = ensure_evaluation_fields(project_data)
    project_data["evaluation"]["edit_count"] += 1
    return project_data


def record_restore(project_data):
    project_data = ensure_evaluation_fields(project_data)
    project_data["evaluation"]["restore_count"] += 1
    return project_data


def record_reopen(project_data):
    project_data = ensure_evaluation_fields(project_data)
    project_data["evaluation"]["reopen_count"] += 1
    return project_data


def record_export(project_data, export_type):
    project_data = ensure_evaluation_fields(project_data)
    evaluation = project_data["evaluation"]
    evaluation["export_count"] += 1

    if export_type and export_type not in evaluation["export_types"]:
        evaluation["export_types"].append(export_type)

    return project_data


def record_adoption(project_data, is_adopted=True):
    project_data = ensure_evaluation_fields(project_data)
    project_data["evaluation"]["is_adopted"] = bool(is_adopted)
    return project_data


def record_feedback(project_data, score=None, feedback=""):
    project_data = ensure_evaluation_fields(project_data)

    if score is not None:
        try:
            parsed_score = int(score)
        except (TypeError, ValueError) as exc:
            raise ValueError("满意度评分必须是 1 到 5 的整数") from exc

        if parsed_score < 1 or parsed_score > 5:
            raise ValueError("满意度评分必须在 1 到 5 之间")

        project_data["evaluation"]["satisfaction_score"] = parsed_score

    if feedback is not None:
        project_data["evaluation"]["user_feedback"] = str(feedback).strip()

    return project_data


def record_generation_duration(project_data, duration_seconds):
    project_data = ensure_evaluation_fields(project_data)

    if duration_seconds is None:
        project_data["evaluation"]["generation_duration"] = None
        return project_data

    project_data["evaluation"]["generation_duration"] = round(float(duration_seconds), 2)
    return project_data
