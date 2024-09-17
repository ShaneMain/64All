import asyncio
import os
import shutil
import sys

from PyQt6.QtCore import QThread, pyqtSignal, QObject, QEventLoop, pyqtSlot
from PyQt6.QtWidgets import QApplication, QTextEdit

from core.dependency_utils import install_packages
from ui.ui_components import UISetup


class Worker(QThread):
    update_text = pyqtSignal(str)
    finished_signal = pyqtSignal(int)  # Change this to emit the return code

    def __init__(self, command: str, directory="."):
        super().__init__()
        self.command = command
        self.directory = directory
        self.process = None
        self.return_code = None

    def run(self):
        asyncio.run(self._async_run())

    async def _async_run(self):
        self.process = await asyncio.create_subprocess_shell(
            self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.directory,
        )

        async def stream_output(stream):
            while True:
                line = await stream.readline()
                if not line:
                    break
                self.update_text.emit(line.decode().strip())

        await asyncio.gather(
            stream_output(self.process.stdout),
            stream_output(self.process.stderr),
        )
        self.return_code = await self.process.wait()
        self.finished_signal.emit(self.return_code)


class DistroboxManager(QObject):
    def __init__(
        self,
        box_name: str,
        image: str = "ubuntu:latest",
        ui_setup: "UISetup" = None,  # Change this line
        directory: str = ".",
    ):
        super().__init__()
        self.ui_setup = ui_setup  # Change this line
        self.created = False
        self.box_name = box_name
        self.image = image
        self.bin_folder = os.path.expanduser("~/.local/bin")
        self.directory = directory

        self.distrobox_installed = self._check_distrobox_installed()
        self.container_manager_installed = self._check_container_manager_installed()
        self.worker = None  # To keep track of the worker thread

        if not self.distrobox_installed:
            asyncio.run(self._install_distrobox())
        if not self.container_manager_installed:
            asyncio.run(self._install_container_manager())

    def _check_distrobox_installed(self) -> bool:
        """Check if Distrobox is installed."""
        return shutil.which("distrobox-create") is not None

    async def _install_distrobox(self):
        """Install Distrobox."""
        install_command = "curl -s https://raw.githubusercontent.com/89luca89/distrobox/main/install | sh -s -- --prefix ~/.local"
        process = await asyncio.create_subprocess_shell(
            install_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.wait()
        output = await process.stdout.read()
        error = await process.stderr.read()

        if process.returncode == 0:
            print("Distrobox installed successfully.")
            self.distrobox_installed = True
        else:
            raise EnvironmentError(f"Failed to install Distrobox: {error.decode()}")

        # Update PATH to include ~/.local/bin
        os.environ["PATH"] += os.pathsep + self.bin_folder

    def _check_container_manager_installed(self) -> bool:
        """Check if a container manager (Podman) is installed."""
        return shutil.which("podman") is not None

    async def _install_container_manager(self):
        """Install container manager (Podman)."""
        install_packages(["podman"])
        # Verify installation
        if not shutil.which("podman"):
            raise EnvironmentError("Failed to install Podman.")

    def _run_command(self, command: str):
        """Run a command asynchronously using the Worker class."""
        self.worker = Worker(command=command, directory=self.directory)
        if self.ui_setup:  # Ensure ui_setup is set before connecting signals
            self.worker.update_text.connect(self.append_text)
        self.worker.finished_signal.connect(self.worker_finished)
        self.worker.start()

    async def create(
        self,
        ephemeral=False,
        run_immediate_command: str = None,
        additional_packages: list = None,
    ):
        """Create a new Distrobox container."""
        base_command = "distrobox-create"
        if ephemeral:
            base_command = "distrobox-ephemeral"
        run_command = ""
        if run_immediate_command is not None:
            run_command = f" -- {run_immediate_command}"
        packages_command = ""
        if additional_packages is not None:
            packages_command = (
                f' --additional-packages "{" ".join(additional_packages)}"'
            )

        create_command = f"{base_command} --name {self.box_name}{packages_command} --image {self.image}{run_command}"

        print(f"Executing command: {create_command}")

        loop = QEventLoop()
        self.worker = Worker(command=create_command, directory=self.directory)
        self.worker.update_text.connect(self.append_text)
        self.worker.finished_signal.connect(loop.quit)
        self.worker.start()
        loop.exec()  # Wait until the worker finishes

        if self.worker.return_code != 0:
            error_output = await self.worker.process.stderr.read()
            error_output = error_output.decode().strip()
            raise RuntimeError(
                f"Failed to create Distrobox container '{self.box_name}'. "
                f"Exit code: {self.worker.return_code}. Error: {error_output}"
            )

        self.created = True

        # If there was an immediate command, we don't need to do anything else
        if run_immediate_command:
            return

        # If there was no immediate command, we need to remove the ephemeral container
        if ephemeral:
            remove_command = f"distrobox rm {self.box_name} -f"
            remove_worker = Worker(command=remove_command, directory=self.directory)
            remove_worker.start()
            remove_worker.wait()

    async def run_command_in_box(self, command: str, ephemeral: bool = False):
        """Run a command inside the Distrobox container asynchronously."""
        if not self.created:
            await self.create()

        command = f"distrobox-enter --name {self.box_name} -- {command}"
        self._run_command(command)

        if ephemeral:
            self.created = False

    @pyqtSlot(str)
    def append_text(self, text: str):
        """Append text to the QTextEdit box."""
        print(text)
        if self.ui_setup:
            self.ui_setup.update_output_text(text)

    @pyqtSlot()
    def worker_finished(self):
        """Handle worker finish signal."""
        print("Worker thread has finished execution.")


def run_ephemeral_command(
    command: str,
    ui_setup: UISetup = None,
    directory=".",
    additional_packages: list = None,
    on_complete: callable = None,  # Added parameter for completion callback
):
    async def run():
        manager = DistroboxManager(
            "ephemeral_runner", ui_setup=ui_setup, directory=directory
        )
        try:
            await manager.create(True, command, additional_packages=additional_packages)
            return True
        except RuntimeError as e:
            error_message = f"Error: {str(e)}"
            if ui_setup:
                ui_setup.update_output_text(f"{error_message}\n")
            print(error_message)
            return False

    def run_async():
        success = asyncio.run(run())
        if ui_setup:
            status_message = (
                "Ephemeral command completed successfully.\n"
                if success
                else "Ephemeral command failed. Check the output for errors.\n"
            )
            ui_setup.update_output_text(status_message)
        if on_complete:
            on_complete(success)  # Call the callback with the success status

    run_async()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    text_box = QTextEdit()
    text_box.show()

    run_ephemeral_command(
        "sudo apt-get update -y && sudo apt-get install neofetch -y && neofetch",
        text_box,
    )

    exit_code = app.exec()
    sys.exit(exit_code)
