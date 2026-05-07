# trip_service.py

import time

from planner import generate_trip_plan
from templates import format_trip_plan
from tool_planner import plan_tool_calls
from tool_executor import execute_tool_plan
from tool_plan_validator import validate_tool_plan, repair_tool_plan
from itinerary_editor import edit_itinerary
from storage import (
    build_project_data,
    save_project,
    save_project_snapshot,
    list_saved_projects,
    load_project,
    mark_project_dirty,
    ensure_project_saved,
    record_export_history
)
from exporter import export_trip_to_markdown, export_trip_to_html, export_trip_to_pdf
from tools.image_tool import match_images_for_trip
from tools.opening_hours_tool import check_trip_opening_hours
from date_utils import build_travel_dates, calculate_day_date
from memory_manager import (
    ensure_memory_fields,
    add_version,
    restore_previous_version,
    extract_memory_from_edit_request,
    get_memory_text
)
from evaluation_manager import (
    record_adoption,
    record_edit,
    record_export,
    record_feedback,
    record_generation_duration,
    record_restore,
    update_project_evaluation,
)


def print_tool_plan(tool_plan):
    """
    打印工具调用计划，方便学习和调试。
    """
    print()
    print("工具调用计划：")
    print("-" * 60)

    tool_calls = tool_plan.get("tool_calls", [])

    if not tool_calls:
        print("暂无工具调用计划。")
        return

    for index, call in enumerate(tool_calls, start=1):
        print(f"{index}. 工具：{call.get('tool_name')}")
        print(f"   参数：{call.get('arguments')}")
        print(f"   原因：{call.get('reason')}")


def print_execution_logs(execution_logs):
    """
    打印工具执行日志，方便学习和调试。
    """
    print()
    print("工具执行日志：")
    print("-" * 60)

    for index, log in enumerate(execution_logs, start=1):
        print(f"{index}. 工具：{log.get('tool_name')}")
        print(f"   调用原因：{log.get('reason')}")
        print(f"   实际参数：{log.get('arguments')}")
        result = log.get("result", {})
        print(f"   执行状态：{result.get('success', '未提供状态')}")
        if not result.get("success", True):
            print(f"   错误信息：{result.get('error')}")


def print_project(project_data):
    """
    格式化展示当前旅行项目。
    """
    trip_data = project_data.get("trip_data", {})
    budget = project_data.get("budget", {})
    location_info = project_data.get("location_info", {})
    weather_info = project_data.get("weather_info", {})

    final_text = format_trip_plan(
        trip_data=trip_data,
        budget=budget,
        location_info=location_info,
        weather_info=weather_info
    )

    print()
    print(final_text)
    print_opening_hours_summary(project_data.get("opening_hours_info", {}))


def print_opening_hours_summary(opening_hours_info):
    """
    打印开放时间风险摘要。
    """
    if not opening_hours_info:
        return

    summary = opening_hours_info.get("summary", {})
    checks = opening_hours_info.get("checks", [])
    high_risks = [item for item in checks if item.get("risk_level") == "high"]
    medium_risks = [item for item in checks if item.get("risk_level") == "medium"]

    if not high_risks and not medium_risks:
        return

    print()
    print("开放时间风险提示")
    print("-" * 60)

    if high_risks:
        print("高风险：")
        for item in high_risks[:5]:
            print(
                f"- 第 {item.get('day')} 天 {item.get('period')}："
                f"{item.get('place_name')}｜{item.get('message')}"
            )

    if medium_risks:
        print("需确认：")
        for item in medium_risks[:5]:
            print(
                f"- 第 {item.get('day')} 天 {item.get('period')}："
                f"{item.get('place_name')}｜{item.get('message')}"
            )

    print(summary.get("suggestion", "建议出行前确认官方开放时间。"))


