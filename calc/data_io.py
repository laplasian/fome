"""Чтение экспериментальных спектров и сохранение результатов в текстовые (ASCII) файлы."""

import re
from pathlib import Path

import numpy as np

from calc.angular_spectrum import AngularSpectrum
from calc.parameters import Material, describe_material
from calc.spectrum import Spectrum


# ---------- Чтение эксперимента ----------

def parse_two_numbers(line):
    """Достаёт из строки два числа (λ и значение) или None, если это заголовок/мусор.

    Понимает разделители: пробелы, табуляцию, «;» и «,».
    Запятая — это либо разделитель («190.5, 45.3» или «190,45»),
    либо десятичный знак, как в русском Excel («190,5;45,3» -> 190.5, 45.3).
    """
    line = line.strip()
    if not line:
        return None

    comma_is_separator = "." in line or not re.search(r"[\s;]", line)
    if comma_is_separator:
        parts = re.split(r"[\s;,]+", line)
    else:
        parts = re.split(r"[\s;]+", line.replace(",", "."))

    try:
        return float(parts[0]), float(parts[1])
    except (ValueError, IndexError):
        return None


def load_experimental_spectrum(path):
    """Файл из 2 столбцов: длина волны [нм] и T или R [%].

    Возвращает (wavelength_nm, values_percent), отсортированные по λ.
    Строки, которые не читаются как два числа (заголовки), пропускаются.
    """
    rows = []
    with open(path, encoding="utf-8", errors="replace") as file:
        for line in file:
            pair = parse_two_numbers(line)
            if pair is not None:
                rows.append(pair)

    if not rows:
        raise ValueError(f"В файле {path} не найдено ни одной строки с двумя числами")

    data = np.array(sorted(rows))
    return data[:, 0], data[:, 1]


# ---------- Сохранение ----------

def save_table(path, columns: dict, header_lines=()):
    """Сохраняет столбцы в текстовый файл через табуляцию.

    columns      — {имя столбца: массив}, порядок сохраняется
    header_lines — строки комментария в начале файла (начинаются с «#»)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    names = list(columns)
    table = np.column_stack([np.asarray(columns[name], dtype=float) for name in names])
    header = "\n".join([*header_lines, "\t".join(names)])

    np.savetxt(path, table, delimiter="\t", fmt="%.8g", header=header, comments="# ", encoding="ascii")
    return path


def save_spectrum(path, spectrum: Spectrum, quantities, material: Material, x_axis="nm"):
    """Сохраняет выбранные величины спектра.

    quantities — список ключей из SPECTRUM_QUANTITIES, например ["n", "k"]
    x_axis     — "nm" (по умолчанию) или "ev"
    """
    if x_axis == "ev":
        columns = {"energy_eV": spectrum.energy_ev}
    else:
        columns = {"wavelength_nm": spectrum.wavelength_nm}

    for key in quantities:
        columns[key] = getattr(spectrum, key)

    header = [
        "Drude-Lorentz model, normal incidence from air",
        *describe_material(material),
        f"film thickness d = {spectrum.film_thickness_nm:g} nm",
    ]
    return save_table(path, columns, header)


def save_angular_spectrum(path, angular: AngularSpectrum, quantities, material: Material):
    """Сохраняет выбранные величины зависимости от угла.

    Длина волны и энергия фотона пишутся в заголовок файла.
    """
    columns = {"angle_deg": angular.angle_deg}
    for key in quantities:
        columns[key] = getattr(angular, key)

    header = [
        "Drude-Lorentz model, oblique incidence from air",
        f"lambda = {angular.wavelength_nm:g} nm, E = {angular.energy_ev:.4g} eV",
        f"N = {angular.N.real:.6g} + i*{angular.N.imag:.6g}",
        *describe_material(material),
    ]
    return save_table(path, columns, header)


def angular_file_name(base_name, wavelength_nm):
    """Имя файла с длиной волны: 'gold' -> 'gold_633nm.txt'."""
    return f"{base_name}_{wavelength_nm:g}nm.txt"
