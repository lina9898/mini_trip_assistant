# tools/transport_tool.py

import os
import requests
from dotenv import load_dotenv


load_dotenv()


def geocode_place(address):
    """
    使用高德地理编码接口，将地点名称转换为经纬度。
    """
    api_key = os.getenv("AMAP_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "未配置 AMAP_API_KEY"
        }

    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": api_key,
        "address": address,
        "output": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "1":
            return {
                "success": False,
                "error": data.get("info", "地理编码失败"),
                "raw": data
            }

        geocodes = data.get("geocodes", [])

        if not geocodes:
            return {
                "success": False,
                "error": "未找到地点坐标"
            }

        item = geocodes[0]
        location = item.get("location", "")
        longitude = ""
        latitude = ""

        if "," in location:
            longitude, latitude = location.split(",", 1)

        return {
            "success": True,
            "formatted_address": item.get("formatted_address"),
            "province": item.get("province"),
            "city": item.get("city"),
            "district": item.get("district"),
            "adcode": item.get("adcode"),
            "longitude": longitude,
            "latitude": latitude,
            "location": location
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def call_driving_route(origin_location, destination_location):
    """
    调用高德驾车路径规划接口。
    """
    api_key = os.getenv("AMAP_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "未配置 AMAP_API_KEY"
        }

    url = "https://restapi.amap.com/v3/direction/driving"
    params = {
        "key": api_key,
        "origin": origin_location,
        "destination": destination_location,
        "extensions": "base",
        "output": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "1":
            return {
                "success": False,
                "error": data.get("info", "驾车路线规划失败"),
                "raw": data
            }

        route = data.get("route", {})
        paths = route.get("paths", [])

        if not paths:
            return {
                "success": False,
                "error": "未获取到驾车路线"
            }

        path = paths[0]

        distance_m = int(path.get("distance", 0))
        duration_s = int(path.get("duration", 0))

        return {
            "success": True,
            "distance_m": distance_m,
            "distance_km": round(distance_m / 1000, 2),
            "duration_s": duration_s,
            "duration_min": round(duration_s / 60, 1),
            "duration_hour": round(duration_s / 3600, 1),
            "strategy": path.get("strategy")
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def call_transit_route(origin_location, destination_location, origin_city=None, destination_city=None):
    """
    调用高德公交路径规划接口。
    跨城场景通常需要 city 和 cityd。
    """
    api_key = os.getenv("AMAP_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "未配置 AMAP_API_KEY"
        }

    url = "https://restapi.amap.com/v3/direction/transit/integrated"
    params = {
        "key": api_key,
        "origin": origin_location,
        "destination": destination_location,
        "city": origin_city or "",
        "cityd": destination_city or "",
        "strategy": 0,
        "output": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "1":
            return {
                "success": False,
                "error": data.get("info", "公交路径规划失败"),
                "raw": data
            }

        route = data.get("route", {})
        transits = route.get("transits", [])

        if not transits:
            return {
                "success": False,
                "error": "未获取到公共交通方案",
                "raw": data
            }

        option = transits[0]

        try:
            duration_s = int(option.get("duration", 0))
        except (TypeError, ValueError):
            duration_s = 0

        try:
            distance_m = int(option.get("distance", 0))
        except (TypeError, ValueError):
            distance_m = 0

        return {
            "success": True,
            "distance_m": distance_m,
            "distance_km": round(distance_m / 1000, 2) if distance_m else None,
            "duration_s": duration_s,
            "duration_min": round(duration_s / 60, 1) if duration_s else None,
            "duration_hour": round(duration_s / 3600, 1) if duration_s else None,
            "cost": option.get("cost"),
            "walking_distance": option.get("walking_distance"),
            "segments_count": len(option.get("segments", []))
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def build_transport_recommendation(origin, destination, driving_result, transit_result, budget_level="中"):
    """
    根据距离、耗时和预算档位生成交通建议。
    """
    driving_distance_km = driving_result.get("distance_km") if driving_result.get("success") else None
    driving_duration_hour = driving_result.get("duration_hour") if driving_result.get("success") else None
    transit_duration_hour = transit_result.get("duration_hour") if transit_result.get("success") else None

    if driving_distance_km is None:
        return {
            "main_mode": "公共交通或铁路",
            "reason": "未能准确获取驾车距离，建议结合铁路、飞机或当地交通平台进一步确认。",
            "first_day_advice": "建议第一天安排轻量行程，预留到达和入住时间。"
        }

    if driving_distance_km <= 80:
        main_mode = "城际公交、地铁/铁路或短途打车"
        reason = "出发地与目的地距离较近，可优先选择公共交通或短途打车，时间安排相对灵活。"
    elif driving_distance_km <= 300:
        if budget_level == "低":
            main_mode = "高铁 / 城际铁路 / 长途汽车"
            reason = "距离中等，低预算下建议优先选择高铁二等座、城际铁路或长途汽车。"
        else:
            main_mode = "高铁或自驾"
            reason = "距离中等，高铁通常较稳定，自驾也有一定灵活性。"
    elif driving_distance_km <= 800:
        main_mode = "高铁优先，飞机备选"
        reason = "距离较远，自驾耗时较长，高铁通常更适合大多数旅行场景。"
    else:
        main_mode = "飞机或高铁"
        reason = "距离很远，自驾耗时过长，建议优先考虑飞机或高铁。"

    if driving_duration_hour and driving_duration_hour >= 5:
        first_day_advice = "由于路途时间较长，第一天建议安排轻松活动，如入住、周边散步、简单夜景或美食体验。"
    else:
        first_day_advice = "到达压力相对较小，第一天可以安排半日轻量游览，但仍建议预留交通缓冲时间。"

    if transit_duration_hour:
        reason += f" 公共交通方案预计约 {transit_duration_hour} 小时，可作为参考。"

    return {
        "main_mode": main_mode,
        "reason": reason,
        "first_day_advice": first_day_advice
    }


def plan_intercity_transport(origin, destination, budget_level="中"):
    """
    出发地到目的地交通规划工具。
    """
    if not origin or origin == "未填写":
        return {
            "tool_name": "transport_tool",
            "success": False,
            "error": "未填写出发地，无法规划城际交通。",
            "origin": origin,
            "destination": destination
        }

    origin_geo = geocode_place(origin)
    destination_geo = geocode_place(destination)

    if not origin_geo.get("success"):
        return {
            "tool_name": "transport_tool",
            "success": False,
            "error": f"出发地解析失败：{origin_geo.get('error')}",
            "origin": origin,
            "destination": destination
        }

    if not destination_geo.get("success"):
        return {
            "tool_name": "transport_tool",
            "success": False,
            "error": f"目的地解析失败：{destination_geo.get('error')}",
            "origin": origin,
            "destination": destination
        }

    driving_result = call_driving_route(
        origin_location=origin_geo["location"],
        destination_location=destination_geo["location"]
    )

    transit_result = call_transit_route(
        origin_location=origin_geo["location"],
        destination_location=destination_geo["location"],
        origin_city=origin_geo.get("city") or origin_geo.get("adcode"),
        destination_city=destination_geo.get("city") or destination_geo.get("adcode")
    )

    recommendation = build_transport_recommendation(
        origin=origin,
        destination=destination,
        driving_result=driving_result,
        transit_result=transit_result,
        budget_level=budget_level
    )

    return {
        "tool_name": "transport_tool",
        "success": True,
        "origin": origin,
        "destination": destination,
        "budget_level": budget_level,
        "origin_location": origin_geo,
        "destination_location": destination_geo,
        "driving": driving_result,
        "transit": transit_result,
        "recommendation": recommendation,
        "note": "交通建议基于地图路径规划和距离估算，不包含实时票价、余票、航班或高铁车次信息。"
    }
