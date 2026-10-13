"""Streamlit-дашборд по диалогам поддержки."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    
from src.db import get_engine

st.set_page_config(page_title="Dialog Analytics", layout="wide")

st.title("Dialog Analytics")
st.caption("Аналитика диалогов поддержки: метрики, разметка, каналы, статусы.")


@st.cache_data(ttl=60)
def load_data() -> dict[str, pd.DataFrame]:
    """Загрузить данные из Postgres. Кэш на 60 секунд."""
    engine = get_engine()
    dialogues = pd.read_sql("SELECT * FROM dialogues", engine)
    clients = pd.read_sql("SELECT * FROM clients", engine)
    labels = pd.read_sql("SELECT * FROM labels", engine)
    dialogues["started_at"] = pd.to_datetime(dialogues["started_at"])
    dialogues["ended_at"] = pd.to_datetime(dialogues["ended_at"])
    dialogues["duration_min"] = (
        (dialogues["ended_at"] - dialogues["started_at"]).dt.total_seconds() / 60
    )
    return {"dialogues": dialogues, "clients": clients, "labels": labels}


data = load_data()
dialogues = data["dialogues"]
clients = data["clients"]
labels = data["labels"]

# --- верхняя панель метрик ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Диалогов", f"{len(dialogues):,}")
col2.metric("Клиентов", f"{len(clients):,}")
col3.metric("Средняя длительность", f"{dialogues['duration_min'].mean():.1f} мин")

per_client = dialogues.groupby("client_id").size()
retention = (per_client > 1).mean() if len(per_client) else 0.0
col4.metric("Retention", f"{retention:.1%}")

# --- сайдбар с фильтрами ---
st.sidebar.header("Фильтры")

channels = sorted(dialogues["channel"].unique())
selected_channels = st.sidebar.multiselect(
    "Канал", channels, default=channels
)

statuses = sorted(dialogues["status"].unique())
selected_statuses = st.sidebar.multiselect(
    "Статус", statuses, default=statuses
)

min_date = dialogues["started_at"].min().date()
max_date = dialogues["started_at"].max().date()
date_range = st.sidebar.date_input(
    "Диапазон дат", value=(min_date, max_date),
    min_value=min_date, max_value=max_date,
)

filtered = dialogues[
    dialogues["channel"].isin(selected_channels)
    & dialogues["status"].isin(selected_statuses)
]
if isinstance(date_range, tuple) and len(date_range) == 2:
    lo, hi = date_range
    filtered = filtered[
        (filtered["started_at"].dt.date >= lo)
        & (filtered["started_at"].dt.date <= hi)
    ]

# --- ряд 1: распределения ---
st.subheader("Распределения")
c1, c2, c3 = st.columns(3)

with c1:
    fig = px.bar(
        filtered["channel"].value_counts().reset_index(),
        x="channel", y="count",
        title="Диалоги по каналам",
        labels={"channel": "Канал", "count": "Диалогов"},
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = px.bar(
        filtered["status"].value_counts().reset_index(),
        x="status", y="count",
        title="Диалоги по статусам",
        labels={"status": "Статус", "count": "Диалогов"},
    )
    st.plotly_chart(fig, use_container_width=True)

with c3:
    fig = px.histogram(
        filtered, x="duration_min", nbins=25,
        title="Длительность диалога",
        labels={"duration_min": "Минут"},
    )
    st.plotly_chart(fig, use_container_width=True)

# --- ряд 2: динамика по дням ---
st.subheader("Динамика")
daily = (
    filtered.assign(day=filtered["started_at"].dt.date)
    .groupby("day")
    .size()
    .reset_index(name="dialogues")
)
fig = px.line(
    daily, x="day", y="dialogues",
    title="Диалоги по дням",
    labels={"day": "Дата", "dialogues": "Диалогов"},
)
st.plotly_chart(fig, use_container_width=True)

# --- ряд 3: LLM-разметка ---
st.subheader("LLM-разметка диалогов")
if len(labels) == 0:
    st.info("Метки пока не созданы. Запусти: `python -m src.labeling`")
else:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            labels["topic"].value_counts().reset_index(),
            x="topic", y="count",
            title="Темы обращений",
            labels={"topic": "Тема", "count": "Диалогов"},
        )
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.pie(
            labels, names="sentiment",
            title="Тональность клиентов",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.caption("Примеры разметки")
    st.dataframe(
        labels[["dialogue_id", "topic", "sentiment", "reason"]]
        .sort_values("dialogue_id")
        .head(50),
        use_container_width=True,
    )