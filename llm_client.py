# llm_client.py

import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def get_llm_client():
    """
    创建并返回一个 OpenAI 兼容格式的大模型客户端。
    只要你的 LLM_BASE_URL 是 OpenAI-compatible API，就可以这样调用。
    """

    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")

    if not api_key:
        raise ValueError("未读取到 LLM_API_KEY，请检查 .env 文件。")

    if not base_url:
        raise ValueError("未读取到 LLM_BASE_URL，请检查 .env 文件。")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    return client


def chat_with_llm(messages, temperature=0.7):
    """
    调用大模型并返回文本结果。
    """

    model = os.getenv("LLM_MODEL")

    if not model:
        raise ValueError("未读取到 LLM_MODEL，请检查 .env 文件。")

    client = get_llm_client()

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )

    return response.choices[0].message.content