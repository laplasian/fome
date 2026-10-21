"""Левая панель главного окна: все параметры модели, которые задаёт пользователь."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QSpinBox,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from calc.parameters import (
    DEFAULT_FILM_THICKNESS_NM,
    DEFAULT_WAVELENGTH_RANGE_NM,
    MAX_BOUND_MODES,
    BoundMode,
    FreeCarriers,
    Material,
)
from calc.plasma_frequency import bound_plasma_frequencies, free_plasma_frequency
from calc.units import make_wavelength_grid
from ui.scientific_input import ScientificInput


def spin_box(value, minimum, maximum, decimals=3, step=1.0, suffix=""):
    """QDoubleSpinBox с нужными пределами — чтобы не повторять 5 строк каждый раз."""
    box = QDoubleSpinBox()
    box.setRange(minimum, maximum)
    box.setDecimals(decimals)
    box.setSingleStep(step)
    box.setValue(value)
    if suffix:
        box.setSuffix(suffix)
    box.setKeyboardTracking(False)  # пересчёт после окончания ввода, а не на каждой цифре
    return box


class ParameterPanel(QWidget):
    """Собирает ввод в объект Material и сообщает об изменениях сигналом changed."""

    changed = Signal()

    # Столбцы таблицы мод связанных зарядов
    MODE_COLUMNS = ["Ni, см⁻³", "mi / mₑ", "λi, нм", "Γi, см⁻¹"]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(self._build_medium_group())
        layout.addWidget(self._build_free_group())
        layout.addWidget(self._build_bound_group())
        layout.addWidget(self._build_range_group())
        layout.addWidget(self._build_plasma_group())
        layout.addStretch()

        self._update_visible_modes()
        self._update_plasma_label()

    # ---------- построение групп ----------

    def _build_medium_group(self):
        group = QGroupBox("Среда")
        form = QFormLayout(group)
        self.eps_inf = spin_box(1.0, 0.001, 1000.0, decimals=4, step=0.1)
        self.thickness = spin_box(DEFAULT_FILM_THICKNESS_NM, 1.0, 1e7, decimals=1, step=100.0, suffix=" нм")
        form.addRow("ε∞", self.eps_inf)
        form.addRow("Толщина плёнки d", self.thickness)
        self._watch(self.eps_inf, self.thickness)
        return group

    def _build_free_group(self):
        group = QGroupBox("Свободные носители (Друде)")
        form = QFormLayout(group)
        self.n0 = ScientificInput(0.0, 0, max_exponent=23)
        self.m0 = spin_box(1.0, 0.001, 1000.0, decimals=3, step=0.1)
        self.gamma0 = spin_box(100.0, -100_000.0, 100_000.0, decimals=1, step=10.0)
        form.addRow("N0, см⁻³", self.n0)
        form.addRow("m0 / mₑ", self.m0)
        form.addRow("Γ0, см⁻¹", self.gamma0)
        self._watch(self.n0, self.m0, self.gamma0)
        return group

    def _build_bound_group(self):
        group = QGroupBox("Связанные заряды (Лоренц)")
        layout = QVBoxLayout(group)

        form = QFormLayout()
        self.mode_count = QSpinBox()
        self.mode_count.setRange(1, MAX_BOUND_MODES)
        self.mode_count.setValue(1)
        self.mode_count.valueChanged.connect(self._update_visible_modes)
        form.addRow("Число мод K", self.mode_count)
        layout.addLayout(form)

        # Создаём сразу все 10 строк и просто прячем лишние — так значения не теряются.
        self.mode_table = QTableWidget(MAX_BOUND_MODES, len(self.MODE_COLUMNS))
        self.mode_table.setHorizontalHeaderLabels(self.MODE_COLUMNS)
        self.mode_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.mode_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.mode_rows = []
        for row in range(MAX_BOUND_MODES):
            defaults = BoundMode()
            widgets = (
                ScientificInput(defaults.concentration_cm3, 0, max_exponent=24),
                spin_box(defaults.mass_in_me, 0.001, 1000.0, decimals=3, step=0.1),
                spin_box(defaults.wavelength_nm, 100.0, 10_000.0, decimals=1, step=10.0),
                spin_box(defaults.damping_cm1, -100_000.0, 100_000.0, decimals=1, step=100.0),
            )
            for column, widget in enumerate(widgets):
                self.mode_table.setCellWidget(row, column, widget)
            self._watch(*widgets)
            self.mode_rows.append(widgets)
        self.mode_table.resizeRowsToContents()
        layout.addWidget(self.mode_table)
        return group

    def _build_range_group(self):
        group = QGroupBox("Диапазон длин волн")
        form = QFormLayout(group)
        start, stop = DEFAULT_WAVELENGTH_RANGE_NM
        self.wl_start = spin_box(start, 1.0, 1e6, decimals=1, step=10.0, suffix=" нм")
        self.wl_stop = spin_box(stop, 1.0, 1e6, decimals=1, step=10.0, suffix=" нм")
        self.points = QSpinBox()
        self.points.setRange(100, 50_000)
        self.points.setValue(2000)
        self.points.setKeyboardTracking(False)
        form.addRow("от", self.wl_start)
        form.addRow("до", self.wl_stop)
        form.addRow("точек", self.points)
        self._watch(self.wl_start, self.wl_stop, self.points)
        return group

    def _build_plasma_group(self):
        group = QGroupBox("Плазменные частоты")
        layout = QVBoxLayout(group)
        self.plasma_label = QLabel()
        self.plasma_label.setStyleSheet("font-family: Consolas, monospace;")
        layout.addWidget(self.plasma_label)
        return group

    # ---------- реакция на изменения ----------

    def _watch(self, *widgets):
        for widget in widgets:
            widget.valueChanged.connect(self._on_changed)

    def _on_changed(self, *_):
        self._update_plasma_label()
        self.changed.emit()

    def _update_visible_modes(self):
        for row in range(MAX_BOUND_MODES):
            self.mode_table.setRowHidden(row, row >= self.mode_count.value())
        self._on_changed()

    def _update_plasma_label(self):
        try:
            material = self.material()
            lines = [f"Ω_p0 = {free_plasma_frequency(material):12.2f} см⁻¹"]
            for i, omega in enumerate(bound_plasma_frequencies(material), start=1):
                lines.append(f"Ω_p{i:<2}= {omega:12.2f} см⁻¹")
            self.plasma_label.setText("\n".join(lines))
        except ValueError as error:
            self.plasma_label.setText(str(error))

    # ---------- чтение значений ----------

    def material(self) -> Material:
        modes = []
        for concentration, mass, wavelength, damping in self.mode_rows[: self.mode_count.value()]:
            modes.append(BoundMode(
                concentration_cm3=concentration.value(),
                mass_in_me=mass.value(),
                wavelength_nm=wavelength.value(),
                damping_cm1=damping.value(),
            ))
        return Material(
            eps_inf=self.eps_inf.value(),
            free=FreeCarriers(
                concentration_cm3=self.n0.value(),
                mass_in_me=self.m0.value(),
                damping_cm1=self.gamma0.value(),
            ),
            bound_modes=modes,
        )

    def film_thickness_nm(self) -> float:
        return self.thickness.value()

    def set_model(self, material: Material, film_thickness_nm: float):
        """Записывает значения в поля (например, результат подгонки).

        Поля округляют до своего числа знаков после запятой.
        """
        self.eps_inf.setValue(material.eps_inf)
        self.thickness.setValue(film_thickness_nm)
        self.n0.setValue(material.free.concentration_cm3)
        self.m0.setValue(material.free.mass_in_me)
        self.gamma0.setValue(material.free.damping_cm1)
        self.mode_count.setValue(len(material.bound_modes))
        for mode, (concentration, mass, wavelength, damping) in zip(material.bound_modes, self.mode_rows):
            concentration.setValue(mode.concentration_cm3)
            mass.setValue(mode.mass_in_me)
            wavelength.setValue(mode.wavelength_nm)
            damping.setValue(mode.damping_cm1)

    def wavelength_grid(self):
        start, stop = self.wl_start.value(), self.wl_stop.value()
        if start >= stop:
            raise ValueError("Начало диапазона длин волн должно быть меньше конца")
        return make_wavelength_grid(start, stop, self.points.value())
