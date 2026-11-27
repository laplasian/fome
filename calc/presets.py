"""Готовые примеры сред для меню «Примеры» главного окна.

По умолчанию программа открывается с вакуумом (так требует задание),
и все графики — прямые линии. Примеры позволяют одним щелчком
увидеть, как выглядят типичные спектры. Числа упрощённые, это учебные
модели.
"""

from calc.parameters import (
    DEFAULT_FILM_THICKNESS_NM,
    BoundMode,
    FreeCarriers,
    Material,
)

# Параметры каждого примера. Пустой список мод означает одну моду
# с нулевой концентрацией, как в значениях по умолчанию.
PRESETS = {
    'По умолчанию (вакуум, как в задании)': {
        'eps_inf': 1.0,
        'n0': 0.0,
        'm0': 1.0,
        'gamma0': 100.0,
        'modes': [],
        'thickness': DEFAULT_FILM_THICKNESS_NM,
    },
    'Стекло без дисперсии (n = 1,5)': {
        'eps_inf': 2.25,
        'n0': 0.0,
        'm0': 1.0,
        'gamma0': 100.0,
        'modes': [],
        'thickness': DEFAULT_FILM_THICKNESS_NM,
    },
    'Кварцевое стекло: дисперсия и поглощение в УФ (Лоренц)': {
        'eps_inf': 1.0,
        'n0': 0.0,
        'm0': 1.0,
        'gamma0': 100.0,
        'modes': [
            {'n': 3e22, 'm': 1.0, 'wavelength': 150.0, 'gamma': 3000.0},
        ],
        'thickness': DEFAULT_FILM_THICKNESS_NM,
    },
    'Полупроводник, похожий на Si: край поглощения (Лоренц)': {
        'eps_inf': 1.0,
        'n0': 0.0,
        'm0': 1.0,
        'gamma0': 100.0,
        'modes': [
            {'n': 8.7e22, 'm': 1.0, 'wavelength': 370.0, 'gamma': 5000.0},
        ],
        'thickness': 10_000.0,
    },
    'Металл: плазменный край в УФ (Друде)': {
        'eps_inf': 1.0,
        'n0': 5.9e22,
        'm0': 1.0,
        'gamma0': 150.0,
        'modes': [],
        'thickness': 100.0,
    },
    'Сильно легированный n-Si: плазменный край в ИК (Друде)': {
        'eps_inf': 11.7,
        'n0': 1e21,
        'm0': 0.26,
        'gamma0': 300.0,
        'modes': [],
        'thickness': DEFAULT_FILM_THICKNESS_NM,
    },
}


def get_preset_names():
    """Возвращает названия примеров в том порядке, как они в меню."""
    names = []
    for name in PRESETS:
        names.append(name)
    return names


def get_preset_material(name):
    """Собирает Material из словаря примера."""
    preset = PRESETS[name]
    modes = []
    for mode in preset['modes']:
        modes.append(BoundMode(
            concentration_cm3=mode['n'],
            mass_in_me=mode['m'],
            wavelength_nm=mode['wavelength'],
            damping_cm1=mode['gamma'],
        ))
    if not modes:
        modes.append(BoundMode())

    free = FreeCarriers(
        concentration_cm3=preset['n0'],
        mass_in_me=preset['m0'],
        damping_cm1=preset['gamma0'],
    )
    return Material(eps_inf=preset['eps_inf'], free=free, bound_modes=modes)


def get_preset_thickness(name):
    """Возвращает толщину плёнки примера, нм."""
    return PRESETS[name]['thickness']
