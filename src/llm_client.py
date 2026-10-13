"""Универсальный LLM-клиент: OpenRouter / HuggingFace / OpenAI."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "huggingface")
API_KEY = os.getenv("LLM_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-72B-Instruct")
BASE_URL = os.getenv("LLM_BASE_URL", "")


def _openai_client():
    """Клиент для OpenAI-совместимых API."""
    from openai import OpenAI

    if PROVIDER == "openrouter":
        return OpenAI(
            api_key=API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
    if PROVIDER == "ollama":
        return OpenAI(
            api_key="ollama",
            base_url="http://localhost:11434/v1",
        )
    return OpenAI(api_key=API_KEY)


def _hf_client():
    from huggingface_hub import InferenceClient

    return InferenceClient(model=MODEL, token=API_KEY)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def chat(
    system: str,
    user: str,
    temperature: float = 0.0,
    max_tokens: int = 300,
) -> str:
    """Один запрос к LLM. Возвращает текст ответа."""
    if PROVIDER == "huggingface":
        client = _hf_client()
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    client = _openai_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""