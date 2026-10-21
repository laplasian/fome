"""Комплексный показатель преломления N = n + ik и коэффициент поглощения α."""

import numpy as np


def refractive_index(eps):
    """N = sqrt(ε) = n + i·k.

    numpy берёт главную ветвь корня (Re N ≥ 0), поэтому при ε'' ≥ 0
    автоматически получаются n ≥ 0 и k ≥ 0.
    """
    return np.sqrt(np.asarray(eps, dtype=complex))


def absorption_coefficient(k, nu):
    """Коэффициент поглощения α = 4π · k · ν  [см⁻¹], ν в см⁻¹."""
    return 4 * np.pi * np.asarray(k) * np.asarray(nu)
