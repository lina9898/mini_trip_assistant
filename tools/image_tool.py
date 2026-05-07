# tools/image_tool.py

import os
import re

import requests
from dotenv import load_dotenv
from tools.poi_tool import search_poi_v5_by_keyword


load_dotenv()


def build_image_queries(destination, preference=None, poi_info=None, max_queries=4):
    """
    根据目的地、偏好和 POI 信息构造图片搜索关键词。
    """
    queries = []

    if destination:
        queries.append(f"{destination} travel")

    preference = preference or ""

    if "自然" in preference or "风光" in preference or "拍照" in preference:
        queries.append(f"{destination} landscape")
    if "历史" in preference or "文化" in preference:
        queries.append(f"{destination} architecture")
    if "美食" in preference:
        queries.append(f"{destination} food")
    if "购物" in preference:
        queries.append(f"{destination} city street")

    pois = poi_info.get("pois", []) if poi_info else []

    for poi in pois[:3]:
        name = poi.get("name")
        if name:
            queries.append(f"{destination} {name}")

    unique_queries = []
    seen = set()

    for query in queries:
        if query not in seen:
            seen.add(query)
            unique_queries.append(query)

    return unique_queries[:max_queries]


def extract_trip_text(trip_data):
    """
    提取行程文本，用于判断哪些 POI 真正在最终行程中出现。
    """
    if not trip_data:
        return ""

    parts = [
        str(trip_data.get("destination", "")),
        str(trip_data.get("route_strategy", "")),
        str(trip_data.get("advice", "")),
        str(trip_data.get("backup_plan", ""))
    ]

    for day_plan in trip_data.get("plan", []):
        parts.extend([
            str(day_plan.get("morning", "")),
            str(day_plan.get("afternoon", "")),
            str(day_plan.get("evening", "")),
            str(day_plan.get("note", "")),
            str(day_plan.get("reason", ""))
        ])

    return "\n".join(parts)


def select_planned_pois(trip_data, poi_info=None, max_pois=6):
    """
    从 POI 列表中筛选真正出现在最终行程文本里的地点。
    """
    trip_text = extract_trip_text(trip_data)
    pois = poi_info.get("pois", []) if poi_info else []
    selected = []
    seen_names = set()

    for poi in pois:
        name = poi.get("name")
        if not name or name in seen_names:
            continue

        if name in trip_text:
            selected.append(poi)
            seen_names.add(name)

        if len(selected) >= max_pois:
            break

    return selected


def build_trip_image_queries(destination, trip_data, poi_info=None, max_queries=6):
    """
    基于最终行程中实际出现的 POI 构造图片搜索关键词。
    """
    queries = []
    planned_pois = select_planned_pois(
        trip_data=trip_data,
        poi_info=poi_info,
        max_pois=max_queries
    )

    for poi in planned_pois:
        name = poi.get("name")
        district = poi.get("district")
        if name:
            query = f"{destination} {name}"
            if district and district not in name:
                query = f"{query} {district}"
            queries.append(query)

    if not queries and destination:
        queries.append(f"{destination} travel")

    unique_queries = []
    seen = set()

    for query in queries:
        if query not in seen:
            seen.add(query)
            unique_queries.append(query)

    return unique_queries[:max_queries]


def search_unsplash_photos(query, per_page=3, orientation="landscape"):
    """
    调用 Unsplash Search Photos API 搜索图片。
    """
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")

    if not access_key:
        return {
            "success": False,
            "query": query,
            "error": "未配置 UNSPLASH_ACCESS_KEY",
            "photos": []
        }

    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "per_page": per_page,
        "page": 1,
        "orientation": orientation,
        "client_id": access_key
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200:
            return {
                "success": False,
                "query": query,
                "error": data.get("errors", data),
                "photos": []
            }

        photos = []

        for item in data.get("results", []):
            user = item.get("user", {}) or {}
            urls = item.get("urls", {}) or {}
            links = item.get("links", {}) or {}
            user_links = user.get("links", {}) or {}

            photos.append({
                "id": item.get("id"),
                "query": query,
                "description": item.get("description") or item.get("alt_description") or "",
                "image_url": urls.get("regular") or urls.get("small"),
                "thumb_url": urls.get("thumb"),
                "download_location": links.get("download_location"),
                "photo_page": links.get("html"),
                "photographer_name": user.get("name"),
                "photographer_profile": user_links.get("html"),
                "unsplash_source": "Unsplash"
            })

        return {
            "success": True,
            "query": query,
            "count": len(photos),
            "photos": photos
        }

    except Exception as e:
        return {
            "success": False,
            "query": query,
            "error": str(e),
            "photos": []
        }


