# refractive_index.py — показатель преломления и поглощение

## Комплексный показатель преломления

$$
\boxed{\;N(\nu) = \sqrt{\varepsilon(\nu)} = n(\nu) + i\,k(\nu)\;}
$$

- $n$ — обычный показатель преломления (фазовая скорость $c/n$);
- $k$ — показатель экстинкции (затухание амплитуды волны в среде).

Связь с $\varepsilon = \varepsilon' + i\varepsilon''$ (для самопроверки):

$$
\varepsilon' = n^2 - k^2, \qquad \varepsilon'' = 2nk
$$

$$
n = \sqrt{\frac{|\varepsilon| + \varepsilon'}{2}}, \qquad
k = \sqrt{\frac{|\varepsilon| - \varepsilon'}{2}}
$$

**Ветвь корня.** Корень из комплексного числа двузначен. `numpy.sqrt` берёт
главную ветвь с $n = \operatorname{Re}N \ge 0$. При $\varepsilon'' \ge 0$
отсюда автоматически $k \ge 0$ — то, что нужно для поглощающей среды.

## Коэффициент поглощения

Интенсивность в среде спадает как $I(z) = I_0\,e^{-\alpha z}$, где

$$
\boxed{\;\alpha = 4\pi\,k\,\nu\;} \qquad [\text{см}^{-1}],\quad \nu\ \text{в см}^{-1}
$$

Откуда: амплитуда $\propto e^{-k\,\omega z/c}$, интенсивность — квадрат,
значит $\alpha = 2k\omega/c = 2k\cdot 2\pi c\nu / c = 4\pi k\nu$.

Глубина проникновения света $\delta = 1/\alpha$.

## Функции

| Функция                           | Что возвращает                 |
|-----------------------------------|--------------------------------|
| `refractive_index(eps)`           | $N = n + ik$ (комплексный)     |
| `absorption_coefficient(k, nu)`   | $\alpha = 4\pi k\nu$, см⁻¹     |

Реальная и мнимая части: `N.real` → $n$, `N.imag` → $k$.
