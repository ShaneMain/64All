import os
import shutil
import threading
import git
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtWidgets import QComboBox, QTextEdit
from yaml import safe_load
from functools import wraps


class CloneProgress(git.remote.RemoteProgress):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def update(self, op_code, cur_count, max_count=None, message=''):
        super().update(op_code, cur_count, max_count, message)
        progress_message = f'Progress: {cur_count} out of {max_count}, {message}\n'
        self.signal.emit(progress_message)


class CloneWorker(QObject):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

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

            clone_progress = CloneProgress(self.progress_signal)
            self.progress_signal.emit(
                f"Cloning repository from {self.repo_url} (branch: {self.branch}) to {self.clone_dir}...\n")
            git.Repo.clone_from(
                self.repo_url,
                self.clone_dir,
                progress=clone_progress,
                branch=self.branch,
                depth=1,  # Perform shallow clone
                single_branch=True  # Clone only the specified branch
            )
            self.progress_signal.emit("Repository cloned successfully.\n")

        except git.exc.GitCommandError as e:
            self.progress_signal.emit(f"An error occurred while executing git command: {e}\n")
            self.clean_up_directory()
        except ValueError as e:
            self.progress_signal.emit(f"An error occurred: {e}\n")
            self.clean_up_directory()
        except Exception as e:
            self.progress_signal.emit(f"An error occurred while cloning the repository: {e}\n")
            self.clean_up_directory()
        finally:
            self.finished_signal.emit()

    def clean_up_directory(self):
        try:
            if os.path.exists(self.clone_dir):
                shutil.rmtree(self.clone_dir)
                self.progress_signal.emit(f"Cleaned up directory '{self.clone_dir}'.\n")
        except Exception as e:
            self.progress_signal.emit(f"Error cleaning up directory '{self.clone_dir}': {e}\n")


def update_branch_menu(repo_name, REPOS, branch_menu: QComboBox):
    try:
        print(f"Updating branch menu for repo: {repo_name}\n")
        repo_url = next((repo['url'] for repo in REPOS if repo['name'] == repo_name), None)
        if not repo_url:
            print("No repository URL found for the selected repository.\n")
            return

        result = git.cmd.Git().ls_remote('--heads', repo_url)

        branch_lines = result.strip().split('\n')
        branches = [line.split()[1].replace('refs/heads/', '') for line in branch_lines]
        print(f"Branches found: {branches}\n")

        default_branch = 'master' if 'master' in branches else 'main' if 'main' in branches else branches[0]

        branch_menu.clear()
        branch_menu.addItems(branches)
        branch_menu.setCurrentText(default_branch)

    except git.exc.GitCommandError as e:
        print(f"Error in update_branch_menu: {e}\n")
