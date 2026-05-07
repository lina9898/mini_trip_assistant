# tool_planner.py

import json
from llm_client import chat_with_llm
from prompts import build_tool_plan_prompt
from tools.tool_registry import list_tools


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


def build_user_request(origin, destination, start_date, end_date, days, preference, pace, budget_level, people):
    """
    将用户输入整理成一段完整需求描述，方便大模型理解。
    """
    return f"""
出发地：{origin}
目的地：{destination}
计划出行日期：{start_date}
计划结束日期：{end_date}
旅行天数：{days}
旅行偏好：{preference}
旅行节奏：{pace}
预算档位：{budget_level}
出行人数：{people}
"""


def plan_tool_calls(origin, destination, start_date, end_date, days, preference, pace, budget_level, people):
    """
    让大模型根据用户需求和已注册工具，生成工具调用计划。
    """
    user_request = build_user_request(
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        days=days,
        preference=preference,
        pace=pace,
        budget_level=budget_level,
        people=people
    )

    tool_list = [
        tool for tool in list_tools()
        if tool.get("name") not in ["opening_hours_tool"]
    ]

    messages = build_tool_plan_prompt(
        user_request=user_request,
        tool_list=tool_list
    )

    llm_result = chat_with_llm(messages, temperature=0.1)

    try:
        return extract_json_from_text(llm_result)
    except json.JSONDecodeError:
        raise ValueError(
            "大模型返回的工具调用计划不是合法 JSON。\n"
            f"模型原始返回内容：\n{llm_result}"
        )
