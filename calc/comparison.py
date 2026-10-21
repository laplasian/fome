"""Сравнение рассчитанного спектра с экспериментальным."""

from dataclasses import dataclass

import numpy as np


@dataclass
class Comparison:
    """Расчёт и эксперимент на ОДНОЙ сетке длин волн (сетка эксперимента)."""

    wavelength_nm: np.ndarray
    experiment: np.ndarray
    calculation: np.ndarray
    rms: float  # среднеквадратичное отклонение, в тех же единицах (%)


def interpolate_onto(x_calc, y_calc, x_new):
    """Линейная интерполяция расчёта на точки x_new (np.interp требует возрастания x)."""
    order = np.argsort(x_calc)
    return np.interp(x_new, np.asarray(x_calc)[order], np.asarray(y_calc)[order])


def compare_with_experiment(calc_wavelength_nm, calc_values, exp_wavelength_nm, exp_values) -> Comparison:
    """Переносит расчёт на точки эксперимента и считает отклонение.

    Берутся только экспериментальные точки внутри диапазона расчёта
    (без экстраполяции).
    """
    exp_wavelength_nm = np.asarray(exp_wavelength_nm, dtype=float)
    exp_values = np.asarray(exp_values, dtype=float)

    inside = (exp_wavelength_nm >= np.min(calc_wavelength_nm)) & (exp_wavelength_nm <= np.max(calc_wavelength_nm))
    wl = exp_wavelength_nm[inside]
    experiment = exp_values[inside]
    calculation = interpolate_onto(calc_wavelength_nm, calc_values, wl)

    rms = float(np.sqrt(np.mean((calculation - experiment) ** 2))) if wl.size else float("nan")
    return Comparison(wl, experiment, calculation, rms)
