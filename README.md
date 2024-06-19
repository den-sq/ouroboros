# Ourobors Python Package

This python package organizes all of the core functionality of the Ouroboros segmentation pipeline.

### Development

[Poetry](https://python-poetry.org/) is the virtual environment and dependency manager for this project.

`poetry install` - install all dependencies of this project into a local virtual environment
`poetry add [package]` - add a new dependency to the project
`poetry run [file.py]` - run a python file locally without activating the virtual environment
`poetry shell` - active the virtual environment in this shell

**To have VSCode recognize the poetry venv, follow these instructions:**

You just need to type in your shell:

```bash
poetry config virtualenvs.in-project true
```

The virtualenv will be created inside the project path and vscode will recognize. Consider adding this to your .bashrc or .zshrc.

If you already have created your project, you need to re-create the virtualenv to make it appear in the correct place:

```bash
poetry env list  # shows the name of the current environment
poetry env remove <current environment>
poetry install  # will create a new environment using your updated configuration
```

Instructions From: https://stackoverflow.com/questions/59882884/vscode-doesnt-show-poetry-virtualenvs-in-select-interpreter-option


### Testing

In VSCode, use the testing tab. Otherwise, use `pytest` or `pytest --benchmark-only`.