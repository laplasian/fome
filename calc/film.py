"""Пропускание и отражение плёнки толщины d (в процентах).

Без учёта интерференции, но с многократными переотражениями по интенсивности.
"""

import numpy as np

from calc.units import nm_to_cm


def film_transmission(R12, alpha, thickness_nm):
    """T_film = (1 − R)² · e^(−αd) / (1 − R² · e^(−2αd)) · 100   [%]."""
    d = nm_to_cm(thickness_nm)
    single_pass = np.exp(-alpha * d)       # e^(−αd)
    round_trip = np.exp(-2 * alpha * d)    # e^(−2αd)
    return (1 - R12) ** 2 * single_pass / (1 - R12**2 * round_trip) * 100


def film_reflection(R12, alpha, thickness_nm):
    """R_film = R · (1 + e^(−2αd) − 2R · e^(−2αd)) / (1 − R² · e^(−2αd)) · 100   [%]."""
    d = nm_to_cm(thickness_nm)
    round_trip = np.exp(-2 * alpha * d)
    return R12 * (1 + round_trip - 2 * R12 * round_trip) / (1 - R12**2 * round_trip) * 100
