# Ouroboros

`or-uh-bore-us`

Quickly extract ROIs from cloud-hosted medical scans.

This repository is a monorepo containing the code for the Ouroboros app and the Ouroboros Python package (`python` folder). 

For a usage guide, check out the [Documentation](https://wegold.me/ouroboros/).

# Quick Start

There are prebuilt applications available in [Releases](https://github.com/We-Gold/ouroboros/releases).

- Windows: `*-setup.exe`
- Mac: `*.dmg`
- Linux: Multiple options available

When you open the app, the GUI will open immediately, but **the local server that runs the processing could take up to 15 seconds to start**. There is an indicator in the GUI that shows if the server is connected.

Currently, none of the apps are notarized. 

For Mac, if an error occurs when you try to run the app, find the app installation (should be called `ouroboros.app`) and run `xattr -d com.apple.quarantine ouroboros.app`. 

# Development Quick Start

Ouroboros has two main components:

- Python package (`python` folder within repository)
- Electron app (main repository)

These two components are packaged together when the app is built, but in development mode, they are run separately. 

The Python package and the Electron app have separate setup steps which are listed below. Before you begin, **it is recommended that you open the Python package (`python` folder) in a separate VSCode window whenever you are running or writing Python code** (one window for the Electron app and one window for Python).

**Before you begin, `git clone` the project locally.**

## Electron Setup

VScode Setup: [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint) & [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)

### 1. Install Node.js and NPM

If you don't already have them installed, follow the instructions at the following link: https://nodejs.org/en/download/

### 2. Install Dependencies

```bash
$ npm install
```

### 3. Run Electron App In Development Mode

```bash
$ npm run dev
```

## Python Setup

The following steps are here to streamline the setup process for Python. For more advanced development, like testing PyInstaller, or if you encounter any issues, you may need to follow the instructions available in the [Python README](./python/README.md).

### 1. Install Python

Due to some Python dependencies, it is highly recommended that the default Python installation for the system is `3.10`.

**Easy Installation**

Download and install Python `3.10` from their website: https://www.python.org/downloads/.

**Advanced Installation**

If you use [pyenv](https://github.com/pyenv/pyenv) or a similar Python version manager, install `3.10` and set it to be the global default.

If you don't make it the global version, you'll need to use `poetry env use 3.10` later to set the Python version before running `poetry install`. 

_Example:_

```
pyenv install 3.10
pyenv global 3.10
```

I recommend following the instructions below first if you want to be able to compile the Python server using PyInstaller:

https://stackoverflow.com/questions/60917013/how-to-build-python-with-enable-framework-enable-shared-on-macos

### 2. Install Poetry and Dependencies

[Poetry](https://python-poetry.org/) is the Python project and dependency manager used for the Ouroboros Python package.

Follow the instructions on the following page to install Poetry on your system: https://python-poetry.org/docs/#installing-with-the-official-installer

**Before you continue, it is recommended that you open the Python folder (`python`) of the project in a separate window in VSCode.**

**It is also usually easier to run the setup commands in the VSCode integrated terminal, which can be opened with `CMD/CTRL + J`.**

Configure Poetry to install the virtual environment in the project folder. This allows VSCode to detect the virtual environment.

```
poetry config virtualenvs.in-project true
```

Install the project dependencies. **Make sure the terminal is in the `python` folder before running this command.**

```
poetry install
```

Now kill the current terminal and open a new one, and it should indicate that it is using the local virtual environment for Ouroboros. If not, you can run `poetry shell` to activate the shell in the current terminal.

Poetry makes it easier to run the built-in CLI or server with the following commands:

- `ouroboros-cli` - Runs the CLI in the current folder. Use `--help` to learn more.

- `ouroboros-server` - Runs the server that communicates with the Electron app.


## Running the App in Development Mode

In the Electron VSCode window, run `npm run dev` to start the Electron app. 

In the Python VSCode window, run `ouroboros-server` to start the server.

These two components should automatically talk to each other, and the server connection component in the app should indicate this.