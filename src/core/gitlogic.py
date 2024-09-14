import os
import shutil

import git
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtWidgets import QComboBox


class CloneProgress(git.remote.RemoteProgress):
    def __init__(self, text_signal, progress_signal):
        super().__init__()
        self.text_signal = text_signal
        self.progress_signal = progress_signal
        self.total_progress = 0

    def update(self, op_code, cur_count, max_count=None, message=""):
        super().update(op_code, cur_count, max_count, message)

        # Ensure max_count is a positive number to avoid division by zero or negative values
        if max_count and max_count > 0:
            self.total_progress = int((cur_count / max_count) * 100)

        # Ensure progress is within 0-100% range
        self.total_progress = max(0, min(self.total_progress, 100))

        # Emit progress
        self.progress_signal.emit(self.total_progress)

        # Emit a progress message with color
        progress_message = (
            f"[32m Progress: {cur_count:,} out of {max_count:,} ({(cur_count / max_count) * 100:.2f}%) [0m"
            if max_count
            else f"[32m Progress: {cur_count:,}, max count unknown. [0m"
        )
        if message:
            progress_message += f"[36m Message: {message} [0m"

        self.text_signal.emit(progress_message)


class CloneWorker(QObject):
    progress_signal = pyqtSignal(int)
    text_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)  # Emit a bool indicating success or failure

    def __init__(self, repo_url, clone_dir, branch):
        super().__init__()
        self.repo_url = repo_url
        self.clone_dir = clone_dir
        self.branch = branch

    def run(self):
        try:
            os.makedirs(self.clone_dir, exist_ok=True)
            if not self.branch:
                raise ValueError("Branch is not specified. Please select a valid branch.")

            clone_progress = CloneProgress(self.text_signal, self.progress_signal)
            self.text_signal.emit(f"[34mCloning repository from {self.repo_url} (branch: {self.branch}) to {self.clone_dir}...[0m\n")

            git.Repo.clone_from(
                self.repo_url,
                self.clone_dir,
                progress=clone_progress,
                branch=self.branch,
                depth=1,  # Perform shallow clone
                single_branch=True,  # Clone only the specified branch
            )
            self.text_signal.emit("[32mRepository cloned successfully.[0m\n")
            self.finished_signal.emit(True)  # Indicate success

        except Exception as e:
            self.text_signal.emit(f"[31mAn error occurred while cloning the repository: {e}[0m\n")
            self.clean_up_directory()
            self.finished_signal.emit(False)  # Indicate failure

    def clean_up_directory(self):
        try:
            if os.path.exists(self.clone_dir):
                shutil.rmtree(self.clone_dir)
                self.text_signal.emit(f"[33mCleaned up directory '{self.clone_dir}'.[0m\n")
        except Exception as e:
            self.text_signal.emit(f"[31mError cleaning up directory '{self.clone_dir}': {e}[0m\n")


def update_branch_menu(repo_name, repos, branch_menu: QComboBox):
    try:
        print(f"Updating branch menu for repo: {repo_name}\n")
        repo_url = next(
            (repo["url"] for repo in repos if repo["name"] == repo_name), None
        )
        if not repo_url:
            print("No repository URL found for the selected repository.\n")
            return

        result = git.cmd.Git().ls_remote("--heads", repo_url)

        branch_lines = result.strip().split("\n")
        branches = [line.split()[1].replace("refs/heads/", "") for line in branch_lines]
        print(f"Branches found: {branches}\n")

        default_branch = (
            "master"
            if "master" in branches
            else "main"
            if "main" in branches
            else branches[0]
        )

        branch_menu.clear()
        branch_menu.addItems(branches)
        branch_menu.setCurrentText(default_branch)

    except git.exc.GitCommandError as e:
        print(f"Error in update_branch_menu: {e}\n")
