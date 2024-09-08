import os
import shutil
import threading
import git
from PyQt6.QtWidgets import QComboBox
from yaml import safe_load
from functools import wraps


class CloneProgress(git.remote.RemoteProgress):
    def __init__(self, output_text):
        super().__init__()
        self.output_text = output_text

    def update(self, op_code, cur_count, max_count=None, message=''):
        super().update(op_code, cur_count, max_count, message)
        progress_message = f'Progress: {cur_count} out of {max_count}, {message}\n'
        self.output_text.append(progress_message)


def run_in_thread(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()

    return wrapper

def clone_repository(repo_url, clone_dir, branch, output_text):
    try:
        os.makedirs(clone_dir, exist_ok=True)
        if not branch:
            raise ValueError("Branch is not specified. Please select a valid branch.")

        clone_progress = CloneProgress(output_text)
        output_text.append(f"Cloning repository from {repo_url} (branch: {branch}) to {clone_dir}...\n")
        git.Repo.clone_from(repo_url, clone_dir, progress=clone_progress, branch=branch)
        output_text.append("Repository cloned successfully.\n")

    except git.exc.GitCommandError as e:
        output_text.append(f"An error occurred while executing git command: {e}\n")
        clean_up_directory(clone_dir, output_text)
    except ValueError as e:
        output_text.append(f"An error occurred: {e}\n")
        clean_up_directory(clone_dir, output_text)
    except Exception as e:
        output_text.append(f"An error occurred while cloning the repository: {e}\n")
        clean_up_directory(clone_dir, output_text)


def clean_up_directory(clone_dir, output_text):
    try:
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir)
            output_text.append(f"Cleaned up directory '{clone_dir}'.\n")
    except Exception as e:
        output_text.append(f"Error cleaning up directory '{clone_dir}': {e}\n")


import git
from functools import wraps
import threading

def update_branch_menu(repo_name, REPOS, branch_menu:QComboBox):
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
