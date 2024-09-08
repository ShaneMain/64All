import darkdetect
from ttkthemes import THEMES


def is_dark_theme():
    """
    Uses the darkdetect library to determine if a dark theme is enabled.
    """
    try:
        dark_theme = darkdetect.isDark()
        if dark_theme is None:
            print("Darkdetect could not determine the theme.")
        else:
            print(f"Darkdetect returned: {dark_theme}")
        return dark_theme
    except Exception as e:
        print(f"Error using darkdetect: {e}")
        return False


def set_theme(root):
    """
    Apply the theme based on the system's dark mode setting.
    """
    try:
        if is_dark_theme():
            selected_theme = "equilux"  # "equilux" is a known dark theme in ttkthemes
            print("Dark theme is enabled.")
        else:
            selected_theme = "arc"  # "arc" is a known light theme in ttkthemes
            print("Light theme is enabled.")

        if selected_theme in THEMES:
            root.set_theme(selected_theme)
            print(f"Applying {selected_theme} theme completed.")
        else:
            print(f"Theme {selected_theme} not found. Applying default light theme.")
            root.set_theme("arc")

    except Exception as e:
        print(f"Error detecting or applying system theme: {e}")
        # Default to light theme if detection or application fails
        print("Applying default light theme: arc")
        root.set_theme("arc")