def search_images(destination, preference=None, poi_info=None, per_page=2):
    """
    图片搜索工具。
    根据目的地、偏好和 POI 信息，从 Unsplash 搜索旅行相关图片。
    """
    queries = build_image_queries(
        destination=destination,
        preference=preference,
        poi_info=poi_info
    )

    all_photos = []
    search_logs = []
    seen_ids = set()

    for query in queries:
        result = search_unsplash_photos(
            query=query,
            per_page=per_page,
            orientation="landscape"
        )

        search_logs.append({
            "query": query,
            "success": result.get("success"),
            "count": result.get("count", 0),
            "error": result.get("error")
        })

        if result.get("success"):
            for photo in result.get("photos", []):
                photo_id = photo.get("id")

                if photo_id in seen_ids:
                    continue

                seen_ids.add(photo_id)
                all_photos.append(photo)

    return {
        "tool_name": "image_tool",
        "success": True if all_photos else False,
        "destination": destination,
        "preference": preference,
        "queries": queries,
        "count": len(all_photos),
        "photos": all_photos,
        "search_logs": search_logs,
        "error": None if all_photos else "未查询到有效图片结果"
    }


def search_trip_images(destination, trip_data, poi_info=None, per_page=1):
    """
    根据最终行程中实际出现的 POI 搜索图片。
    这比通用目的地图片更贴近 HTML / PDF 报告内容。
    """
    queries = build_trip_image_queries(
        destination=destination,
        trip_data=trip_data,
        poi_info=poi_info
    )

    all_photos = []
    search_logs = []
    seen_ids = set()

    for query in queries:
        result = search_unsplash_photos(
            query=query,
            per_page=per_page,
            orientation="landscape"
        )

        search_logs.append({
            "query": query,
            "success": result.get("success"),
            "count": result.get("count", 0),
            "error": result.get("error")
        })

        if result.get("success"):
            for photo in result.get("photos", []):
                photo_id = photo.get("id")

                if photo_id in seen_ids:
                    continue

                seen_ids.add(photo_id)
                all_photos.append(photo)

    return {
        "tool_name": "image_tool",
        "success": True if all_photos else False,
        "destination": destination,
        "queries": queries,
        "count": len(all_photos),
        "photos": all_photos,
        "search_logs": search_logs,
        "image_strategy": "matched_final_itinerary_pois",
        "error": None if all_photos else "未根据最终行程查询到有效图片结果"
    }


def extract_places_from_text(text, destination=None):
    """
    从一段行程文本中粗略提取地点名称。
    当前使用规则法，避免为了配图额外调用 LLM。
    """
    if not text:
        return []

    candidates = []
    parts = re.split(r"[，。；;、,\n/→\-—]", str(text))
    stop_words = [
        "上午", "下午", "晚上", "早餐", "午餐", "晚餐",
        "游览", "前往", "体验", "打卡", "参观", "漫步",
        "安排", "建议", "附近", "周边", "自由活动",
        "休息", "拍照", "美食", "夜景", "路线", "适合"
    ]

    for part in parts:
        part = part.strip()

        if not part:
            continue

        if destination:
            part = part.replace(destination, "").strip()

        for word in stop_words:
            part = part.replace(word, "").strip()

        part = part.strip(" ：:（）()“”\"'")

        if 2 <= len(part) <= 12:
            candidates.append(part)

    result = []
    seen = set()

    for item in candidates:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result


def extract_places_from_trip_data(trip_data, max_places_per_day=4):
    """
    从 trip_data.plan 中提取每天涉及的地点。
    """
    plan = trip_data.get("plan", [])
    destination = trip_data.get("destination")
    day_places = []

    for day_plan in plan:
        day = day_plan.get("day")
        date = day_plan.get("date")
        texts = [
            day_plan.get("morning", ""),
            day_plan.get("afternoon", ""),
            day_plan.get("evening", "")
        ]

        places = []

        for text in texts:
            places.extend(extract_places_from_text(text, destination=destination))

        unique_places = []
        seen = set()

        for place in places:
            if place not in seen:
                seen.add(place)
                unique_places.append(place)

            if len(unique_places) >= max_places_per_day:
                break

        day_places.append({
            "day": day,
            "date": date,
            "places": unique_places
        })

    return day_places


