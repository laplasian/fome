"""Панель машинной подгонки в окне плёнки: таблица параметров, метод, кнопки Старт/Стоп."""

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from calc.fitting import FitResult, fit_parameters, list_parameters
from ui.parameter_panel import ParameterPanel

METHODS = {
    "local": "Локальный (быстро, от текущих значений)",
    "global": "Глобальный (медленно, по всей области)",
}

# Столбцы таблицы
FIT, NAME, CURRENT, LOWER, UPPER = range(5)
COLUMNS = ["Подгонять", "Параметр", "Текущее", "от", "до"]


def number_text(value):
    return f"{value:.6g}"


def parse_number(text):
    """'1e21', '1,5' и '1.5' -> float."""
    return float(text.strip().replace(",", "."))


class FitWorker(QObject):
    """Подгонка в отдельном потоке, чтобы окно не «зависало»."""

    progress = Signal(int, float)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, material, thickness, parameters, experiments, method):
        super().__init__()
        self.arguments = (material, thickness, parameters, experiments, method)
        self.stop_requested = False

    @Slot()
    def run(self):
        material, thickness, parameters, experiments, method = self.arguments
        try:
            result = fit_parameters(
                material, thickness, parameters, experiments, method,
                on_progress=self.progress.emit,
                should_stop=lambda: self.stop_requested,
            )
        except Exception as error:  # покажем любую ошибку пользователю, а не уроним программу
            self.failed.emit(str(error))
            return
        self.finished.emit(result)


class FitPanel(QGroupBox):
    """experiments_provider() должна возвращать {"T": (λ, %), "R": (λ, %)} загруженных спектров."""

    def __init__(self, panel: ParameterPanel, experiments_provider, parent=None):
        super().__init__("Машинная подгонка параметров", parent)
        self.panel = panel
        self.experiments_provider = experiments_provider
        self.rows = {}           # ключ параметра -> (галочка, поле «от», поле «до»)
        self.thread = None
        self.worker = None
        self.undo_model = None   # (material, d) до последней подгонки

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Отметьте параметры для подгонки и задайте физически разумные пределы.\n"
                                "Неотмеченные параметры закреплены."))

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for column in (FIT, NAME):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, stretch=1)

        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Метод:"))
        self.method = QComboBox()
        for key, label in METHODS.items():
            self.method.addItem(label, key)
        method_row.addWidget(self.method, stretch=1)
        layout.addLayout(method_row)

        buttons = QHBoxLayout()
        self.start_button = QPushButton("▶ Подогнать")
        self.start_button.clicked.connect(self.start)
        self.stop_button = QPushButton("■ Стоп")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)
        self.undo_button = QPushButton("↶ Вернуть как было")
        self.undo_button.setEnabled(False)
        self.undo_button.clicked.connect(self.undo)
        for button in (self.start_button, self.stop_button, self.undo_button):
            buttons.addWidget(button)
        layout.addLayout(buttons)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.status)

        panel.changed.connect(self.sync_with_panel)
        self.sync_with_panel()

    # ---------- таблица ----------

    def sync_with_panel(self):
        """Обновляет столбец «Текущее»; если изменилось число мод — перестраивает таблицу."""
        parameters = list_parameters(self.panel.material(), self.panel.film_thickness_nm())
        if [p.key for p in parameters] != list(self.rows):
            self._rebuild(parameters)
        for row, p in enumerate(parameters):
            self.table.item(row, CURRENT).setText(number_text(p.value))

    def _rebuild(self, parameters):
        """Строит строки заново, сохраняя галочки и пределы уже существующих параметров."""
        old = {key: (check.isChecked(), lower.text(), upper.text()) for key, (check, lower, upper) in self.rows.items()}
        self.rows = {}
        self.table.setRowCount(len(parameters))
        for row, p in enumerate(parameters):
            checked, lower_text, upper_text = old.get(p.key, (False, number_text(p.lower), number_text(p.upper)))

            check = QCheckBox()
            check.setChecked(checked)
            holder = QWidget()                      # чтобы галочка стояла по центру ячейки
            holder_layout = QHBoxLayout(holder)
            holder_layout.setContentsMargins(0, 0, 0, 0)
            holder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            holder_layout.addWidget(check)
            self.table.setCellWidget(row, FIT, holder)

            for column, text in ((NAME, p.label), (CURRENT, number_text(p.value))):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # только для чтения
                self.table.setItem(row, column, item)

            lower, upper = QLineEdit(lower_text), QLineEdit(upper_text)
            self.table.setCellWidget(row, LOWER, lower)
            self.table.setCellWidget(row, UPPER, upper)
            self.rows[p.key] = (check, lower, upper)
        self.table.resizeRowsToContents()

    def read_parameters(self):
        """Параметры из таблицы: текущие значения из панели, галочки и пределы — из таблицы."""
        parameters = list_parameters(self.panel.material(), self.panel.film_thickness_nm())
        for p in parameters:
            check, lower, upper = self.rows[p.key]
            p.fit = check.isChecked()
            if p.fit:
                try:
                    p.lower, p.upper = parse_number(lower.text()), parse_number(upper.text())
                except ValueError:
                    raise ValueError(f"{p.label}: пределы должны быть числами (например 1e21 или 2.5)")
        return parameters

    # ---------- запуск и остановка ----------

    def start(self):
        try:
            parameters = self.read_parameters()
        except ValueError as error:
            self.status.setText(f"⚠ {error}")
            return

        material, thickness = self.panel.material(), self.panel.film_thickness_nm()
        self.undo_model = (material, thickness)
        self.worker = FitWorker(material, thickness, parameters, self.experiments_provider(), self.method.currentData())
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)

        self._set_running(True)
        self.status.setText("Подгонка запущена…")
        self.thread.start()

    def stop(self):
        if self.worker is not None:
            self.worker.stop_requested = True  # флаг читается внутри fit_parameters
            self.status.setText("Останавливаю…")

    def undo(self):
        if self.undo_model is not None:
            self.panel.set_model(*self.undo_model)
            self.status.setText("Параметры возвращены к состоянию до подгонки.")
            self.undo_button.setEnabled(False)

    def _set_running(self, running):
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.table.setEnabled(not running)
        self.method.setEnabled(not running)
        if running:
            self.undo_button.setEnabled(False)

    def _finish_thread(self):
        self.thread.quit()
        self.thread.wait()
        self.thread = self.worker = None
        self._set_running(False)

    def _on_progress(self, evaluations, best):
        self.status.setText(f"Вычислений спектра: {evaluations}.  Лучшее √(RMS_T² + RMS_R²) = {best:.4f} %")

    def _on_failed(self, message):
        self._finish_thread()
        self.status.setText(f"⚠ {message}")

    def _on_finished(self, result: FitResult):
        self._finish_thread()
        self.panel.set_model(result.material, result.film_thickness_nm)
        self.undo_button.setEnabled(True)

        lines = ["Остановлено — применён лучший найденный результат." if result.stopped
                 else f"Готово за {result.evaluations} вычислений спектра."]
        for name in result.rms:
            lines.append(f"RMS {name}: {result.rms_before[name]:.4f} % → {result.rms[name]:.4f} %")
        labels = {p.key: p.label for p in list_parameters(result.material, result.film_thickness_nm)}
        lines.append("Найдено: " + ", ".join(f"{labels[key]} = {number_text(value)}" for key, value in result.values.items()))
        self.status.setText("\n".join(lines))

    def shutdown(self):
        """Вызывается при закрытии окна: аккуратно останавливает поток."""
        if self.thread is not None:
            self.stop()
            self.thread.quit()
            self.thread.wait()
