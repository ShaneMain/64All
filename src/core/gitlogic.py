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
    finished_signal = pyqtSignal(bool)

    def __init__(self, repo_url, clone_dir, branch):
        super().__init__()
        self.repo_url = repo_url
        self.clone_dir = clone_dir
        self.branch = branch

    def run(self):
        try:
            self.text_signal.emit(f"Cloning {self.repo_url} into {self.clone_dir}\n")
            
            # Check if the directory already exists
            if os.path.exists(self.clone_dir):
                self.text_signal.emit(f"Directory {self.clone_dir} already exists. Removing it...\n")
                shutil.rmtree(self.clone_dir)
            
            progress = CloneProgress(self.text_signal, self.progress_signal)
            
            # Use single-branch cloning
            git.Repo.clone_from(
                self.repo_url,
                self.clone_dir,
                branch=self.branch,
                progress=progress,
                single_branch=True,
                depth=1
            )
            
            self.text_signal.emit("Cloning completed successfully.\n")
            self.finished_signal.emit(True)
        except git.exc.GitCommandError as e:
            self.text_signal.emit(f"Error during cloning: {str(e)}\n")
            self.text_signal.emit(f"Git command output: {e.stdout}\n")
            self.text_signal.emit(f"Git command error output: {e.stderr}\n")
            self.finished_signal.emit(False)
        except Exception as e:
            self.text_signal.emit(f"Unexpected error during cloning: {str(e)}\n")
            self.finished_signal.emit(False)


def update_branch_menu(repo_name, repos, branch_menu: QComboBox):
    try:
        print(f"Updating branch menu for repo: {repo_name}\n")
        repo_url = next(
            (repo["url"] for repo in repos if repo["name"] == repo_name), None
        )
        if not repo_url:
            print("No repository URL found for the selected repository.\n")
            return

        # Fetch only the branch names without cloning
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
