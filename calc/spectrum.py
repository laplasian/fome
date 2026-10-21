"""Сборка всех величин в спектр: зависимость от длины волны.

Это главная функция расчётного блока для основного окна программы.
"""

from dataclasses import dataclass

import numpy as np

from calc.dielectric_function import dielectric_function
from calc.film import film_reflection, film_transmission
from calc.normal_reflection import amplitude_reflection, intensity_reflection, reflection_phase
from calc.parameters import DEFAULT_FILM_THICKNESS_NM, Material
from calc.refractive_index import absorption_coefficient, refractive_index
from calc.units import nm_to_ev, nm_to_wavenumber

# Что можно построить или сохранить: ключ -> подпись для графика / файла.
SPECTRUM_QUANTITIES = {
    "eps_real": "ε' — Re ε",
    "eps_imag": "ε'' — Im ε",
    "n": "n — Re N",
    "k": "k — Im N",
    "R12": "R12 — отражение от полубесконечной среды",
    "phase12_rad": "φ12 — фаза отражения, рад",
    "alpha_cm1": "α — коэффициент поглощения, см⁻¹",
    "film_T_percent": "T плёнки, %",
    "film_R_percent": "R плёнки, %",
}


@dataclass
class Spectrum:
    """Результат расчёта. Все массивы одной длины — по точкам сетки λ."""

    wavelength_nm: np.ndarray
    wavenumber_cm1: np.ndarray
    energy_ev: np.ndarray
    eps_real: np.ndarray
    eps_imag: np.ndarray
    n: np.ndarray
    k: np.ndarray
    alpha_cm1: np.ndarray
    R12: np.ndarray
    phase12_rad: np.ndarray
    film_T_percent: np.ndarray
    film_R_percent: np.ndarray
    film_thickness_nm: float


def calculate_spectrum(
    material: Material,
    wavelength_nm,
    film_thickness_nm: float = DEFAULT_FILM_THICKNESS_NM,
) -> Spectrum:
    """Считает всё по порядку: λ → ν → ε → N → α, R12, φ12 → плёнка."""
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)

    # 1. Длина волны -> волновое число (весь расчёт идёт в см⁻¹)
    nu = nm_to_wavenumber(wavelength_nm)

    # 2. Диэлектрическая проницаемость Друде–Лоренца
    eps = dielectric_function(nu, material)

    # 3. Показатель преломления и поглощение
    N = refractive_index(eps)
    alpha = absorption_coefficient(N.imag, nu)

    # 4. Отражение от полубесконечной среды
    r12 = amplitude_reflection(N)
    R12 = intensity_reflection(r12)

    # 5. Плёнка толщины d
    T_film = film_transmission(R12, alpha, film_thickness_nm)
    R_film = film_reflection(R12, alpha, film_thickness_nm)

    return Spectrum(
        wavelength_nm=wavelength_nm,
        wavenumber_cm1=nu,
        energy_ev=nm_to_ev(wavelength_nm),
        eps_real=eps.real,
        eps_imag=eps.imag,
        n=N.real,
        k=N.imag,
        alpha_cm1=alpha,
        R12=R12,
        phase12_rad=reflection_phase(r12),
        film_T_percent=T_film,
        film_R_percent=R_film,
        film_thickness_nm=film_thickness_nm,
    )
