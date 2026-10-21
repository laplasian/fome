# ФОМЭ 2026 — Задача 1

**Расчёт комплексного показателя преломления среды и коэффициента отражения
в модели Друде–Лоренца.**

Программа состоит из двух частей:

| Папка    | Что внутри                                                   |
|----------|--------------------------------------------------------------|
| `calc/`  | Расчётный блок: только физика и числа, никакого интерфейса.   |
| `ui/`    | Интерфейс: PySide6 + matplotlib ([описание](ui/README.md)).   |

Каждый файл в `calc/` решает одну логическую задачу, и рядом с ним лежит
`.md`-файл с теми же именем, где выписаны формулы и пояснения.

## Порядок расчёта

```
parameters  ──►  plasma_frequency  ──►  dielectric_function  ──►  refractive_index
                                                                      │
                     ┌────────────────────────┬───────────────────────┤
                     ▼                        ▼                       ▼
              normal_reflection      oblique_reflection       (α — поглощение)
                     │                                                │
                     └──────────────►  film  ◄────────────────────────┘

spectrum         — собирает всё в одну таблицу по длинам волн
angular_spectrum — собирает отражение под углом в таблицу по углам
data_io          — чтение экспериментальных файлов и сохранение результатов
comparison       — сравнение расчёта с экспериментом
```

| Файл                                   | Что считает                                       |
|----------------------------------------|---------------------------------------------------|
| [constants](calc/constants.md)         | Физические константы в СГС                        |
| [units](calc/units.md)                 | Перевод нм ↔ см⁻¹ ↔ эВ, градусы ↔ радианы         |
| [parameters](calc/parameters.md)       | Входные параметры, значения по умолчанию, пределы |
| [plasma_frequency](calc/plasma_frequency.md) | Плазменные частоты $\Omega_{p0}$, $\Omega_{pi}$ |
| [dielectric_function](calc/dielectric_function.md) | $\varepsilon(\nu)$ модели Друде–Лоренца |
| [refractive_index](calc/refractive_index.md) | $N = n + ik$ и коэффициент поглощения $\alpha$ |
| [normal_reflection](calc/normal_reflection.md) | $r_{12}$, $R_{12}$, $\varphi_{12}$ при нормальном падении |
| [oblique_reflection](calc/oblique_reflection.md) | TE/TM-отражение под углом $\theta$ |
| [film](calc/film.md)                   | Пропускание и отражение плёнки в %                |
| [spectrum](calc/spectrum.md)           | Все величины как функции длины волны              |
| [angular_spectrum](calc/angular_spectrum.md) | Все величины как функции угла падения       |
| [data_io](calc/data_io.md)             | Импорт эксперимента и экспорт в ASCII             |
| [comparison](calc/comparison.md)       | Сравнение расчёта с экспериментом                 |

## Установка и запуск

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

Запуск программы:

```bash
.venv\Scripts\python main.py
```

Сборка в один файл `dist\DrudeLorentz.exe` (≈ 75 МБ, запускается на любом
Windows 10/11 без установки Python):

```bash
build_exe.bat
```

Пример расчёта без интерфейса (сохраняет файлы в `output/`):

```bash
.venv\Scripts\python examples\example_calculation.py
```

Проверки физики (сумма R + T = 100 % без поглощения, угол Брюстера и т.д.):

```bash
.venv\Scripts\python -m pytest
```

## Соглашения

- Внутри расчёта всё в **СГС** и частоты в **см⁻¹** ($\nu = 1/\lambda$).
- На вход и на выход (графики, файлы) — **нанометры** (или эВ по желанию).
- Фазы — в **радианах**, в диапазоне $(-\pi, \pi]$.
- Знак мнимой части: $N = n + ik$, $k \ge 0$ для поглощающей среды.
