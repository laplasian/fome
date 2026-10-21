"""Пример: как пользоваться расчётным блоком без интерфейса.

Запуск из корня проекта:
    python examples/example_calculation.py

Результаты сохраняются в папку output/.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calc.angular_spectrum import ANGULAR_QUANTITIES, calculate_angular_spectrum
from calc.data_io import angular_file_name, save_angular_spectrum, save_spectrum
from calc.parameters import BoundMode, FreeCarriers, Material
from calc.plasma_frequency import bound_plasma_frequencies, free_plasma_frequency
from calc.spectrum import SPECTRUM_QUANTITIES, calculate_spectrum
from calc.units import make_wavelength_grid

OUTPUT = Path(__file__).resolve().parent.parent / "output"

# 1. Задаём среду: немного свободных электронов + одна мода связанных зарядов
material = Material(
    eps_inf=2.0,
    free=FreeCarriers(concentration_cm3=1e20, mass_in_me=0.3, damping_cm1=200),
    bound_modes=[BoundMode(concentration_cm3=1e21, mass_in_me=1, wavelength_nm=300, damping_cm1=3000)],
)

# 2. Плазменные частоты (их программа показывает на экране)
print(f"Ω_p0 = {free_plasma_frequency(material):10.1f} см⁻¹")
for i, omega in enumerate(bound_plasma_frequencies(material), start=1):
    print(f"Ω_p{i} = {omega:10.1f} см⁻¹")

# 3. Спектр от 190 до 2500 нм, плёнка 1 мкм
wavelengths = make_wavelength_grid(190, 2500, 2000)
spectrum = calculate_spectrum(material, wavelengths, film_thickness_nm=1000)

print("\n  λ, нм      n        k        R12     T_film,%  R_film,%")
for j in range(0, len(wavelengths), 250):
    print(
        f"{spectrum.wavelength_nm[j]:7.1f} {spectrum.n[j]:8.4f} {spectrum.k[j]:8.4f} "
        f"{spectrum.R12[j]:8.4f} {spectrum.film_T_percent[j]:9.2f} {spectrum.film_R_percent[j]:9.2f}"
    )

# 4. Отражение под углом на 633 нм
angular = calculate_angular_spectrum(material, wavelength_nm=633)
brewster = angular.angle_deg[angular.R_tm.argmin()]
print(f"\nλ = 633 нм: N = {angular.N:.4f}, минимум R_TM при θ = {brewster:.1f}°")

# 5. Сохраняем
path1 = save_spectrum(OUTPUT / "spectrum.txt", spectrum, list(SPECTRUM_QUANTITIES), material)
path2 = save_angular_spectrum(
    OUTPUT / angular_file_name("angular", 633), angular, list(ANGULAR_QUANTITIES), material
)
print(f"\nСохранено:\n  {path1}\n  {path2}")
