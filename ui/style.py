"""Внешний вид графиков: цвета, толщина линий, шрифты, нормировка."""

import numpy as np
from matplotlib import rcParams

LINE_WIDTH = 2.8
EXPERIMENT_LINE_WIDTH = 1.6

# Свой яркий цвет для каждой величины — одинаковый во всех окнах.
COLORS = {
    "eps_real": "#1f77b4",
    "eps_imag": "#d62728",
    "n": "#2ca02c",
    "k": "#ff7f0e",
    "R12": "#9467bd",
    "phase12_rad": "#8c564b",
    "alpha_cm1": "#e377c2",
    "film_T_percent": "#1f77b4",
    "film_R_percent": "#d62728",
    "R_te": "#1f77b4",
    "R_tm": "#d62728",
    "phase_te_rad": "#2ca02c",
    "phase_tm_rad": "#ff7f0e",
    "R_np": "#9467bd",
    "experiment": "#222222",
}

NORMALIZATION_MODES = {
    "none": "Без нормировки",
    "max": "На максимум |y| = 1",
    "minmax": "Мин–макс → [0, 1]",
}


def apply_matplotlib_style():
    """Крупные шрифты и сетка — вызывается один раз при запуске."""
    rcParams.update({
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "grid.alpha": 0.35,
        "lines.linewidth": LINE_WIDTH,
        "figure.autolayout": False,
    })


def normalize(y, mode):
    """Нормировка кривой для удобного сравнения формы.

    none   — как есть
    max    — y / max|y|
    minmax — (y − min) / (max − min)
    """
    y = np.asarray(y, dtype=float)
    finite = y[np.isfinite(y)]
    if mode == "none" or finite.size == 0:
        return y
    if mode == "max":
        peak = np.max(np.abs(finite))
        return y / peak if peak else y
    if mode == "minmax":
        span = np.ptp(finite)
        return (y - finite.min()) / span if span else y - finite.min()
    raise ValueError(f"Неизвестный режим нормировки: {mode}")
