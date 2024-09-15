import os
import sys
from typing import Any

from PyQt6.QtCore import QObject, QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from yaml import safe_load

from src.core.gitlogic import update_branch_menu, CloneWorker


class CloningManager(QObject):
    progress_signal = pyqtSignal(int)
    text_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None

    def start_cloning(self, repo_url: str, clone_dir: str, branch: str):
        self.text_signal.emit(f"Setting up cloning process for {repo_url}\n")
        self.thread = QThread()
        self.worker = CloneWorker(repo_url, clone_dir, branch)
        self.worker.moveToThread(self.thread)

        self.worker.progress_signal.connect(self.progress_signal.emit)
        self.worker.text_signal.connect(self.text_signal.emit)
        self.worker.finished_signal.connect(self.on_finished)

        self.thread.started.connect(self.worker.run)

        self.text_signal.emit("Starting cloning thread...\n")
        self.thread.start()

    def on_finished(self, success: bool):
        self.text_signal.emit("Cloning process finished.\n")
        self.finished_signal.emit(success)
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()
        self.worker.deleteLater()
        self.thread = None
        self.worker = None

    def cleanup(self):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
            self.thread.deleteLater()
        if self.worker:
            self.worker.deleteLater()
        self.thread = None
        self.worker = None


def start_cloning(window: Any):
    window.ui_setup.update_output_text("Starting cloning process...\n")
    repo_name = window.ui_setup.repo_url_combobox.currentText()
    repo = next((r for r in window.repo_manager.REPOS if r["name"] == repo_name), None)
    if repo:
        repo_url = repo.get("url")
        branch = window.ui_setup.branch_menu.currentText()
        clone_dir = os.path.abspath("./.workspace")
        window.start_cloning(repo_url, clone_dir, branch)
    else:
        window.ui_setup.update_output_text("Error: Selected repository not found.\n")


def load_repos(repo_manager: Any):
    # Try to find the config directory
    config_dirs = [
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../..", "config", "repos"
        ),
        os.path.join(sys._MEIPASS, "config", "repos")
        if hasattr(sys, "_MEIPASS")
        else None,
        os.path.join(os.getcwd(), "config", "repos"),
    ]

    repos_dir = next((d for d in config_dirs if d and os.path.exists(d)), None)

    if not repos_dir:
        print("Error: Could not find the config/repos directory")
        return

    repo_manager.REPOS = []

    try:
        for filename in os.listdir(repos_dir):
            if filename.endswith(".yaml"):
                file_path = os.path.join(repos_dir, filename)
                with open(file_path, "r") as file:
                    data = safe_load(file)
                    if isinstance(data, list):
                        repo_manager.REPOS.extend(data)
                    elif isinstance(data, dict):
                        repo_manager.REPOS.append(data)

        repo_manager.populate_repo_urls()
        print(f"Total repos loaded: {len(repo_manager.REPOS)}")

        # Populate fork menu with all repos
        window = repo_manager.parent
        window.ui_setup.branch_combobox.clear()
        for repo in repo_manager.REPOS:
            window.ui_setup.branch_combobox.addItem(repo["name"])
        window.ui_setup.branch_combobox.setCurrentIndex(0)

    except Exception as error:
        print(f"Error loading repo configurations: {error}")


def populate_repo_urls(self):
    self.parent.ui_setup.repo_url_combobox.clear()
    self.parent.ui_setup.branch_combobox.clear()
    for repo in self.REPOS:
        self.parent.ui_setup.repo_url_combobox.addItem(repo["name"])
        self.parent.ui_setup.branch_combobox.addItem(repo["name"])

    # Set the current index to 0 for both comboboxes
    self.parent.ui_setup.repo_url_combobox.setCurrentIndex(0)
    self.parent.ui_setup.branch_combobox.setCurrentIndex(0)

    # Trigger the repo selection handler
    self.parent.ui_setup.on_repo_selection()


def connect_signals(self):
    self.advanced_checkbox.stateChanged.connect(self.update_advanced_options)
    self.browse_button.clicked.connect(self.parent.repo_manager.browse_directory)
    self.repo_url_combobox.currentIndexChanged.connect(self.on_repo_selection)


def on_fork_selection(window: Any):
    fork_name = window.ui_setup.branch_combobox.currentText()

    fork = next(
        (repo for repo in window.repo_manager.REPOS if repo["name"] == fork_name), None
    )
    if fork:
        window.repo_url = fork.get("url")

        default_dir = os.path.abspath(f"./{fork_name}")
        window.ui_setup.clone_dir_entry.setText(default_dir)

        # Set dependencies
        window.build_dependencies = fork.get("dependencies", [])

        # Update branch menu and other options
        update_branch_menu(
            fork_name, window.repo_manager.REPOS, window.ui_setup.branch_menu
        )
        window.repo_options = fork.get("options", {})
        window.build_manager.update_build_options(window.repo_options)

        # Update advanced options
        window.ui_setup.update_advanced_options()

        # Refresh the options layout
        window.ui_setup.refresh_options_layout()

    # Update fork info
    if "info" in fork:
        info = fork["info"]
        try:
            image_path = os.path.join("config", "images", info.get("image", ""))
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale the pixmap to fit within the frame while maintaining aspect ratio
                frame_size = window.ui_setup.image_frame.size()
                scaled_pixmap = pixmap.scaled(
                    frame_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                window.ui_setup.repo_image.setPixmap(scaled_pixmap)
            else:
                window.ui_setup.repo_image.clear()

            trailer_link = info.get("trailer", "")
            window.ui_setup.repo_trailer.setText(
                f'<a href="{trailer_link}">Watch Trailer</a>'
            )
            window.ui_setup.repo_trailer.setOpenExternalLinks(True)

            description = info.get("description", "")
            window.ui_setup.repo_description.setText(description)
        except Exception as e:
            print(f"Error updating fork info: {e}")
    else:
        try:
            window.ui_setup.repo_image.clear()
            window.ui_setup.repo_trailer.clear()
            window.ui_setup.repo_description.clear()
        except Exception as e:
            print(f"Error clearing fork info: {e}")

    print(f"Selected fork: {fork_name}, Options: {window.repo_options}")
