"""Тесты ML-метрик."""
from __future__ import annotations

import numpy as np

from src.evaluate import classification_metrics


def test_perfect_prediction():
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 0, 1, 1])
    y_proba = np.array([0.1, 0.2, 0.9, 0.8])
    m = classification_metrics(y_true, y_pred, y_proba)
    assert m["accuracy"] == 1.0
    assert m["precision"] == 1.0
    assert m["recall"] == 1.0
    assert m["f1"] == 1.0
    assert m["roc_auc"] == 1.0


def test_worst_prediction():
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([1, 1, 0, 0])
    m = classification_metrics(y_true, y_pred)
    assert m["accuracy"] == 0.0
    assert m["f1"] == 0.0


def test_metrics_without_proba():
    y_true = np.array([0, 1, 0, 1])
    y_pred = np.array([0, 1, 1, 1])
    m = classification_metrics(y_true, y_pred)
    assert "roc_auc" not in m
    assert "pr_auc" not in m