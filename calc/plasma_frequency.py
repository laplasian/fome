"""Плазменные частоты свободных и связанных зарядов (в см⁻¹)."""

import numpy as np

from calc.constants import ELECTRON_CHARGE, ELECTRON_MASS, SPEED_OF_LIGHT
from calc.parameters import Material


def plasma_frequency(concentration_cm3, mass_in_me, eps_inf):
    """Плазменная частота Ω_p [см⁻¹]:

        Ω_p = e / (2π c) · sqrt( 4π N / (m · ε∞) )

    concentration_cm3 — N, см⁻³
    mass_in_me        — m в массах электрона (умножаем на 9.1e-28 г)
    eps_inf           — ε∞
    """
    if eps_inf <= 0:
        raise ValueError("ε∞ должна быть больше нуля: она стоит в знаменателе Ω_p")

    mass_g = mass_in_me * ELECTRON_MASS
    return ELECTRON_CHARGE / (2 * np.pi * SPEED_OF_LIGHT) * np.sqrt(
        4 * np.pi * concentration_cm3 / (mass_g * eps_inf)
    )


def free_plasma_frequency(material: Material):
    """Ω_p0 — плазменная частота свободных носителей, см⁻¹."""
    free = material.free
    return plasma_frequency(free.concentration_cm3, free.mass_in_me, material.eps_inf)


def bound_plasma_frequencies(material: Material):
    """[Ω_p1, Ω_p2, ..., Ω_pK] — плазменные частоты всех мод связанных зарядов, см⁻¹."""
    return [
        plasma_frequency(mode.concentration_cm3, mode.mass_in_me, material.eps_inf)
        for mode in material.bound_modes
    ]
