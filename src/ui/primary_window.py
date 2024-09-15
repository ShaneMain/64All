import os

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow

from src.core.romfinder import N64RomValidator
from .build_manager import BuildManager
from .git_utils import CloningManager
from .repo_manager import RepoManager
from .ui_components import UISetup


class Mario64All(QMainWindow):
    def __init__(self):
        super().__init__()
        self.repo_manager = RepoManager(self)
        self.ui_setup = None  # Initialize as None
        self.build_manager = None  # Initialize as None
        self.cloning_manager = CloningManager()
        self.repo_url = ""
        self.rom_region, self.rom_dir = N64RomValidator().find_or_select_file()
        self.build_dependencies = []
        self.workspace = os.path.abspath("./.workspace")
        self.repo_options = {}
        self.setup_ui()

    def setup_ui(self):
        self.ui_setup = UISetup(self)  # Create UISetup instance
        self.build_manager = BuildManager(self)  # Create BuildManager instance
        self.ui_setup.setup()
        self.repo_manager.load_repos()
        self.repo_manager.populate_repo_urls()  # Call this after ui_setup is created

    def update_progress_bar(self, value):
        self.ui_setup.update_progress_bar(value)

    def update_output_text(self, text):
        self.ui_setup.update_output_text(text)

    def start_cloning(self, repo_url, clone_dir, branch):
        self.ui_setup.update_output_text(
            f"Initiating cloning: {repo_url} to {clone_dir} (branch: {branch})\n"
        )
        self.cloning_manager.progress_signal.connect(self.update_progress_bar)
        self.cloning_manager.text_signal.connect(self.update_output_text)
        self.cloning_manager.finished_signal.connect(self.cloning_finished)
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
