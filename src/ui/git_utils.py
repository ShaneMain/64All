import os

from PyQt6.QtCore import QThread
from yaml import safe_load

from src.core.gitlogic import update_branch_menu, CloneWorker
from ui.primary_window import Mario64All


def start_cloning(obj):
    branch = obj.branch_menu.currentText()
    repo_url = obj.repo_url

    # Create worker and thread locally
    worker = CloneWorker(repo_url, os.path.abspath("./.workspace"), branch)
    thread = QThread()
    worker.moveToThread(thread)

    worker.progress_signal.connect(obj.update_progress_bar)
    worker.text_signal.connect(obj.update_output_text)
    worker.finished_signal.connect(lambda success: obj.cloning_finished(success))

    thread.started.connect(worker.run)
    worker.finished_signal.connect(thread.quit)
    worker.finished_signal.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    print("Starting cloning process...")
    thread.start()

    # Reference to keep thread and worker alive
    obj.worker_thread = thread
    obj.worker = worker


def load_repos(obj):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    yaml_file = os.path.join(current_directory, "../..", "config", "repos.yaml")
    yaml_file = os.path.abspath(yaml_file)
    try:
        with open(yaml_file, "r") as file:
            data = safe_load(file)
            obj.REPOS = data.get("repos", [])
            obj.populate_repo_urls()
            print(obj.REPOS)
            on_repo_selection(obj)
    except Exception as error:
        print(f"Error loading YAML file: {error}")


def on_repo_selection(obj):
    repo_name = obj.repo_url_combobox.currentText()

    repo = next((repo for repo in obj.REPOS if repo["name"] == repo_name), None)
    if repo:
        obj.repo_url = repo.get("url")

        default_dir = os.path.abspath(f"./{repo_name}")
        obj.clone_dir_entry.setText(default_dir)

        # Set dependencies
        obj.build_dependencies = repo.get("dependencies", [])

        # Update branch menu and other options
        update_branch_menu(repo_name, obj.REPOS, obj.branch_menu)
        obj.repo_options = repo.get("options", {})
        obj.update_build_options(obj.repo_options)

        # Update advanced options
        obj.update_advanced_options()


def connect_signals(instance: Mario64All):
    obj = instance  # Get singleton instance
    print(obj)
    load_repos(obj)
    obj.repo_url_combobox.currentIndexChanged.connect(lambda _: on_repo_selection(obj))
    obj.clone_button.clicked.connect(lambda _: start_cloning(obj))
