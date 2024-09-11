import hashlib
import os
import time

from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox


def _compute_file_hash(file_path, hash_algorithm="sha1"):
    """Compute the hash of a file using the specified algorithm."""
    hash_func = hashlib.new(hash_algorithm)
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def _prompt_user_to_select_file(file_list):
    """Prompt the user to select a single file from a list of valid files."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # Display the information message box
    QMessageBox.information(
        None, "Select ROM File", "Multiple valid ROM files found. Please select one."
    )

    # Ensure the message box is processed and closed
    app.processEvents()
    time.sleep(0.5)  # Add a small delay to ensure the message box is rendered

    # Open the file dialog for selection
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    dialog.setNameFilter("N64 ROM files (*.z64)")
    dialog.setViewMode(QFileDialog.ViewMode.List)
    dialog.setDirectory(
        os.getcwd()
    )  # Set the directory to the current working directory

    # Set options to ensure only one file can be selected
    dialog.setOption(
        QFileDialog.Option.DontUseNativeDialog
    )  # Optional: Use custom dialog for consistency

    if dialog.exec() == QFileDialog.DialogCode.Accepted:
        selected_files = dialog.selectedFiles()
        if selected_files:
            return selected_files[0]  # Return the first (and only) selected file
    return None


def _prompt_user_for_file():
    """Prompt the user to select a .z64 file and inform them of the specific requirement."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # Display the information message box
    QMessageBox.information(
        None, "Select ROM File", "Please select a valid Mario 64 .z64 ROM file."
    )

    # Ensure the message box is processed and closed
    app.processEvents()
    time.sleep(0.5)  # Add a small delay to ensure the message box is rendered

    # Open the file dialog
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    dialog.setNameFilter("N64 ROM files (*.z64)")
    dialog.setViewMode(QFileDialog.ViewMode.List)

    # Set options to ensure only one file can be selected
    dialog.setOption(
        QFileDialog.Option.DontUseNativeDialog
    )  # Optional: Use custom dialog for consistency

    if dialog.exec() == QFileDialog.DialogCode.Accepted:
        selected_files = dialog.selectedFiles()
        if selected_files:
            return selected_files[0]  # Return the first (and only) selected file
    return None


def get_key_from_value(dictionary, value):
    """Get the key from a value in a dictionary."""
    for key, val in dictionary.items():
        if val == value:
            return key
    return None


class N64RomValidator:
    KNOWN_HASHES = {
        "jp": "8a20a5c83d6ceb0f0506cfc9fa20d8f438cafe51",
        "us": "9bef1128717f958171a4afac3ed78ee2bb4e86ce",
        "eu": "4ac5721683d0e0b6bbb561b58a71740845dceea9",
        "sh": "3f319ae697533a255a1003d09202379d78d5a2e0",
    }

    def __init__(self):
        self.file_path = None

    def check_rom_files(self):
        """Check for .z64 files, compute their hashes, and return those with known hashes."""
        current_directory = os.getcwd()
        rom_files = [f for f in os.listdir(current_directory) if f.endswith(".z64")]

        valid_files = []
        for file_name in rom_files:
            file_path = os.path.join(current_directory, file_name)
            file_hash = _compute_file_hash(file_path)
            if file_hash in self.KNOWN_HASHES.values():
                key = get_key_from_value(self.KNOWN_HASHES, file_hash)
                valid_files.append((key, file_path))

        return valid_files

    def find_or_select_file(self):
        """Find known ROM files or prompt user to select a file, validating the selected file."""
        valid_files = self.check_rom_files()
        final_file_region = None
        final_file_path = None

        if valid_files:
            if len(valid_files) == 1:
                # Only one valid file found
                final_file_region, final_file_path = valid_files[0]
                self.file_path = final_file_path
                print(f"Found valid N64 ROM: {self.file_path}")
            else:
                # Multiple valid files found, prompt the user to select one
                selected_file_path = _prompt_user_to_select_file(
                    [f for _, f in valid_files]
                )
                if selected_file_path:
                    self.file_path = selected_file_path
                    # Find the corresponding key for the selected file
                    for key, path in valid_files:
                        if path == self.file_path:
                            final_file_region = key
                            final_file_path = self.file_path
                            print(f"Selected valid ROM: {self.file_path}")
                            break
                else:
                    print("No file selected.")
        else:
            while True:
                self.file_path = _prompt_user_for_file()
                if self.file_path:
                    file_hash = _compute_file_hash(self.file_path)
                    key = get_key_from_value(self.KNOWN_HASHES, file_hash)
                    if key:
                        final_file_region = key
                        final_file_path = self.file_path
                        print(f"Selected valid ROM: {self.file_path}")
                        break
                    else:
                        QMessageBox.critical(
                            None,
                            "Invalid ROM",
                            "Invalid ROM! Please select a valid Mario 64 .z64 file.",
                        )
                        print(f"Computed Hash: {file_hash}, Expected Hash: None")
                else:
                    print("No file selected.")
                    break

        return final_file_region, final_file_path


# Example usage
if __name__ == "__main__":
    validator = N64RomValidator()
    print(validator.find_or_select_file())
