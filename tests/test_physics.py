"""Проверки физики на случаях, ответ для которых известен заранее.

Запуск:  python -m pytest
"""

import numpy as np
import pytest

from calc.angular_spectrum import calculate_angular_spectrum
from calc.comparison import compare_with_experiment
from calc.constants import N_AIR
from calc.data_io import load_experimental_spectrum, parse_two_numbers, save_spectrum
from calc.parameters import BoundMode, FreeCarriers, Material
from calc.plasma_frequency import plasma_frequency
from calc.spectrum import SPECTRUM_QUANTITIES, calculate_spectrum
from calc.units import make_wavelength_grid, nm_to_ev, nm_to_wavenumber

WAVELENGTHS = make_wavelength_grid(190, 2500, 500)

GLASS = Material(eps_inf=2.25)  # n = 1.5, k = 0
METAL = Material(free=FreeCarriers(concentration_cm3=1e22, damping_cm1=500))
LORENTZ = Material(
    eps_inf=2.0,
    bound_modes=[BoundMode(concentration_cm3=1e21, wavelength_nm=500, damping_cm1=2000)],
)


def test_unit_conversions():
    assert nm_to_wavenumber(1000) == pytest.approx(10_000)
    assert nm_to_wavenumber(500) == pytest.approx(20_000)
    assert nm_to_ev(1240) == pytest.approx(1.0)


def test_plasma_frequency_value():
    # N = 1e22 см⁻³, m = m_e  ->  ≈ 2.99e4 см⁻¹ (расчёт вручную в plasma_frequency.md)
    assert plasma_frequency(1e22, 1.0, 1.0) == pytest.approx(2.994e4, rel=1e-3)


def test_plasma_frequency_rejects_zero_eps_inf():
    with pytest.raises(ValueError):
        plasma_frequency(1e22, 1.0, 0.0)


def test_glass_is_transparent_with_four_percent_reflection():
    s = calculate_spectrum(GLASS, WAVELENGTHS)
    assert np.allclose(s.n, 1.5)
    assert np.allclose(s.k, 0)
    assert np.allclose(s.alpha_cm1, 0)
    expected_R = abs((N_AIR - 1.5) / (N_AIR + 1.5)) ** 2
    assert np.allclose(s.R12, expected_R)       # ≈ 0.04
    assert np.allclose(np.abs(s.phase12_rad), np.pi)  # потеря полуволны


def test_eps_equals_n_and_k():
    s = calculate_spectrum(LORENTZ, WAVELENGTHS)
    assert np.allclose(s.eps_real, s.n**2 - s.k**2)
    assert np.allclose(s.eps_imag, 2 * s.n * s.k)


def test_absorption_is_positive_and_peaks_near_resonance():
    s = calculate_spectrum(LORENTZ, WAVELENGTHS)
    assert np.all(s.k >= 0)
    assert np.all(s.alpha_cm1 >= 0)
    peak_nm = s.wavelength_nm[np.argmax(s.eps_imag)]
    assert peak_nm == pytest.approx(500, abs=15)


def test_metal_reflects_strongly_in_infrared():
    s = calculate_spectrum(METAL, WAVELENGTHS)
    assert s.R12[-1] > 0.9           # 2500 нм — далеко ниже плазменной частоты
    assert s.eps_real[-1] < 0


@pytest.mark.parametrize("material", [GLASS, METAL, LORENTZ])
def test_reflection_between_zero_and_one(material):
    s = calculate_spectrum(material, WAVELENGTHS)
    assert np.all((s.R12 >= 0) & (s.R12 <= 1))


def test_film_without_absorption_conserves_energy():
    s = calculate_spectrum(GLASS, WAVELENGTHS, film_thickness_nm=1000)
    assert np.allclose(s.film_T_percent + s.film_R_percent, 100)
    assert s.film_T_percent[0] == pytest.approx(92.3, abs=0.1)


def test_thick_absorbing_film_reflects_like_half_space():
    s = calculate_spectrum(METAL, WAVELENGTHS, film_thickness_nm=1e7)
    assert np.allclose(s.film_T_percent, 0, atol=1e-6)
    assert np.allclose(s.film_R_percent, s.R12 * 100)


@pytest.mark.parametrize("material", [GLASS, METAL, LORENTZ])
def test_oblique_equals_normal_at_zero_angle(material):
    s = calculate_spectrum(material, [633])
    a = calculate_angular_spectrum(material, 633, angle_deg=[0])
    assert a.R_te[0] == pytest.approx(s.R12[0])
    assert a.R_tm[0] == pytest.approx(s.R12[0])


@pytest.mark.parametrize("material", [GLASS, METAL, LORENTZ])
def test_oblique_reflection_between_zero_and_one(material):
    a = calculate_angular_spectrum(material, 633)
    for R in (a.R_te, a.R_tm, a.R_np):
        assert np.all((R >= -1e-12) & (R <= 1 + 1e-12))
    assert a.R_te[-1] == pytest.approx(1)  # скользящее падение, 90°


def test_brewster_angle_for_glass():
    a = calculate_angular_spectrum(GLASS, 633, angle_deg=np.linspace(0, 90, 9001))
    brewster = np.degrees(np.arctan(1.5 / N_AIR.real))
    assert a.angle_deg[np.argmin(a.R_tm)] == pytest.approx(brewster, abs=0.01)
    assert a.R_tm.min() == pytest.approx(0, abs=1e-8)


@pytest.mark.parametrize(
    "line, expected",
    [
        ("190.5\t45.3", (190.5, 45.3)),
        ("190.5   45.3", (190.5, 45.3)),
        ("190,5;45,3", (190.5, 45.3)),
        ("190,5\t45,3", (190.5, 45.3)),
        ("190.5,45.3", (190.5, 45.3)),
        ("190.5, 45.3", (190.5, 45.3)),
        ("190,45", (190.0, 45.0)),
        ("Wavelength (nm)\t%T", None),
        ("", None),
    ],
)
def test_parse_two_numbers(line, expected):
    assert parse_two_numbers(line) == expected


def test_save_and_load_roundtrip(tmp_path):
    s = calculate_spectrum(METAL, WAVELENGTHS)
    path = save_spectrum(tmp_path / "metal.txt", s, list(SPECTRUM_QUANTITIES), METAL)

    table = np.loadtxt(path)
    assert table.shape == (len(WAVELENGTHS), 1 + len(SPECTRUM_QUANTITIES))
    assert np.allclose(table[:, 0], s.wavelength_nm)

    wl, values = load_experimental_spectrum(path)  # первые два столбца: λ и ε'
    assert np.allclose(wl, s.wavelength_nm)
    assert np.allclose(values, s.eps_real, rtol=1e-6)


def test_comparison_of_identical_spectra_gives_zero_rms():
    s = calculate_spectrum(GLASS, WAVELENGTHS, film_thickness_nm=1000)
    c = compare_with_experiment(s.wavelength_nm, s.film_T_percent, s.wavelength_nm[::7], s.film_T_percent[::7])
    assert c.rms == pytest.approx(0, abs=1e-9)
