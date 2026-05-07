# tools/poi_tool.py

import os

import requests
from dotenv import load_dotenv


load_dotenv()


def build_keywords(destination, preference):
    """
    根据旅行偏好构造 POI 搜索关键词。
    """
    preference = preference or ""
    keywords = []

    if "自然" in preference or "风光" in preference or "拍照" in preference:
        keywords.extend(["景点", "公园", "风景区"])

    if "历史" in preference or "文化" in preference:
        keywords.extend(["博物馆", "历史文化", "古迹"])

    if "美食" in preference:
        keywords.extend(["美食", "小吃", "餐厅"])

    if "购物" in preference:
        keywords.extend(["商场", "步行街", "购物中心"])

    if "亲子" in preference:
        keywords.extend(["亲子", "游乐园", "动物园"])

    if not keywords:
        keywords.append("景点")

    return [f"{destination}{keyword}" for keyword in keywords]


def search_poi_by_keyword(keyword, city=None, page_size=10):
    """
    调用高德 POI 关键字搜索接口。
    """
    api_key = os.getenv("AMAP_API_KEY")

    if not api_key:
        return {
            "tool_name": "poi_tool",
            "success": False,
            "error": "未配置 AMAP_API_KEY",
            "keyword": keyword,
            "pois": []
        }

    url = "https://restapi.amap.com/v3/place/text"
    params = {
        "key": api_key,
        "keywords": keyword,
        "offset": page_size,
        "page": 1,
        "extensions": "base",
        "output": "JSON"
    }

    if city:
        params["city"] = city
        params["citylimit"] = "true"

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "1":
            return {
                "tool_name": "poi_tool",
                "success": False,
                "error": data.get("info", "POI 查询失败"),
                "keyword": keyword,
                "pois": []
            }

        pois = []

        for poi in data.get("pois", []):
            location = poi.get("location", "")
            longitude = ""
            latitude = ""

            if "," in location:
                longitude, latitude = location.split(",", 1)

            pois.append({
                "id": poi.get("id"),
                "name": poi.get("name"),
                "type": poi.get("type"),
                "typecode": poi.get("typecode"),
                "address": poi.get("address"),
                "province": poi.get("pname"),
                "city": poi.get("cityname"),
                "district": poi.get("adname"),
                "longitude": longitude,
                "latitude": latitude,
                "tel": poi.get("tel"),
                "keyword": keyword
            })

        return {
            "tool_name": "poi_tool",
            "success": True,
            "keyword": keyword,
            "count": len(pois),
            "pois": pois
        }

    except Exception as e:
        return {
            "tool_name": "poi_tool",
            "success": False,
            "error": str(e),
            "keyword": keyword,
            "pois": []
        }


def search_poi_v5_by_keyword(keyword, city=None, page_size=5):
    """
    使用高德 POI 2.0 关键字搜索，尝试获取 photos 字段。
    """
    api_key = os.getenv("AMAP_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "未配置 AMAP_API_KEY",
            "keyword": keyword,
            "pois": []
        }

    url = "https://restapi.amap.com/v5/place/text"
    params = {
        "key": api_key,
        "keywords": keyword,
        "region": city or "",
        "city_limit": "true" if city else "false",
        "page_size": page_size,
        "page_num": 1,
        "show_fields": "photos",
        "output": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "1":
            return {
                "success": False,
                "error": data.get("info", "POI 2.0 查询失败"),
                "keyword": keyword,
                "pois": [],
                "raw": data
            }

        pois = []

        for poi in data.get("pois", []):
            location = poi.get("location", "")
            longitude = ""
            latitude = ""

            if "," in location:
                longitude, latitude = location.split(",", 1)

            photos = []

            for photo in poi.get("photos", []) or []:
                photo_url = photo.get("url")
                photo_title = photo.get("title")

                if photo_url:
                    photos.append({
                        "title": photo_title,
                        "url": photo_url
                    })

            pois.append({
                "id": poi.get("id"),
                "name": poi.get("name"),
                "type": poi.get("type"),
                "typecode": poi.get("typecode"),
                "address": poi.get("address"),
                "province": poi.get("pname"),
                "city": poi.get("cityname"),
                "district": poi.get("adname"),
                "longitude": longitude,
                "latitude": latitude,
                "photos": photos,
                "keyword": keyword,
                "source": "amap_v5"
            })

        return {
            "success": True,
            "keyword": keyword,
            "count": len(pois),
            "pois": pois
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "keyword": keyword,
            "pois": []
        }


def search_pois(destination, preference=None, city=None, page_size=8):
    """
    综合 POI 搜索工具。
    根据目的地和偏好，搜索多个关键词，并合并结果。
    """
    keywords = build_keywords(destination, preference)
    all_pois = []
    search_logs = []
    seen_ids = set()

    for keyword in keywords:
        result = search_poi_by_keyword(
            keyword=keyword,
            city=city,
            page_size=page_size
        )

        search_logs.append({
            "keyword": keyword,
            "success": result.get("success"),
            "count": result.get("count", 0),
            "error": result.get("error")
        })

        if result.get("success"):
            for poi in result.get("pois", []):
                poi_id = poi.get("id") or poi.get("name")

                if poi_id in seen_ids:
                    continue

                seen_ids.add(poi_id)
                all_pois.append(poi)

    return {
        "tool_name": "poi_tool",
        "success": True if all_pois else False,
        "destination": destination,
        "preference": preference,
        "city": city,
        "keywords": keywords,
        "count": len(all_pois),
        "pois": all_pois,
        "search_logs": search_logs,
        "error": None if all_pois else "未查询到有效 POI 结果"
    }
