import os
import tkinter as tk
from tkinter import ttk, filedialog
from ttkthemes import ThemedTk
from gitlogic import update_branch_menu, start_cloning
from theme_setter import set_theme
from yaml import safe_load


class Tooltip:
    def __init__(self, widget, text, bg_color, fg_color):
        self.widget = widget
        self.text = text
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=self.text, background=self.bg_color, foreground=self.fg_color,
                         relief='solid', borderwidth=1)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def load_repos_from_yaml(yaml_file):
    try:
        with open(yaml_file, 'r') as file:
            data = safe_load(file)
            return data['repos']
    except Exception as error:
        print(f"Error loading YAML file: {error}")
        return []


def create_build_option_widgets(repo_options, bg_color, fg_color, advanced=False):
    # Destroy previous build option widgets
    for widget in main_frame.grid_slaves():
        if int(widget.grid_info()["row"]) >= 6:
            widget.destroy()


    # Remove advanced options from the repo_options before processing
    if(not advanced):
        advanced_options = repo_options.pop('advanced', {})

    checkboxes = [(opt_name, opt_info) for opt_name, opt_info in repo_options.items() if
                  "values" in opt_info and isinstance(opt_info["values"], list) and len(
                      opt_info["values"]) == 2 and 0 in opt_info["values"]]
    dropdowns = [(opt_name, opt_info) for opt_name, opt_info in repo_options.items() if
                 "values" in opt_info and not (
                         isinstance(opt_info["values"], list) and len(opt_info["values"]) == 2 and 0 in opt_info[
                     "values"])]

    for i, (opt_name, opt_info) in enumerate(checkboxes):
        row_offset = 6 + (i // 2)
        col = (i % 2) * 4  # Moving to alternate columns with space in between

        label = ttk.Label(main_frame, text=f"{opt_name}:")
        label.grid(row=row_offset, column=col, padx=5, pady=3, sticky=tk.E)
        Tooltip(label, opt_info.get('description', ''), bg_color, fg_color)

        var = tk.IntVar(value=opt_info.get('default', 0))
        widget = ttk.Checkbutton(main_frame, variable=var)
        widget.grid(row=row_offset, column=col + 1, padx=5, pady=3, sticky=tk.W)
        Tooltip(widget, opt_info.get('description', ''), bg_color, fg_color)
        build_options_vars[opt_name] = var

    start_row = 6 + (len(checkboxes) // 2) + 1

    for i, (opt_name, opt_info) in enumerate(dropdowns):
        row_offset = start_row + i
        label = ttk.Label(main_frame, text=f"{opt_name}:")
        label.grid(row=row_offset, column=8, padx=5, pady=3, sticky=tk.E)
        Tooltip(label, opt_info.get('description', ''), bg_color, fg_color)

        var = tk.StringVar(value=opt_info.get('default', ''))
        values = opt_info.get('values', [])
        menu = ttk.OptionMenu(main_frame, var, var.get(), *values)
        menu.grid(row=row_offset, column=9, padx=5, pady=3, sticky=tk.W)
        Tooltip(menu, opt_info.get('description', ''), bg_color, fg_color)
        build_options_vars[opt_name] = var


def on_repo_selection(event):
    try:
        repo_name = repo_url_combobox.get()
        default_dir = os.path.abspath(f"./{repo_name}")
        clone_dir_entry.delete(0, tk.END)
        clone_dir_entry.insert(0, default_dir)
        update_branch_menu(repo_name, REPOS, branch_var, branch_menu)

        # Load options for the selected repository regardless of name
        repo = next(repo for repo in REPOS if repo['name'] == repo_name)
        options = repo.get('options', {})
        create_build_option_widgets(options, tooltip_bg_color, tooltip_fg_color)
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


def init_window():
    global root, REPOS, build_options_vars, sm64ex_repo_names, main_frame, repo_url_combobox, clone_dir_entry, branch_var, branch_menu, progress_bar, output_text, tooltip_bg_color, tooltip_fg_color
    # Initialize Tkinter with themed window
    root = ThemedTk(theme="equilux")  # Explicitly set a dark theme to minimize white outline
    set_theme(root)  # Apply theme using the function from theme_setter
    root.title("Git Repo Cloner")
    # Prevent window resizing
    root.resizable(width=False, height=False)
    # Remove padding around the main window
    root.configure(padx=0, pady=0)
    yaml_file = 'repos.yaml'
    REPOS = load_repos_from_yaml(yaml_file)
    build_options_vars = {}
    repo_names = [repo['name'] for repo in REPOS]
    sm64ex_repo_names = ['sm64ex', 'Render96ex']  # Include Render96ex here

    # Fetch the theme colors for tooltips
    style = ttk.Style(root)
    tooltip_bg_color = style.lookup('TLabel', 'background')
    tooltip_fg_color = style.lookup('TLabel', 'foreground')

    # Create a main frame that will hold all other widgets in the center without extra padding
    main_frame = ttk.Frame(root, padding=0)
    main_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
    # Ensure the main frame can expand and fill the window
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    # Configure main_frame columns for even spacing
    for i in range(10):  # Assuming up to 5 pairs of checkboxes and dropdowns with existing columns
        main_frame.columnconfigure(i, weight=1)
    ttk.Label(main_frame, text="Repository URL:").grid(row=0, column=0, columnspan=2, padx=5, pady=3, sticky=tk.W)
    repo_url_combobox = ttk.Combobox(main_frame, values=repo_names, width=47)
    repo_url_combobox.grid(row=0, column=2, columnspan=8, padx=5, pady=3, sticky=tk.W)
    repo_url_combobox.current(0)
    repo_url_combobox.bind("<<ComboboxSelected>>", on_repo_selection)
    ttk.Label(main_frame, text="Base Directory:").grid(row=1, column=0, columnspan=2, padx=5, pady=3, sticky=tk.W)
    clone_dir_entry = ttk.Entry(main_frame, width=50)
    clone_dir_entry.grid(row=1, column=2, columnspan=6, padx=5, pady=3, sticky=tk.W)
    browse_button = ttk.Button(main_frame, text="Browse...", command=browse_directory)
    browse_button.grid(row=1, column=8, columnspan=2, padx=5, pady=3, sticky=tk.W)
    initial_repo_name = repo_url_combobox.get()
    default_clone_dir = os.path.abspath(f"./{initial_repo_name}")
    clone_dir_entry.insert(0, default_clone_dir)
    ttk.Label(main_frame, text="Branch:").grid(row=2, column=0, columnspan=2, padx=5, pady=3, sticky=tk.W)
    branch_var = tk.StringVar()
    branch_menu = ttk.OptionMenu(main_frame, branch_var, "")
    branch_menu.config(width=45)
    branch_menu.grid(row=2, column=2, columnspan=8, padx=5, pady=3, sticky=tk.W)
    clone_button = ttk.Button(main_frame, text="Clone", command=lambda: start_cloning(
        repo_url_combobox, clone_dir_entry, branch_var, REPOS, progress_bar, output_text, root
    ))
    clone_button.grid(row=3, column=0, columnspan=10, padx=5, pady=8, sticky=tk.W + tk.E)
    progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=400, mode="determinate")
    progress_bar.grid(row=4, column=0, columnspan=10, padx=5, pady=5, sticky=tk.W + tk.E)
    output_text = tk.Text(main_frame, height=10, width=60)
    output_text.grid(row=5, column=0, columnspan=10, padx=5, pady=5, sticky=tk.W + tk.E)
    # Set initial branch menu
    update_branch_menu(initial_repo_name, REPOS, branch_var, branch_menu)

    repo = next(repo for repo in REPOS if repo['name'] == initial_repo_name)
    options = repo.get('options', {})
    create_build_option_widgets(options, tooltip_bg_color, tooltip_fg_color)

    root.mainloop()