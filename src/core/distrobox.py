import os
import shutil
import subprocess

from core.dependency_utils import install_packages


class DistroboxManager:
    def __init__(self, box_name: str, image: str = "docker.io/library/fedora:latest"):
        self.box_name = box_name
        self.image = image
        self.bin_folder = os.path.expanduser("~/.local/bin")
        self.distrobox_installed = self._check_distrobox_installed()
        self.container_manager_installed = self._check_container_manager_installed()
        if not self.distrobox_installed:
            self._install_distrobox()
        if not self.container_manager_installed:
            self._install_container_manager()

    def _check_distrobox_installed(self) -> bool:
        """Check if Distrobox is installed."""
        result = shutil.which("distrobox-create")
        return result is not None

    def _install_distrobox(self):
        """Install Distrobox."""
        install_command = "curl -s https://raw.githubusercontent.com/89luca89/distrobox/main/install | sh -s -- --prefix ~/.local"
        result = subprocess.run(
            install_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            print("Distrobox installed successfully.")
            self.distrobox_installed = True
        else:
            raise EnvironmentError(f"Failed to install Distrobox: {result.stderr}")

        # Update PATH to include ~/.local/bin
        os.environ["PATH"] += os.pathsep + self.bin_folder

    def _check_container_manager_installed(self) -> bool:
        """Check if a container manager (Podman) is installed."""
        return shutil.which("podman") is not None

    def _install_container_manager(self):
        install_packages(["podman"])

        # Verify installation
        if not shutil.which("podman"):
            raise EnvironmentError("Failed to install Podman.")

    def create(self):
        """Create a new Distrobox container."""
        # Automatically respond with 'yes' to pull the image if not found
        create_command = (
            f"echo 'Y' | distrobox-create --name {self.box_name} --image {self.image}"
        )
        result = subprocess.run(
            create_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            print(f"Distrobox container '{self.box_name}' created successfully.")
        else:
            raise RuntimeError(
                f"Failed to create Distrobox container '{self.box_name}'. Error: {result.stderr}"
            )

    def enter(self):
        """Enter the Distrobox container."""
        enter_command = f"distrobox-enter --name {self.box_name}"
        subprocess.run(enter_command, shell=True)

    def run_command_in_box(self, command: str):
        """Run a command inside the Distrobox container."""
        run_command = f'distrobox-enter --name {self.box_name} -- "{command}"'
        result = subprocess.run(
            run_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"An error occurred: {result.stderr.strip()}")
            return None


if __name__ == "__main__":
    """
    # Example usage:
    manager = DistroboxManager(box_name="mydistrobox")

    # Create a Distrobox container
    manager.create()

    # Enter the Distrobox container
    try:
        print("Entering the Distrobox container...")
        manager.enter()
    except KeyboardInterrupt:
        print("Exited the Distrobox container.")

    # Run a command inside the Distrobox container
    output = manager.run_command_in_box("echo 'Hello from inside Distrobox!'")
    if output:
        print(output)
    """
