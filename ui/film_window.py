"""Окно «Плёнка и эксперимент»: T и R плёнки рядом с измеренными спектрами."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from calc.comparison import compare_with_experiment
from calc.data_io import load_experimental_spectrum, save_spectrum
from calc.spectrum import calculate_spectrum
from ui.fit_panel import FitPanel
from ui.parameter_panel import ParameterPanel
from ui.plot_grid import Curve, Panel, PlotGrid
from ui.style import COLORS

# Два графика окна: ключ величины в Spectrum -> (заголовок, подпись оси Y)
FILM_PLOTS = {
    "film_T_percent": ("Пропускание плёнки T", "T, %"),
    "film_R_percent": ("Отражение плёнки R", "R, %"),
}


class FilmWindow(QMainWindow):
    """Параметры берутся из панели главного окна, пересчёт — по её сигналу changed."""

    def __init__(self, panel: ParameterPanel):
        super().__init__()
        self.setWindowTitle("Плёнка и эксперимент")
        self.resize(1700, 850)
        self.panel = panel
        self.spectrum = None
        self.experiments = {key: None for key in FILM_PLOTS}  # key -> (λ, значения, имя файла)

        self.plots = PlotGrid()
        right = QWidget()
        layout = QVBoxLayout(right)
        layout.addLayout(self._build_controls())
        layout.addWidget(self.plots, stretch=1)

        # Слева — панель машинной подгонки, справа — графики
        self.fit_panel = FitPanel(panel, self.loaded_experiments)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.fit_panel)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([520, 1080])
        self.setCentralWidget(splitter)

        self.timer = QTimer(self, singleShot=True, interval=150)
        self.timer.timeout.connect(self.recalculate)
        panel.changed.connect(self.timer.start)

        self.recalculate()

    def _build_controls(self):
        grid = QGridLayout()

        hint = QLabel("Параметры среды и толщина плёнки меняются в <b>главном окне</b>. "
                      "Цель — минимальное RMS для T и R.")
        grid.addWidget(hint, 0, 0, 1, 6)

        self.file_labels = {}
        self.rms_labels = {}
        for row, (key, (title, _)) in enumerate(FILM_PLOTS.items(), start=1):
            button = QPushButton(f"📂 Загрузить эксперимент: {title.split()[-1]}…")
            button.clicked.connect(lambda _=False, k=key: self.load_experiment(k))
            self.file_labels[key] = QLabel("файл не загружен")
            self.rms_labels[key] = QLabel("")
            self.rms_labels[key].setStyleSheet("font-weight: bold;")
            grid.addWidget(button, row, 0)
            grid.addWidget(self.file_labels[key], row, 1)
            grid.addWidget(self.rms_labels[key], row, 2)

        save_nk = QPushButton("💾 Сохранить n и k…")
        save_nk.clicked.connect(lambda: self.save(["n", "k"], "n_k.txt"))
        save_tr = QPushButton("💾 Сохранить T и R…")
        save_tr.clicked.connect(lambda: self.save(list(FILM_PLOTS), "film_T_R.txt"))
        self.autoscale = QCheckBox("Автомасштаб")
        self.autoscale.setChecked(True)
        self.autoscale.toggled.connect(self._on_autoscale)

        grid.addWidget(save_nk, 1, 4)
        grid.addWidget(save_tr, 2, 4)
        grid.addWidget(self.autoscale, 1, 5)
        grid.setColumnStretch(3, 1)
        return grid

    # ---------- данные ----------

    def loaded_experiments(self):
        """Загруженные спектры в виде, нужном подгонке: {"T": (λ, %), "R": (λ, %)}."""
        names = {"film_T_percent": "T", "film_R_percent": "R"}
        return {
            names[key]: (experiment[0], experiment[1])
            for key, experiment in self.experiments.items()
            if experiment is not None
        }

    def load_experiment(self, key):
        path, _ = QFileDialog.getOpenFileName(
            self, "Экспериментальный спектр", "", "Текст (*.txt *.dat *.csv *.asc);;Все файлы (*)"
        )
        if not path:
            return
        try:
            wavelength, values = load_experimental_spectrum(path)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Ошибка чтения", str(error))
            return
        self.experiments[key] = (wavelength, values, Path(path).name)
        self.file_labels[key].setText(f"{Path(path).name}  ({len(wavelength)} точек)")
        self.redraw()

    def recalculate(self):
        try:
            self.spectrum = calculate_spectrum(
                self.panel.material(), self.panel.wavelength_grid(), self.panel.film_thickness_nm()
            )
        except (ValueError, ArithmeticError) as error:
            self.statusBar().showMessage(f"Ошибка: {error}")
            return
        self.statusBar().showMessage(f"Толщина плёнки d = {self.panel.film_thickness_nm():g} нм")
        self.redraw()

    def redraw(self):
        if self.spectrum is None:
            return
        panels = []
        for key, (title, y_label) in FILM_PLOTS.items():
            curves = [Curve(self.spectrum.wavelength_nm, getattr(self.spectrum, key), "расчёт", COLORS[key])]
            experiment = self.experiments[key]
            if experiment is not None:
                wavelength, values, name = experiment
                curves.append(Curve(wavelength, values, f"эксперимент: {name}", COLORS["experiment"], experiment=True))
                comparison = compare_with_experiment(
                    self.spectrum.wavelength_nm, getattr(self.spectrum, key), wavelength, values
                )
                self.rms_labels[key].setText(f"RMS = {comparison.rms:.3f} %")
            panels.append(Panel(key, title, "Длина волны λ, нм", y_label, curves))
        self.plots.draw(panels)

    def _on_autoscale(self, enabled):
        self.plots.autoscale = enabled
        self.redraw()

    def closeEvent(self, event):
        self.fit_panel.shutdown()
        super().closeEvent(event)

    def save(self, keys, default_name):
        if self.spectrum is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить", default_name, "Текст (*.txt *.dat);;Все файлы (*)")
        if path:
            save_spectrum(path, self.spectrum, keys, self.panel.material())
            self.statusBar().showMessage(f"Сохранено: {path}", 5000)
