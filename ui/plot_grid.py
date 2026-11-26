"""Область графиков: несколько осей matplotlib в сетке + панель масштабирования."""

import math
from dataclasses import dataclass, field

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ui.style import EXPERIMENT_LINE_WIDTH, LINE_WIDTH


@dataclass
class Curve:
    """Одна линия на графике."""

    x: object
    y: object
    label: str
    color: str
    experiment: bool = False  # эксперимент рисуется тонкой тёмной линией


@dataclass
class Panel:
    """Один график (одни оси) со своими линиями."""

    key: str
    title: str
    x_label: str
    y_label: str
    curves: list = field(default_factory=list)


class PlotGrid(QWidget):
    """Рисует список Panel в сетке, автоматически подбирая число столбцов."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(layout="constrained")  # оси занимают всё место, заголовки не сжимают их
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # Автомасштаб: True — оси подстраиваются под данные при каждом пересчёте,
        # False — сохраняются пределы, выставленные пользователем (лупой).
        self.autoscale = True
        self._axes_by_key = {}

        # Двойной щелчок по графику разворачивает его на всю область, повторный — возвращает сетку.
        self.focused_key = None
        self._last_panels = []
        self.canvas.mpl_connect("button_press_event", self._on_click)
        self.canvas.setToolTip("Двойной щелчок по графику — развернуть его на всё окно, ещё раз — вернуть все")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def _on_click(self, event):
        if not event.dblclick or event.inaxes is None:
            return
        clicked = next((key for key, ax in self._axes_by_key.items() if ax is event.inaxes), None)
        self.focused_key = None if self.focused_key is not None else clicked
        self.draw(self._last_panels)

    def draw(self, panels):
        self._last_panels = list(panels)
        if self.focused_key is not None:
            focused = [panel for panel in panels if panel.key == self.focused_key]
            if focused:
                panels = focused
            else:
                self.focused_key = None  # развёрнутый график сняли галочкой
        old_limits = {}
        if not self.autoscale:
            old_limits = {key: (ax.get_xlim(), ax.get_ylim()) for key, ax in self._axes_by_key.items()}

        self.figure.clear()
        self._axes_by_key = {}

        if not panels:
            self.figure.text(0.5, 0.5, "Отметьте галочками, какие графики строить",
                             ha="center", va="center", fontsize=14, color="gray")
            self.canvas.draw_idle()
            return

        # До 4 графиков — сетка 2×2, больше — две строки (7 графиков: 4 + 3), без пустых рядов
        columns = 1 if len(panels) == 1 else 2 if len(panels) <= 4 else math.ceil(len(panels) / 2)
        rows = math.ceil(len(panels) / columns)

        for index, panel in enumerate(panels, start=1):
            ax = self.figure.add_subplot(rows, columns, index)
            for curve in panel.curves:
                ax.plot(
                    curve.x, curve.y,
                    color=curve.color,
                    label=curve.label,
                    linewidth=EXPERIMENT_LINE_WIDTH if curve.experiment else LINE_WIDTH,
                )
            ax.set_title(panel.title)
            ax.set_xlabel(panel.x_label)
            ax.set_ylabel(panel.y_label)
            if len(panel.curves) > 1:
                ax.legend(loc="best")
            if panel.key in old_limits:
                ax.set_xlim(old_limits[panel.key][0])
                ax.set_ylim(old_limits[panel.key][1])
            self._axes_by_key[panel.key] = ax

        self.canvas.draw_idle()
