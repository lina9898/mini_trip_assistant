# planner.py

import json
from llm_client import chat_with_llm
from prompts import build_trip_plan_prompt


def extract_json_from_text(text):
    """
    尝试从大模型返回内容中提取 JSON。
    兼容 ```json ... ``` 格式。
    """
    text = text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
    elif text.startswith("```"):
        text = text.replace("```", "").strip()

    return json.loads(text)


def generate_trip_plan(
    origin,
    destination,
    start_date,
    travel_dates,
    days,
    preference,
    pace,
    budget_level,
    people,
    location_info=None,
    weather_info=None,
    budget=None,
    poi_info=None,
    route_info=None,
    hotel_info=None,
    transport_info=None,
    event_info=None
):
    """
    使用大模型生成旅行计划。
    大模型会参考地图、天气、预算、POI 和路线距离信息。
    """
    messages = build_trip_plan_prompt(
        origin=origin,
        destination=destination,
        start_date=start_date,
        travel_dates=travel_dates,
        days=days,
        preference=preference,
        pace=pace,
        budget_level=budget_level,
        people=people,
        location_info=location_info,
        weather_info=weather_info,
        budget=budget,
        poi_info=poi_info,
        route_info=route_info,
        hotel_info=hotel_info,
        transport_info=transport_info,
        event_info=event_info
    )

    llm_result = chat_with_llm(messages, temperature=0.2)

    try:
        return extract_json_from_text(llm_result)
    except json.JSONDecodeError:
        raise ValueError(
            "大模型返回内容不是合法 JSON，请降低 temperature 或检查提示词。\n"
            f"模型原始返回内容：\n{llm_result}"
        )
