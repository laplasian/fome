"""Отражение под углом при фиксированной длине волны: зависимость от угла θ.

Главная функция для окна «падение под углом».
"""

from dataclasses import dataclass

import numpy as np

from calc.dielectric_function import dielectric_function
from calc.normal_reflection import intensity_reflection, reflection_phase
from calc.oblique_reflection import (
    te_amplitude_reflection,
    tm_amplitude_reflection,
    unpolarized_reflection,
)
from calc.parameters import Material
from calc.refractive_index import refractive_index
from calc.units import degrees_to_radians, nm_to_ev, nm_to_wavenumber

# Что можно построить или сохранить: ключ -> подпись.
ANGULAR_QUANTITIES = {
    "R_te": "R TE (s-волна)",
    "R_tm": "R TM (p-волна)",
    "phase_te_rad": "φ TE, рад",
    "phase_tm_rad": "φ TM, рад",
    "R_np": "R неполяризованный",
}


@dataclass
class AngularSpectrum:
    """Результат. Массивы — по точкам сетки углов."""

    wavelength_nm: float
    energy_ev: float
    N: complex          # показатель преломления среды на этой длине волны
    angle_deg: np.ndarray
    R_te: np.ndarray
    R_tm: np.ndarray
    phase_te_rad: np.ndarray
    phase_tm_rad: np.ndarray
    R_np: np.ndarray


def make_angle_grid(points=901):
    """Углы от 0 до 90 градусов (по умолчанию шаг 0.1°)."""
    return np.linspace(0.0, 90.0, points)


def calculate_angular_spectrum(material: Material, wavelength_nm: float, angle_deg=None) -> AngularSpectrum:
    """λ фиксирована → N(λ) → r_TE(θ), r_TM(θ) → R и фазы."""
    if angle_deg is None:
        angle_deg = make_angle_grid()
    angle_deg = np.asarray(angle_deg, dtype=float)

    # 1. Показатель преломления на выбранной длине волны
    nu = nm_to_wavenumber(wavelength_nm)
    N = complex(refractive_index(dielectric_function(nu, material)))

    # 2. Градусы -> радианы (в формулы только радианы!)
    theta = degrees_to_radians(angle_deg)

    # 3. Коэффициенты Френеля
    r_te = te_amplitude_reflection(N, theta)
    r_tm = tm_amplitude_reflection(N, theta)
    R_te = intensity_reflection(r_te)
    R_tm = intensity_reflection(r_tm)

    return AngularSpectrum(
        wavelength_nm=float(wavelength_nm),
        energy_ev=float(nm_to_ev(wavelength_nm)),
        N=N,
        angle_deg=angle_deg,
        R_te=R_te,
        R_tm=R_tm,
        phase_te_rad=reflection_phase(r_te),
        phase_tm_rad=reflection_phase(r_tm),
        R_np=unpolarized_reflection(R_te, R_tm),
    )
