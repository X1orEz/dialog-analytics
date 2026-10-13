"""Универсальный LLM-клиент: OpenRouter / HuggingFace / Ollama / OpenAI."""
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

PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
API_KEY = os.getenv("LLM_API_KEY", "ollama")
MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")


def _client():
    """Клиент для OpenAI-совместимого API (OpenRouter, Ollama, OpenAI)."""
    from openai import OpenAI

    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


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
    client = _client()
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