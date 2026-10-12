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
        segment = clients.loc[clients["client_id"] == client_id, "segment"].iloc[0]

        # канал
        channel = random.choices(["chat", "email", "phone"], weights=[0.6, 0.3, 0.1])[0]

        # длительность зависит от канала и сегмента
        base_duration = {"chat": 25, "email": 45, "phone": 15}[channel]
        segment_factor = {"new": 1.2, "regular": 1.0, "vip": 0.8}[segment]
        duration = max(3, int(random.gauss(base_duration * segment_factor, 10)))

        started = now - timedelta(days=random.randint(0, 90),
                                  minutes=random.randint(0, 1440))
        ended = started + timedelta(minutes=duration)

        # базовая вероятность эскалации
        base_p = 0.15

        # канал: email решается лучше, chat чаще эскалируют, phone — средний
        channel_factor = {"chat": 1.8, "email": 0.4, "phone": 0.6}[channel]

        # сегмент: VIP решают быстрее, new — сложнее
        segment_factor = {"new": 1.3, "regular": 1.0, "vip": 0.5}[segment]

        # длительность нормируем к 30 минутам
        duration_factor = duration / 30.0

        p_escalated = min(0.85, base_p * channel_factor * segment_factor * duration_factor)
        p_abandoned = 0.05

        # оставшееся — resolved
        p_resolved = max(0.05, 1.0 - p_escalated - p_abandoned)

        status = random.choices(
            ["resolved", "escalated", "abandoned"],
            weights=[p_resolved, p_escalated, p_abandoned],
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
