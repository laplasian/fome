"""Поле ввода числа вида  мантисса × 10^степень  (степень редактируется отдельно)."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QLabel, QSpinBox, QWidget


class ScientificInput(QWidget):
    """Например, концентрация 5.9 × 10^22 см⁻³."""

    valueChanged = Signal(float)

    def __init__(self, mantissa=0.0, exponent=0, max_exponent=24, parent=None):
        super().__init__(parent)

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
        self.exponent.valueChanged.connect(self._emit)

    def value(self) -> float:
        return self.mantissa.value() * 10.0 ** self.exponent.value()

    def _emit(self):
        self.valueChanged.emit(self.value())
