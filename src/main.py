import sys

from PyQt6.QtWidgets import QApplication

from src.ui.primary_window import Mario64All
from ui.git_utils import connect_signals

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = Mario64All()
    connect_signals(window)
    window.show()
    sys.exit(app.exec())
