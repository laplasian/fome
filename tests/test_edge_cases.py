"""Граничные случаи и новые возможности.

Отрицательное и нулевое затухание, кодировки файлов, пределы ввода,
примеры материалов, сетка графиков.
"""

import numpy as np
import pytest

from calc.data_io import load_experimental_spectrum
from calc.film import (
    count_generation_points,
    get_film_reflection,
    get_film_transmission,
)
from calc.parameters import LIMITS, BoundMode, FreeCarriers, Material
from calc.presets import (
    get_preset_material,
    get_preset_names,
    get_preset_thickness,
)
from calc.spectrum import calculate_spectrum
from calc.units import make_wavelength_grid

WAVELENGTHS = make_wavelength_grid(190, 2500, 500)
GAIN = Material(bound_modes=[
    BoundMode(concentration_cm3=1e22, wavelength_nm=500, damping_cm1=-1000),
])
ENCODINGS = ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'cp1251']


def test_film_formulas_match_assignment():
    """При α ≥ 0 результат совпадает с формулами условия «в лоб»."""
    R = np.array([0.04, 0.3, 0.9])
    alpha = np.array([0.0, 50.0, 3e3])
    d_nm = 2000.0
    x = np.exp(-2 * alpha * d_nm * 1e-7)
    T_direct = (1 - R) ** 2 * np.sqrt(x) / (1 - R ** 2 * x) * 100
    R_direct = R * (1 + x - 2 * R * x) / (1 - R ** 2 * x) * 100
    assert np.allclose(get_film_transmission(R, alpha, d_nm), T_direct)
    assert np.allclose(get_film_reflection(R, alpha, d_nm), R_direct)


def test_negative_damping_never_gives_inf_or_negative():
    """При Γ < 0 нет ни бесконечностей, ни отрицательных процентов."""
    for d in [1e6, 1e3, 100.0]:
        s = calculate_spectrum(GAIN, WAVELENGTHS, d)
        for y in [s.film_T_percent, s.film_R_percent]:
            assert not np.isinf(y).any()
            assert (y[~np.isnan(y)] >= 0).all()


def test_generation_threshold_marked_as_nan():
    """Выше порога генерации T и R равны NaN, и эти точки посчитаны."""
    s = calculate_spectrum(GAIN, WAVELENGTHS, 1e6)
    count = count_generation_points(s.R12, s.alpha_cm1, 1e6)
    assert count > 0
    assert count == np.isnan(s.film_T_percent).sum()
    assert count == np.isnan(s.film_R_percent).sum()


def test_below_threshold_gain_film_amplifies():
    """Ниже порога плёнка с Γ < 0 отдаёт больше света: T + R ≥ 100 %."""
    s = calculate_spectrum(GAIN, WAVELENGTHS, 10.0)
    total = s.film_T_percent + s.film_R_percent
    below = ~np.isnan(total)
    assert below.sum() > 0.8 * len(total)
    assert (total[below] >= 100 - 1e-9).all()


def test_zero_damping_exactly_on_resonance_is_finite():
    """Γ = 0 точно на резонансе даёт высокий пик, а не NaN."""
    material = Material(
        free=FreeCarriers(1e22, 1, 0),
        bound_modes=[BoundMode(1e22, 1, 200, 0)],
    )
    s = calculate_spectrum(material, np.array([200.0, 300.0, 1000.0]))
    for y in [s.n, s.k, s.R12, s.film_T_percent]:
        assert np.isfinite(y).all()


@pytest.mark.parametrize('encoding', ENCODINGS)
def test_experiment_file_encodings(tmp_path, encoding):
    """Файл эксперимента читается в любой из кодировок приборов."""
    path = tmp_path / 'spectrum.txt'
    text = 'Длина волны, нм\tT, %\n190,5\t45,3\n200\t46\n'
    path.write_text(text, encoding=encoding)
    x, y = load_experimental_spectrum(path)
    assert np.allclose(x, [190.5, 200])
    assert np.allclose(y, [45.3, 46])


def test_presets_are_within_limits():
    """Все примеры укладываются в пределы из условия и считаются."""
    for name in get_preset_names():
        material = get_preset_material(name)
        low, high = LIMITS['free.concentration_cm3']
        assert low <= material.free.concentration_cm3 <= high
        for mode in material.bound_modes:
            low, high = LIMITS['bound.concentration_cm3']
            assert low <= mode.concentration_cm3 <= high
            low, high = LIMITS['bound.wavelength_nm']
            assert low <= mode.wavelength_nm <= high
        thickness = get_preset_thickness(name)
        low, high = LIMITS['film_thickness_nm']
        assert low <= thickness <= high
        s = calculate_spectrum(material, WAVELENGTHS, thickness)
        assert np.isfinite(s.n).all()
        assert ((s.R12 >= 0) & (s.R12 <= 1)).all()


def test_preset_physics():
    """Примеры ведут себя как обещают названия."""
    names = get_preset_names()
    glass = calculate_spectrum(get_preset_material(names[1]), WAVELENGTHS)
    assert np.allclose(glass.n, 1.5)

    metal_name = 'Металл: плазменный край в УФ (Друде)'
    metal = calculate_spectrum(get_preset_material(metal_name), WAVELENGTHS)
    assert (metal.R12[WAVELENGTHS > 400] > 0.9).all()


def test_grid_size_has_no_empty_rows():
    """Сетка графиков без пустых рядов: 7 графиков — это 4 + 3."""
    from ui.plot_grid import get_grid_size

    assert get_grid_size(1) == (1, 1)
    assert get_grid_size(4) == (2, 2)
    assert get_grid_size(7) == (2, 4)
    for count in range(1, 8):
        rows, columns = get_grid_size(count)
        assert rows * columns >= count
        assert (rows - 1) * columns < count


def test_concentration_inputs_respect_limits():
    """В поля концентраций нельзя ввести больше 1e23 и 1e24."""
    pytest.importorskip('PySide6')
    from PySide6.QtWidgets import QApplication

    from ui.parameter_panel import ParameterPanel

    app = QApplication.instance() or QApplication([])
    panel = ParameterPanel()
    panel.n0.exponent.setValue(23)
    panel.n0.mantissa.setValue(9.9)
    assert panel.n0.value() <= 1e23 * (1 + 1e-12)

    first_mode = panel.mode_rows[0][0]
    first_mode.exponent.setValue(24)
    first_mode.mantissa.setValue(5)
    assert first_mode.value() <= 1e24 * (1 + 1e-12)

    # Обычные значения ограничение не трогает.
    panel.n0.setValue(5.9e22)
    assert panel.n0.value() == pytest.approx(5.9e22)
    assert app is not None
