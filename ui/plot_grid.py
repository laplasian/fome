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
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # Автомасштаб: True — оси подстраиваются под данные при каждом пересчёте,
        # False — сохраняются пределы, выставленные пользователем (лупой).
        self.autoscale = True
        self._axes_by_key = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def draw(self, panels):
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

        columns = 1 if len(panels) == 1 else 2 if len(panels) <= 4 else 3
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

        self.figure.tight_layout()
        self.canvas.draw_idle()
