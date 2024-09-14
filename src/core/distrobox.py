import asyncio
import os
import shutil
import sys

from PyQt6.QtCore import QThread, pyqtSignal, QObject, QEventLoop, pyqtSlot
from PyQt6.QtWidgets import QApplication, QTextEdit

from core.dependency_utils import install_packages


class Worker(QThread):
    update_text = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, command: str, directory="."):
        super().__init__()
        self.command = command
        self.directory = directory

    def run(self):
        asyncio.run(self._async_run())

    async def _async_run(self):
        process = await asyncio.create_subprocess_shell(
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
            stream_output(process.stdout),
            stream_output(process.stderr),
        )
        await process.wait()
        self.finished_signal.emit()


class DistroboxManager(QObject):
    def __init__(
        self,
        box_name: str,
        image: str = "ubuntu:latest",
        text_box: QTextEdit = None,
        directory: str = ".",
    ):
        super().__init__()
        self.text_box = text_box
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
        if self.text_box:  # Ensure text_box is set before connecting signals
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

        print(create_command)

        loop = QEventLoop()
        self.worker = Worker(command=create_command, directory=self.directory)
        self.worker.update_text.connect(self.append_text)
        self.worker.finished_signal.connect(loop.quit)
        self.worker.start()
        loop.exec()  # Wait until the worker finishes

        if not self.worker.isFinished():
            raise RuntimeError(
                f"Failed to create Distrobox container '{self.box_name}'."
            )

        self.created = True

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
        if self.text_box:
            self.text_box.append(text)

    @pyqtSlot()
    def worker_finished(self):
        """Handle worker finish signal."""
        print("Worker thread has finished execution.")


def run_ephemeral_command(
    command: str,
    textbox: QTextEdit = None,
    directory=".",
    additional_packages: list = None,
):
    async def run():
        manager = DistroboxManager(
            "ephemeral_runner", text_box=textbox, directory=directory
        )
        await manager.create(True, command, additional_packages=additional_packages)
        # Create an event loop to keep the application running until the worker finishes
        loop = QEventLoop()
        manager.worker.finished_signal.connect(loop.quit)
        loop.exec()

    # Run the async function using asyncio.run()
    asyncio.run(run())


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
