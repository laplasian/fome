"""Пропускание и отражение плёнки толщины d (в процентах).

Без учёта интерференции, но с многократными переотражениями
по интенсивности.

Формулы из условия — сумма геометрической прогрессии со знаменателем
q = R² · e^(−2αd). При обычном поглощении (α ≥ 0) всегда q < 1.
При отрицательном затухании (Γ < 0, значит k < 0 и α < 0) свет внутри
плёнки усиливается, и для толстой плёнки q ≥ 1: ряд расходится (порог
генерации), конечных T и R нет. В таких точках возвращается NaN.
"""

import numpy as np

from calc.units import nm_to_cm

# Больше этого показателя np.exp даёт inf (предел float — около 709).
MAX_EXP = 700.0


def get_film_terms(R12, alpha, thickness_nm):
    """Возвращает R, ln e^(−αd), q = R²e^(−2αd) и маску расходимости.

    Экспоненты считаются через логарифмы: при d = 1 мм и α ~ −10⁴ см⁻¹
    показатель e^(−αd) достигает 1000, и прямой расчёт переполняется.
    """
    R = np.asarray(R12, dtype=float)
    alpha = np.asarray(alpha, dtype=float)
    d = nm_to_cm(thickness_nm)

    log_single = -alpha * d
    with np.errstate(divide='ignore'):
        # При R = 0 логарифм равен −inf, тогда q = 0, это верно.
        log_q = 2 * np.log(R) + 2 * log_single
    diverges = log_q >= 0
    q = np.exp(np.minimum(log_q, 0.0))
    return R, log_single, q, diverges


def get_film_transmission(R12, alpha, thickness_nm):
    """T_film = (1 − R)² · e^(−αd) / (1 − R² · e^(−2αd)) · 100   [%]."""
    R, log_single, q, diverges = get_film_terms(R12, alpha, thickness_nm)
    single_pass = np.exp(np.minimum(log_single, MAX_EXP))
    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
        T = (1 - R) ** 2 * single_pass / (1 - q) * 100
    return np.where(diverges, np.nan, T)


def get_film_reflection(R12, alpha, thickness_nm):
    """R_film = R·(1 + e^(−2αd) − 2R·e^(−2αd)) / (1 − R²e^(−2αd))·100.

    Считается в равносильном виде R + (1 − R)² · R·e^(−2αd) / (1 − q),
    где R·e^(−2αd) = q / R: так нет экспоненты, которая переполнится.
    """
    R, _, q, diverges = get_film_terms(R12, alpha, thickness_nm)
    safe_R = np.where(R > 0, R, 1.0)
    with np.errstate(divide='ignore', invalid='ignore'):
        round_trip = np.where(R > 0, q / safe_R, 0.0)
        R_film = (R + (1 - R) ** 2 * round_trip / (1 - q)) * 100
    return np.where(diverges, np.nan, R_film)


def count_generation_points(R12, alpha, thickness_nm):
    """Считает точки выше порога генерации, где T и R не определены."""
    diverges = get_film_terms(R12, alpha, thickness_nm)[3]
    return int(np.count_nonzero(diverges))

