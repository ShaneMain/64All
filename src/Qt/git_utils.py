import os

from PyQt6.QtCore import QThread
from yaml import safe_load

from src.Qt.primary_window import Mario64All
from src.logic.gitlogic import CloneWorker, update_branch_menu


def start_cloning(obj:Mario64All):
    clone_dir = obj.clone_dir_entry.text()
    branch = obj.branch_menu.currentText()

    obj.worker = CloneWorker(obj.repo_url, clone_dir, branch)
    obj.thread = QThread()
    obj.worker.moveToThread(obj.thread)

    obj.worker.progress_signal.connect(obj.update_progress_bar)
    obj.worker.text_signal.connect(obj.update_output_text)
    obj.worker.finished_signal.connect(obj.cloning_finished)

    obj.thread.started.connect(obj.worker.run)
    obj.worker.finished_signal.connect(obj.thread.quit)
    obj.worker.finished_signal.connect(obj.worker.deleteLater)
    obj.thread.finished.connect(obj.thread.deleteLater)

    print("Starting cloning process...")
    obj.thread.start()

def load_repos(obj:Mario64All):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    yaml_file = os.path.join(current_directory, "../..", "config", "repos.yaml")
    yaml_file = os.path.abspath(yaml_file)
    try:
        with open(yaml_file, "r") as file:
            data = safe_load(file)
            obj.REPOS = data.get("repos", [])
            obj.populate_repo_urls()
    except Exception as error:
        print(f"Error loading YAML file: {error}")

def on_repo_selection(obj:Mario64All):
    repo_name = obj.repo_url_combobox.currentText()

    obj.repo_url = next(
        (repo["url"] for repo in obj.REPOS if repo["name"] == repo_name), None
    )

    default_dir = os.path.abspath(f"./{repo_name}")
    obj.clone_dir_entry.setText(default_dir)
    repo = next((repo for repo in obj.REPOS if repo["name"] == repo_name), None)
    if repo:
        update_branch_menu(repo_name, obj.REPOS, obj.branch_menu)
        obj.repo_options = repo.get("options", {})
        obj.update_build_options(obj.repo_options)