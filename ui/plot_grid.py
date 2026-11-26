"""Область графиков: несколько осей matplotlib в сетке + панель масштабирования."""

import math
from dataclasses import dataclass, field

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import numpy as np
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ui.style import EXPERIMENT_LINE_WIDTH, LINE_WIDTH


HINT_TEXT = (
    'Двойной щелчок по графику — развернуть его на всё окно, '
    'ещё раз — вернуть все.'
)
NO_DATA_TEXT = 'Нет значений для построения'


def get_clicked_key(axes_by_key, clicked_ax):
    """Возвращает ключ графика, по осям которого щёлкнули."""
    for key, ax in axes_by_key.items():
        if ax is clicked_ax:
            return key
    return None


def get_focused_panels(panels, focused_key):
    """Оставляет только развёрнутый график, если он ещё отмечен."""
    if focused_key is None:
        return panels
    focused = []
    for panel in panels:
        if panel.key == focused_key:
            focused.append(panel)
    if focused:
        return focused
    return panels


def get_grid_size(count):
    """Возвращает (строки, столбцы) сетки для count графиков.

    Больше четырёх графиков ставим в две строки (7 графиков: 4 + 3):
    экран широкий, и так не остаётся пустого третьего ряда.
    """
    if count == 1:
        columns = 1
    elif count <= 4:
        columns = 2
    else:
        columns = math.ceil(count / 2)
    rows = math.ceil(count / columns)
    return rows, columns


def has_values(curves):
    """Проверяет, есть ли у графика хоть одна конечная точка."""
    for curve in curves:
        if np.isfinite(np.asarray(curve.y, dtype=float)).any():
            return True
    return False


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
        # Constrained layout не даёт длинным заголовкам сжимать оси.
        self.figure = Figure(layout='constrained')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # Автомасштаб: True — оси подстраиваются под данные при каждом пересчёте,
        # False — сохраняются пределы, выставленные пользователем (лупой).
        self.autoscale = True
        self._axes_by_key = {}

        # Двойной щелчок разворачивает график, повторный — сетка.
        self.focused_key = None
        self._last_panels = []
        self._last_notes = {}
        self.canvas.mpl_connect('button_press_event', self._on_click)
        self.hint = QLabel(HINT_TEXT)
        self.hint.setStyleSheet('color: gray;')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.hint)
        layout.addWidget(self.canvas, stretch=1)

    def _on_click(self, event):
        """Разворачивает график по двойному щелчку или даёт сетку."""
        if not event.dblclick or event.inaxes is None:
            return
        if self.focused_key is not None:
            self.focused_key = None
        else:
            self.focused_key = get_clicked_key(
                self._axes_by_key, event.inaxes
            )
        self.draw(self._last_panels, self._last_notes)

    def draw(self, panels, notes=None):
        """Рисует графики; notes — пояснения к пустым графикам."""
        notes = notes or {}
        self._last_panels = list(panels)
        self._last_notes = notes
        shown = get_focused_panels(panels, self.focused_key)
        if shown is panels:
            # Развёрнутого графика нет или его сняли галочкой: сетка.
            self.focused_key = None
        panels = shown
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

        rows, columns = get_grid_size(len(panels))

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
            if panel.key in notes or not has_values(panel.curves):
                # Пустые оси без делений: числа ±0.04 только путают.
                ax.set_xticks([])
                ax.set_yticks([])
                ax.text(
                    0.5, 0.5, notes.get(panel.key, NO_DATA_TEXT),
                    transform=ax.transAxes, ha='center', va='center',
                    fontsize=12, color='firebrick',
                )
            if panel.key in old_limits:
                ax.set_xlim(old_limits[panel.key][0])
                ax.set_ylim(old_limits[panel.key][1])
            self._axes_by_key[panel.key] = ax

        self.canvas.draw_idle()
