"""Отражение под углом θ для TE (s) и TM (p) волн от полубесконечной среды."""

import numpy as np

from calc.constants import N_AIR


def cos_refraction_angle(N, theta_rad, n_air=N_AIR):
    """Косинус угла преломления θ'' (в общем случае КОМПЛЕКСНЫЙ):

        cos θ'' = sqrt( 1 − (N_air / N)² · sin²θ )
    """
    return np.sqrt(1 - (n_air / N) ** 2 * np.sin(theta_rad) ** 2)


def te_amplitude_reflection(N, theta_rad, n_air=N_AIR):
    """r_TE = (N_air·cos θ − N·cos θ'') / (N_air·cos θ + N·cos θ'')."""
    cos_i = np.cos(theta_rad)
    cos_t = cos_refraction_angle(N, theta_rad, n_air)
    return (n_air * cos_i - N * cos_t) / (n_air * cos_i + N * cos_t)


def tm_amplitude_reflection(N, theta_rad, n_air=N_AIR):
    """r_TM = (N_air·cos θ'' − N·cos θ) / (N_air·cos θ'' + N·cos θ)."""
    cos_i = np.cos(theta_rad)
    cos_t = cos_refraction_angle(N, theta_rad, n_air)
    return (n_air * cos_t - N * cos_i) / (n_air * cos_t + N * cos_i)


def unpolarized_reflection(R_te, R_tm):
    """Неполяризованный свет: R_NP = (R_TE + R_TM) / 2."""
    return 0.5 * (R_te + R_tm)
