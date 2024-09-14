import os
from PyQt6.QtCore import QThread
from yaml import safe_load
from src.core.gitlogic import update_branch_menu, CloneWorker
from typing import Any

def start_cloning(window: Any):
    branch = window.ui_setup.branch_menu.currentText()
    repo_url = window.repo_url

    # Create worker and thread locally
    worker = CloneWorker(repo_url, os.path.abspath("./.workspace"), branch)
    thread = QThread()
    worker.moveToThread(thread)

    worker.progress_signal.connect(window.update_progress_bar)
    worker.text_signal.connect(window.update_output_text)
    worker.finished_signal.connect(lambda success: window.cloning_finished(success))

    thread.started.connect(worker.run)
    worker.finished_signal.connect(thread.quit)
    worker.finished_signal.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    print("Starting cloning process...")
    thread.start()

    # Reference to keep thread and worker alive
    window.worker_thread = thread
    window.worker = worker


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

    print(f"Selected fork: {fork_name}, Options: {window.repo_options}")

