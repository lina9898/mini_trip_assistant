# tools/tool_registry.py

from tools.budget_tool import estimate_budget
from tools.event_tool import search_city_events
from tools.hotel_tool import recommend_hotels
from tools.image_tool import search_images
from tools.map_tool import get_location
from tools.opening_hours_tool import check_trip_opening_hours
from tools.poi_tool import search_pois
from tools.route_tool import analyze_poi_distances
from tools.transport_tool import plan_intercity_transport
from tools.weather_tool import get_weather_by_adcode


TOOL_REGISTRY = {
    "budget_tool": {
        "name": "budget_tool",
        "description": "根据旅行天数、预算档位和出行人数，估算旅行预算。",
        "function": estimate_budget,
        "required_params": ["days", "budget_level", "people"]
    },
    "map_tool": {
        "name": "map_tool",
        "description": "根据目的地名称或地址，查询经纬度、城市、行政区编码等地图信息。",
        "function": get_location,
        "required_params": ["address"]
    },
    "weather_tool": {
        "name": "weather_tool",
        "description": "根据高德地图 adcode 和计划出行日期，查询实况天气、短期天气预报或返回日期超范围提示。",
        "function": get_weather_by_adcode,
        "required_params": ["adcode"]
    },
    "poi_tool": {
        "name": "poi_tool",
        "description": "根据目的地和旅行偏好，搜索景点、餐饮、商圈等 POI 信息。",
        "function": search_pois,
        "required_params": ["destination", "preference"]
    },
    "route_tool": {
        "name": "route_tool",
        "description": "根据 POI 工具返回的地点经纬度，计算候选地点之间的距离和通勤时间，用于判断行程路线是否顺路。",
        "function": analyze_poi_distances,
        "required_params": ["poi_info"]
    },
    "hotel_tool": {
        "name": "hotel_tool",
        "description": "根据目的地、POI 行程地点和预算档位，搜索酒店候选并计算酒店到主要景点的距离，用于给出住宿选址建议。",
        "function": recommend_hotels,
        "required_params": ["destination"]
    },
    "transport_tool": {
        "name": "transport_tool",
        "description": "根据出发地、目的地和预算档位，估算城际交通距离与耗时，并给出高铁、飞机、自驾或公共交通建议。",
        "function": plan_intercity_transport,
        "required_params": ["origin", "destination"]
    },
    "opening_hours_tool": {
        "name": "opening_hours_tool",
        "description": "根据最终行程中的地点，查询 POI 开放时间并判断是否存在闭馆或时段冲突风险。",
        "function": check_trip_opening_hours,
        "required_params": ["trip_data"]
    },
    "event_tool": {
        "name": "event_tool",
        "description": "根据目的地和出行日期范围查询城市活动、演唱会、体育赛事、展览等特殊事件，并给出行程影响提示。",
        "function": search_city_events,
        "required_params": ["destination", "start_date", "end_date"]
    },
    "image_tool": {
        "name": "image_tool",
        "description": "根据目的地、旅行偏好和 POI 信息，搜索旅行相关图片，用于生成图文旅行报告。",
        "function": search_images,
        "required_params": ["destination", "preference"]
    }
}


def list_tools():
    """
    返回当前已注册的工具信息。
    """
    tools = []

    for tool_name, tool_info in TOOL_REGISTRY.items():
        tools.append({
            "name": tool_name,
            "description": tool_info["description"],
            "required_params": tool_info["required_params"]
        })

    return tools


def get_tool_info(tool_name):
    """
    根据工具名称获取工具注册信息。
    """
    return TOOL_REGISTRY.get(tool_name)


def run_tool(tool_name, **kwargs):
    """
    根据工具名称和参数，统一调用对应工具。
    """
    if tool_name not in TOOL_REGISTRY:
        return {
            "tool_name": tool_name,
            "success": False,
            "error": f"工具 {tool_name} 未注册。"
        }

    tool_info = TOOL_REGISTRY[tool_name]
    required_params = tool_info["required_params"]

    missing_params = []

    for param in required_params:
        if param not in kwargs or kwargs.get(param) is None:
            missing_params.append(param)

    if missing_params:
        return {
            "tool_name": tool_name,
            "success": False,
            "error": f"缺少必要参数：{missing_params}"
        }

    try:
        function = tool_info["function"]
        return function(**kwargs)

    except Exception as e:
        return {
            "tool_name": tool_name,
            "success": False,
            "error": str(e)
        }
