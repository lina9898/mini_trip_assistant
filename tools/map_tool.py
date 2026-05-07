# tools/map_tool.py

import os
import requests
from dotenv import load_dotenv


load_dotenv()


def get_location(address):
    """
    地图查询工具。
    根据地址或城市名称，查询经纬度和行政区划信息。
    """

    api_key = os.getenv("AMAP_API_KEY")

    if not api_key:
        return {
            "tool_name": "map_tool",
            "success": False,
            "error": "未配置 AMAP_API_KEY",
            "address": address
        }

    url = "https://restapi.amap.com/v3/geocode/geo"

    params = {
        "key": api_key,
        "address": address
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "1" or not data.get("geocodes"):
            return {
                "tool_name": "map_tool",
                "success": False,
                "error": data.get("info", "地图查询失败"),
                "address": address
            }

        geocode = data["geocodes"][0]

        location = geocode.get("location", "")
        longitude, latitude = location.split(",") if "," in location else ("", "")

        return {
            "tool_name": "map_tool",
            "success": True,
            "address": address,
            "formatted_address": geocode.get("formatted_address"),
            "province": geocode.get("province"),
            "city": geocode.get("city"),
            "district": geocode.get("district"),
            "adcode": geocode.get("adcode"),
            "longitude": longitude,
            "latitude": latitude
        }

    except Exception as e:
        return {
            "tool_name": "map_tool",
            "success": False,
            "error": str(e),
            "address": address
        }