"""Окно «Падение под углом»: R и фазы для TE/TM от угла 0…90° при фиксированной λ."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from calc.angular_spectrum import ANGULAR_QUANTITIES, calculate_angular_spectrum
from calc.data_io import angular_file_name, save_angular_spectrum
from calc.units import ev_to_nm, nm_to_ev
from ui.parameter_panel import ParameterPanel
from ui.plot_grid import Curve, Panel, PlotGrid
from ui.style import COLORS

# 5 графиков из условия: ключ -> (заголовок, подпись оси Y)
ANGULAR_PLOTS = {
    "R_te": ("R TE (s-волна)", "R TE"),
    "R_tm": ("R TM (p-волна)", "R TM"),
    "phase_te_rad": ("Фаза отражения TE", "φ TE, рад"),
    "phase_tm_rad": ("Фаза отражения TM", "φ TM, рад"),
    "R_np": ("R неполяризованного света", "R NP"),
}

DEFAULT_WAVELENGTH_NM = 633.0


class AngularWindow(QMainWindow):
    def __init__(self, panel: ParameterPanel):
        super().__init__()
        self.setWindowTitle("Падение под углом")
        self.resize(1400, 800)
        self.panel = panel
        self.result = None

        self.plots = PlotGrid()
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(self._build_controls())
        layout.addWidget(self.plots, stretch=1)
        self.setCentralWidget(central)

        self.timer = QTimer(self, singleShot=True, interval=150)
        self.timer.timeout.connect(self.recalculate)
        panel.changed.connect(self.timer.start)

        self.recalculate()

    def _build_controls(self):
        layout = QVBoxLayout()

        top = QHBoxLayout()
        top.addWidget(QLabel("<b>Фиксированная</b>"))
        self.unit = QComboBox()
        self.unit.addItem("длина волны, нм", "nm")
        self.unit.addItem("энергия фотона, эВ", "ev")
        self.unit.currentIndexChanged.connect(self._on_unit_changed)
        top.addWidget(self.unit)

        self.value = QDoubleSpinBox()
        self.value.setDecimals(6)
        self.value.setRange(1.0, 1e6)
        self.value.setValue(DEFAULT_WAVELENGTH_NM)
        self.value.setKeyboardTracking(False)
        self.value.valueChanged.connect(self.recalculate)
        top.addWidget(self.value)

        self.info = QLabel()
        self.info.setStyleSheet("font-family: Consolas, monospace;")
        top.addWidget(self.info)
        top.addStretch()

        self.autoscale = QCheckBox("Автомасштаб")
        self.autoscale.setChecked(True)
        self.autoscale.toggled.connect(self._on_autoscale)
        top.addWidget(self.autoscale)
        save = QPushButton("💾 Сохранить отмеченные…")
        save.clicked.connect(self.save)
        top.addWidget(save)

        checks = QHBoxLayout()
        checks.addWidget(QLabel("<b>Графики:</b>"))
        self.checkboxes = {}
        for key in ANGULAR_PLOTS:
            box = QCheckBox(ANGULAR_QUANTITIES[key])
            box.setChecked(True)
            box.toggled.connect(self.redraw)
            self.checkboxes[key] = box
            checks.addWidget(box)
        checks.addStretch()

        layout.addLayout(top)
        layout.addLayout(checks)
        return layout

    # ---------- длина волны / энергия ----------

    def wavelength_nm(self):
        if self.unit.currentData() == "ev":
            return float(ev_to_nm(self.value.value()))
        return self.value.value()

    def _on_unit_changed(self):
        # Переводим текущее значение в новые единицы, чтобы λ не менялась
        old = self.value.value()
        new = float(nm_to_ev(old) if self.unit.currentData() == "ev" else ev_to_nm(old))
        self.value.blockSignals(True)
        if self.unit.currentData() == "ev":
            self.value.setRange(0.001, 1000.0)
        else:
            self.value.setRange(1.0, 1e6)
        self.value.setValue(new)
        self.value.blockSignals(False)
        self.recalculate()

    # ---------- расчёт и рисование ----------

    def recalculate(self):
        try:
            self.result = calculate_angular_spectrum(self.panel.material(), self.wavelength_nm())
        except (ValueError, ArithmeticError) as error:
            self.statusBar().showMessage(f"Ошибка: {error}")
            return
        r = self.result
        sign = "+" if r.N.imag >= 0 else "−"
        self.info.setText(
            f"  λ = {r.wavelength_nm:.2f} нм   E = {r.energy_ev:.4f} эВ   "
            f"N = {r.N.real:.4f} {sign} {abs(r.N.imag):.4f}i"
        )
        self.redraw()

    def redraw(self):
        if self.result is None:
            return
        panels = []
        for key, (title, y_label) in ANGULAR_PLOTS.items():
            if self.checkboxes[key].isChecked():
                curve = Curve(self.result.angle_deg, getattr(self.result, key), title, COLORS[key])
                panels.append(Panel(key, title, "Угол падения θ, °", y_label, [curve]))
        self.plots.draw(panels)

    def _on_autoscale(self, enabled):
        self.plots.autoscale = enabled
        self.redraw()

    def save(self):
        keys = [key for key, box in self.checkboxes.items() if box.isChecked()]
        if self.result is None or not keys:
            QMessageBox.information(self, "Сохранение", "Отметьте хотя бы один график.")
            return
        default = angular_file_name("angular", round(self.result.wavelength_nm, 2))
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить", default, "Текст (*.txt *.dat);;Все файлы (*)")
        if path:
            save_angular_spectrum(path, self.result, keys, self.panel.material())
            self.statusBar().showMessage(f"Сохранено: {path}", 5000)
