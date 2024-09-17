import sys

from PyQt6.QtWidgets import QApplication

from core.distrobox import cleanup_ubuntu_image
from ui.primary_window import Sixty4All
from ui.signal_connections import connect_signals

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(cleanup_ubuntu_image)
    window = Sixty4All()
    connect_signals(window)
    window.show()
    sys.exit(app.exec())