def create_project_by_requirements(requirements, verbose=False, display_result=False):
    """
    根据前端或命令行传入的 requirements 创建旅行项目。
    """
    generation_started_at = time.perf_counter()
    origin = requirements["origin"]
    destination = requirements["destination"]
    start_date = requirements["start_date"]
    days = requirements["days"]
    people = requirements["people"]
    preference = requirements["preference"]
    pace = requirements["pace"]
    budget_level = requirements["budget_level"]
    travel_dates = build_travel_dates(start_date=start_date, days=days)
    end_date = travel_dates["end_date"]

    if verbose:
        print()
        print("正在让大模型分析需要调用哪些工具...")
    tool_plan = plan_tool_calls(
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        days=days,
        preference=preference,
        pace=pace,
        budget_level=budget_level,
        people=people
    )

    if verbose:
        print_tool_plan(tool_plan)

    if verbose:
        print()
        print("正在校验大模型生成的工具调用计划...")
    validation_errors = validate_tool_plan(tool_plan)

    if verbose:
        if validation_errors:
            print("发现工具调用计划存在问题：")
            for error in validation_errors:
                print(f"- {error}")
        else:
            print("工具调用计划初步校验通过。")

    if verbose:
        print()
        print("正在修复和补全工具调用计划...")
    tool_plan = repair_tool_plan(
        tool_plan=tool_plan,
        destination=destination,
        days=days,
        budget_level=budget_level,
        people=people,
        preference=preference,
        start_date=start_date,
        end_date=end_date,
        origin=origin
    )

    if verbose:
        print_tool_plan(tool_plan)

    if verbose:
        print()
        print("正在再次校验修复后的工具调用计划...")
    validation_errors = validate_tool_plan(tool_plan)

    if verbose:
        if validation_errors:
            print("修复后的工具调用计划仍存在问题：")
            for error in validation_errors:
                print(f"- {error}")
            print("将继续执行可执行部分，但结果可能不完整。")
        else:
            print("修复后的工具调用计划校验通过。")

    if verbose:
        print()
        print("正在根据工具调用计划执行工具...")
    execution_result = execute_tool_plan(tool_plan)

    tool_results = execution_result["tool_results"]
    execution_logs = execution_result["execution_logs"]

    if verbose:
        print_execution_logs(execution_logs)

    location_info = tool_results.get("map_tool", {
        "tool_name": "map_tool",
        "success": False,
        "error": "未调用地图工具。"
    })

    weather_info = tool_results.get("weather_tool", {
        "tool_name": "weather_tool",
        "success": False,
        "error": "未调用天气工具。"
    })

    budget = tool_results.get("budget_tool", {
        "tool_name": "budget_tool",
        "success": False,
        "error": "未调用预算工具。",
        "people": people,
        "hotel": 0,
        "food": 0,
        "transport": 0,
        "ticket": 0,
        "single_person_total": 0,
        "total": 0
    })

    poi_info = tool_results.get("poi_tool", {
        "tool_name": "poi_tool",
        "success": False,
        "error": "未调用 POI 工具。",
        "pois": []
    })

    route_info = tool_results.get("route_tool", {
        "tool_name": "route_tool",
        "success": False,
        "error": "未调用路线距离工具。",
        "routes": []
    })

    hotel_info = tool_results.get("hotel_tool", {
        "tool_name": "hotel_tool",
        "success": False,
        "error": "未调用酒店选址工具。",
        "hotel_candidates": [],
        "reference_places": []
    })

    transport_info = tool_results.get("transport_tool", {
        "tool_name": "transport_tool",
        "success": False,
        "error": "未调用城际交通工具。",
        "origin": origin,
        "destination": destination
    })

    event_info = tool_results.get("event_tool", {
        "tool_name": "event_tool",
        "success": False,
        "error": "未调用城市活动工具。",
        "events": [],
        "summary": {
            "event_count": 0,
            "high_impact_count": 0,
            "suggestion": "暂无活动信息。"
        }
    })

    if verbose:
        print()
        print("正在调用大模型生成最终旅行计划...")
    trip_data = generate_trip_plan(
        origin=origin,
        destination=destination,
        start_date=start_date,
        travel_dates=travel_dates,
        days=days,
        preference=preference,
        pace=pace,
        budget_level=budget_level,
        people=people,
        location_info=location_info,
        weather_info=weather_info,
        budget=budget,
        poi_info=poi_info,
        route_info=route_info,
        hotel_info=hotel_info,
        transport_info=transport_info,
        event_info=event_info
    )

    trip_data.setdefault("origin", origin)
    trip_data.setdefault("start_date", travel_dates["start_date"])
    trip_data.setdefault("end_date", travel_dates["end_date"])
    trip_data.setdefault("travel_dates", travel_dates)

    transport_recommendation = transport_info.get("recommendation", {})
    if transport_recommendation:
        trip_data.setdefault(
            "intercity_transport_advice",
            f"{transport_recommendation.get('main_mode', '交通方式待确认')}："
            f"{transport_recommendation.get('reason', '')} "
            f"{transport_recommendation.get('first_day_advice', '')}"
        )

    for index, day_plan in enumerate(trip_data.get("plan", []), start=1):
        day_number = day_plan.get("day") or index
        try:
            day_plan.setdefault("date", calculate_day_date(start_date, int(day_number)))
        except (TypeError, ValueError):
            day_plan.setdefault("date", calculate_day_date(start_date, index))

    if verbose:
        print()
        print("正在检查行程地点开放时间...")
    opening_hours_info = check_trip_opening_hours(
        trip_data=trip_data,
        city=location_info.get("city")
    )

    if verbose:
        print()
        print("正在根据最终行程匹配地点图片...")
    image_info = match_images_for_trip(
        trip_data=trip_data,
        poi_info=poi_info,
        destination=destination
    )

    project_data = build_project_data(
        trip_data=trip_data,
        budget=budget,
        location_info=location_info,
        weather_info=weather_info,
        poi_info=poi_info,
        route_info=route_info,
        hotel_info=hotel_info,
        transport_info=transport_info,
        event_info=event_info,
        opening_hours_info=opening_hours_info,
        image_info=image_info,
        tool_plan=tool_plan,
        execution_logs=execution_logs,
        travel_dates=travel_dates
    )

    project_data = ensure_memory_fields(project_data)
    project_data = add_version(
        project_data=project_data,
        action="initial_create",
        summary="初始生成行程"
    )
    project_data = record_generation_duration(
        project_data,
        time.perf_counter() - generation_started_at
    )
    project_data = update_project_evaluation(project_data)

    if display_result:
        print_project(project_data)

    return project_data


