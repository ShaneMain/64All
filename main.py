import os
import tkinter as tk
from tkinter import ttk, filedialog
from ttkthemes import ThemedTk
from theme_setter import set_theme
from gitlogic import update_branch_menu, start_cloning

# List of repositories as tuples (name, URL)
REPOS = [
    ("Render96ex", "https://github.com/Render96/Render96ex.git"),
    ("sm64ex", "https://github.com/sm64pc/sm64ex"),
]


def on_repo_selection(event):
    try:
        repo_name = repo_url_combobox.get()
        default_dir = os.path.abspath(f"./{repo_name}")
        clone_dir_entry.delete(0, tk.END)
        clone_dir_entry.insert(0, default_dir)
        update_branch_menu(repo_name, REPOS, branch_var, branch_menu)  # Use imported function
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


# Create the main window
root = ThemedTk(theme="arc")
set_theme(root)
root.title("Git Repo Cloner")

try:
    # Create and arrange widgets
    tk.Label(root, text="Repository URL:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.E)

    repo_names = [name for name, _ in REPOS]
    repo_url_combobox = ttk.Combobox(root, values=repo_names, width=47)
    repo_url_combobox.grid(row=0, column=1, columnspan=2, padx=10, pady=5)
    repo_url_combobox.current(0)
    repo_url_combobox.bind("<<ComboboxSelected>>", on_repo_selection)

    tk.Label(root, text="Base Directory:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.E)
    clone_dir_entry = tk.Entry(root, width=50)
    clone_dir_entry.grid(row=1, column=1, padx=10, pady=5)

    # Initial default directory setup
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

    root.mainloop()

except Exception as e:
    print(f"Error setting up the main window: {e}")