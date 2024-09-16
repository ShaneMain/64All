import os


def symlink_file_to_dir(file_path: str, dir_path: str, link_name: str):
    """Create a symbolic link to a file in a specified directory."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"{file_path} is not a valid file")
    if not os.path.isdir(dir_path):
        raise NotADirectoryError(f"{dir_path} is not a valid directory")

    link_path = os.path.join(dir_path, link_name)

    try:
        # Remove the existing symlink if it exists
        if os.path.islink(link_path):
            os.unlink(link_path)

        # Create a symbolic link
        os.symlink(file_path, link_path)
        print(f"Symlink created: {link_path} -> {file_path}")
    except OSError as e:
        print(f"Error creating symlink: {e}")
