"""Отражение при нормальном падении из воздуха на полубесконечную среду."""

import numpy as np

from calc.constants import N_AIR


def amplitude_reflection(N, n_air=N_AIR):
    """Комплексный коэффициент отражения по амплитуде:

        r12 = (N_air − N) / (N_air + N) = |r12| · exp(i·φ12)
    """
    return (n_air - N) / (n_air + N)


def intensity_reflection(r):
    """Отражение по интенсивности: R = r · r* = |r|²."""
    return np.abs(r) ** 2


def reflection_phase(r):
    """Фаза φ коэффициента отражения r, радианы в (−π, π]."""
    return np.angle(r)
