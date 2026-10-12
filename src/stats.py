"""Статистические утилиты."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def ttest_two_groups(
    a: pd.Series, b: pd.Series, alpha: float = 0.05
) -> dict:
    """t-тест Уэлча для двух независимых выборок."""
    t_stat, p_value = stats.ttest_ind(a.dropna(), b.dropna(), equal_var=False)
    return {
        "t": float(t_stat),
        "p_value": float(p_value),
        "significant": bool(p_value < alpha),
        "mean_a": float(a.mean()),
        "mean_b": float(b.mean()),
    }


def chi_square_independence(
    df: pd.DataFrame, col_a: str, col_b: str, alpha: float = 0.05
) -> dict:
    """Критерий хи-квадрат для проверки независимости двух категориальных признаков."""
    table = pd.crosstab(df[col_a], df[col_b])
    chi2, p_value, dof, _ = stats.chi2_contingency(table)
    return {
        "chi2": float(chi2),
        "p_value": float(p_value),
        "dof": int(dof),
        "significant": bool(p_value < alpha),
    }


def bootstrap_ci(
    data: np.ndarray, n_boot: int = 1000, alpha: float = 0.05, seed: int = 42
) -> tuple[float, float]:
    """Доверительный интервал для среднего через bootstrap."""
    rng = np.random.default_rng(seed)
    data = np.asarray(data)
    means = [
        rng.choice(data, size=len(data), replace=True).mean()
        for _ in range(n_boot)
    ]
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)