def find_matching_poi(place_name, poi_info):
    """
    从 poi_info 中查找和 place_name 最相近的 POI。
    """
    pois = poi_info.get("pois", []) if poi_info else []

    for poi in pois:
        poi_name = poi.get("name", "")

        if not poi_name:
            continue

        if place_name == poi_name:
            return poi

        if place_name in poi_name or poi_name in place_name:
            return poi

    return None


def build_image_from_amap_poi(place_name, poi):
    """
    如果 POI 中有 photos，则构造图片对象。
    """
    photos = poi.get("photos", []) or []

    if not photos:
        return None

    first_photo = photos[0]
    image_url = first_photo.get("url")

    if not image_url:
        return None

    return {
        "place_name": place_name,
        "image_url": image_url,
        "description": first_photo.get("title") or poi.get("name") or place_name,
        "source": "amap_poi",
        "matched_poi_name": poi.get("name"),
        "credit": "图片来源：高德 POI",
        "photo_page": None,
        "photographer_name": None,
        "photographer_profile": None
    }


def build_image_from_unsplash(place_name, destination=None):
    """
    使用 Unsplash 按具体地点兜底搜索图片。
    """
    query = f"{destination} {place_name}" if destination else place_name
    result = search_unsplash_photos(
        query=query,
        per_page=1,
        orientation="landscape"
    )

    if not result.get("success") or not result.get("photos"):
        return None

    photo = result["photos"][0]

    return {
        "place_name": place_name,
        "image_url": photo.get("image_url"),
        "description": photo.get("description") or place_name,
        "source": "unsplash",
        "matched_poi_name": None,
        "credit": f"Photo by {photo.get('photographer_name')} on Unsplash",
        "photo_page": photo.get("photo_page"),
        "photographer_name": photo.get("photographer_name"),
        "photographer_profile": photo.get("photographer_profile")
    }


def build_image_from_amap_v5(place_name, destination=None):
    """
    使用高德 POI 2.0 按具体地点搜索图片。
    """
    keyword = f"{destination}{place_name}" if destination else place_name
    result = search_poi_v5_by_keyword(
        keyword=keyword,
        city=destination,
        page_size=3
    )

    if not result.get("success"):
        return None

    for poi in result.get("pois", []):
        image_item = build_image_from_amap_poi(
            place_name=place_name,
            poi=poi
        )

        if image_item:
            return image_item

    return None


def match_images_for_trip(trip_data, poi_info=None, destination=None, max_images_per_day=3):
    """
    根据最终行程中的具体地点匹配图片。

    优先级：
    1. 从 poi_info 中匹配同名 POI，并使用 POI photos
    2. 如果没有 POI 图片，则用 Unsplash 按具体地点兜底搜索
    3. 如果仍然没有图片，则该地点不展示图片
    """
    destination = destination or trip_data.get("destination")
    day_places = extract_places_from_trip_data(trip_data)
    day_images = []
    total_images = 0
    logs = []

    for day_item in day_places:
        day = day_item.get("day")
        date = day_item.get("date")
        places = day_item.get("places", [])
        place_images = []

        for place_name in places:
            image_item = None
            matched_poi = find_matching_poi(place_name, poi_info)

            if matched_poi:
                image_item = build_image_from_amap_poi(
                    place_name=place_name,
                    poi=matched_poi
                )

            if not image_item:
                image_item = build_image_from_amap_v5(
                    place_name=place_name,
                    destination=destination
                )

            if not image_item:
                image_item = build_image_from_unsplash(
                    place_name=place_name,
                    destination=destination
                )

            if image_item and image_item.get("image_url"):
                place_images.append(image_item)
                total_images += 1
                logs.append({
                    "day": day,
                    "place_name": place_name,
                    "success": True,
                    "source": image_item.get("source"),
                    "matched_poi_name": image_item.get("matched_poi_name")
                })
            else:
                logs.append({
                    "day": day,
                    "place_name": place_name,
                    "success": False,
                    "source": None,
                    "matched_poi_name": matched_poi.get("name") if matched_poi else None
                })

            if len(place_images) >= max_images_per_day:
                break

        day_images.append({
            "day": day,
            "date": date,
            "place_images": place_images
        })

    return {
        "tool_name": "image_tool",
        "success": total_images > 0,
        "mode": "place_matched",
        "destination": destination,
        "total_images": total_images,
        "day_images": day_images,
        "logs": logs,
        "error": None if total_images > 0 else "未能为行程地点匹配到有效图片"
    }
