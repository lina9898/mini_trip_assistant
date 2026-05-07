# tools/hotel_tool.py

import os
import requests
from dotenv import load_dotenv


load_dotenv()


def format_location(item):
    """
    从 POI / 酒店对象中提取 location 字符串。
    """
    longitude = item.get("longitude")
    latitude = item.get("latitude")

    if not longitude or not latitude:
        return None

    return f"{longitude},{latitude}"


def search_hotels_by_keyword(destination, city=None, page_size=6):
    """
    使用高德 POI 2.0 关键字搜索酒店。
    """
    api_key = os.getenv("AMAP_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "未配置 AMAP_API_KEY",
            "hotels": []
        }

    url = "https://restapi.amap.com/v5/place/text"
    params = {
        "key": api_key,
        "keywords": f"{destination} 酒店",
        "region": city or destination,
        "city_limit": "true",
        "page_size": page_size,
        "page_num": 1,
        "show_fields": "business,photos",
        "output": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "1":
            return {
                "success": False,
                "error": data.get("info", "酒店 POI 查询失败"),
                "hotels": [],
                "raw": data
            }

        hotels = []

        for poi in data.get("pois", []):
            location = poi.get("location", "")
            longitude = ""
            latitude = ""

            if "," in location:
                longitude, latitude = location.split(",", 1)

            poi_type = poi.get("type", "")
            if poi_type and not any(word in poi_type for word in ["住宿服务", "酒店", "宾馆", "旅馆"]):
                continue

            photos = []
            for photo in poi.get("photos", []) or []:
                if photo.get("url"):
                    photos.append({
                        "title": photo.get("title"),
                        "url": photo.get("url")
                    })

            hotels.append({
                "id": poi.get("id"),
                "name": poi.get("name"),
                "type": poi_type,
                "address": poi.get("address"),
                "province": poi.get("pname"),
                "city": poi.get("cityname"),
                "district": poi.get("adname"),
                "longitude": longitude,
                "latitude": latitude,
                "location": location,
                "photos": photos,
                "source": "amap_v5"
            })

        return {
            "success": True,
            "hotels": hotels,
            "count": len(hotels)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "hotels": []
        }


def select_reference_places(poi_info, max_places=4):
    """
    从 poi_info 中选择核心景点作为酒店选址参考点。
    """
    pois = poi_info.get("pois", []) if poi_info else []
    reference_places = []

    for poi in pois:
        location = format_location(poi)

        if not location:
            continue

        name = poi.get("name")
        poi_type = poi.get("type", "")

        if any(keyword in poi_type for keyword in ["风景名胜", "公园", "博物馆", "文化", "旅游"]):
            reference_places.append({
                "name": name,
                "type": poi_type,
                "address": poi.get("address"),
                "district": poi.get("district"),
                "longitude": poi.get("longitude"),
                "latitude": poi.get("latitude"),
                "location": location
            })

        if len(reference_places) >= max_places:
            break

    if not reference_places:
        for poi in pois:
            location = format_location(poi)

            if not location:
                continue

            reference_places.append({
                "name": poi.get("name"),
                "type": poi.get("type"),
                "address": poi.get("address"),
                "district": poi.get("district"),
                "longitude": poi.get("longitude"),
                "latitude": poi.get("latitude"),
                "location": location
            })

            if len(reference_places) >= max_places:
                break

    return reference_places


def call_distance_api(origins, destination, distance_type="1"):
    """
    调用高德距离测量接口。
    origins 可以包含多个坐标，用 | 分隔。
    destination 是一个坐标。
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


def calculate_hotel_distances(hotel, reference_places):
    """
    计算某个酒店到多个参考景点的距离。
    """
    hotel_location = format_location(hotel)

    if not hotel_location or not reference_places:
        return []

    distance_results = []

    for place in reference_places:
        place_location = place.get("location")

        if not place_location:
            continue

        api_result = call_distance_api(
            origins=hotel_location,
            destination=place_location,
            distance_type="1"
        )

        if not api_result.get("success"):
            distance_results.append({
                "place_name": place.get("name"),
                "success": False,
                "error": api_result.get("error")
            })
            continue

        results = api_result.get("raw", {}).get("results", [])

        if not results:
            continue

        item = results[0]

        try:
            distance_m = int(item.get("distance"))
        except (TypeError, ValueError):
            distance_m = None

        try:
            duration_s = int(item.get("duration"))
        except (TypeError, ValueError):
            duration_s = None

        distance_results.append({
            "place_name": place.get("name"),
            "place_type": place.get("type"),
            "distance_m": distance_m,
            "distance_km": round(distance_m / 1000, 2) if distance_m is not None else None,
            "duration_s": duration_s,
            "duration_min": round(duration_s / 60, 1) if duration_s is not None else None
        })

    return distance_results


def score_hotel_candidate(hotel, distance_results, budget_level="中"):
    """
    根据距离结果给酒店候选打分。
    """
    valid_distances = [
        item for item in distance_results
        if item.get("distance_km") is not None
    ]

    if not valid_distances:
        return 50, "缺少有效距离数据，仅作为普通候选。"

    avg_distance = sum(item["distance_km"] for item in valid_distances) / len(valid_distances)

    if avg_distance <= 3:
        score = 90
        reason = "距离主要景点整体较近，适合作为高便利度住宿点。"
    elif avg_distance <= 6:
        score = 78
        reason = "距离主要景点适中，适合兼顾价格和通勤便利。"
    elif avg_distance <= 10:
        score = 65
        reason = "距离部分景点较远，适合预算有限或不介意通勤的行程。"
    else:
        score = 50
        reason = "距离主要景点整体偏远，不建议作为优先住宿选择。"

    if budget_level == "低" and avg_distance <= 6:
        reason += " 低预算下可优先关注该区域的平价酒店或连锁酒店。"
    elif budget_level == "高" and avg_distance <= 3:
        reason += " 高预算下可考虑选择该区域品质更高的酒店。"

    return score, reason


def recommend_hotels(destination, poi_info=None, city=None, budget_level="中", max_hotels=5):
    """
    酒店选址工具主函数。
    """
    hotel_result = search_hotels_by_keyword(
        destination=destination,
        city=city,
        page_size=max_hotels
    )

    if not hotel_result.get("success"):
        return {
            "tool_name": "hotel_tool",
            "success": False,
            "destination": destination,
            "error": hotel_result.get("error"),
            "hotel_candidates": [],
            "reference_places": []
        }

    hotels = hotel_result.get("hotels", [])
    reference_places = select_reference_places(poi_info=poi_info, max_places=4)
    hotel_candidates = []

    for hotel in hotels:
        distance_results = calculate_hotel_distances(
            hotel=hotel,
            reference_places=reference_places
        )

        score, reason = score_hotel_candidate(
            hotel=hotel,
            distance_results=distance_results,
            budget_level=budget_level
        )

        valid_distances = [
            item for item in distance_results
            if item.get("distance_km") is not None
        ]

        avg_distance_km = None
        nearest_place = None
        farthest_place = None

        if valid_distances:
            avg_distance_km = round(
                sum(item["distance_km"] for item in valid_distances) / len(valid_distances),
                2
            )
            nearest_place = min(valid_distances, key=lambda item: item["distance_km"]).get("place_name")
            farthest_place = max(valid_distances, key=lambda item: item["distance_km"]).get("place_name")

        hotel_candidates.append({
            "name": hotel.get("name"),
            "type": hotel.get("type"),
            "address": hotel.get("address"),
            "district": hotel.get("district"),
            "longitude": hotel.get("longitude"),
            "latitude": hotel.get("latitude"),
            "photos": hotel.get("photos", []),
            "avg_distance_km": avg_distance_km,
            "nearest_place": nearest_place,
            "farthest_place": farthest_place,
            "distance_results": distance_results,
            "score": score,
            "reason": reason
        })

    hotel_candidates.sort(key=lambda item: item.get("score", 0), reverse=True)
    top_districts = {}

    for item in hotel_candidates:
        district = item.get("district") or "未知区域"
        top_districts[district] = top_districts.get(district, 0) + 1

    district_suggestion = "、".join(list(top_districts.keys())[:3]) or "交通便利区域"

    return {
        "tool_name": "hotel_tool",
        "success": True,
        "destination": destination,
        "city": city,
        "budget_level": budget_level,
        "reference_places": reference_places,
        "hotel_candidates": hotel_candidates,
        "area_suggestion": f"建议优先关注 {district_suggestion} 等区域，并结合预算选择交通便利的酒店。",
        "note": "酒店候选基于高德 POI 和距离测算，仅用于住宿选址参考，不代表实时价格、库存或评分。"
    }
