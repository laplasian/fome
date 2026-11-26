"""Комплексная диэлектрическая проницаемость ε(ν) в модели Друде–Лоренца."""

import numpy as np

from calc.parameters import BoundMode, Material
from calc.plasma_frequency import free_plasma_frequency, plasma_frequency
from calc.units import nm_to_wavenumber

# Если затухание Γ = 0 и ν попало точно на резонанс (или ν = 0 у Друде), знаменатель
# обращается в ноль — это настоящий полюс модели без потерь. Чтобы на графике была
# не дыра (NaN), а высокий пик, в таких точках берётся бесконечно малое затухание.
_POLE_DAMPING_CM1 = 1e-6


def _safe(denominator, nu, sign):
    """Заменяет нулевой знаменатель на sign·i·ν·Γ_min (Γ_min → 0); sign — знак iνΓ в формуле."""
    denominator = np.asarray(denominator, dtype=complex)
    zero = denominator == 0
    if np.any(zero):
        tiny = sign * 1j * np.maximum(np.broadcast_to(nu, denominator.shape), 1.0) * _POLE_DAMPING_CM1
        denominator = np.where(zero, tiny, denominator)
    return denominator


def drude_term(nu, material: Material):
    """Вклад свободных носителей:  Ω_p0² / (ν² + i·ν·Γ0)."""
    omega_p0 = free_plasma_frequency(material)
    gamma_0 = material.free.damping_cm1
    return omega_p0**2 / _safe(nu**2 + 1j * nu * gamma_0, nu, +1)


def lorentz_term(nu, mode: BoundMode, eps_inf):
    """Вклад одной моды связанных зарядов:  Ω_pi² / (νi² − ν² − i·ν·Γi)."""
    omega_pi = plasma_frequency(mode.concentration_cm3, mode.mass_in_me, eps_inf)
    nu_i = nm_to_wavenumber(mode.wavelength_nm)
    gamma_i = mode.damping_cm1
    return omega_pi**2 / _safe(nu_i**2 - nu**2 - 1j * nu * gamma_i, nu, -1)


def dielectric_function(nu, material: Material):
    """ε(ν) = ε∞ · ( 1 − Друде + Σ Лоренц_i ).

    nu — волновое число (число или массив), см⁻¹.
    Возвращает комплексный массив той же формы.
    """
    nu = np.asarray(nu, dtype=float)

    bracket = 1 - drude_term(nu, material)
    for mode in material.bound_modes:
        bracket = bracket + lorentz_term(nu, mode, material.eps_inf)

    return material.eps_inf * bracket
