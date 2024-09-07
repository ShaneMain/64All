import git
import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkthemes import ThemedTk
from theme_setter import set_theme
import subprocess
import platform

# List of repositories as tuples (name, URL)
REPOS = [
    ("Render96ex", "https://github.com/Render96/Render96ex.git"),
    ("sm64ex", "https://github.com/sm64pc/sm64ex"),
    ("OtherRepo2", "https://github.com/other/repo2.git"),
]


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
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END)
            self.output_text.update_idletasks()


def clone_repo(repo_url, clone_dir, branch, progress_bar, output_text):
    try:
        if os.path.exists(clone_dir) and os.listdir(clone_dir):
            raise Exception(f"Destination path '{clone_dir}' already exists and is not an empty directory.")

        os.makedirs(clone_dir, exist_ok=True)
        output_text.insert(tk.END, f"Cloning repository from {repo_url} (branch: {branch}) to {clone_dir}...\n")
        progress_bar.master.title(f"Cloning repository from {repo_url} to {clone_dir}...")
        progress = CloneProgress(progress_bar, output_text)

        # Using shallow clone (depth=1) and specified branch
        git.Repo.clone_from(repo_url, clone_dir, progress=progress, depth=1, branch=branch)

        progress_bar.master.title("Repository cloned successfully.")
        output_text.insert(tk.END, "Repository cloned successfully.\n")
    except KeyboardInterrupt:
        messagebox.showerror("Error", "Cloning process was interrupted.")
        if os.path.exists(clone_dir) and not os.listdir(clone_dir):
            shutil.rmtree(clone_dir)
    except Exception as e:
        output_text.insert(tk.END, f"An error occurred while cloning the repository: {e}\n")
        messagebox.showerror("Error", f"An error occurred while cloning the repository: {e}")
        if os.path.exists(clone_dir) and not os.listdir(clone_dir):
            shutil.rmtree(clone_dir)


def start_cloning():
    threading.Thread(target=run_clone_thread).start()


def run_clone_thread():
    try:
        repo_name = repo_url_combobox.get()
        base_dir = clone_dir_entry.get()
        branch = branch_var.get()
        clone_dir = os.path.join(base_dir, repo_name)

        repo_url = next((url for name, url in REPOS if name == repo_name), None)

        if not repo_url or not base_dir:
            messagebox.showerror("Input Error", "Please provide both repository URL and base directory.")
            return

        if os.path.exists(clone_dir) and os.listdir(clone_dir):
            messagebox.showerror("Directory Error",
                                 f"Destination path '{clone_dir}' already exists and is not an empty directory. Please select another directory.")
            return

        progress_bar["value"] = 0
        clone_repo(repo_url, clone_dir, branch, progress_bar, output_text)
    except Exception as e:
        print(f"Error in run_clone_thread: {e}")


def on_repo_selection(event):
    try:
        repo_name = repo_url_combobox.get()
        default_clone_dir = os.path.abspath(f"./{repo_name}")
        clone_dir_entry.delete(0, tk.END)
        clone_dir_entry.insert(0, default_clone_dir)
        update_branch_menu(repo_name)
    except Exception as e:
        print(f"Error in on_repo_selection: {e}")


def update_branch_menu(repo_name):
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
                branch_menu['menu'].add_command(label=branch, command=tk._setit(branch_var, branch))
            branch_var.set(default_branch if default_branch else branches[0])
        else:
            branch_var.set("No branches found")
    except Exception as e:
        print(f"Error in update_branch_menu: {e}")
        messagebox.showerror("Error", f"An error occurred while fetching branches: {e}")


def browse_directory():
    try:
        directory = filedialog.askdirectory()
        if directory:
            clone_dir_entry.delete(0, tk.END)
            clone_dir_entry.insert(0, directory)
    except Exception as e:
        print(f"Error in browse_directory: {e}")

# Create the main window
root = ThemedTk(theme="arc")
set_theme(root)
root.title("Git Repo Cloner")

# Create and arrange widgets
try:
    tk.Label(root, text="Repository URL:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.E)

    repo_names = [name for name, _ in REPOS]
    repo_url_combobox = ttk.Combobox(root, values=repo_names, width=47)
    repo_url_combobox.grid(row=0, column=1, columnspan=2, padx=10, pady=5)
    repo_url_combobox.current(0)
    repo_url_combobox.bind("<<ComboboxSelected>>", on_repo_selection)

    tk.Label(root, text="Base Directory:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.E)
    clone_dir_entry = tk.Entry(root, width=50)
    clone_dir_entry.grid(row=1, column=1, padx=10, pady=5)
    default_clone_dir = os.path.abspath(f"./{repo_url_combobox.get()}")
    clone_dir_entry.insert(0, default_clone_dir)

    browse_button = tk.Button(root, text="Browse...", command=browse_directory)
    browse_button.grid(row=1, column=2, padx=10, pady=5)

    tk.Label(root, text="Branch:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.E)
    branch_var = tk.StringVar()
    branch_menu = ttk.OptionMenu(root, branch_var, "")
    branch_menu.config(width=45)
    branch_menu.grid(row=2, column=1, columnspan=2, padx=10, pady=5)

    clone_button = tk.Button(root, text="Clone", command=start_cloning)
    clone_button.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

    progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
    progress_bar.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

    output_text = tk.Text(root, height=10, width=60)
    output_text.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

    update_branch_menu(repo_url_combobox.get())

    root.mainloop()

except Exception as e:
    print(f"Error setting up the main window: {e}")