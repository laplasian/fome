"""Машинная подгонка параметров модели под экспериментальные T и R плёнки.

Минимизируется  RMS_T² + RMS_R²  по параметрам, отмеченным «подгонять»,
каждый — в своих пределах [от, до]. Остальные параметры закреплены.
"""

import copy
from dataclasses import dataclass

import numpy as np
from scipy.optimize import differential_evolution, least_squares

from calc.parameters import Material
from calc.spectrum import calculate_spectrum

# Какие величины спектра сравниваются с какими экспериментами
EXPERIMENT_QUANTITY = {"T": "film_T_percent", "R": "film_R_percent"}

# Подписи параметров для интерфейса (для мод — шаблоны с номером i)
LABELS = {
    "eps_inf": "ε∞",
    "film_thickness_nm": "d, нм",
    "concentration_cm3": "N{i}, см⁻³",
    "mass_in_me": "m{i} / mₑ",
    "wavelength_nm": "λ{i}, нм",
    "damping_cm1": "Γ{i}, см⁻¹",
}

# Если невязка не число (переполнение экспоненты при диких параметрах) —
# подставляем большое значение, чтобы оптимизатор ушёл из этой области.
BAD_RESIDUAL = 1e3


class FitStopped(Exception):
    """Пользователь нажал «Стоп»."""


@dataclass
class FitParameter:
    """Один параметр модели в подгонке."""

    key: str      # "eps_inf", "film_thickness_nm", "free.damping_cm1", "bound.0.wavelength_nm"
    label: str
    value: float  # текущее значение (стартовая точка)
    lower: float  # предел «от»
    upper: float  # предел «до»
    fit: bool = False  # True — подгонять, False — закрепить

    @property
    def log_scale(self):
        """Концентрации меняются на порядки — для них ищем log10(N), а не N."""
        return self.key.endswith("concentration_cm3") and self.lower > 0


@dataclass
class FitResult:
    material: Material
    film_thickness_nm: float
    values: dict         # ключ параметра -> найденное значение
    rms: dict            # "T"/"R" -> RMS после подгонки, %
    rms_before: dict     # "T"/"R" -> RMS до подгонки, %
    evaluations: int     # сколько раз считался спектр
    stopped: bool        # остановлено пользователем (результат — лучший найденный)


# ---------- доступ к параметру модели по ключу ----------

def _owner_and_field(material: Material, key):
    """'free.damping_cm1' -> (material.free, 'damping_cm1') и т.п."""
    parts = key.split(".")
    if parts[0] == "free":
        return material.free, parts[1]
    if parts[0] == "bound":
        return material.bound_modes[int(parts[1])], parts[2]
    return material, parts[0]


def get_value(material: Material, film_thickness_nm, key):
    if key == "film_thickness_nm":
        return film_thickness_nm
    owner, field = _owner_and_field(material, key)
    return getattr(owner, field)


def with_values(material: Material, film_thickness_nm, values: dict):
    """Копия модели, в которой параметры из values заменены. Оригинал не меняется."""
    material = copy.deepcopy(material)
    for key, value in values.items():
        if key == "film_thickness_nm":
            film_thickness_nm = value
        else:
            owner, field = _owner_and_field(material, key)
            setattr(owner, field, value)
    return material, film_thickness_nm


# ---------- список параметров и пределы по умолчанию ----------

def default_bounds(key, value):
    """Разумные пределы «от–до» вокруг текущего значения (пользователь может поменять)."""
    field = key.split(".")[-1]
    if field == "concentration_cm3":
        return (value / 10, value * 10) if value > 0 else (1e15, 1e22)
    if field == "wavelength_nm":
        return max(100.0, value * 0.8), min(10_000.0, value * 1.2)
    if field == "damping_cm1":
        return (max(1.0, value / 10), value * 10) if value > 0 else (1.0, 10_000.0)
    if field == "eps_inf":
        return max(0.01, value / 2), value * 2
    if field == "film_thickness_nm":
        return max(1.0, value * 0.5), value * 1.5
    return value / 3, value * 3  # массы


def list_parameters(material: Material, film_thickness_nm) -> list[FitParameter]:
    """Все параметры модели в порядке: ε∞, d, свободные носители, моды 1…K."""
    keys = ["eps_inf", "film_thickness_nm"]
    keys += [f"free.{field}" for field in ("concentration_cm3", "mass_in_me", "damping_cm1")]
    for i in range(len(material.bound_modes)):
        keys += [f"bound.{i}.{field}" for field in ("concentration_cm3", "mass_in_me", "wavelength_nm", "damping_cm1")]

    parameters = []
    for key in keys:
        field = key.split(".")[-1]
        if key.startswith("free."):
            number = "0"
        elif key.startswith("bound."):
            number = str(int(key.split(".")[1]) + 1)
        else:
            number = ""
        value = get_value(material, film_thickness_nm, key)
        lower, upper = default_bounds(key, value)
        parameters.append(FitParameter(key, LABELS[field].format(i=number), value, lower, upper))
    return parameters


