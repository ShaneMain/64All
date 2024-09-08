import os
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkthemes import ThemedTk
import git
import shutil
from yaml import safe_load


def load_repos_from_yaml(yaml_file):
    try:
        with open(yaml_file, 'r') as file:
            data = safe_load(file)
            return data['repos']
    except Exception as error:
        print(f"Error loading YAML file: {error}")
        return []


def create_build_option_widgets(repo_options):
    row = 6
    for opt_name, opt_info in repo_options.items():
        ttk.Label(root, text=f"{opt_name}:").grid(row=row, column=0, padx=10, pady=5, sticky=tk.E)
        if isinstance(opt_info["values"], list) and len(opt_info["values"]) == 2 and 0 in opt_info["values"]:
            var = tk.IntVar(value=opt_info.get('default', 0))
            ttk.Checkbutton(root, variable=var).grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)
        else:
            var = tk.StringVar(value=opt_info.get('default', ''))
            values = opt_info.get('values', [])
            menu = ttk.OptionMenu(root, var, var.get(), *values)
            menu.grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)
        build_options_vars[opt_name] = var
        row += 1


def on_repo_selection(event):
    try:
        repo_name = repo_url_combobox.get()
        default_dir = os.path.abspath(f"./{repo_name}")
        clone_dir_entry.delete(0, tk.END)
        clone_dir_entry.insert(0, default_dir)
        update_branch_menu(repo_name, REPOS, branch_var, branch_menu)

        if repo_name in sm64ex_repo_names:
            for widget in root.grid_slaves():
                if int(widget.grid_info()["row"]) >= 6:
                    widget.grid_forget()

            repo = next(repo for repo in REPOS if repo['name'] == repo_name)
            options = repo.get('options', {})
            create_build_option_widgets(options)
    except Exception as error:
        print(f"Error in on_repo_selection: {error}")


def browse_directory():
    try:
        directory = filedialog.askdirectory()
        if directory:
            clone_dir_entry.delete(0, tk.END)
            clone_dir_entry.insert(0, directory)
    except Exception as error:
        print(f"Error in browse_directory: {error}")


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

        repo_url = next((repo['url'] for repo in REPOS if repo['name'] == repo_name), None)

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
        repo_url = next((repo['url'] for repo in REPOS if repo['name'] == repo_name), None)
        if not repo_url:
            branch_var.set("No branches found")
            print("No repository URL found for the selected repository.")
            return

        result = subprocess.run(["git", "ls-remote", "--heads", repo_url], capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Failed to get remote branches: {result.stderr}")

        branch_lines = result.stdout.splitlines()
        branches = [line.split()[1].replace('refs/heads/', '') for line in branch_lines]
        print(f"Branches found: {branches}")

        default_branch = 'master' if 'master' in branches else 'main' if 'main' in branches else branches[0]

        branch_menu['menu'].delete(0, 'end')
        for branch in branches:
            branch_menu['menu'].add_command(label=branch, command=lambda b=branch: branch_var.set(b))
        branch_var.set(default_branch)
    except Exception as e:
        print(f"Error in update_branch_menu: {e}")
        messagebox.showerror("Error", f"An error occurred while fetching branches: {e}")


root = ThemedTk(theme="arc")
root.title("Git Repo Cloner")

yaml_file = 'repos.yaml'
REPOS = load_repos_from_yaml(yaml_file)
build_options_vars = {}

tk.Label(root, text="Repository URL:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.E)

repo_names = [repo['name'] for repo in REPOS]
sm64ex_repo_names = ['sm64ex']

repo_url_combobox = ttk.Combobox(root, values=repo_names, width=47)
repo_url_combobox.grid(row=0, column=1, columnspan=2, padx=10, pady=5)
repo_url_combobox.current(0)
repo_url_combobox.bind("<<ComboboxSelected>>", on_repo_selection)

tk.Label(root, text="Base Directory:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.E)
clone_dir_entry = tk.Entry(root, width=50)
clone_dir_entry.grid(row=1, column=1, padx=10, pady=5)

initial_repo_name = repo_url_combobox.get()
default_clone_dir = os.path.abspath(f"./{initial_repo_name}")
clone_dir_entry.insert(0, default_clone_dir)

browse_button = tk.Button(root, text="Browse...", command=browse_directory)
browse_button.grid(row=1, column=2, padx=10, pady=5)

tk.Label(root, text="Branch:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.E)
branch_var = tk.StringVar()
branch_menu = ttk.OptionMenu(root, branch_var, "")
branch_menu.config(width=45)
branch_menu.grid(row=2, column=1, columnspan=2, padx=10, pady=5)

clone_button = tk.Button(root, text="Clone",
                         command=lambda: start_cloning(repo_url_combobox, clone_dir_entry, branch_var, REPOS,
                                                       progress_bar, output_text))
clone_button.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

output_text = tk.Text(root, height=10, width=60)
output_text.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

update_branch_menu(initial_repo_name, REPOS, branch_var, branch_menu)

if initial_repo_name in sm64ex_repo_names:
    repo = next(repo for repo in REPOS if repo['name'] == initial_repo_name)
    options = repo.get('options', {})
    create_build_option_widgets(options)

root.mainloop()