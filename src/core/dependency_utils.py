import shutil
import subprocess
import sys

import distro
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog

app = QApplication(sys.argv)


def get_required_packages():
    """Get the required packages and binaries based on the operating system."""
    return {
        "apt": {
            "packages": ["libsdl2-dev", "libglew-dev", "hexdump", "python3"],
            "binaries": {
                "hexdump": "hexdump"
            },  # Key: binary, Value: package containing the binary
        },
        "dnf": {
            "packages": ["SDL2-devel", "glew-devel", "hexdump", "python3"],
            "binaries": {"hexdump": "hexdump"},
        },
        "zypper": {
            "packages": ["libSDL2-devel", "libGLEW-devel", "hexdump", "python3"],
            "binaries": {"hexdump": "hexdump"},
        },
        "pacman": {
            "packages": ["sdl2", "glew", "hexdump", "python"],
            "binaries": {"hexdump": "hexdump"},
        },
    }


def detect_package_manager():
    """Detect the package manager used by the system."""
    dist = distro.id()
    if dist in ["ubuntu", "debian"]:
        return "apt"
    elif dist in ["fedora", "centos", "rhel"]:
        return "dnf"
    elif dist in ["opensuse"]:
        return "zypper"
    elif dist in ["arch"]:
        return "pacman"
    else:
        show_message_box(f"Unsupported distribution: {dist}", error=True)
        return None


def is_package_installed(package_manager, package):
    """Check if a package is installed using the system's package manager."""
    try:
        if package_manager == "apt":
            result = subprocess.run(
                ["dpkg", "-l", package], stdout=subprocess.PIPE, text=True
            )
        elif package_manager == "dnf" or package_manager == "zypper":
            result = subprocess.run(
                ["rpm", "-q", package], stdout=subprocess.PIPE, text=True
            )
        elif package_manager == "pacman":
            result = subprocess.run(
                ["pacman", "-Qi", package], stdout=subprocess.PIPE, text=True
            )
        else:
            return False

        installed = result.returncode == 0
        print(
            f"Package '{package}' is {'installed' if installed else 'not installed'}."
        )
        return installed
    except subprocess.CalledProcessError:
        print(f"Package '{package}' is not installed due to an error.")
        return False


def find_missing_packages_and_binaries(required, package_manager):
    """Find which required packages and binaries are missing."""
    missing_packages = [
        pkg
        for pkg in required["packages"]
        if not is_package_installed(package_manager, pkg)
    ]

    for binary, package in required["binaries"].items():
        if shutil.which(binary) is not None:
            if package in missing_packages:
                missing_packages.remove(package)

    return missing_packages


def confirm_installation(missing_packages):
    """Ask the user for confirmation to install the missing packages."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setText(
        f"Missing packages detected:\n{', '.join(missing_packages)}\nDo you want to install them?"
    )
    msg_box.setWindowTitle("Confirm Installation")
    msg_box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )

    return msg_box.exec() == QMessageBox.StandardButton.Yes


def show_message_box(message, error=False):
    """Show a message box with the given message."""
    msg_box = QMessageBox()
    msg_box.setIcon(
        QMessageBox.Icon.Critical if error else QMessageBox.Icon.Information
    )
    msg_box.setText(message)
    msg_box.setWindowTitle("Error" if error else "Information")
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()


def check_sudo_password(password=None):
    """Check if sudo requires a password."""
    check_cmd = ["sudo", "ls"]
    result = subprocess.run(check_cmd, capture_output=True, input=password)
    return result.returncode == 0


def show_progress_dialog(message):
    app = QApplication.instance() or QApplication(sys.argv)
    progress_dialog = QProgressDialog(message, None, 0, 0)
    progress_dialog.setWindowTitle("Please wait")
    progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress_dialog.setCancelButton(None)
    progress_dialog.setMinimumDuration(0)
    progress_dialog.show()
    return progress_dialog


def close_progress_dialog(progress_dialog):
    progress_dialog.cancel()
    QApplication.processEvents()


def elevate_privileges(cmd, message="Authentication Required"):
    """Elevate privileges using zenity and run command."""
    # Check if sudo requires a password
    if check_sudo_password(None):
        return None
    while True:
        # Prompt for password using Zenity
        zenity_command = ["zenity", "--password", f"--title={message}"]
        password_proc = subprocess.run(zenity_command, capture_output=True, text=True)
        password = password_proc.stdout.strip()

        # Check if the provided password is correct
        if check_sudo_password(password):
            return password
        else:
            show_message_box("Incorrect password!", error=True)


def install_packages(packages, package_manager=None):
    """Install the missing packages using the system's package manager."""
    show_message_box(
        f'The following required packages will be installed: {" ".join(packages)}'
    )

    if package_manager is None:
        package_manager = detect_package_manager()

    match package_manager:
        case "apt":
            cmd = ["apt", "install", "-y"] + packages
        case "dnf":
            cmd = ["dnf", "install", "-y"] + packages
        case "zypper":
            cmd = ["zypper", "--non-interactive", "install"] + packages
        case "pacman":
            cmd = ["pacman", "-S", "--noconfirm"] + packages
        case _:
            show_message_box("Unsupported package manager detected.", error=True)
            return

    password = elevate_privileges(cmd)

    result = subprocess.run(["sudo", "-S"] + cmd, input=password, text=True, check=True)
    if result and result.returncode == 0:
        show_message_box("Packages installed successfully.")
        return True
    else:
        show_message_box(
            f"Failed to install packages with error code: {result.returncode if result else 'unknown'}",
            error=True,
        )
        return False


def check_and_install():
    """Main function to run the package check and install process."""
    try:
        package_manager = detect_package_manager()
        if not package_manager:
            show_message_box(
                "Could not verify required packages. You may not be able to build."
            )
            print("No package manager detected. Exiting.")
            return

        print(f"Detected package manager: {package_manager}")

        required = get_required_packages().get(package_manager, {})
        missing_packages = find_missing_packages_and_binaries(required, package_manager)
        if not required:
            print(
                f"No required packages mapping for package manager: {package_manager}"
            )
            return

        if missing_packages:
            print(f"Missing packages detected: {missing_packages}")

            # Confirm installation
            if confirm_installation(missing_packages):
                install_packages(missing_packages, package_manager)
                if missing_packages:
                    show_message_box(
                        "Installation failed or user cancelled. You will not be able to build."
                    )
            else:
                show_message_box(
                    "Installation cancelled by user. You will not be able to build."
                )

        else:
            print("All required packages are installed.")

        print("check_and_install finished successfully.")
    except Exception as e:
        show_message_box(f"An error occurred: {e}", error=True)
        print(f"An error occurred during check_and_install: {e}")


if __name__ == "__main__":
    elevate_privileges(["ls"])
    check_and_install()
