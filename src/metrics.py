"""Бизнес-метрики по диалогам."""
from __future__ import annotations

import pandas as pd


def dialogues_per_day(dialogues: pd.DataFrame) -> pd.DataFrame:
    """Количество диалогов по дням."""
    return (
        dialogues
        .assign(day=dialogues["started_at"].dt.date)
        .groupby("day")
        .size()
        .reset_index(name="dialogues")
    )


def retention(df: pd.DataFrame) -> float:
    """Доля клиентов с более одного диалога."""
    if df.empty:
        return 0.0
    per_client = df.groupby("client_id").size()
    return float((per_client > 1).mean())


def avg_duration_min(df: pd.DataFrame) -> float:
    """Средняя длительность диалога в минутах."""
    if df.empty or df["ended_at"].isna().all():
        return 0.0
    delta = (df["ended_at"] - df["started_at"]).dt.total_seconds() / 60
    return float(delta.mean())


def dialogues_by_channel(df: pd.DataFrame) -> pd.DataFrame:
    """Распределение диалогов по каналам."""
    return (
        df.groupby("channel")
        .size()
        .reset_index(name="dialogues")
        .sort_values("dialogues", ascending=False)
    )


def dialogues_by_status(df: pd.DataFrame) -> pd.DataFrame:
    """Распределение диалогов по статусам с долями."""
    out = df.groupby("status").size().reset_index(name="cnt")
    out["share"] = out["cnt"] / out["cnt"].sum()
    return out.sort_values("cnt", ascending=False)