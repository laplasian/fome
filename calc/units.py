"""Перевод единиц: нанометры, обратные сантиметры, электронвольты, градусы.

Все функции работают и с числами, и с массивами numpy.
"""

import numpy as np

from calc.constants import EV_TIMES_NM, NM_PER_CM


def nm_to_wavenumber(wavelength_nm):
    """Длина волны [нм] -> волновое число ν [см⁻¹]:  ν = 10^7 / λ."""
    return NM_PER_CM / np.asarray(wavelength_nm, dtype=float)


def wavenumber_to_nm(wavenumber_cm1):
    """Волновое число ν [см⁻¹] -> длина волны [нм]:  λ = 10^7 / ν."""
    return NM_PER_CM / np.asarray(wavenumber_cm1, dtype=float)


def nm_to_ev(wavelength_nm):
    """Длина волны [нм] -> энергия фотона [эВ]:  E = 1240 / λ."""
    return EV_TIMES_NM / np.asarray(wavelength_nm, dtype=float)


def ev_to_nm(energy_ev):
    """Энергия фотона [эВ] -> длина волны [нм]:  λ = 1240 / E."""
    return EV_TIMES_NM / np.asarray(energy_ev, dtype=float)


def nm_to_cm(length_nm):
    """Длина [нм] -> [см]: делим на 10^7 (толщина плёнки)."""
    return np.asarray(length_nm, dtype=float) / NM_PER_CM


def degrees_to_radians(angle_deg):
    """Угол [градусы] -> [радианы]:  θ_рад = θ_град · π / 180."""
    return np.asarray(angle_deg, dtype=float) * np.pi / 180.0


def make_wavelength_grid(start_nm=190.0, stop_nm=2500.0, points=2000):
    """Равномерная сетка длин волн [нм] для построения графиков."""
    return np.linspace(start_nm, stop_nm, points)