def create_project(requirements):
    """
    CLI 创建项目。
    """
    return create_project_by_requirements(
        requirements=requirements,
        verbose=True,
        display_result=True
    )


def load_project_flow():
    """
    读取已有完整旅行项目。
    """
    saved_projects = list_saved_projects()

    if not saved_projects:
        print("当前还没有已保存的行程。")
        return None

    print()
    print("已保存行程：")
    for index, item in enumerate(saved_projects, start=1):
        print(
            f"{index}. {item['filename']} | "
            f"目的地：{item['destination']} | "
            f"天数：{item['days']} | "
            f"人数：{item['people']} | "
            f"更新时间：{item['updated_at']}"
        )

    load_choice = input("请输入要读取的行程编号，或直接回车返回首页：").strip()

    if not load_choice:
        return None

    try:
        selected_index = int(load_choice)

        if selected_index < 1 or selected_index > len(saved_projects):
            print("编号超出范围。")
            return None

        selected_project = saved_projects[selected_index - 1]
        project_data = load_project(selected_project["filepath"])

        print()
        print(f"已读取行程：{selected_project['filename']}")

        print_project(project_data)

        return project_data

    except ValueError:
        print("请输入有效的数字编号。")
        return None
    except Exception as e:
        print(f"读取行程失败：{e}")
        return None


def edit_project(project_data):
    """
    修改当前项目中的 trip_data，同时更新项目记忆和版本历史。
    """
    user_edit_request = input("请输入你的修改要求：").strip()

    if not user_edit_request:
        print("修改要求不能为空。")
        return project_data

    project_data = edit_project_by_request(
        project_data=project_data,
        user_edit_request=user_edit_request,
        verbose=True
    )
    print_project(project_data)
    return project_data


def edit_project_by_request(project_data, user_edit_request, verbose=False):
    """
    根据用户修改要求修改项目。
    这是 Web API 使用的版本，不使用 input()。
    """
    project_data = ensure_memory_fields(project_data)

    if not user_edit_request:
        raise ValueError("修改要求不能为空")

    project_data = extract_memory_from_edit_request(
        project_data=project_data,
        user_edit_request=user_edit_request
    )

    trip_data = project_data.get("trip_data", {})
    budget = project_data.get("budget", {})
    location_info = project_data.get("location_info", {})
    weather_info = project_data.get("weather_info", {})
    memory_text = get_memory_text(project_data)

    if verbose:
        print()
        print("正在根据你的要求和项目记忆修改行程...")

    updated_trip_data = edit_itinerary(
        original_trip_data=trip_data,
        user_edit_request=user_edit_request,
        location_info=location_info,
        weather_info=weather_info,
        budget=budget,
        memory_text=memory_text
    )

    project_data["trip_data"] = updated_trip_data

    poi_info = project_data.get("poi_info", {})
    destination = updated_trip_data.get("destination")

    if verbose:
        print()
        print("正在根据修改后的行程重新检查开放时间...")
    opening_hours_info = check_trip_opening_hours(
        trip_data=updated_trip_data,
        city=location_info.get("city")
    )
    project_data["opening_hours_info"] = opening_hours_info

    if verbose:
        print()
        print("正在根据修改后的行程重新匹配地点图片...")
    image_info = match_images_for_trip(
        trip_data=updated_trip_data,
        poi_info=poi_info,
        destination=destination
    )
    project_data["image_info"] = image_info

    edit_summary = updated_trip_data.get("edit_summary", user_edit_request)
    project_data = add_version(
        project_data=project_data,
        action="edit",
        summary=edit_summary
    )
    project_data = record_edit(project_data)
    project_data = update_project_evaluation(project_data)
    project_data = mark_project_dirty(project_data)

    return project_data


