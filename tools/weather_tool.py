# tools/weather_tool.py

import os
import requests
from dotenv import load_dotenv
from date_utils import days_from_today


load_dotenv()


def request_amap_weather(adcode, extensions):
    """
    调用高德天气查询接口。
    extensions=base：实况天气
    extensions=all：预报天气
    """
    api_key = os.getenv("AMAP_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "未配置 AMAP_API_KEY"
        }

    url = "https://restapi.amap.com/v3/weather/weatherInfo"

    params = {
        "key": api_key,
        "city": adcode,
        "extensions": extensions,
        "output": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "1":
            return {
                "success": False,
                "error": data.get("info", "天气查询失败"),
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


def parse_live_weather(raw_data, start_date=None, days=1):
    """
    解析实况天气。
    """
    lives = raw_data.get("lives", [])

    if not lives:
        return {
            "tool_name": "weather_tool",
            "success": False,
            "mode": "live",
            "error": "未获取到实况天气数据"
        }

    live = lives[0]

    return {
        "tool_name": "weather_tool",
        "success": True,
        "mode": "live",
        "start_date": start_date,
        "days": days,
        "province": live.get("province"),
        "city": live.get("city"),
        "weather": live.get("weather"),
        "temperature": live.get("temperature"),
        "winddirection": live.get("winddirection"),
        "windpower": live.get("windpower"),
        "humidity": live.get("humidity"),
        "reporttime": live.get("reporttime"),
        "note": "当前出行日期为今天或未提供出行日期，已使用实况天气。"
    }


def parse_forecast_weather(raw_data, start_date=None, days=1):
    """
    解析天气预报。
    """
    forecasts = raw_data.get("forecasts", [])

    if not forecasts:
        return {
            "tool_name": "weather_tool",
            "success": False,
            "mode": "forecast",
            "error": "未获取到天气预报数据"
        }

    forecast = forecasts[0]
    casts = forecast.get("casts", [])

    if start_date:
        selected_casts = [
            item for item in casts
            if item.get("date") and item.get("date") >= start_date
        ][:days]
    else:
        selected_casts = casts[:days]

    if not selected_casts:
        selected_casts = casts[:days]

    return {
        "tool_name": "weather_tool",
        "success": True,
        "mode": "forecast",
        "start_date": start_date,
        "days": days,
        "province": forecast.get("province"),
        "city": forecast.get("city"),
        "adcode": forecast.get("adcode"),
        "reporttime": forecast.get("reporttime"),
        "forecasts": [
            {
                "date": item.get("date"),
                "week": item.get("week"),
                "dayweather": item.get("dayweather"),
                "nightweather": item.get("nightweather"),
                "daytemp": item.get("daytemp"),
                "nighttemp": item.get("nighttemp"),
                "daywind": item.get("daywind"),
                "nightwind": item.get("nightwind"),
                "daypower": item.get("daypower"),
                "nightpower": item.get("nightpower")
            }
            for item in selected_casts
        ],
        "note": "计划出行日期在短期预报范围内，已使用天气预报数据。"
    }


def get_weather_by_adcode(adcode, start_date=None, days=1):
    """
    根据 adcode 和计划出行日期查询天气。

    规则：
    1. start_date 为空：查询实况天气
    2. start_date 是今天：查询实况天气
    3. start_date 是未来 1-4 天：查询预报天气
    4. start_date 超过未来 4 天：返回超范围提示
    5. start_date 是过去日期：返回无效日期提示
    """
    if not adcode:
        return {
            "tool_name": "weather_tool",
            "success": False,
            "mode": "missing_adcode",
            "error": "缺少 adcode，无法查询天气"
        }

    if not start_date:
        result = request_amap_weather(adcode=adcode, extensions="base")

        if not result.get("success"):
            return {
                "tool_name": "weather_tool",
                "success": False,
                "mode": "live",
                "error": result.get("error")
            }

        return parse_live_weather(result["raw"], start_date=start_date, days=days)

    try:
        delta_days = days_from_today(start_date)
    except Exception:
        return {
            "tool_name": "weather_tool",
            "success": False,
            "mode": "invalid_date",
            "start_date": start_date,
            "error": "出行日期格式无效，请使用 YYYY-MM-DD"
        }

    if delta_days < 0:
        return {
            "tool_name": "weather_tool",
            "success": False,
            "mode": "past_date",
            "start_date": start_date,
            "days": days,
            "error": "出行日期早于今天，无法查询历史天气。"
        }

    if delta_days == 0:
        result = request_amap_weather(adcode=adcode, extensions="base")

        if not result.get("success"):
            return {
                "tool_name": "weather_tool",
                "success": False,
                "mode": "live",
                "start_date": start_date,
                "error": result.get("error")
            }

        return parse_live_weather(result["raw"], start_date=start_date, days=days)

    if 1 <= delta_days <= 4:
        result = request_amap_weather(adcode=adcode, extensions="all")

        if not result.get("success"):
            return {
                "tool_name": "weather_tool",
                "success": False,
                "mode": "forecast",
                "start_date": start_date,
                "days": days,
                "error": result.get("error")
            }

        return parse_forecast_weather(result["raw"], start_date=start_date, days=days)

    return {
        "tool_name": "weather_tool",
        "success": False,
        "mode": "out_of_range",
        "start_date": start_date,
        "days": days,
        "error": "出行日期超出短期天气预报范围，当前无法准确查询出行当天的天气。请临近出发前再次查询。",
        "note": "行程生成时不要编造具体天气，只能给出通用季节性提醒。"
    }
