# tools/event_tool.py

import os
import requests
from dotenv import load_dotenv


load_dotenv()


def to_ticketmaster_datetime(date_text, end_of_day=False):
    """
    将 YYYY-MM-DD 转换为 Ticketmaster 需要的日期时间格式。
    """
    if end_of_day:
        return f"{date_text}T23:59:59Z"

    return f"{date_text}T00:00:00Z"


def normalize_event_category(classifications):
    """
    从 Ticketmaster classifications 中提取活动类别。
    """
    if not classifications:
        return "other"

    item = classifications[0]
    segment = item.get("segment", {}) or {}
    genre = item.get("genre", {}) or {}

    segment_name = segment.get("name", "").lower()
    genre_name = genre.get("name", "").lower()

    if "music" in segment_name or "concert" in genre_name:
        return "music"

    if "sports" in segment_name:
        return "sports"

    if "arts" in segment_name or "theatre" in genre_name or "theater" in genre_name:
        return "arts"

    if "film" in segment_name:
        return "film"

    return segment.get("name") or genre.get("name") or "other"


def build_event_recommendation(event):
    """
    根据活动类别和时间生成简单建议。
    """
    category = event.get("category")
    name = event.get("name")
    date = event.get("date")
    time = event.get("time")
    venue = event.get("venue")

    if category == "music":
        return f"{name} 可作为夜间特色活动备选，若感兴趣需提前确认票务和散场交通。"

    if category == "sports":
        return f"{name} 可能带来场馆周边人流和交通压力，建议避开散场高峰或预留交通时间。"

    if category == "arts":
        return f"{name} 可作为文化体验活动备选，适合替代部分室内景点安排。"

    return f"{name} 位于 {venue}，时间为 {date} {time}，可根据兴趣作为备选活动。"


def search_ticketmaster_events(destination, start_date, end_date, size=10):
    """
    使用 Ticketmaster Discovery API 查询活动。
    """
    api_key = os.getenv("TICKETMASTER_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "未配置 TICKETMASTER_API_KEY",
            "events": []
        }

    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": api_key,
        "city": destination,
        "startDateTime": to_ticketmaster_datetime(start_date),
        "endDateTime": to_ticketmaster_datetime(end_date, end_of_day=True),
        "size": size,
        "sort": "date,asc"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200:
            return {
                "success": False,
                "error": data.get("fault", {}).get("faultstring", data),
                "events": [],
                "raw": data
            }

        raw_events = data.get("_embedded", {}).get("events", [])
        events = []

        for item in raw_events:
            dates = item.get("dates", {}) or {}
            start = dates.get("start", {}) or {}
            venues = item.get("_embedded", {}).get("venues", [])
            venue = venues[0] if venues else {}
            images = item.get("images", []) or []
            image_url = images[0].get("url") if images else None

            event = {
                "name": item.get("name"),
                "date": start.get("localDate"),
                "time": start.get("localTime"),
                "venue": venue.get("name"),
                "city": venue.get("city", {}).get("name"),
                "address": venue.get("address", {}).get("line1"),
                "url": item.get("url"),
                "image_url": image_url,
                "category": normalize_event_category(item.get("classifications", [])),
                "source": "ticketmaster"
            }
            event["recommendation"] = build_event_recommendation(event)
            events.append(event)

        return {
            "success": True,
            "events": events,
            "count": len(events)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "events": []
        }


def analyze_event_impact(events):
    """
    分析活动对旅行的影响。
    """
    high_impact_categories = ["music", "sports"]
    high_impact_events = [
        event for event in events
        if event.get("category") in high_impact_categories
    ]

    if not events:
        return {
            "event_count": 0,
            "high_impact_count": 0,
            "suggestion": "未查询到明确活动信息。"
        }

    if high_impact_events:
        return {
            "event_count": len(events),
            "high_impact_count": len(high_impact_events),
            "suggestion": "出行期间可能存在演唱会、赛事等大型活动，建议提前关注场馆周边交通、住宿价格和人流情况。"
        }

    return {
        "event_count": len(events),
        "high_impact_count": 0,
        "suggestion": "出行期间查询到部分活动，可根据兴趣作为备选安排；仍建议以官方活动信息为准。"
    }


def search_city_events(destination, start_date, end_date):
    """
    城市活动工具主函数。
    """
    ticketmaster_result = search_ticketmaster_events(
        destination=destination,
        start_date=start_date,
        end_date=end_date
    )

    if not ticketmaster_result.get("success"):
        return {
            "tool_name": "event_tool",
            "success": False,
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "events": [],
            "summary": {
                "event_count": 0,
                "high_impact_count": 0,
                "suggestion": "未能查询到实时活动数据，建议出行前通过官方票务平台或城市活动平台确认。"
            },
            "error": ticketmaster_result.get("error"),
            "note": "当前活动工具未接入国内主流票务平台，结果可能不覆盖本地演出、漫展、展览等活动。"
        }

    events = ticketmaster_result.get("events", [])
    summary = analyze_event_impact(events)

    return {
        "tool_name": "event_tool",
        "success": True,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "events": events,
        "summary": summary,
        "note": "活动信息来自 Ticketmaster Discovery API，仅作出行参考；请以活动官方页面和票务平台为准。"
    }
