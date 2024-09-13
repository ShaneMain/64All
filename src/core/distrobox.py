import os
import shutil
import subprocess
import sys

from core.dependency_utils import install_packages


class DistroboxManager:
    def __init__(
        self,
        box_name: str,
        image: str = "registry.fedoraproject.org/fedora-toolbox:latest",
    ):
        self.created = False
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
            input="Y",
        )
        if result.returncode == 0:
            print(f"Distrobox container '{self.box_name}' created successfully.")
            self.created = True
        else:
            raise RuntimeError(
                f"Failed to create Distrobox container '{self.box_name}'. Error: {result.stderr}"
            )

    def run_command_in_box(self, command: str, ephemeral: bool = False):
        original_name = self.box_name
        if ephemeral:
            self.box_name += "_ephemeral ephemeral"
        """Run a command inside the Distrobox container."""
        if not self.created:
            self.create()

        run_command = f"distrobox-enter --name {self.box_name} -- {command}"
        process = subprocess.Popen(
            run_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Stream outputs to the console
        for stdout_line in iter(process.stdout.readline, ""):
            print(stdout_line, end="")
        for stderr_line in iter(process.stderr.readline, ""):
            print(stderr_line, end="", file=sys.stderr)

        process.stdout.close()
        process.stderr.close()
        returncode = process.wait()

        if ephemeral:
            self.created = False

        if returncode == 0:
            print("Command completed successfully")
            self.box_name = original_name
        else:
            print(f"An error occurred with return code {returncode}")

        return returncode


if __name__ == "__main__":
    # Example usage:
    manager = DistroboxManager(box_name="test")

    # Run a command inside the Distrobox container
    output = manager.run_command_in_box(
        "sudo dnf update -y && sudo dnf install neofetch -y && neofetch", True
    )
    if output:
        print(output)
