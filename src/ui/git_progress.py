from PyQt6.QtCore import QObject, pyqtSignal

class GitProgress(QObject):
    update_progress = pyqtSignal(str)