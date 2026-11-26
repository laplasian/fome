"""Поле ввода числа вида  мантисса × 10^степень  (степень редактируется отдельно)."""

import math

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QLabel, QSpinBox, QWidget


class ScientificInput(QWidget):
    """Например, концентрация 5.9 × 10^22 см⁻³."""

    valueChanged = Signal(float)

    def __init__(self, mantissa=0.0, exponent=0, max_exponent=24, max_value=None, parent=None):
        super().__init__(parent)
        # Верхний предел самого числа (например, N0 ≤ 1e23): при степени max_exponent
        # мантисса ограничивается, чтобы нельзя было ввести 9.999·10^23.
        self.max_value = max_value

        self.mantissa = QDoubleSpinBox()
        self.mantissa.setRange(0.0, 9.999)
        self.mantissa.setDecimals(3)
        self.mantissa.setSingleStep(0.1)
        self.mantissa.setValue(mantissa)

        self.exponent = QSpinBox()
        self.exponent.setRange(0, max_exponent)
        self.exponent.setValue(exponent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.mantissa, stretch=2)
        layout.addWidget(QLabel("× 10^"))
        layout.addWidget(self.exponent, stretch=1)

        self.mantissa.valueChanged.connect(self._emit)
        self.exponent.valueChanged.connect(self._on_exponent_changed)
        self._apply_limit()

    def _apply_limit(self):
        """Ставит максимум мантиссы так, чтобы мантисса·10^степень ≤ max_value."""
        if self.max_value is None:
            return
        limit = min(9.999, self.max_value / 10.0 ** self.exponent.value())
        self.mantissa.setMaximum(limit)  # Qt сам уменьшит значение, если оно больше

    def _on_exponent_changed(self, *_):
        self.mantissa.blockSignals(True)
        self._apply_limit()
        self.mantissa.blockSignals(False)
        self._emit()

    def value(self) -> float:
        return self.mantissa.value() * 10.0 ** self.exponent.value()

    def setValue(self, value: float):
        """Раскладывает число на мантиссу и степень: 5.9e22 -> 5.9 и 22."""
        if value > 0:
            exponent = math.floor(math.log10(value))
            mantissa = round(value / 10.0**exponent, self.mantissa.decimals())
            if mantissa >= 10:  # округление 9.9996 -> 10.000
                mantissa, exponent = mantissa / 10, exponent + 1
        else:
            mantissa, exponent = 0.0, self.exponent.value()

        for box in (self.mantissa, self.exponent):
            box.blockSignals(True)
        self.exponent.setValue(exponent)
        self._apply_limit()
        self.mantissa.setValue(mantissa)
        for box in (self.mantissa, self.exponent):
            box.blockSignals(False)
        self._emit()

    def _emit(self):
        self.valueChanged.emit(self.value())
