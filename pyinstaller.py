# Builds the backend into a single executable file using PyInstaller,
# allowing it to be packaged into the electron app.
# Usage: poetry install && poetry run build-executable

OUTPUT_NAME = "cli"

# Output: ./dist/OUTPUT_NAME

import PyInstaller.__main__
from pathlib import Path

CURRENT_PATH = Path(__file__).parent.absolute()
path_to_main = str(CURRENT_PATH / "ouroboros" / "cli.py")


def install():
    PyInstaller.__main__.run(["cli.spec"])
    # PyInstaller.__main__.run([path_to_main, "--onefile", "-n", OUTPUT_NAME, "cli.spec"])
