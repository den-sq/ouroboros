# syntax=docker/dockerfile:1

FROM thehale/python-poetry:1.8.3-py3.10-slim as python-base

RUN apt-get update -y
RUN apt-get install gcc -y

COPY poetry.lock pyproject.toml ./
COPY ./ouroboros ./ouroboros
COPY ./README.md ./README.md
COPY ./pyinstaller.py ./pyinstaller.py

RUN poetry install

CMD ["poetry", "run", "ouroboros-docker-server"]