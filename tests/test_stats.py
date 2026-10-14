"""Тесты статистических функций."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.stats import (
    bootstrap_ci,
    chi_square_independence,
    ttest_two_groups,
)


def test_ttest_significant():
    rng = np.random.default_rng(42)
    a = pd.Series(rng.normal(10, 1, 200))
    b = pd.Series(rng.normal(12, 1, 200))
    result = ttest_two_groups(a, b)
    assert result["significant"] is True
    assert result["p_value"] < 0.05
    assert result["mean_a"] < result["mean_b"]


def test_ttest_not_significant():
    rng = np.random.default_rng(42)
    a = pd.Series(rng.normal(10, 1, 200))
    b = pd.Series(rng.normal(10, 1, 200))
    result = ttest_two_groups(a, b)
    assert result["significant"] is False


def test_bootstrap_ci_contains_mean():
    rng = np.random.default_rng(42)
    data = rng.normal(50, 5, 500)
    lo, hi = bootstrap_ci(data, n_boot=500, seed=42)
    assert lo < data.mean() < hi
    assert lo < hi


def test_chi_square_independent():
    df = pd.DataFrame(
        {
            "a": ["x"] * 100 + ["y"] * 100,
            "b": (["p", "q"] * 100),
        }
    )
    result = chi_square_independence(df, "a", "b")
    assert result["significant"] is False


def test_chi_square_dependent():
    df = pd.DataFrame(
        {
            "a": ["x"] * 100 + ["y"] * 100,
            "b": ["p"] * 100 + ["q"] * 100,
        }
    )
    result = chi_square_independence(df, "a", "b")
    assert result["significant"] is True