"""Подключение к Postgres и загрузка CSV."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_URL = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)


def get_engine():
    return create_engine(DB_URL)


def truncate_tables(tables: list[str]) -> None:
    """Очистить таблицы, сбросить SERIAL и каскадно удалить зависимые."""
    if not tables:
        return
    stmt = text(
        f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;"
    )
    with get_engine().begin() as conn:
        conn.execute(stmt)


def load_csv_to_table(csv_path: Path, table: str, if_exists: str = "append") -> int:
    df = pd.read_csv(csv_path)
    with get_engine().begin() as conn:
        df.to_sql(table, conn, if_exists=if_exists, index=False)
    return len(df)


if __name__ == "__main__":
    # удаляем данные в порядке: потомки → родители
    truncate_tables(["messages", "dialogues", "clients", "labels"])

    root = Path("data/raw")
    n1 = load_csv_to_table(root / "clients.csv", "clients")
    n2 = load_csv_to_table(root / "dialogues.csv", "dialogues")
    n3 = load_csv_to_table(root / "messages.csv", "messages")
    print(f"clients={n1}, dialogues={n2}, messages={n3}")
