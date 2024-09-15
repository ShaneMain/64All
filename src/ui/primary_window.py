import os

from PyQt6.QtCore import QThread, QTimer
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout

from src.core.distrobox import DistroboxManager
from src.core.romfinder import N64RomValidator
from .build_manager import BuildManager
from .git_utils import load_repos, CloningManager
from .repo_manager import RepoManager
from .ui_components import UISetup


class Mario64All(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mario Sixty For All")
        # self.setFixedSize(1400, 600)

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
        self.cloning_manager = CloningManager()
        self.cloning_manager.progress_signal.connect(self.update_progress_bar)
        self.cloning_manager.text_signal.connect(self.update_output_text)
        self.cloning_manager.finished_signal.connect(self.cloning_finished)
        self.ui_setup = UISetup(self)
        self.repo_manager = RepoManager(self)
        self.build_manager = BuildManager(self)
        self.distrobox_manager = DistroboxManager(
            "ephemeral_runner", ui_setup=self.ui_setup
        )

        self.setup_ui()
        load_repos(self.repo_manager)

    def setup_ui(self):
        self.ui_setup.setup()

    def update_progress_bar(self, value):
        self.ui_setup.update_progress_bar(value)

    def update_output_text(self, text):
        self.ui_setup.update_output_text(text)

    def start_cloning(self, repo_url, clone_dir, branch):
        self.cloning_manager.start_cloning(repo_url, clone_dir, branch)

    def cloning_finished(self, success):
        if success:
            self.update_output_text("[32mCloning finished successfully![0m\n")
            self.update_output_text("[32mStarting build process...[0m\n")
            QTimer.singleShot(0, self.build_manager.start_building)
        else:
            self.update_output_text(
                "[31mCloning failed. Check the output for errors.[0m\n"
            )
            self.update_output_text("[33mYou may need to try cloning again.[0m\n")

    def update_build_options(self, repo_options):
        self.build_manager.update_build_options(repo_options)

    def update_advanced_options(self):
        self.ui_setup.update_advanced_options()

    def closeEvent(self, event):
        self.ui_setup.cleanup()
        super().closeEvent(event)
