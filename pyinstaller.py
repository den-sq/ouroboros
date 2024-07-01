# Builds the backend into a single executable file using PyInstaller,
# allowing it to be packaged into the electron app.
# Usage: poetry install and poetry run build-cli-executable or poetry run build-server-executable

# To create a new spec file:
# CURRENT_PATH = Path(__file__).parent.absolute()
# path_to_main = str(CURRENT_PATH / "ouroboros" / "main-name.py")
# PyInstaller.__main__.run([path_to_main, "--onefile", "-n", OUTPUT_NAME])
# Output: ./dist/OUTPUT_NAME

import PyInstaller.__main__


def build_cli_executable():
    PyInstaller.__main__.run(["cli.spec"])


def build_server_executable():
    PyInstaller.__main__.run(["server.spec"])
