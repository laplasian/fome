# angular_spectrum.py — отражение в зависимости от угла

Для окна «падение под углом». **Длина волны фиксирована**, угол $\theta$
пробегает от $0$ до $90^\circ$.

Если пользователь задаёт энергию фотона, сначала переводим:
$\lambda = 1240 / E$ (функция `ev_to_nm` из `units.py`).

## Цепочка расчёта

$$
\lambda
\;\to\;
\nu = \frac{10^7}{\lambda}
\;\to\;
\varepsilon(\nu)
\;\to\;
N = \sqrt{\varepsilon}
\qquad\text{(одно комплексное число)}
$$

$$
\theta\,[^\circ] \;\to\; \theta\,[\text{рад}]
\;\to\;
\cos\theta''
\;\to\;
r^{TE}_{12}(\theta),\ r^{TM}_{12}(\theta)
\;\to\;
R^{TE},\ R^{TM},\ \varphi^{TE},\ \varphi^{TM},\ R^{NP}
$$

Формулы — в [oblique_reflection.md](oblique_reflection.md).

## Что возвращается (`AngularSpectrum`)

| Поле            | Величина                        | Номер графика в условии |
|-----------------|---------------------------------|-------------------------|
| `angle_deg`     | $\theta$, градусы — ось X       |                         |
| `R_te`          | $R^{TE}_{12}$                   | 1                       |
| `R_tm`          | $R^{TM}_{12}$                   | 2                       |
| `phase_te_rad`  | $\varphi^{TE}_{12}$, рад        | 3                       |
| `phase_tm_rad`  | $\varphi^{TM}_{12}$, рад        | 4                       |
| `R_np`          | $R^{NP}_{12} = \frac12(R^{TE} + R^{TM})$ | 5              |
| `wavelength_nm`, `energy_ev` | при какой $\lambda$ считали — пишется в файл |  |
| `N`             | $N(\lambda)$ среды              |                         |

## Пример

```python
from calc.parameters import Material
from calc.angular_spectrum import calculate_angular_spectrum

glass = Material(eps_inf=2.25)          # n = 1.5, без поглощения
a = calculate_angular_spectrum(glass, wavelength_nm=633)

a.angle_deg[a.R_tm.argmin()]            # ≈ 56.3° — угол Брюстера
```
