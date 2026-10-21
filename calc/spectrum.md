# spectrum.py — расчёт спектра целиком

Главная функция для основного окна: по параметрам среды и сетке длин волн
считает **все** величины одним вызовом.

## Цепочка расчёта

$$
\lambda\,[\text{нм}]
\;\xrightarrow{\;10^7/\lambda\;}\;
\nu\,[\text{см}^{-1}]
\;\xrightarrow{\text{Друде–Лоренц}}\;
\varepsilon(\nu)
\;\xrightarrow{\sqrt{\ }}\;
N = n + ik
\;\longrightarrow\;
\begin{cases}
\alpha = 4\pi k\nu \\[2pt]
r_{12} = \dfrac{N_{air} - N}{N_{air} + N} \;\to\; R_{12},\ \varphi_{12}\\[8pt]
T_{film},\ R_{film}\ \ (\text{из } R_{12},\ \alpha,\ d)
\end{cases}
$$

Каждый шаг — отдельный модуль со своим `.md`:

| Шаг | Модуль                     |
|-----|----------------------------|
| 1   | `units.py`                 |
| 2   | `dielectric_function.py` (+ `plasma_frequency.py`) |
| 3   | `refractive_index.py`      |
| 4   | `normal_reflection.py`     |
| 5   | `film.py`                  |

## Что возвращается (`Spectrum`)

| Поле              | Величина                             | Номер графика в условии |
|-------------------|--------------------------------------|-------------------------|
| `wavelength_nm`   | $\lambda$, нм — **ось X по умолчанию** |                       |
| `energy_ev`       | $E = 1240/\lambda$, эВ — ось X по желанию |                    |
| `wavenumber_cm1`  | $\nu$, см⁻¹                          |                         |
| `eps_real`        | $\varepsilon'$                       | 1                       |
| `eps_imag`        | $\varepsilon''$                      | 2                       |
| `n`               | $n$                                  | 3                       |
| `k`               | $k$                                  | 4                       |
| `R12`             | $R_{12}$ (доля, 0…1)                 | 5                       |
| `phase12_rad`     | $\varphi_{12}$, рад                  | 6                       |
| `alpha_cm1`       | $\alpha$, см⁻¹                       | 7                       |
| `film_T_percent`  | $T_{film}$, %                        | плёнка                  |
| `film_R_percent`  | $R_{film}$, %                        | плёнка                  |

Словарь `SPECTRUM_QUANTITIES` — подписи для галочек и легенд в интерфейсе.

## Пример

```python
from calc.parameters import Material, FreeCarriers
from calc.spectrum import calculate_spectrum
from calc.units import make_wavelength_grid

metal = Material(free=FreeCarriers(concentration_cm3=1e22))
s = calculate_spectrum(metal, make_wavelength_grid(190, 2500), film_thickness_nm=50)

s.n, s.k        # массивы n(λ), k(λ)
s.R12           # отражение
```
