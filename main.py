"""
Application entry point for 2-Gate Ion Mobility Spectrometry (IMS) System Control.
"""

import sys
import os

# Ensure src package is on Python import path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.gui.styles import DARK_THEME_QSS


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_THEME_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
