import os
import sys

from core.distrobox import run_ephemeral_command


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


def run_make(
    workspace,
    build_dependencies=None,
    text_box=None,
    user_selections=None,
):
    # Prepare base make command
    command = ["make", "-j4"]
    for key, value in user_selections.items():
        command.append(f"{key}={value}")

    runner = run_ephemeral_command(
        command=" ".join(command),
        directory=workspace,
        textbox=text_box,
        additional_packages=build_dependencies,
    )
    return runner


# Example usage
if __name__ == "__main__":
    # Example directory path where .user_selections.yaml is located
    example_directory = os.path.abspath("../../.workspace")

    # Run make with user selections
    run_make(
        example_directory,
        build_dependencies=["build-essential", "libglew-dev", "libsdl2-dev"],
    )
    """
    # Copy a file
    source_file = "/path/to/source/file.txt"
    target_dir = "/path/to/target/dir"
    file_name = "copied_file.txt"
    symlink_file_to_dir(source_file, target_dir, file_name)
    """
    sys.exit()
