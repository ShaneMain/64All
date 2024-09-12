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

        print(
            f"op_code: {op_code}, cur_count: {cur_count}, max_count: {max_count}, message: {message}"
        )

        # Ensure max_count is a positive number to avoid division by zero or negative values
        if max_count and max_count > 0:
            self.total_progress = int((cur_count / max_count) * 100)

        # Ensure progress is within 0-100% range
        self.total_progress = max(0, min(self.total_progress, 100))

        # Emit progress
        print(f"Total Progress: {self.total_progress} / 100")
        self.progress_signal.emit(self.total_progress)

        # Emit a progress message
        progress_message = (
            f"Progress: {cur_count:,} out of {max_count:,} ({(cur_count / max_count) * 100:.2f}%)"
            if max_count
            else f"Progress: {cur_count:,}, max count unknown."
        )
        if message:
            progress_message += f" Message: {message}"

        self.text_signal.emit(progress_message)


class CloneWorker(QObject):
    progress_signal = pyqtSignal(int)
    text_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)  # Emit a bool indicating success or failure

    def __init__(self):
        super().__init__()

    def run(self, repo_url, clone_dir, branch):
        try:
            os.makedirs(clone_dir, exist_ok=True)
            if not branch:
                raise ValueError(
                    "Branch is not specified. Please select a valid branch."
                )

            clone_progress = CloneProgress(self.text_signal, self.progress_signal)
            self.text_signal.emit(
                f"Cloning repository from {repo_url} (branch: {branch}) to {clone_dir}...\n"
            )

            git.Repo.clone_from(
                repo_url,
                clone_dir,
                progress=clone_progress,
                branch=branch,
                depth=1,  # Perform shallow clone
                single_branch=True,  # Clone only the specified branch
            )
            self.text_signal.emit("Repository cloned successfully.\n")

            # Emit finished signal with success status
            self.finished_signal.emit(True)
            self.terminate_thread(True)

        except FileExistsError as e:
            self.text_signal.emit(f"Warning: {e}\n")
            self.terminate_thread(False)
        except git.exc.GitCommandError as e:
            self.text_signal.emit(
                f"An error occurred while executing git command: {e}\n"
            )
            self.text_signal.emit(
                f"Full Command: {e.command}\nOutput:\n{e.stdout}\nError Output:\n{e.stderr}\n"
            )
            self.clean_up_directory(repo_url, clone_dir, branch)
            self.terminate_thread(False)
        except ValueError as e:
            self.text_signal.emit(f"An error occurred: {e}\n")
            self.clean_up_directory()
            self.terminate_thread(False)
        except Exception as e:
            self.text_signal.emit(
                f"An unexpected error occurred while cloning the repository: {e}\n"
            )
            self.clean_up_directory(repo_url, clone_dir, branch)
            self.terminate_thread(False)

    def terminate_thread(self, success):
        # Emit the finished signal to indicate the task is complete and should terminate the thread
        self.finished_signal.emit(success)

    def clean_up_directory(self, repo_url, clone_dir, branch):
        try:
            if os.path.exists(clone_dir):
                shutil.rmtree(clone_dir)
                self.text_signal.emit(f"Cleaned up directory '{clone_dir}'.\n")
                self.run(repo_url, clone_dir, branch)
        except Exception as e:
            self.text_signal.emit(f"Error cleaning up directory '{clone_dir}': {e}\n")


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
