"""Граничные случаи: отрицательное и нулевое затухание, кодировки файлов, пределы ввода."""

import numpy as np
import pytest

from calc.data_io import load_experimental_spectrum
from calc.film import film_generation_points, film_reflection, film_transmission
from calc.parameters import BoundMode, FreeCarriers, Material
from calc.spectrum import calculate_spectrum
from calc.units import make_wavelength_grid

WAVELENGTHS = make_wavelength_grid(190, 2500, 500)
GAIN = Material(bound_modes=[BoundMode(concentration_cm3=1e22, wavelength_nm=500, damping_cm1=-1000)])


def test_film_formulas_unchanged_for_absorbing_film():
    # Обычный случай (α ≥ 0): совпадает с формулами из условия, записанными «в лоб».
    R, alpha, d_nm = np.array([0.04, 0.3, 0.9]), np.array([0.0, 50.0, 3e3]), 2000.0
    x = np.exp(-2 * alpha * d_nm * 1e-7)
    T_direct = (1 - R) ** 2 * np.sqrt(x) / (1 - R**2 * x) * 100
    R_direct = R * (1 + x - 2 * R * x) / (1 - R**2 * x) * 100
    assert np.allclose(film_transmission(R, alpha, d_nm), T_direct)
    assert np.allclose(film_reflection(R, alpha, d_nm), R_direct)


def test_negative_damping_never_gives_inf_or_negative():
    for d in (1e6, 1e3, 100.0):
        s = calculate_spectrum(GAIN, WAVELENGTHS, d)
        for values in (s.film_T_percent, s.film_R_percent):
            finite = values[~np.isnan(values)]
            assert not np.isinf(values).any()
            assert (finite >= 0).all()


def test_generation_threshold_marked_as_nan():
    # Толстая плёнка с усилением: ряд переотражений расходится -> NaN, и это посчитано.
    s = calculate_spectrum(GAIN, WAVELENGTHS, 1e6)
    count = film_generation_points(s.R12, s.alpha_cm1, 1e6)
    assert count == np.isnan(s.film_T_percent).sum() == np.isnan(s.film_R_percent).sum()
    assert count > 0


def test_below_threshold_gain_film_amplifies():
    # Ниже порога генерации плёнка с Γ < 0 отдаёт больше света, чем получила: T + R ≥ 100 %.
    s = calculate_spectrum(GAIN, WAVELENGTHS, 10.0)
    total = s.film_T_percent + s.film_R_percent
    below = ~np.isnan(total)
    assert below.sum() > 0.8 * len(total)
    assert (total[below] >= 100 - 1e-9).all()


def test_zero_damping_exactly_on_resonance_is_finite():
    m = Material(free=FreeCarriers(1e22, 1, 0), bound_modes=[BoundMode(1e22, 1, 200, 0)])
    s = calculate_spectrum(m, np.array([200.0, 300.0, 1000.0]))
    for values in (s.n, s.k, s.R12, s.film_T_percent):
        assert np.isfinite(values).all()


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "utf-16", "utf-16-le", "cp1251"])
def test_experiment_file_encodings(tmp_path, encoding):
    path = tmp_path / "spectrum.txt"
    path.write_text("Длина волны, нм\tT, %\n190,5\t45,3\n200\t46\n", encoding=encoding)
    wavelength, values = load_experimental_spectrum(path)
    assert np.allclose(wavelength, [190.5, 200])
    assert np.allclose(values, [45.3, 46])


def test_concentration_inputs_respect_limits():
    pytest.importorskip("PySide6")
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
    panel.n0.setValue(5.9e22)                     # обычные значения не трогаются
    assert panel.n0.value() == pytest.approx(5.9e22)
    assert app is not None
