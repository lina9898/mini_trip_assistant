# tools/route_tool.py

import os

import requests
from dotenv import load_dotenv


load_dotenv()


def format_location(poi):
    """
    从 POI 中提取经纬度，格式化为 'longitude,latitude'。
    """
    longitude = poi.get("longitude")
    latitude = poi.get("latitude")

    if not longitude or not latitude:
        return None

    return f"{longitude},{latitude}"


def build_candidate_pois(poi_info, max_pois=8):
    """
    从 poi_info 中筛选可用于计算距离的 POI。
    """
    pois = poi_info.get("pois", []) if poi_info else []
    candidates = []

    for poi in pois:
        location = format_location(poi)

        if not location:
            continue

        candidates.append({
            "name": poi.get("name"),
            "type": poi.get("type"),
            "address": poi.get("address"),
            "district": poi.get("district"),
            "longitude": poi.get("longitude"),
            "latitude": poi.get("latitude"),
            "location": location
        })

        if len(candidates) >= max_pois:
            break

    return candidates


def call_amap_distance_api(origins, destination, distance_type="1"):
    """
    调用高德距离测量接口。

    distance_type:
    0：直线距离
    1：驾车导航距离，默认
    3：步行规划距离
    """
    api_key = os.getenv("AMAP_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "未配置 AMAP_API_KEY"
        }

    url = "https://restapi.amap.com/v3/distance"
    params = {
        "key": api_key,
        "origins": origins,
        "destination": destination,
        "type": distance_type,
        "output": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "1":
            return {
                "success": False,
                "error": data.get("info", "距离测量失败"),
                "raw": data
            }

        return {
            "success": True,
            "raw": data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def analyze_poi_distances(poi_info, max_pois=8, distance_type="1"):
    """
    路线距离工具。
    从 POI 列表中选取候选地点，计算它们相对于第一个 POI 的距离。
    """
    candidates = build_candidate_pois(poi_info, max_pois=max_pois)

    if len(candidates) < 2:
        return {
            "tool_name": "route_tool",
            "success": False,
            "error": "可用于距离计算的 POI 数量不足。",
            "candidates": candidates,
            "routes": []
        }

    reference_poi = candidates[0]
    destination = reference_poi["location"]

    origin_pois = candidates[1:]
    origins = "|".join([poi["location"] for poi in origin_pois])

    api_result = call_amap_distance_api(
        origins=origins,
        destination=destination,
        distance_type=distance_type
    )

    if not api_result.get("success"):
        return {
            "tool_name": "route_tool",
            "success": False,
            "error": api_result.get("error"),
            "reference_poi": reference_poi,
            "candidates": candidates,
            "routes": []
        }

    raw_results = api_result.get("raw", {}).get("results", [])
    routes = []

    for index, item in enumerate(raw_results):
        if index >= len(origin_pois):
            break

        origin_poi = origin_pois[index]
        distance = item.get("distance")
        duration = item.get("duration")

        try:
            distance_m = int(distance)
        except (TypeError, ValueError):
            distance_m = None

        try:
            duration_s = int(duration)
        except (TypeError, ValueError):
            duration_s = None

        route_level = "未知"

        if distance_m is not None:
            if distance_m <= 2000:
                route_level = "很近，适合安排在同一时间段或同一天"
            elif distance_m <= 8000:
                route_level = "中等距离，适合安排在同一天"
            else:
                route_level = "较远，不建议和参考点安排得过于紧密"

        routes.append({
            "from": origin_poi,
            "to": reference_poi,
            "distance_m": distance_m,
            "distance_km": round(distance_m / 1000, 2) if distance_m is not None else None,
            "duration_s": duration_s,
            "duration_min": round(duration_s / 60, 1) if duration_s is not None else None,
            "route_level": route_level
        })

    nearby = [
        route for route in routes
        if route.get("distance_m") is not None and route["distance_m"] <= 8000
    ]
    faraway = [
        route for route in routes
        if route.get("distance_m") is not None and route["distance_m"] > 8000
    ]

    return {
        "tool_name": "route_tool",
        "success": True,
        "reference_poi": reference_poi,
        "candidate_count": len(candidates),
        "route_count": len(routes),
        "nearby_count": len(nearby),
        "faraway_count": len(faraway),
        "routes": routes,
        "summary": {
            "reference": reference_poi.get("name"),
            "nearby_names": [route["from"].get("name") for route in nearby],
            "faraway_names": [route["from"].get("name") for route in faraway],
            "suggestion": "优先将距离较近的 POI 安排在同一天，距离较远的 POI 单独安排或减少跨区移动。"
        }
    }
