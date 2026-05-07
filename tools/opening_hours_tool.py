# tools/opening_hours_tool.py

import os
import re
import requests
from dotenv import load_dotenv


load_dotenv()


PERIOD_TIME = {
    "morning": "09:00",
    "afternoon": "14:00",
    "evening": "19:00"
}


def search_place_business_info(place_name, city=None):
    """
    使用高德 POI 2.0 查询地点 business 信息，包括开放时间。
    """
    api_key = os.getenv("AMAP_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "未配置 AMAP_API_KEY",
            "place_name": place_name
        }

    url = "https://restapi.amap.com/v5/place/text"
    params = {
        "key": api_key,
        "keywords": place_name,
        "region": city or "",
        "city_limit": "true" if city else "false",
        "page_size": 3,
        "page_num": 1,
        "show_fields": "business",
        "output": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "1":
            return {
                "success": False,
                "error": data.get("info", "开放时间查询失败"),
                "place_name": place_name,
                "raw": data
            }

        pois = data.get("pois", [])

        if not pois:
            return {
                "success": False,
                "error": "未匹配到 POI",
                "place_name": place_name
            }

        poi = pois[0]
        business = poi.get("business", {}) or {}

        return {
            "success": True,
            "place_name": place_name,
            "matched_poi_name": poi.get("name"),
            "type": poi.get("type"),
            "address": poi.get("address"),
            "city": poi.get("cityname"),
            "district": poi.get("adname"),
            "opentime_today": business.get("opentime_today"),
            "opentime_week": business.get("opentime_week"),
            "business_area": business.get("business_area")
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "place_name": place_name
        }


def extract_places_from_day_text(text):
    """
    从某个时段文本中粗略提取地点名称。
    """
    if not text:
        return []

    parts = re.split(r"[，。；;、,\n/→\-—]", text)
    stop_words = [
        "上午", "下午", "晚上", "早餐", "午餐", "晚餐",
        "游览", "前往", "体验", "打卡", "参观", "漫步",
        "安排", "建议", "附近", "周边", "自由活动",
        "休息", "拍照", "美食", "夜景", "路线", "时间"
    ]

    places = []

    for part in parts:
        part = part.strip()

        if not part:
            continue

        for word in stop_words:
            part = part.replace(word, "").strip()

        if 2 <= len(part) <= 12:
            places.append(part)

    result = []
    seen = set()

    for place in places:
        if place not in seen:
            seen.add(place)
            result.append(place)

    return result


def parse_hour_minute(time_text):
    """
    将 HH:MM 转换为分钟。
    """
    try:
        hour, minute = time_text.split(":")
        return int(hour) * 60 + int(minute)
    except Exception:
        return None


def extract_time_ranges(open_time_text):
    """
    从开放时间文本中提取类似 09:00-17:00 的时间段。
    """
    if not open_time_text:
        return []

    pattern = r"(\d{1,2}:\d{2})\s*[-~—至到]\s*(\d{1,2}:\d{2})"
    matches = re.findall(pattern, open_time_text)
    ranges = []

    for start, end in matches:
        start_min = parse_hour_minute(start)
        end_min = parse_hour_minute(end)

        if start_min is not None and end_min is not None:
            ranges.append({
                "start": start,
                "end": end,
                "start_min": start_min,
                "end_min": end_min
            })

    return ranges


def check_period_against_opening(period, opentime_today, opentime_week):
    """
    根据行程时段和开放时间判断风险。
    """
    target_time = PERIOD_TIME.get(period)
    target_min = parse_hour_minute(target_time) if target_time else None
    combined_text = f"{opentime_today or ''} {opentime_week or ''}"

    if "全天" in combined_text or "24小时" in combined_text:
        return {
            "risk_level": "low",
            "message": "开放时间显示为全天或 24 小时，当前时段通常可行。"
        }

    if any(word in combined_text for word in ["闭馆", "暂停开放", "不开放", "休息"]):
        return {
            "risk_level": "high",
            "message": "开放时间信息中包含闭馆/暂停开放等提示，建议调整或出行前确认。"
        }

    if not opentime_today and not opentime_week:
        return {
            "risk_level": "medium",
            "message": "未查询到明确开放时间，建议出行前通过官方渠道确认。"
        }

    ranges = extract_time_ranges(combined_text)

    if not ranges or target_min is None:
        return {
            "risk_level": "medium",
            "message": "开放时间格式不够明确，建议出行前确认。"
        }

    for item in ranges:
        start_min = item["start_min"]
        end_min = item["end_min"]

        if end_min < start_min:
            if target_min >= start_min or target_min <= end_min:
                return {
                    "risk_level": "low",
                    "message": "该时段可能在开放时间内，但建议以官方信息为准。"
                }
        elif start_min <= target_min <= end_min:
            return {
                "risk_level": "low",
                "message": "该时段大致在开放时间内。"
            }

    if period == "evening":
        return {
            "risk_level": "high",
            "message": "该地点开放时间可能不覆盖晚上时段，不建议安排为晚间活动。"
        }

    return {
        "risk_level": "medium",
        "message": "该时段可能不完全匹配开放时间，建议调整时间或提前确认。"
    }


def check_trip_opening_hours(trip_data, city=None, max_places_per_day=4):
    """
    检查行程中地点的开放时间风险。
    """
    plan = trip_data.get("plan", [])
    checks = []

    for day_plan in plan:
        day = day_plan.get("day")
        date = day_plan.get("date")
        period_fields = {
            "morning": day_plan.get("morning", ""),
            "afternoon": day_plan.get("afternoon", ""),
            "evening": day_plan.get("evening", "")
        }
        day_place_count = 0

        for period, text in period_fields.items():
            places = extract_places_from_day_text(text)

            for place_name in places:
                if day_place_count >= max_places_per_day:
                    break

                info = search_place_business_info(place_name=place_name, city=city)

                if not info.get("success"):
                    checks.append({
                        "day": day,
                        "date": date,
                        "period": period,
                        "place_name": place_name,
                        "success": False,
                        "risk_level": "medium",
                        "message": f"未能查询到该地点开放时间：{info.get('error')}",
                        "opentime_today": None,
                        "opentime_week": None
                    })
                    day_place_count += 1
                    continue

                risk = check_period_against_opening(
                    period=period,
                    opentime_today=info.get("opentime_today"),
                    opentime_week=info.get("opentime_week")
                )

                checks.append({
                    "day": day,
                    "date": date,
                    "period": period,
                    "place_name": place_name,
                    "success": True,
                    "matched_poi_name": info.get("matched_poi_name"),
                    "type": info.get("type"),
                    "address": info.get("address"),
                    "opentime_today": info.get("opentime_today"),
                    "opentime_week": info.get("opentime_week"),
                    "risk_level": risk.get("risk_level"),
                    "message": risk.get("message")
                })
                day_place_count += 1

    high_risk_count = len([item for item in checks if item.get("risk_level") == "high"])
    medium_risk_count = len([item for item in checks if item.get("risk_level") == "medium"])

    return {
        "tool_name": "opening_hours_tool",
        "success": True if checks else False,
        "checks": checks,
        "summary": {
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "total_checked": len(checks),
            "suggestion": "请优先调整高风险地点；开放时间可能受节假日和临时公告影响，出行前仍需确认官方信息。"
        }
    }
