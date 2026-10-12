"""Генерация синтетических диалогов для проекта."""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

fake = Faker("ru_RU")
random.seed(42)
Faker.seed(42)

OUT = Path("data/raw")
OUT.mkdir(parents=True, exist_ok=True)

N_CLIENTS = 200
N_DIALOGUES = 800

TOPICS = {
    "billing": [
        "С меня списали деньги дважды, верните пожалуйста",
        "Почему изменилась стоимость подписки?",
        "Не пришёл чек об оплате",
    ],
    "delivery": [
        "Где мой заказ, уже неделя прошла",
        "Курьер не приехал в назначенное время",
        "Хочу изменить адрес доставки",
    ],
    "tech": [
        "Приложение вылетает при входе",
        "Не приходит код подтверждения",
        "Не могу зайти в личный кабинет",
    ],
    "account": [
        "Как удалить аккаунт?",
        "Хочу сменить номер телефона",
        "Как привязать новую карту?",
    ],
}

AGENT_REPLIES = {
    "billing": "Проверил ваш платёж, оформляю возврат. Ожидайте 3–5 дней.",
    "delivery": "Уточнил у службы доставки, заказ прибудет завтра до 18:00.",
    "tech": "Попробуйте переустановить приложение. Если не поможет — передам в техотдел.",
    "account": "Готово, изменения внесены. Проверьте, пожалуйста, личный кабинет.",
}


def gen_clients() -> pd.DataFrame:
    rows = []
    for i in range(1, N_CLIENTS + 1):
        rows.append({
            "client_id": i,
            "name": fake.name(),
            "segment": random.choices(
                ["new", "regular", "vip"], weights=[0.4, 0.45, 0.15]
            )[0],
            "created_at": fake.date_time_between(start_date="-3y", end_date="now"),
        })
    return pd.DataFrame(rows)


def gen_dialogues_and_messages(clients: pd.DataFrame):
    dialogues, messages = [], []
    msg_id = 1
    dlg_id = 1
    now = datetime.now()

    for _ in range(N_DIALOGUES):
        client_id = random.randint(1, len(clients))
        channel = random.choices(["chat", "email", "phone"], weights=[0.6, 0.3, 0.1])[0]
        started = now - timedelta(days=random.randint(0, 90),
                                  minutes=random.randint(0, 1440))
        duration = random.randint(3, 60)
        ended = started + timedelta(minutes=duration)
        status = random.choices(
            ["resolved", "escalated", "abandoned"], weights=[0.75, 0.15, 0.10]
        )[0]

        dialogues.append({
            "dialogue_id": dlg_id,
            "client_id": client_id,
            "channel": channel,
            "started_at": started,
            "ended_at": ended,
            "status": status,
        })

        topic = random.choice(list(TOPICS.keys()))
        client_text = random.choice(TOPICS[topic])
        messages.append({
            "message_id": msg_id,
            "dialogue_id": dlg_id,
            "sender": "client",
            "text": client_text,
            "created_at": started,
        })
        msg_id += 1

        messages.append({
            "message_id": msg_id,
            "dialogue_id": dlg_id,
            "sender": "agent",
            "text": AGENT_REPLIES[topic],
            "created_at": started + timedelta(minutes=random.randint(1, 5)),
        })
        msg_id += 1

        if random.random() < 0.4:
            messages.append({
                "message_id": msg_id,
                "dialogue_id": dlg_id,
                "sender": "client",
                "text": "Спасибо!",
                "created_at": ended,
            })
            msg_id += 1

        dlg_id += 1

    return pd.DataFrame(dialogues), pd.DataFrame(messages)


def main() -> None:
    clients = gen_clients()
    dialogues, messages = gen_dialogues_and_messages(clients)

    clients.to_csv(OUT / "clients.csv", index=False)
    dialogues.to_csv(OUT / "dialogues.csv", index=False)
    messages.to_csv(OUT / "messages.csv", index=False)

    print(f"clients: {len(clients)}")
    print(f"dialogues: {len(dialogues)}")
    print(f"messages: {len(messages)}")


if __name__ == "__main__":
    main()
