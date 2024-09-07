import git
import os
import shutil
import threading
import subprocess
from tkinter import messagebox


class CloneProgress(git.remote.RemoteProgress):
    def __init__(self, progress_bar, output_text):
        super().__init__()
        self.progress_bar = progress_bar
        self.output_text = output_text
        self.progress_bar["value"] = 0

    def update(self, op_code, cur_count, max_count=None, message=''):
        if max_count is not None:
            self.progress_bar["maximum"] = max_count
        self.progress_bar["value"] = cur_count
        self.progress_bar.update_idletasks()
        if message:
            self.output_text.insert("end", message + "\n")
            self.output_text.see("end")
            self.output_text.update_idletasks()


def clone_repo(repo_url, clone_dir, branch, progress_bar, output_text):
    try:
        if os.path.exists(clone_dir) and os.listdir(clone_dir):
            raise Exception(f"Destination path '{clone_dir}' already exists and is not an empty directory.")

        os.makedirs(clone_dir, exist_ok=True)
        output_text.insert("end", f"Cloning repository from {repo_url} (branch: {branch}) to {clone_dir}...\n")
        progress_bar.master.title(f"Cloning repository from {repo_url} to {clone_dir}...")
        progress = CloneProgress(progress_bar, output_text)

        # Using shallow clone (depth=1) and specified branch
        git.Repo.clone_from(repo_url, clone_dir, progress=progress, depth=1, branch=branch)

        progress_bar.master.title("Repository cloned successfully.")
        output_text.insert("end", "Repository cloned successfully.\n")
    except KeyboardInterrupt:
        messagebox.showerror("Error", "Cloning process was interrupted.")
        if os.path.exists(clone_dir) and not os.listdir(clone_dir):
            shutil.rmtree(clone_dir)
    except Exception as e:
        output_text.insert("end", f"An error occurred while cloning the repository: {e}\n")
        messagebox.showerror("Error", f"An error occurred while cloning the repository: {e}")
        if os.path.exists(clone_dir) and not os.listdir(clone_dir):
            shutil.rmtree(clone_dir)


def start_cloning(repo_url_combobox, clone_dir_entry, branch_var, REPOS, progress_bar, output_text):
    threading.Thread(
        target=run_clone_thread,
        args=(repo_url_combobox, clone_dir_entry, branch_var, REPOS, progress_bar, output_text)
    ).start()


def run_clone_thread(repo_url_combobox, clone_dir_entry, branch_var, REPOS, progress_bar, output_text):
    try:
        repo_name = repo_url_combobox.get()
        base_dir = clone_dir_entry.get()
        branch = branch_var.get()
        clone_dir = os.path.join(base_dir, repo_name)

        repo_url = next((url for name, url in REPOS if name == repo_name), None)

        if not repo_url or not base_dir:
            messagebox.showerror("Input Error", "Please provide both the repository URL and base directory.")
            return

        if os.path.exists(clone_dir) and os.listdir(clone_dir):
            messagebox.showerror("Directory Error",
                                 f"Destination path '{clone_dir}' already exists and is not an empty directory. Please select another directory.")
            return

        progress_bar["value"] = 0
        clone_repo(repo_url, clone_dir, branch, progress_bar, output_text)
    except Exception as e:
        print(f"Error in run_clone_thread: {e}")


def update_branch_menu(repo_name, REPOS, branch_var, branch_menu):
    try:
        print(f"Updating branch menu for repo: {repo_name}")
        repo_url = next((url for name, url in REPOS if name == repo_name), None)
        if not repo_url:
            branch_var.set("No branches found")
            print("No repository URL found for the selected repository.")
            return

        # Use subprocess to run 'git ls-remote --heads'
        result = subprocess.run(["git", "ls-remote", "--heads", repo_url], capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Failed to get remote branches: {result.stderr}")

        branch_lines = result.stdout.splitlines()
        branches = [line.split()[1].replace('refs/heads/', '') for line in branch_lines]
        print(f"Branches found: {branches}")

        # Default to 'master' or 'main' if available
        default_branch = None
        if 'master' in branches:
            default_branch = 'master'
        elif 'main' in branches:
            default_branch = 'main'

        branch_menu['menu'].delete(0, 'end')
        if branches:
            for branch in branches:
                branch_menu['menu'].add_command(label=branch, command=lambda b=branch: branch_var.set(b))
            branch_var.set(default_branch if default_branch else branches[0])
        else:
            branch_var.set("No branches found")
    except Exception as e:
        print(f"Error in update_branch_menu: {e}")
        messagebox.showerror("Error", f"An error occurred while fetching branches: {e}")