import sys

from PyQt6.QtWidgets import QApplication

from ui.primary_window import Mario64All
from ui.signal_connections import connect_signals

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = Mario64All()
    connect_signals(window)
    window.show()
    sys.exit(app.exec())