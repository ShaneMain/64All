import os
from typing import Any

from PyQt6.QtCore import QObject, QThread, pyqtSignal
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
        self.thread = QThread()
        self.worker = CloneWorker(repo_url, clone_dir, branch)
        self.worker.moveToThread(self.thread)

        self.worker.progress_signal.connect(self.progress_signal.emit)
        self.worker.text_signal.connect(self.text_signal.emit)
        self.worker.finished_signal.connect(self.on_finished)

        self.thread.started.connect(self.worker.run)
        
        self.thread.start()

    def on_finished(self, success: bool):
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
    repo_url = window.repo_url
    branch = window.ui_setup.branch_menu.currentText()
    clone_dir = os.path.abspath("./.workspace")

    window.start_cloning(repo_url, clone_dir, branch)

def load_repos(repo_manager: Any):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    yaml_file = os.path.join(current_directory, "../..", "config", "repos.yaml")
    yaml_file = os.path.abspath(yaml_file)
    try:
        with open(yaml_file, "r") as file:
            data = safe_load(file)
            repo_manager.REPOS = data.get("repos", [])
            repo_manager.populate_repo_urls()
            print(repo_manager.REPOS)
            
            # Populate fork menu with all repos
            window = repo_manager.parent
            window.ui_setup.fork_combobox.clear()   
            for repo in repo_manager.REPOS:
                window.ui_setup.fork_combobox.addItem(repo["name"])
            window.ui_setup.fork_combobox.setCurrentIndex(0)
            
            on_repo_selection(repo_manager.parent)
    except Exception as error:
        print(f"Error loading YAML file: {error}")


def on_repo_selection(window: Any):
    repo_name = window.ui_setup.repo_url_combobox.currentText()

    repo = next((repo for repo in window.repo_manager.REPOS if repo["name"] == repo_name), None)
    if repo:
        window.repo_url = repo.get("url")

        default_dir = os.path.abspath(f"./{repo_name}")
        window.ui_setup.clone_dir_entry.setText(default_dir)

        # Set dependencies
        window.build_dependencies = repo.get("dependencies", [])

        # Update branch menu and other options
        update_branch_menu(repo_name, window.repo_manager.REPOS, window.ui_setup.branch_menu)
        window.repo_options = repo.get("options", {})
        window.build_manager.update_build_options(window.repo_options)

        # Update fork options
        window.ui_setup.fork_combobox.setCurrentText(repo_name)

        # Update advanced options
        window.ui_setup.update_advanced_options()

        # Refresh the options layout
        window.ui_setup.refresh_options_layout()

    print(f"Selected repo: {repo_name}, Options: {window.repo_options}")


def on_fork_selection(window: Any):
    fork_name = window.ui_setup.fork_combobox.currentText()

    fork = next((repo for repo in window.repo_manager.REPOS if repo["name"] == fork_name), None)
    if fork:
        window.repo_url = fork.get("url")

        default_dir = os.path.abspath(f"./{fork_name}")
        window.ui_setup.clone_dir_entry.setText(default_dir)

        # Set dependencies
        window.build_dependencies = fork.get("dependencies", [])

        # Update branch menu and other options
        update_branch_menu(fork_name, window.repo_manager.REPOS, window.ui_setup.branch_menu)
        window.repo_options = fork.get("options", {})
        window.build_manager.update_build_options(window.repo_options)

        # Update advanced options
        window.ui_setup.update_advanced_options()

        # Refresh the options layout
        window.ui_setup.refresh_options_layout()

    print(f"Selected fork: {fork_name}, Options: {window.repo_options}")

