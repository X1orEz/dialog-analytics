"""ETL-пайплайн: обновление данных, разметки и метрик.

Запускать периодически через cron или вручную.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.db import get_engine, load_csv_to_table, truncate_tables
from src.labeling import label_dialogues_batch
from src.metrics import avg_duration_min, dialogues_by_status, retention

REPORTS_DIR = Path("reports")
METRICS_PATH = REPORTS_DIR / "metrics_snapshot.json"


def refresh_raw_data() -> None:
    """Сгенерировать синтетику и перезалить в БД."""
    from src.generate_data import main as gen_main

    print("[1/3] Generate raw data...")
    gen_main()

    print("[2/3] Truncate and load into Postgres...")
    truncate_tables(["messages", "dialogues", "clients", "labels"])
    root = Path("data/raw")
    load_csv_to_table(root / "clients.csv", "clients")
    load_csv_to_table(root / "dialogues.csv", "dialogues")
    load_csv_to_table(root / "messages.csv", "messages")


def refresh_labels() -> None:
    """Доразметить диалоги без метки."""
    print("[3/3] Labeling new dialogues...")
    label_dialogues_batch(limit=None)


def snapshot_metrics() -> None:
    """Сохранить снимок бизнес-метрик в JSON."""
    engine = get_engine()
    dialogues = pd.read_sql("SELECT * FROM dialogues", engine)
    dialogues["started_at"] = pd.to_datetime(dialogues["started_at"])
    dialogues["ended_at"] = pd.to_datetime(dialogues["ended_at"])

    snapshot = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_dialogues": int(len(dialogues)),
        "retention": float(retention(dialogues)),
        "avg_duration_min": float(avg_duration_min(dialogues)),
        "by_status": dialogues_by_status(dialogues).to_dict("records"),
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2)
    )
    print(f"Metrics snapshot saved: {METRICS_PATH}")


def run(full_refresh: bool = False) -> None:
    if full_refresh:
        refresh_raw_data()
    refresh_labels()
    snapshot_metrics()


if __name__ == "__main__":
    full = "--full" in sys.argv
    run(full_refresh=full)