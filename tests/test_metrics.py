"""Тесты бизнес-метрик."""
from __future__ import annotations

import pandas as pd
import pytest

from src.metrics import (
    avg_duration_min,
    dialogues_by_channel,
    dialogues_by_status,
    retention,
)


@pytest.fixture
def sample_dialogues() -> pd.DataFrame:
    """Минимальный набор диалогов для тестов."""
    return pd.DataFrame(
        [
            {
                "dialogue_id": 1, "client_id": 1, "channel": "chat",
                "status": "resolved",
                "started_at": pd.Timestamp("2026-01-01 10:00"),
                "ended_at": pd.Timestamp("2026-01-01 10:30"),
            },
            {
                "dialogue_id": 2, "client_id": 1, "channel": "email",
                "status": "resolved",
                "started_at": pd.Timestamp("2026-01-02 10:00"),
                "ended_at": pd.Timestamp("2026-01-02 11:00"),
            },
            {
                "dialogue_id": 3, "client_id": 2, "channel": "chat",
                "status": "escalated",
                "started_at": pd.Timestamp("2026-01-03 10:00"),
                "ended_at": pd.Timestamp("2026-01-03 10:20"),
            },
            {
                "dialogue_id": 4, "client_id": 3, "channel": "chat",
                "status": "resolved",
                "started_at": pd.Timestamp("2026-01-04 10:00"),
                "ended_at": pd.Timestamp("2026-01-04 10:10"),
            },
        ]
    )


def test_retention(sample_dialogues):
    # 3 клиента, у одного 2 диалога → retention = 1/3
    assert retention(sample_dialogues) == pytest.approx(1 / 3)


def test_retention_empty():
    assert retention(pd.DataFrame(columns=["client_id"])) == 0.0


def test_avg_duration_min(sample_dialogues):
    # длительности: 30, 60, 20, 10 → среднее = 30
    assert avg_duration_min(sample_dialogues) == pytest.approx(30.0)


def test_dialogues_by_channel(sample_dialogues):
    result = dialogues_by_channel(sample_dialogues)
    channels = result.set_index("channel")["dialogues"].to_dict()
    assert channels == {"chat": 3, "email": 1}


def test_dialogues_by_status(sample_dialogues):
    result = dialogues_by_status(sample_dialogues)
    shares = result.set_index("status")["share"].to_dict()
    assert shares["resolved"] == pytest.approx(0.75)
    assert shares["escalated"] == pytest.approx(0.25)