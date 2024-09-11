import os
import subprocess
import sys

import yaml


def run_make(directory, target: str = ""):
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
        cmd = ["make", "-j4"]
        if target:
            cmd.append(target)

        for key, value in user_selections.items():
            cmd.append(f"{key}={value}")

        # Run the make command
        print(cmd)
        result = subprocess.run(cmd, capture_output=True, text=True)
        result.check_returncode()  # Raises CalledProcessError if the command exited non-zero
        print(result.stdout)
    except FileNotFoundError as e:
        print(e)
    except subprocess.CalledProcessError as e:
        print(f"Error running make: {e.stderr}")
    finally:
        os.chdir(original_directory)


def symlink_file_to_dir(file_path: str, dir_path: str, symlink_name: str):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"{file_path} is not a valid file")
    if not os.path.isdir(dir_path):
        raise NotADirectoryError(f"{dir_path} is not a valid directory")

    symlink_path = os.path.join(dir_path, symlink_name)

    try:
        os.symlink(file_path, symlink_path)
        print(f"Symlink created: {symlink_path} -> {file_path}")
    except OSError as e:
        print(f"Error creating symlink: {e}")


# Example usage
if __name__ == "__main__":
    # Example directory path where .user_selections.yaml is located
    example_directory = os.path.abspath("../../.workspace")

    # Run make with user selections
    run_make(example_directory)

    # Create a symlink
    source_file = "/path/to/source/file.txt"
    target_dir = "/path/to/target/dir"
    symlink_name = "linked_file.txt"
    symlink_file_to_dir(source_file, target_dir, symlink_name)

    sys.exit()
