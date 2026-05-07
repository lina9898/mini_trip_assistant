# tool_plan_validator.py

from tools.tool_registry import get_tool_info


REQUIRED_BASE_TOOLS = [
    "map_tool",
    "weather_tool",
    "budget_tool",
    "poi_tool",
    "route_tool",
    "hotel_tool",
    "transport_tool",
    "event_tool"
]


POST_GENERATION_TOOLS = [
    "opening_hours_tool"
]


def validate_tool_call(call):
    """
    校验单个工具调用是否合法。
    """
    errors = []

    tool_name = call.get("tool_name")
    arguments = call.get("arguments", {})

    if not tool_name:
        errors.append("缺少 tool_name。")
        return errors

    tool_info = get_tool_info(tool_name)

    if not tool_info:
        errors.append(f"工具 {tool_name} 未注册。")
        return errors

    required_params = tool_info.get("required_params", [])

    for param in required_params:
        if param not in arguments:
            errors.append(f"工具 {tool_name} 缺少必要参数：{param}。")

    return errors


def validate_tool_plan(tool_plan):
    """
    校验完整工具调用计划。
    """
    errors = []
    tool_calls = tool_plan.get("tool_calls", [])

    if not isinstance(tool_calls, list):
        return ["tool_calls 必须是列表。"]

    if not tool_calls:
        return ["tool_calls 不能为空。"]

    for index, call in enumerate(tool_calls, start=1):
        call_errors = validate_tool_call(call)
        for error in call_errors:
            errors.append(f"第 {index} 个工具调用错误：{error}")

    return errors


def has_tool(tool_calls, tool_name):
    """
    判断工具调用计划中是否已经包含某个工具。
    """
    return any(call.get("tool_name") == tool_name for call in tool_calls)


def build_default_tool_call(
    tool_name,
    destination,
    days,
    budget_level,
    people,
    preference="综合体验",
    start_date=None,
    end_date=None,
    origin=None
):
    """
    构造默认工具调用。
    当大模型漏掉必要工具时，用这个函数进行补全。
    """
    if tool_name == "map_tool":
        return {
            "tool_name": "map_tool",
            "arguments": {
                "address": destination
            },
            "reason": "默认补全：旅行规划需要目的地地图信息。"
        }

    if tool_name == "weather_tool":
        arguments = {
            "adcode": "{{map_tool.adcode}}"
        }

        if start_date:
            arguments["start_date"] = start_date
            arguments["days"] = days

        return {
            "tool_name": "weather_tool",
            "arguments": arguments,
            "reason": "默认补全：旅行规划需要根据计划出行日期查询天气。"
        }

    if tool_name == "budget_tool":
        return {
            "tool_name": "budget_tool",
            "arguments": {
                "days": days,
                "budget_level": budget_level,
                "people": people
            },
            "reason": "默认补全：旅行规划需要估算预算。"
        }

    if tool_name == "poi_tool":
        return {
            "tool_name": "poi_tool",
            "arguments": {
                "destination": destination,
                "preference": preference,
                "city": "{{map_tool.city}}"
            },
            "reason": "默认补全：旅行规划需要真实 POI 信息辅助生成行程。"
        }

    if tool_name == "route_tool":
        return {
            "tool_name": "route_tool",
            "arguments": {
                "poi_info": "{{poi_tool}}"
            },
            "reason": "默认补全：旅行规划需要根据 POI 结果计算路线距离，辅助判断行程是否顺路。"
        }

    if tool_name == "hotel_tool":
        return {
            "tool_name": "hotel_tool",
            "arguments": {
                "destination": destination,
                "poi_info": "{{poi_tool}}",
                "city": "{{map_tool.city}}",
                "budget_level": budget_level
            },
            "reason": "默认补全：完整旅行规划需要住宿选址建议，并参考酒店到主要景点的距离。"
        }

    if tool_name == "transport_tool":
        return {
            "tool_name": "transport_tool",
            "arguments": {
                "origin": origin or "未填写",
                "destination": destination,
                "budget_level": budget_level
            },
            "reason": "默认补全：完整旅行规划需要根据出发地和目的地给出城际交通建议。"
        }

    if tool_name == "event_tool":
        return {
            "tool_name": "event_tool",
            "arguments": {
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date
            },
            "reason": "默认补全：出行期间可能存在演唱会、展览、赛事等特殊活动，需要作为行程安排参考。"
        }

    if tool_name == "image_tool":
        return {
            "tool_name": "image_tool",
            "arguments": {
                "destination": destination,
                "preference": preference,
                "poi_info": "{{poi_tool}}"
            },
            "reason": "默认补全：图文旅行报告需要目的地和景点相关图片。"
        }

    return None


