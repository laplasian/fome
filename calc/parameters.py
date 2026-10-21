"""Входные параметры модели Друде–Лоренца.

Здесь только данные: что задаёт пользователь, значения по умолчанию
и допустимые пределы из условия задачи. Никаких расчётов.
"""

from dataclasses import dataclass, field

MAX_BOUND_MODES = 10


@dataclass
class FreeCarriers:
    """Свободные носители заряда (вклад Друде)."""

    concentration_cm3: float = 0.0  # N0, см⁻³   (0 = диэлектрик)
    mass_in_me: float = 1.0         # m0 в массах свободного электрона
    damping_cm1: float = 100.0      # Γ0, см⁻¹


@dataclass
class BoundMode:
    """Одна мода связанных зарядов (осциллятор Лоренца)."""

    concentration_cm3: float = 0.0  # Ni, см⁻³
    mass_in_me: float = 1.0         # mi в массах свободного электрона
    wavelength_nm: float = 200.0    # λi, нм  (резонанс; νi = 10^7 / λi)
    damping_cm1: float = 1000.0     # Γi, см⁻¹


@dataclass
class Material:
    """Среда целиком: ε∞, свободные носители и K мод связанных зарядов."""

    eps_inf: float = 1.0
    free: FreeCarriers = field(default_factory=FreeCarriers)
    bound_modes: list[BoundMode] = field(default_factory=lambda: [BoundMode()])


# Допустимые пределы (от, до) — для проверки ввода в интерфейсе.
LIMITS = {
    "eps_inf": (0.0, 1000.0),
    "free.concentration_cm3": (0.0, 1e23),
    "free.mass_in_me": (0.0, None),
    "free.damping_cm1": (-100_000.0, 100_000.0),  # отрицательные разрешены
    "bound.concentration_cm3": (0.0, 1e24),
    "bound.mass_in_me": (0.0, None),
    "bound.wavelength_nm": (100.0, 10_000.0),
    "bound.damping_cm1": (-100_000.0, 100_000.0),  # отрицательные разрешены
    "bound_modes_count": (1, MAX_BOUND_MODES),
    "film_thickness_nm": (1.0, 1e7),
    "wavelength_nm": (190.0, 2500.0),              # по умолчанию, можно менять
    "angle_deg": (0.0, 90.0),
}

DEFAULT_FILM_THICKNESS_NM = 1_000_000.0  # 1 мм
DEFAULT_WAVELENGTH_RANGE_NM = (190.0, 2500.0)


def describe_material(material: Material) -> list[str]:
    """Параметры среды в виде строк — для заголовка сохраняемых файлов."""
    free = material.free
    lines = [
        f"eps_inf = {material.eps_inf:g}",
        f"N0 = {free.concentration_cm3:g} cm^-3, m0 = {free.mass_in_me:g} m_e, "
        f"Gamma0 = {free.damping_cm1:g} cm^-1",
        f"K = {len(material.bound_modes)}",
    ]
    for i, mode in enumerate(material.bound_modes, start=1):
        lines.append(
            f"mode {i}: N = {mode.concentration_cm3:g} cm^-3, m = {mode.mass_in_me:g} m_e, "
            f"lambda = {mode.wavelength_nm:g} nm, Gamma = {mode.damping_cm1:g} cm^-1"
        )
    return lines
