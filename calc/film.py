"""Пропускание и отражение плёнки толщины d (в процентах).

Без учёта интерференции, но с многократными переотражениями по интенсивности.

Формулы из условия — это сумма геометрической прогрессии с знаменателем
q = R² · e^(−2αd). При обычном поглощении (α ≥ 0) всегда q < 1.
При отрицательном затухании (Γ < 0 → k < 0 → α < 0) свет внутри плёнки
усиливается, и для толстой плёнки q ≥ 1: ряд расходится (это порог генерации),
T и R конечного значения не имеют. В таких точках возвращается NaN —
окно плёнки сообщает об этом в строке состояния.

Экспоненты считаются через логарифмы, чтобы e^(−αd) не переполнялось
(при d = 1 мм и α ~ −10⁴ см⁻¹ показатель достигает 1000, а e^709 — предел float).
"""

import numpy as np

from calc.units import nm_to_cm

# Больше этого показателя np.exp даёт inf
_MAX_EXP = 700.0


def _film_terms(R12, alpha, thickness_nm):
    """Общие части формул: log e^(−αd), q = R²e^(−2αd) и маска «ряд расходится»."""
    R = np.asarray(R12, dtype=float)
    alpha = np.asarray(alpha, dtype=float)
    d = nm_to_cm(thickness_nm)

    log_single = -alpha * d                    # ln e^(−αd)
    with np.errstate(divide="ignore"):
        log_q = 2 * np.log(R) + 2 * log_single  # ln (R² e^(−2αd)); R = 0 -> −inf
    diverges = log_q >= 0

    q = np.exp(np.minimum(log_q, 0.0))
    return R, log_single, q, diverges


def film_transmission(R12, alpha, thickness_nm):
    """T_film = (1 − R)² · e^(−αd) / (1 − R² · e^(−2αd)) · 100   [%]."""
    R, log_single, q, diverges = _film_terms(R12, alpha, thickness_nm)
    single_pass = np.exp(np.minimum(log_single, _MAX_EXP))
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        T = (1 - R) ** 2 * single_pass / (1 - q) * 100
    return np.where(diverges, np.nan, T)


def film_reflection(R12, alpha, thickness_nm):
    """R_film = R · (1 + e^(−2αd) − 2R · e^(−2αd)) / (1 − R² · e^(−2αd)) · 100   [%].

    Записано в равносильном виде R + R(1 − R)²e^(−2αd) / (1 − q), где
    R·e^(−2αd) = q / R — так нет отдельной экспоненты, которая могла бы переполниться.
    """
    R, _, q, diverges = _film_terms(R12, alpha, thickness_nm)
    with np.errstate(divide="ignore", invalid="ignore"):
        round_trip_times_R = np.where(R > 0, q / np.where(R > 0, R, 1.0), 0.0)  # R·e^(−2αd)
        R_film = (R + (1 - R) ** 2 * round_trip_times_R / (1 - q)) * 100
    return np.where(diverges, np.nan, R_film)


def film_generation_points(R12, alpha, thickness_nm):
    """Сколько точек спектра выше порога генерации (там T и R не определены)."""
    return int(np.count_nonzero(_film_terms(R12, alpha, thickness_nm)[3]))