def restore_project_previous_version(project_data):
    """
    恢复上一版行程，并标记为已修改。
    """
    project_data, result = restore_previous_version(project_data)

    if result.get("success"):
        project_data = record_restore(project_data)
        project_data = update_project_evaluation(project_data)
        project_data = mark_project_dirty(project_data)

    return project_data, result


def save_current_project(project_data):
    """
    保存当前完整旅行项目。
    如果项目被修改，会生成新的快照；
    如果项目未修改，会覆盖当前快照。
    """
    old_version = project_data.get("snapshot_version", 1)
    old_filepath = project_data.get("project_filepath")

    filepath = save_project(project_data)

    new_version = project_data.get("snapshot_version", 1)
    new_filepath = project_data.get("project_filepath")

    if old_filepath != new_filepath or old_version != new_version:
        print(f"当前修改已保存为新快照：v{new_version}")
    else:
        print(f"当前项目快照已更新：v{new_version}")

    print(f"保存路径：{filepath}")

    return project_data


def export_current_project(project_data, export_type):
    """
    导出当前旅行项目。
    导出前自动确保当前项目快照已经保存。
    export_type: markdown / html / pdf
    """
    old_version = project_data.get("snapshot_version", 1)
    old_filepath = project_data.get("project_filepath")

    project_filepath, created_or_updated = ensure_project_saved(project_data)

    new_version = project_data.get("snapshot_version", 1)
    new_filepath = project_data.get("project_filepath")

    if old_filepath != new_filepath or old_version != new_version:
        print(f"导出前已将当前修改保存为新快照：v{new_version}")
    else:
        print(f"导出前已确认当前快照为最新：v{new_version}")

    trip_data = project_data.get("trip_data", {})
    budget = project_data.get("budget", {})
    location_info = project_data.get("location_info", {})
    weather_info = project_data.get("weather_info", {})
    image_info = project_data.get("image_info", {})
    hotel_info = project_data.get("hotel_info", {})
    transport_info = project_data.get("transport_info", {})
    event_info = project_data.get("event_info", {})
    opening_hours_info = project_data.get("opening_hours_info", {})
    exported_filepath = None

    if export_type == "markdown":
        exported_filepath = export_trip_to_markdown(
            trip_data=trip_data,
            budget=budget,
            location_info=location_info,
            weather_info=weather_info,
            hotel_info=hotel_info,
            transport_info=transport_info,
            opening_hours_info=opening_hours_info,
            event_info=event_info
        )
        print(f"Markdown 旅行报告已导出：{exported_filepath}")

    elif export_type == "html":
        exported_filepath = export_trip_to_html(
            trip_data=trip_data,
            budget=budget,
            location_info=location_info,
            weather_info=weather_info,
            image_info=image_info,
            hotel_info=hotel_info,
            transport_info=transport_info,
            opening_hours_info=opening_hours_info,
            event_info=event_info
        )
        print(f"HTML 旅行报告已导出：{exported_filepath}")
        print("你可以在浏览器中打开该文件查看可视化报告。")

    elif export_type == "pdf":
        try:
            exported_filepath = export_trip_to_pdf(
                trip_data=trip_data,
                budget=budget,
                location_info=location_info,
                weather_info=weather_info,
                image_info=image_info,
                hotel_info=hotel_info,
                transport_info=transport_info,
                opening_hours_info=opening_hours_info,
                event_info=event_info,
            )
            print(f"PDF 旅行报告已导出：{exported_filepath}")
        except Exception as e:
            print(f"PDF 导出失败：{e}")
            print("你也可以先导出 HTML 报告，然后用浏览器打开 HTML，再通过 Ctrl + P 手动另存为 PDF。")
            return project_data

    else:
        print("未知导出类型。")
        return project_data

    if exported_filepath:
        project_data = record_export_history(
            project_data=project_data,
            export_type=export_type,
            filepath=exported_filepath
        )
        project_data = record_export(project_data, export_type)
        project_data = update_project_evaluation(project_data)
        save_project_snapshot(project_data)

    return project_data


def adopt_project(project_data):
    """
    标记当前项目已被采纳。
    """
    project_data = record_adoption(project_data, True)
    project_data = update_project_evaluation(project_data)
    return project_data


def submit_project_feedback(project_data, score=None, feedback=""):
    """
    提交满意度评分与文字反馈。
    """
    project_data = record_feedback(project_data, score=score, feedback=feedback)
    project_data = update_project_evaluation(project_data)
    return project_data
