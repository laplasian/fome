"""Проверки подгонки: по «эксперименту», рассчитанному при известных параметрах,
подгонка должна найти эти параметры обратно."""

import numpy as np
import pytest

from calc.fitting import (
    fit_parameters,
    get_value,
    list_parameters,
    residuals,
    rms_by_experiment,
    with_values,
)
from calc.parameters import BoundMode, Material
from calc.spectrum import calculate_spectrum

WAVELENGTHS = np.linspace(250, 2400, 300)

TRUE_MATERIAL = Material(
    eps_inf=2.0,
    bound_modes=[BoundMode(concentration_cm3=5e20, wavelength_nm=800, damping_cm1=1500)],
)
TRUE_THICKNESS = 2000.0


def synthetic_experiments():
    s = calculate_spectrum(TRUE_MATERIAL, WAVELENGTHS, TRUE_THICKNESS)
    return {"T": (WAVELENGTHS, s.film_T_percent), "R": (WAVELENGTHS, s.film_R_percent)}


def start_model():
    """Стартовая точка — специально немного неправильная."""
    return with_values(TRUE_MATERIAL, TRUE_THICKNESS, {
        "bound.0.wavelength_nm": 760.0,
        "bound.0.concentration_cm3": 3e20,
        "film_thickness_nm": 1500.0,
    })


def mark_for_fit(parameters, bounds):
    for p in parameters:
        if p.key in bounds:
            p.fit = True
            p.lower, p.upper = bounds[p.key]
    return parameters


BOUNDS = {
    "bound.0.wavelength_nm": (650.0, 950.0),
    "bound.0.concentration_cm3": (1e20, 2e21),
    "film_thickness_nm": (500.0, 5000.0),
}


def test_get_and_set_by_key():
    material, d = with_values(TRUE_MATERIAL, 100.0, {"free.damping_cm1": 7.0, "bound.0.mass_in_me": 2.0, "film_thickness_nm": 5.0})
    assert get_value(material, d, "free.damping_cm1") == 7.0
    assert get_value(material, d, "bound.0.mass_in_me") == 2.0
    assert d == 5.0
    assert TRUE_MATERIAL.free.damping_cm1 == 100.0  # оригинал не изменился


def test_parameter_list_has_all_fields():
    parameters = list_parameters(TRUE_MATERIAL, TRUE_THICKNESS)
    assert len(parameters) == 2 + 3 + 4  # ε∞, d, свободные, одна мода
    assert [p.label for p in parameters][:2] == ["ε∞", "d, нм"]
    assert all(p.lower < p.upper for p in parameters)


def test_residuals_sum_equals_rms_squared():
    material, d = start_model()
    experiments = synthetic_experiments()
    total = np.sum(residuals(material, d, experiments) ** 2)
    rms = rms_by_experiment(material, d, experiments)
    assert total == pytest.approx(rms["T"] ** 2 + rms["R"] ** 2)


@pytest.mark.parametrize("method", ["local", "global"])
def test_fit_recovers_true_parameters(method):
    material, d = start_model()
    parameters = mark_for_fit(list_parameters(material, d), BOUNDS)

    result = fit_parameters(material, d, parameters, synthetic_experiments(), method=method)

    assert result.values["bound.0.wavelength_nm"] == pytest.approx(800, rel=1e-3)
    assert result.values["bound.0.concentration_cm3"] == pytest.approx(5e20, rel=1e-2)
    assert result.film_thickness_nm == pytest.approx(TRUE_THICKNESS, rel=1e-2)
    assert result.rms["T"] < 0.01 and result.rms["R"] < 0.01
    assert result.rms["T"] < result.rms_before["T"]


def test_fixed_parameters_do_not_change():
    material, d = start_model()
    parameters = mark_for_fit(list_parameters(material, d), {"film_thickness_nm": (500.0, 5000.0)})
    result = fit_parameters(material, d, parameters, synthetic_experiments())
    assert result.material.bound_modes[0].wavelength_nm == 760.0
    assert set(result.values) == {"film_thickness_nm"}


def test_stop_returns_starting_point():
    material, d = start_model()
    parameters = mark_for_fit(list_parameters(material, d), BOUNDS)
    result = fit_parameters(material, d, parameters, synthetic_experiments(), should_stop=lambda: True)
    assert result.stopped
    assert result.film_thickness_nm == pytest.approx(1500.0)


def test_errors_are_explained():
    material, d = start_model()
    parameters = list_parameters(material, d)
    with pytest.raises(ValueError, match="Отметьте"):
        fit_parameters(material, d, parameters, synthetic_experiments())
    with pytest.raises(ValueError, match="Загрузите"):
        fit_parameters(material, d, mark_for_fit(parameters, BOUNDS), {})
    parameters[0].fit, parameters[0].lower, parameters[0].upper = True, 5.0, 1.0
    with pytest.raises(ValueError, match="меньше"):
        fit_parameters(material, d, parameters, synthetic_experiments())