# ---------- целевая функция ----------

def residuals(material: Material, film_thickness_nm, experiments: dict):
    """Невязки (расчёт − эксперимент)/√M для всех загруженных спектров подряд.

    Сумма их квадратов ровно равна  RMS_T² + RMS_R².
    experiments — {"T": (λ, значения %), "R": (λ, значения %)}, можно только один.
    """
    parts = []
    for name, (wavelength_nm, measured) in experiments.items():
        spectrum = calculate_spectrum(material, wavelength_nm, film_thickness_nm)
        calculated = getattr(spectrum, EXPERIMENT_QUANTITY[name])
        parts.append((calculated - measured) / np.sqrt(len(measured)))
    vector = np.concatenate(parts)
    return np.nan_to_num(vector, nan=BAD_RESIDUAL, posinf=BAD_RESIDUAL, neginf=-BAD_RESIDUAL)


def rms_by_experiment(material: Material, film_thickness_nm, experiments: dict):
    """{"T": RMS_T, "R": RMS_R} в процентах."""
    return {
        name: float(np.sqrt(np.sum(residuals(material, film_thickness_nm, {name: data}) ** 2)))
        for name, data in experiments.items()
    }


# ---------- сама подгонка ----------

def _check(parameters, experiments):
    if not experiments:
        raise ValueError("Загрузите хотя бы один экспериментальный спектр (T или R)")
    if not any(p.fit for p in parameters):
        raise ValueError("Отметьте хотя бы один параметр для подгонки")
    for p in parameters:
        if p.fit and not p.lower < p.upper:
            raise ValueError(f"{p.label}: предел «от» должен быть меньше «до»")
        if p.fit and p.key == "eps_inf" and p.lower <= 0:
            raise ValueError("ε∞: нижний предел должен быть больше нуля")
        if p.fit and p.key.split(".")[-1] in ("concentration_cm3", "mass_in_me", "film_thickness_nm") and p.lower < 0:
            raise ValueError(f"{p.label}: нижний предел не может быть отрицательным")


def fit_parameters(
    material: Material,
    film_thickness_nm,
    parameters: list[FitParameter],
    experiments: dict,
    method="local",
    on_progress=None,
    should_stop=None,
) -> FitResult:
    """Подбирает отмеченные параметры.

    method      — "local" (быстро, от текущих значений) или
                  "global" (дифференциальная эволюция по всей области + уточнение)
    on_progress — функция(число вычислений, лучшее √(RMS_T² + RMS_R²)) для индикатора
    should_stop — функция() -> True, если пора остановиться
    """
    _check(parameters, experiments)
    free = [p for p in parameters if p.fit]

    # Оптимизатор работает в «единичном кубе»: каждый параметр u ∈ [0, 1],
    # u = 0 — предел «от», u = 1 — предел «до» (для концентраций — в логарифме).
    def to_internal(p, x):
        return np.log10(x) if p.log_scale else x

    lows = np.array([to_internal(p, p.lower) for p in free])
    highs = np.array([to_internal(p, p.upper) for p in free])

    def unpack(u):
        internal = lows + np.asarray(u) * (highs - lows)
        values = {p.key: (10**x if p.log_scale else x) for p, x in zip(free, internal)}
        return values

    start_internal = np.array([to_internal(p, min(max(p.value, p.lower), p.upper)) for p in free])
    u_start = (start_internal - lows) / (highs - lows)

    best = {"cost": np.inf, "u": u_start}
    evaluations = 0

    def residual_vector(u):
        nonlocal evaluations
        if should_stop is not None and should_stop():
            raise FitStopped
        model = with_values(material, film_thickness_nm, unpack(u))
        vector = residuals(*model, experiments)
        evaluations += 1
        cost = float(np.sum(vector**2))
        if cost < best["cost"]:
            best["cost"], best["u"] = cost, np.array(u, dtype=float)
        if on_progress is not None and evaluations % 25 == 0:
            on_progress(evaluations, float(np.sqrt(best["cost"])))
        return vector

    stopped = False
    try:
        if method == "global":
            differential_evolution(
                lambda u: float(np.sum(residual_vector(u) ** 2)),
                bounds=[(0.0, 1.0)] * len(free),
                x0=u_start,
                maxiter=150,
                popsize=15,
                tol=1e-7,
                polish=False,
                seed=0,
            )
            u_start = best["u"]  # уточняем лучшую точку локальным методом
        least_squares(residual_vector, u_start, bounds=(0.0, 1.0), max_nfev=200 * (len(free) + 1))
    except FitStopped:
        stopped = True

    values = unpack(best["u"])
    fitted_material, fitted_thickness = with_values(material, film_thickness_nm, values)
    return FitResult(
        material=fitted_material,
        film_thickness_nm=fitted_thickness,
        values=values,
        rms=rms_by_experiment(fitted_material, fitted_thickness, experiments),
        rms_before=rms_by_experiment(material, film_thickness_nm, experiments),
        evaluations=evaluations,
        stopped=stopped,
    )
