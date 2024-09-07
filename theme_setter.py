import darkdetect


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
    try:
        if is_dark_theme():
            theme = "dark"
            print("Dark theme is enabled.")
        else:
            theme = "light"
            print("Light theme is enabled.")

        if "dark" in theme:
            print("Applying dark theme: equilux")
            root.set_theme("equilux")  # Dark theme
        else:
            print("Applying light theme: arc")
            root.set_theme("arc")  # Light theme

    except Exception as e:
        print(f"Error detecting system theme: {e}")
        # Default to light theme if detection fails
        print("Applying default light theme: arc")
        root.set_theme("arc")