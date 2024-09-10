import os
import subprocess

class MakeHandler:
    def __init__(self, directory: str):
        if not os.path.isdir(directory):
            raise NotADirectoryError(f"{directory} is not a valid directory")
        self.directory = directory

    def run_make(self, target: str = ""):
        original_directory = os.getcwd()
        try:
            os.chdir(self.directory)
            cmd = ["make"]
            if target:
                cmd.append(target)
            result = subprocess.run(cmd, capture_output=True, text=True)
            result.check_returncode()  # Raises CalledProcessError if the command exited non-zero
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error running make: {e.stderr}")
        finally:
            os.chdir(original_directory)

# Example usage
if __name__ == "__main__":
    make_handler = MakeHandler(os.path.abspath("../../.workspace"))
    make_handler.run_make()  # Runs "make" with no specific target
    make_handler.run_make("clean")  # Runs "make clean"