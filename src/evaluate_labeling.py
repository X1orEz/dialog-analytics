"""Оценка качества LLM-разметки через сравнение с ручным эталоном."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report, cohen_kappa_score

from src.db import get_engine

SAMPLE_PATH = Path("data/processed/labeling_sample.csv")

def create_sample(n: int = 50, seed: int = 42) -> None:
    """Создать выборку диалогов для ручной разметки."""
    engine = get_engine()
    query ="""
        SELECT l.dialogue_id, l.topic, l.sentiment, l.reason,
               (SELECT text FROM messages
                WHERE dialogue_id = l.dialogue_id AND sender = 'client'
                ORDER BY created_at LIMIT 1) AS client_msg
        FROM labels l
    """
    df = pd.read_sql(query, engine)
    if len(df) < n:
        print(f"В БД только {len(df)} меток, беру все.")
        n = len(df)
    
    sample = df.sample(n=n, random_state=seed).sort_values("dialogue_id")
    sample['topic_human'] = ''
    sample['sentiment_human'] = ''
    
    SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(SAMPLE_PATH, index=False)
    print(f"Выборка сохранена: {SAMPLE_PATH} ({len(sample)} строк).")
    print("Заполни колонки topic_human и sentiment_human вручную.")
    
def evaluate(path: Path = SAMPLE_PATH) -> None:
    """Посчитать метрики согласия между LLM и человеком."""
    df = pd.read_csv(path)
    df = df.dropna(subset=['topic_human', 'sentiment_human'])
    df = df[(df["topic_human"].str.strip() != "") & (df["sentiment_human"].str.strip() != "")]
    if df.empty:
        print("Нет ручных меток. Заполни CSV и запусти снова.")
        return
    
    print(f"Сравниваем {len(df)} диалогов.\n")

    print("=== Topic ===")
    print(f"Accuracy: {(df['topic'] == df['topic_human']).mean():.3f}")
    print(classification_report(df["topic_human"], df["topic"], zero_division=0))

    print("=== Sentiment ===")
    print(f"Accuracy: {(df['sentiment'] == df['sentiment_human']).mean():.3f}")
    print(
        classification_report(
            df["sentiment_human"], df["sentiment"], zero_division=0
        )
    )

    kappa_topic = cohen_kappa_score(df["topic_human"], df["topic"])
    kappa_sent = cohen_kappa_score(df["sentiment_human"], df["sentiment"])
    print(f"Cohen's kappa (topic):     {kappa_topic:.3f}")
    print(f"Cohen's kappa (sentiment): {kappa_sent:.3f}")
    
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sample"
    if cmd == "sample":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        create_sample(n=n)
    elif cmd == "evaluate":
        evaluate()
    else:
        print("Использование: python -m src.evaluate_labeling [sample|evaluate] [n]")