"""Точка входа: запуск программы.

    python main.py
"""

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.style import apply_matplotlib_style


def main():
    app = QApplication(sys.argv)
    apply_matplotlib_style()
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
