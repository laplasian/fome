"""Главное окно: параметры слева, 7 графиков от длины волны справа."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from calc.data_io import save_spectrum
from calc.presets import (
    get_preset_material,
    get_preset_names,
    get_preset_thickness,
)
from calc.spectrum import SPECTRUM_QUANTITIES, calculate_spectrum
from ui.angular_window import AngularWindow
from ui.film_window import FilmWindow
from ui.help_texts import APP_NAME, INSTRUCTION_HTML, about_html
from ui.parameter_panel import ParameterPanel
from ui.plot_grid import Curve, Panel, PlotGrid
from ui.style import COLORS, NORMALIZATION_MODES, normalize

# 7 графиков из условия: ключ -> (заголовок, подпись оси Y)
MAIN_PLOTS = {
    "eps_real": ("ε' — реальная часть ε", "ε'"),
    "eps_imag": ("ε'' — мнимая часть ε", "ε''"),
    "n": ("n — реальная часть N", "n"),
    "k": ("k — мнимая часть N", "k"),
    "R12": ("R₁₂ — отражение по интенсивности", "R₁₂"),
    "phase12_rad": ("φ₁₂ — фаза отражения", "φ₁₂, рад"),
    "alpha_cm1": ("α — коэффициент поглощения", "α, см⁻¹"),
}

X_AXES = {
    "nm": ("Длина волны λ, нм", "wavelength_nm"),
    "ev": ("Энергия фотона E, эВ", "energy_ev"),
}



def show_window(window):
    """Показывает окно и выводит его наверх.

    Свёрнутое или ещё не показанное окно разворачивается на весь экран:
    по заданию графики должны быть во весь экран, а фиксированный размер
    не помещается на экран ноутбука 1366×768.
    """
    if window.isVisible() and not window.isMinimized():
        window.raise_()
        window.activateWindow()
        return
    window.showMaximized()
    window.raise_()
    window.activateWindow()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.spectrum = None
        self.film_window = None
        self.angular_window = None

        self.panel = ParameterPanel()
        self.plots = PlotGrid()

        scroll = QScrollArea()
        scroll.setWidget(self.panel)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(430)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addLayout(self._build_controls())
        right_layout.addWidget(self.plots, stretch=1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(scroll)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self._build_menu()

        # Пересчёт с небольшой задержкой, чтобы не считать на каждый щелчок стрелки
        self.timer = QTimer(self, singleShot=True, interval=120)
        self.timer.timeout.connect(self.recalculate)
        self.panel.changed.connect(self.timer.start)

        self.recalculate()

    # ---------- построение интерфейса ----------

    def _build_controls(self):
        layout = QVBoxLayout()

        checks_row = QHBoxLayout()
        checks_row.addWidget(QLabel("<b>Графики:</b>"))
        self.checkboxes = {}
        for key in MAIN_PLOTS:
            box = QCheckBox(SPECTRUM_QUANTITIES[key].split(" — ")[0])
            box.setToolTip(SPECTRUM_QUANTITIES[key])
            box.setChecked(True)
            box.toggled.connect(self.redraw)
            self.checkboxes[key] = box
            checks_row.addWidget(box)
        checks_row.addStretch()

        options_row = QHBoxLayout()
        options_row.addWidget(QLabel("Ось X:"))
        self.x_axis = QComboBox()
        for key, (label, _) in X_AXES.items():
            self.x_axis.addItem(label, key)
        self.x_axis.currentIndexChanged.connect(self.redraw)
        options_row.addWidget(self.x_axis)

        options_row.addWidget(QLabel("Нормировка:"))
        self.normalization = QComboBox()
        for key, label in NORMALIZATION_MODES.items():
            self.normalization.addItem(label, key)
        self.normalization.currentIndexChanged.connect(self.redraw)
        options_row.addWidget(self.normalization)

        self.autoscale = QCheckBox("Автомасштаб")
        self.autoscale.setChecked(True)
        self.autoscale.toggled.connect(self._on_autoscale)
        options_row.addWidget(self.autoscale)
        options_row.addStretch()

        save_button = QPushButton("💾 Сохранить отмеченные…")
        save_button.clicked.connect(self.save)
        film_button = QPushButton("Плёнка и эксперимент…")
        film_button.clicked.connect(self.open_film_window)
        angular_button = QPushButton("Падение под углом…")
        angular_button.clicked.connect(self.open_angular_window)
        for button in (save_button, film_button, angular_button):
            options_row.addWidget(button)

        layout.addLayout(checks_row)
        layout.addLayout(options_row)
        return layout

    def _build_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("Файл")
        self._add_action(file_menu, "Сохранить отмеченные графики…", self.save, "Ctrl+S")
        file_menu.addSeparator()
        self._add_action(file_menu, "Выход", self.close, "Ctrl+Q")

        examples_menu = menu.addMenu('Примеры')
        for name in get_preset_names():
            self._add_action(
                examples_menu, name,
                lambda _=False, n=name: self.load_preset(n),
            )

        windows_menu = menu.addMenu("Окна")
        self._add_action(windows_menu, "Плёнка и эксперимент", self.open_film_window)
        self._add_action(windows_menu, "Падение под углом", self.open_angular_window)

        help_menu = menu.addMenu("Справка")
        self._add_action(help_menu, "Инструкция", self.show_instruction, "F1")
        self._add_action(help_menu, "О программе", self.show_about)

    def _add_action(self, menu, text, slot, shortcut=None):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        menu.addAction(action)

    # ---------- расчёт и рисование ----------

    def recalculate(self):
        try:
            self.spectrum = calculate_spectrum(
                self.panel.material(),
                self.panel.wavelength_grid(),
                self.panel.film_thickness_nm(),
            )
            self.statusBar().showMessage("Рассчитано", 2000)
        except (ValueError, ArithmeticError) as error:
            self.statusBar().showMessage(f"Ошибка: {error}")
            return
        self.redraw()

    def redraw(self):
        if self.spectrum is None:
            return
        x_label, x_field = X_AXES[self.x_axis.currentData()]
        x = getattr(self.spectrum, x_field)
        mode = self.normalization.currentData()

        panels = []
        for key, (title, y_label) in MAIN_PLOTS.items():
            if not self.checkboxes[key].isChecked():
                continue
            y = normalize(getattr(self.spectrum, key), mode)
            if mode != "none":
                y_label += " (норм.)"
            panels.append(Panel(key, title, x_label, y_label, [Curve(x, y, title, COLORS[key])]))
        self.plots.draw(panels)

    def _on_autoscale(self, enabled):
        self.plots.autoscale = enabled
        self.redraw()

    # ---------- сохранение и окна ----------

    def selected_keys(self):
        return [key for key, box in self.checkboxes.items() if box.isChecked()]

    def save(self):
        keys = self.selected_keys()
        if self.spectrum is None or not keys:
            QMessageBox.information(self, "Сохранение", "Отметьте хотя бы один график.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить графики", "spectrum.txt", "Текст (*.txt *.dat);;Все файлы (*)"
        )
        if path:
            save_spectrum(path, self.spectrum, keys, self.panel.material(), x_axis=self.x_axis.currentData())
            self.statusBar().showMessage(f"Сохранено: {path}", 5000)

    def load_preset(self, name):
        """Подставляет в панель параметры примера из меню «Примеры»."""
        self.panel.set_model(
            get_preset_material(name), get_preset_thickness(name)
        )
        self.statusBar().showMessage(f'Пример: {name}', 5000)

    def open_film_window(self):
        """Открывает окно плёнки, впервые — на весь экран."""
        if self.film_window is None:
            self.film_window = FilmWindow(self.panel)
        show_window(self.film_window)

    def open_angular_window(self):
        """Открывает окно падения под углом, впервые — на весь экран."""
        if self.angular_window is None:
            self.angular_window = AngularWindow(self.panel)
        show_window(self.angular_window)

    def show_instruction(self):
        QMessageBox.information(self, "Инструкция", INSTRUCTION_HTML)

    def show_about(self):
        QMessageBox.about(self, "О программе", about_html())

    def closeEvent(self, event):
        for window in (self.film_window, self.angular_window):
            if window is not None:
                window.close()
        super().closeEvent(event)
