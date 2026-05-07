# itinerary_editor.py

import json
from llm_client import chat_with_llm
from prompts import build_edit_itinerary_prompt


def extract_json_from_text(text):
    """
    从大模型返回内容中提取 JSON。
    兼容 ```json ... ``` 格式。
    """
    text = text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
    elif text.startswith("```"):
        text = text.replace("```", "").strip()

    return json.loads(text)


def edit_itinerary(
    original_trip_data,
    user_edit_request,
    location_info=None,
    weather_info=None,
    budget=None,
    memory_text=None
):
    """
    根据用户修改要求，编辑已有旅行计划。
    """
    messages = build_edit_itinerary_prompt(
        original_trip_data=original_trip_data,
        user_edit_request=user_edit_request,
        location_info=location_info,
        weather_info=weather_info,
        budget=budget,
        memory_text=memory_text
    )

    llm_result = chat_with_llm(messages, temperature=0.2)

    try:
        return extract_json_from_text(llm_result)
    except json.JSONDecodeError:
        raise ValueError(
            "大模型返回的修改后行程不是合法 JSON。\n"
            f"模型原始返回内容：\n{llm_result}"
        )
