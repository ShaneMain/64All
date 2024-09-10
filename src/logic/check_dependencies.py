import os
import subprocess
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton, QVBoxLayout, QLabel, QDialog


def get_system_python_version():
    """Get the version of Python installed on the system."""
    try:
        result = subprocess.run(['python3', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError("Failed to get Python version")

        version_str = result.stdout.strip()
        if version_str.startswith("Python "):
            version_parts = version_str[len("Python "):].split('.')
            return tuple(map(int, version_parts[:3]))
        else:
            raise RuntimeError("Unexpected Python version output")
    except Exception as e:
        print(f"Error checking system Python version: {e}")
        return None

def is_python_version_sufficient(required_version=(3, 6)):
    """Check if the system Python version is sufficient."""
    version = get_system_python_version()
    if version is None:
        return False
    return version >= required_version

def is_command_available(command_name):
    """Check if a command is available in the system's PATH."""
    return subprocess.run(['which', command_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0

def detect_package_manager():
    """Detect the package manager used by the system."""
    if os.path.isfile('/usr/bin/apt-get'):
        return 'apt-get'
    elif os.path.isfile('/usr/bin/yum'):
        return 'yum'
    elif os.path.isfile('/usr/bin/dnf'):
        return 'dnf'
    elif os.path.isfile('/usr/bin/zypper'):
        return 'zypper'
    elif os.path.isfile('/usr/bin/pacman'):
        return 'pacman'
    else:
        raise RuntimeError("Unsupported package manager")

def get_required_commands():
    """Get the required commands based on the package manager."""
    package_manager = detect_package_manager()

    if package_manager == 'apt-get':
        return {
            'libsdl2-dev': 'libsdl2-dev',
            'libglew-dev': 'libglew-dev',
            'hexdump': 'hexdump',
            'python3': 'python3'
        }
    elif package_manager == 'yum':
        return {
            'libsdl2-devel': 'libsdl2-devel',
            'glew-devel': 'glew-devel',
            'hexdump': 'hexdump',
            'python3': 'python3'
        }
    elif package_manager == 'dnf':
        return {
            'libsdl2-devel': 'libsdl2-devel',
            'glew-devel': 'glew-devel',
            'hexdump': 'hexdump',
            'python3': 'python3'
        }
    elif package_manager == 'zypper':
        return {
            'libsdl2-devel': 'libsdl2-devel',
            'libGLEW-devel': 'libGLEW-devel',
            'hexdump': 'hexdump',
            'python3': 'python3'
        }
    elif package_manager == 'pacman':
        return {
            'sdl2': 'sdl2',
            'glew': 'glew',
            'hexdump': 'hexdump',
            'python': 'python'
        }
    else:
        raise RuntimeError("Unsupported package manager")

def install_packages(packages):
    """Install a list of packages using sudo and zenity."""
    package_manager = detect_package_manager()

    if package_manager == 'apt-get':
        command = ['sudo', 'apt-get', 'install', '-y'] + packages
    elif package_manager == 'yum':
        command = ['sudo', 'yum', 'install', '-y'] + packages
    elif package_manager == 'dnf':
        command = ['sudo', 'dnf', 'install', '-y'] + packages
    elif package_manager == 'zypper':
        command = ['sudo', 'zypper', 'install', '-y'] + packages
    elif package_manager == 'pacman':
        command = ['sudo', 'pacman', '-S', '--noconfirm'] + packages
    else:
        raise RuntimeError("Unsupported package manager")

    try:
        # Prompt for password using zenity
        zenity_command = ['zenity', '--password', '--title=Authenticate']
        zenity_process = subprocess.Popen(zenity_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        password = zenity_process.communicate()[0].decode().strip()

        if zenity_process.returncode != 0:
            print("User canceled the authentication.")
            return

        # Run the installation command with sudo
        env = os.environ.copy()
        env['SUDO_ASKPASS'] = '/usr/bin/zenity'

        # Construct the sudo command
        sudo_command = ['sudo', '-A'] + command

        subprocess.run(sudo_command, env=env, check=True)
        print('Packages installed successfully.')
    except subprocess.CalledProcessError as e:
        print(f"Failed to install packages: {e}")
        sys.exit(1)

def show_missing_packages_dialog(missing_packages):
    """Show a dialog to inform the user about missing packages and handle installation."""
    class InstallDialog(QDialog):
        def __init__(self, missing_packages, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setWindowTitle("Missing Packages")
            self.setModal(True)
            self.missing_packages = missing_packages  # Store missing packages as an instance variable
            layout = QVBoxLayout()

            # Information label
            info_label = QLabel(f"The following packages are missing:\n\n{', '.join(missing_packages)}")
            layout.addWidget(info_label)

            # Install button
            install_button = QPushButton("Install", self)
            install_button.clicked.connect(self.install_packages)
            layout.addWidget(install_button)

            # Cancel button
            cancel_button = QPushButton("Cancel", self)
            cancel_button.clicked.connect(self.reject)
            layout.addWidget(cancel_button)

            self.setLayout(layout)
            self.setFixedSize(self.sizeHint())

        def install_packages(self):
            # Perform installation
            install_packages(self.missing_packages)
            QMessageBox.information(self, "Success", "All missing packages have been installed.")
            self.accept()

    app = QApplication(sys.argv)
    dialog = InstallDialog(missing_packages)
    result = dialog.exec()
    sys.exit(result)

def check_and_install():
    """Check for required packages and install them if missing."""
    required_python_version = (3, 6)

    if not is_python_version_sufficient(required_version=required_python_version):
        print(f"Python {'.'.join(map(str, required_python_version))} or greater is required.")
        print("Attempting to install Python and other required packages...")
        required_packages = get_required_commands()
        install_packages([pkg for cmd, pkg in required_packages.items()])
        # Recheck Python version after installation
        if not is_python_version_sufficient(required_version=required_python_version):
            print("Failed to install the required Python version.")
            sys.exit(1)

    required_commands = get_required_commands()

    # Check if each required command is available
    missing_commands = [cmd for cmd, pkg in required_commands.items() if not is_command_available(cmd)]

    if missing_commands:
        print("Some required commands are missing.")
        show_missing_packages_dialog([required_commands[cmd] for cmd in missing_commands])
    else:
        print("All required commands are available.")

if __name__ == "__main__":
    check_and_install()
