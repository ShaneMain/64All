import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import QThread
from .ui_components import UISetup
from .repo_manager import RepoManager
from .build_manager import BuildManager
from src.core.romfinder import N64RomValidator
from .git_utils import load_repos

class Mario64All(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mario Sixty For All")
        self.setFixedSize(700, 600)

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setSpacing(5)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.setCentralWidget(self.main_widget)

        self.workspace = os.path.abspath("./.workspace")
        self.rom_region, self.rom_dir = N64RomValidator().find_or_select_file()
        self.worker_thread = QThread()
        self.build_dependencies = []
        self.repo_url = ""
        self.repo_options = {}

        self.ui_setup = UISetup(self)
        self.repo_manager = RepoManager(self)
        self.build_manager = BuildManager(self) 

        self.setup_ui()
        load_repos(self.repo_manager)

    def setup_ui(self):
        self.ui_setup.setup()

    def update_progress_bar(self, value):
        self.ui_setup.progress_bar.setValue(value)

    def update_output_text(self, text):
        self.ui_setup.output_text.append(text)

    def cloning_finished(self, success):
        if success:
            self.ui_setup.update_output_text("Cloning finished successfully!")
            self.build_manager.start_building()
        else:
            self.ui_setup.update_output_text("Cloning failed. Check the output for errors.")

    def update_build_options(self, repo_options):
        self.build_manager.update_build_options(repo_options)

    def update_advanced_options(self):
        self.ui_setup.update_advanced_options()
    def adjust_window_size(self):
        if self.ui_setup.advanced_checkbox.isChecked():
            self.setFixedSize(700, 700)  # Adjust this size as needed
        else:
            self.setFixedSize(700, 600)  # Original size

