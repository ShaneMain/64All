import asyncio
import os
import subprocess
import sys

import yaml
from PyQt6.QtWidgets import QTextEdit

from core.distrobox import run_ephemeral_command


def run_make(
    directory,
    target: str = "",
    build_dependencies=None,
    text_box: QTextEdit = None,
):
    if build_dependencies is None:
        build_dependencies = []
    original_directory = os.getcwd()
    try:
        os.chdir(directory)

        # Read the user selections from the YAML file
        yaml_file = os.path.join(directory, ".user_selections.yaml")
        if not os.path.isfile(yaml_file):
            raise FileNotFoundError(f"{yaml_file} is not found")

        with open(yaml_file, "r") as file:
            user_selections = yaml.safe_load(file)

        # Construct the make command with the build options
        cmd = ["make", "-C", f'"{directory}" ' "-j4"]
        if target:
            cmd.append(target)

        for key, value in user_selections.items():
            cmd.append(f"{key}={value}")

        # Command to be written to the script
        command = " ".join(cmd)

        print(command)
        # Print the directory and file path
        print(f"Directory: {directory}")

        # Run the script
        asyncio.run(
            run_ephemeral_command(
                command,
                additional_packages=build_dependencies,
            )
        )
    except FileNotFoundError as e:
        print(e)
    except subprocess.CalledProcessError as e:
        print(f"Error running make: {e.stderr}")
    finally:
        os.chdir(original_directory)


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


# distrobox-ephemeral --name ephemeral_runner --additional-packages "build-essential libglew-dev libsdl2-dev" --image debian:stable-slim -- bash -c "cd /home/jc/PycharmProjects/Mario64All/.workspace" && make -j4 DISCORDRPC=False EXT_OPTIONS_MENU=True TEXTURE_FIX=True
# distrobox create --name tester --image ubuntu:latest --additional-packages "build-essential libglew-dev libsdl2-dev" -- bash -c "cd /home/jc/PycharmProjects/Mario64All/.workspace" && make -j4 DISCORDRPC=False EXT_OPTIONS_MENU=True TEXTURE_FIX=True