def complete_required_tools(
    tool_plan,
    destination,
    days,
    budget_level,
    people,
    preference="综合体验",
    start_date=None,
    end_date=None,
    origin=None
):
    """
    补全基础旅行助手必须使用的工具。
    """
    tool_calls = tool_plan.get("tool_calls", [])

    for tool_name in REQUIRED_BASE_TOOLS:
        if not has_tool(tool_calls, tool_name):
            default_call = build_default_tool_call(
                tool_name=tool_name,
                destination=destination,
                days=days,
                budget_level=budget_level,
                people=people,
                preference=preference,
                start_date=start_date,
                end_date=end_date,
                origin=origin
            )

            if default_call:
                tool_calls.append(default_call)

    tool_plan["tool_calls"] = tool_calls
    return tool_plan


def complete_event_tool_arguments(tool_plan, destination, start_date=None, end_date=None):
    """
    如果模型主动调用 event_tool 但漏参数，补齐日期范围。
    """
    for call in tool_plan.get("tool_calls", []):
        if call.get("tool_name") != "event_tool":
            continue

        arguments = call.setdefault("arguments", {})
        arguments.setdefault("destination", destination)

        if start_date:
            arguments.setdefault("start_date", start_date)
        if end_date:
            arguments.setdefault("end_date", end_date)

    return tool_plan


def reorder_tool_plan(tool_plan):
    """
    调整工具调用顺序。
    weather_tool 和 poi_tool 可以依赖 map_tool，route_tool 和 image_tool 依赖 poi_tool。
    """
    tool_calls = tool_plan.get("tool_calls", [])

    priority = {
        "map_tool": 1,
        "weather_tool": 2,
        "budget_tool": 3,
        "poi_tool": 4,
        "route_tool": 5,
        "hotel_tool": 6,
        "transport_tool": 7,
        "event_tool": 8,
        "image_tool": 9
    }

    sorted_calls = sorted(
        tool_calls,
        key=lambda call: priority.get(call.get("tool_name"), 99)
    )

    tool_plan["tool_calls"] = sorted_calls
    return tool_plan


def remove_post_generation_tools(tool_plan):
    """
    移除只能在最终行程生成后运行的工具。
    """
    tool_calls = tool_plan.get("tool_calls", [])
    tool_plan["tool_calls"] = [
        call for call in tool_calls
        if call.get("tool_name") not in POST_GENERATION_TOOLS
    ]
    return tool_plan


def repair_tool_plan(
    tool_plan,
    destination,
    days,
    budget_level,
    people,
    preference="综合体验",
    start_date=None,
    end_date=None,
    origin=None
):
    """
    对工具调用计划进行自动修复：
    1. 补全必要工具
    2. 调整工具顺序
    """
    tool_plan = remove_post_generation_tools(tool_plan)
    tool_plan = complete_event_tool_arguments(
        tool_plan=tool_plan,
        destination=destination,
        start_date=start_date,
        end_date=end_date
    )

    tool_plan = complete_required_tools(
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

    tool_plan = reorder_tool_plan(tool_plan)

    return tool_plan
