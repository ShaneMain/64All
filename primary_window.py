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


class GitRepoClonerApp:
    def __init__(self, root=None):
        if root is None:
            root = ThemedTk(theme="equilux")
        self.root = root
        self.build_options_vars = {}
        self.tooltip_bg_color = ""
        self.tooltip_fg_color = ""
        self.setup_ui()
        self.root.mainloop()

    def setup_ui(self):
        self.root.title("Git Repo Cloner")
        self.root.resizable(width=False, height=False)
        self.root.configure(padx=0, pady=0)

        set_theme(self.root)

        self.load_repos()

        style = ttk.Style(self.root)
        self.tooltip_bg_color = style.lookup('TLabel', 'background')
        self.tooltip_fg_color = style.lookup('TLabel', 'foreground')

        self.main_frame = ttk.Frame(self.root, padding=0)
        self.main_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        for i in range(10):
            self.main_frame.columnconfigure(i, weight=1)

        self.show_advanced_var = tk.IntVar(value=0)
        self.advanced_checkbox = ttk.Checkbutton(
            self.main_frame, text="Show advanced options", variable=self.show_advanced_var,
            command=self.toggle_advanced_options
        )
        self.advanced_checkbox.grid(row=0, column=10, padx=5, pady=3, sticky=tk.E)

        self.setup_repo_options()

        initial_repo_name = self.repo_url_combobox.get()
        self.update_branch_menu(initial_repo_name)
        repo = next((repo for repo in self.REPOS if repo['name'] == initial_repo_name), None)
        if repo:
            self.repo_options = repo.get('options', {})
            self.create_build_option_widgets(self.repo_options, self.tooltip_bg_color, self.tooltip_fg_color)

    def load_repos(self):
        yaml_file = 'repos.yaml'
        try:
            with open(yaml_file, 'r') as file:
                data = safe_load(file)
                self.REPOS = data['repos']
        except Exception as error:
            print(f"Error loading YAML file: {error}")
            self.REPOS = []

    def setup_repo_options(self):
        repo_names = [repo['name'] for repo in self.REPOS]

        self.repo_url_combobox = ttk.Combobox(self.main_frame, values=repo_names, width=47)
        self.repo_url_combobox.grid(row=0, column=2, columnspan=8, padx=5, pady=3, sticky=tk.W)
        self.repo_url_combobox.current(0)
        self.repo_url_combobox.bind("<<ComboboxSelected>>", self.on_repo_selection)

        ttk.Label(self.main_frame, text="Repository URL:").grid(row=0, column=0, columnspan=2, padx=5, pady=3,
                                                                sticky=tk.W)

        self.clone_dir_entry = ttk.Entry(self.main_frame, width=50)
        self.clone_dir_entry.grid(row=1, column=2, columnspan=6, padx=5, pady=3, sticky=tk.W)

        browse_button = ttk.Button(self.main_frame, text="Browse...", command=self.browse_directory)
        browse_button.grid(row=1, column=8, columnspan=2, padx=5, pady=3, sticky=tk.W)

        ttk.Label(self.main_frame, text="Base Directory:").grid(row=1, column=0, columnspan=2, padx=5, pady=3,
                                                                sticky=tk.W)

        initial_repo_name = self.repo_url_combobox.get()
        default_clone_dir = os.path.abspath(f"./{initial_repo_name}")
        self.clone_dir_entry.insert(0, default_clone_dir)

        self.branch_label = ttk.Label(self.main_frame, text="Branch:")
        self.branch_label.grid(row=2, column=0, columnspan=2, padx=5, pady=3, sticky=tk.W)

        self.branch_var = tk.StringVar()
        self.branch_menu = ttk.OptionMenu(self.main_frame, self.branch_var, "")
        self.branch_menu.config(width=45)
        self.branch_menu.grid(row=2, column=2, columnspan=8, padx=5, pady=3, sticky=tk.W)

        clone_button = ttk.Button(self.main_frame, text="Clone", command=self.start_cloning)
        clone_button.grid(row=3, column=0, columnspan=10, padx=5, pady=8, sticky=tk.W + tk.E)

        self.progress_bar = ttk.Progressbar(self.main_frame, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=4, column=0, columnspan=10, padx=5, pady=5, sticky=tk.W + tk.E)

        self.output_text = tk.Text(self.main_frame, height=10, width=60)
        self.output_text.grid(row=5, column=0, columnspan=10, padx=5, pady=5, sticky=tk.W + tk.E)

    def update_branch_menu(self, repo_name):
        update_branch_menu(repo_name, self.REPOS, self.branch_var, self.branch_menu)

    def create_build_option_widgets(self, repo_options, bg_color, fg_color, advanced_options=False):
        for widget in self.main_frame.grid_slaves():
            if int(widget.grid_info()["row"]) >= 6:
                widget.destroy()

        if not advanced_options:
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
            col = (i % 2) * 4

            label = ttk.Label(self.main_frame, text=f"{opt_name}:")
            label.grid(row=row_offset, column=col, padx=5, pady=3, sticky=tk.E)
            Tooltip(label, opt_info.get('description', ''), bg_color, fg_color)

            var = tk.IntVar(value=opt_info.get('default', 0))
            widget = ttk.Checkbutton(self.main_frame, variable=var)
            widget.grid(row=row_offset, column=col + 1, padx=5, pady=3, sticky=tk.W)
            Tooltip(widget, opt_info.get('description', ''), bg_color, fg_color)
            self.build_options_vars[opt_name] = var

        start_row = 6 + (len(checkboxes) // 2) + 1

        for i, (opt_name, opt_info) in enumerate(dropdowns):
            row_offset = start_row + i
            label = ttk.Label(self.main_frame, text=f"{opt_name}:")
            label.grid(row=row_offset, column=8, padx=5, pady=3, sticky=tk.E)
            Tooltip(label, opt_info.get('description', ''), bg_color, fg_color)

            var = tk.StringVar(value=opt_info.get('default', ''))
            values = opt_info.get('values', [])
            menu = ttk.OptionMenu(self.main_frame, var, var.get(), *values)
            menu.grid(row=row_offset, column=9, padx=5, pady=3, sticky=tk.W)
            Tooltip(menu, opt_info.get('description', ''), bg_color, fg_color)
            self.build_options_vars[opt_name] = var

        last_row = start_row + len(dropdowns)
        if hasattr(self, 'advanced_checkbox') and self.advanced_checkbox:
            self.advanced_checkbox.grid(row=last_row, column=0, padx=5, pady=3, sticky=tk.W)

    def toggle_advanced_options(self, reset_grid=True):
        if reset_grid:
            self.repo_name = self.repo_url_combobox.get()
            repo = next((repo for repo in self.REPOS if repo['name'] == self.repo_name), None)
            if repo:
                self.repo_options = repo.get('options', {})

        if self.show_advanced_var.get() == 1:
            self.branch_label.grid()
            self.branch_menu.grid()
        else:
            self.branch_label.grid_remove()
            self.branch_menu.grid_remove()

        if hasattr(self, 'advanced_checkbox') and self.advanced_checkbox:
            self.create_build_option_widgets(self.repo_options, self.tooltip_bg_color, self.tooltip_fg_color,
                                             self.show_advanced_var.get() == 1)

    def on_repo_selection(self, event):
        try:
            repo_name = self.repo_url_combobox.get()
            default_dir = os.path.abspath(f"./{repo_name}")
            self.clone_dir_entry.delete(0, tk.END)
            self.clone_dir_entry.insert(0, default_dir)
            self.update_branch_menu(repo_name)

            repo = next((repo for repo in self.REPOS if repo['name'] == repo_name), None)
            if repo:
                options = repo.get('options', {})
                self.repo_options = options
                self.create_build_option_widgets(options, self.tooltip_bg_color, self.tooltip_fg_color,
                                                 self.show_advanced_var.get() == 1)
        except Exception as error:
            print(f"Error in on_repo_selection: {error}")

    def browse_directory(self):
        try:
            directory = filedialog.askdirectory()
            if directory:
                self.clone_dir_entry.delete(0, tk.END)
                self.clone_dir_entry.insert(0, directory)
        except Exception as error:
            print(f"Error in browse_directory: {error}")

    def start_cloning(self):
        start_cloning(
            self.repo_url_combobox, self.clone_dir_entry, self.branch_var, self.REPOS, self.progress_bar,
            self.output_text, self.root
        )


if __name__ == "__main__":
    app = GitRepoClonerApp()
