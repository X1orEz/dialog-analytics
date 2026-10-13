"""LLM-разметка диалогов: тема, тональность, причина обращения."""
from __future__ import annotations

import json
import re
import sys
import time

import pandas as pd
from sqlalchemy import text

from src.db import get_engine
from src.llm_client import MODEL, chat

SYSTEM_PROMPT = """Ты — аналитик службы поддержки. Тебе дано первое сообщение клиента — его запрос или жалоба.
Разметь его строго в формате JSON без пояснений.

Поля:
- topic: одно из billing, delivery, tech, account.
  billing — оплата, списания, возвраты, подписка, чеки
  delivery — доставка, заказ, курьер, адрес
  tech — ошибки приложения, вход, код, сбои
  account — данные аккаунта, смена телефона, привязка карты, удаление
- sentiment: одно из negative, neutral, positive.
  negative — клиент жалуется, чем-то недоволен, что-то не работает или нарушено (например, "уже неделя прошла", "списали дважды", "вылетает")
  neutral — обычный вопрос без эмоций (например, "как удалить аккаунт", "как сменить номер")
  positive — благодарность, похвала
- reason: 2–5 слов, что случилось или что клиент хочет. Без слов "оценка", "вопрос", "запрос", "проблема". Без кавычек.

Примеры:
"С меня списали деньги дважды" → {"topic": "billing", "sentiment": "negative", "reason": "двойное списание"}
"Как удалить аккаунт?" → {"topic": "account", "sentiment": "neutral", "reason": "удаление аккаунта"}
"Где мой заказ, уже неделя прошла" → {"topic": "delivery", "sentiment": "negative", "reason": "задержка заказа"}
"Приложение вылетает при входе" → {"topic": "tech", "sentiment": "negative", "reason": "сбой при входе"}

Отвечай ТОЛЬКО JSON.
"""

ALLOWED_TOPICS = {"billing", "delivery", "tech", "account"}
ALLOWED_SENTIMENTS = {"negative", "neutral", "positive"}


def build_client_request(messages: list[dict]) -> str:
    """Вернуть первое сообщение клиента — суть обращения."""
    for m in messages:
        if m["sender"] == "client":
            return m["text"]
    return ""


def parse_json_response(raw: str) -> dict | None:
    """Вытащить JSON из ответа модели, даже если есть мусор вокруг."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None


def validate_label(label: dict) -> bool:
    """Проверить поля и допустимые значения."""
    if not label:
        return False
    if label.get("topic") not in ALLOWED_TOPICS:
        return False
    if label.get("sentiment") not in ALLOWED_SENTIMENTS:
        return False
    reason = label.get("reason")
    if not isinstance(reason, str):
        return False
    if not (2 <= len(reason) <= 100):
        return False
    return True


def label_dialogue(messages: list[dict], max_attempts: int = 3) -> dict | None:
    """Разметить один диалог. Возвращает dict или None при неудаче."""
    text = build_client_request(messages)
    if not text:
        return None

    for _ in range(max_attempts):
        raw = chat(system=SYSTEM_PROMPT, user=text, max_tokens=100)
        label = parse_json_response(raw)
        if validate_label(label):
            return label
        print(f"    retry: raw={raw[:200]!r}")
        time.sleep(1)
    return None


def label_dialogues_batch(limit: int | None = None) -> None:
    """Разметить все диалоги без метки и сохранить в БД."""
    engine = get_engine()

    sql = (
        "SELECT dialogue_id FROM dialogues "
        "WHERE dialogue_id NOT IN (SELECT dialogue_id FROM labels) "
        "ORDER BY dialogue_id"
    )
    if limit:
        sql += f" LIMIT {limit}"

    with engine.begin() as conn:
        dialogue_ids = [row[0] for row in conn.execute(text(sql))]

    total = len(dialogue_ids)
    if total == 0:
        print("Все диалоги уже размечены.")
        return

    all_msgs = pd.read_sql(
        "SELECT dialogue_id, sender, text FROM messages "
        "ORDER BY dialogue_id, created_at",
        engine,
    )
    grouped = {
        dlg_id: grp.to_dict("records")
        for dlg_id, grp in all_msgs.groupby("dialogue_id")
    }

    print(f"К разметке: {total} диалогов, модель: {MODEL}")
    saved = 0
    failed = 0
    t0 = time.time()

    for i, dlg_id in enumerate(dialogue_ids, 1):
        messages = grouped.get(dlg_id, [])
        label = label_dialogue(messages)

        if label:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO labels "
                        "(dialogue_id, topic, sentiment, reason, model_name) "
                        "VALUES (:d, :t, :s, :r, :m)"
                    ),
                    {
                        "d": dlg_id,
                        "t": label["topic"],
                        "s": label["sentiment"],
                        "r": label["reason"],
                        "m": MODEL,
                    },
                )
            saved += 1
            status = "ok"
        else:
            failed += 1
            status = "FAIL"

        elapsed = time.time() - t0
        rate = i / elapsed if elapsed > 0 else 0
        eta_min = (total - i) / rate / 60 if rate > 0 else 0
        print(
            f"[{i}/{total}] dlg={dlg_id} {status} "
            f"elapsed={elapsed/60:.1f}m eta={eta_min:.1f}m"
        )

    print(
        f"\nDone. Saved={saved}, Failed={failed}, "
        f"total time={(time.time()-t0)/60:.1f}m"
    )


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    label_dialogues_batch(limit=limit)