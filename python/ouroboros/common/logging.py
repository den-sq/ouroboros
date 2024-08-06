import logging

server_logger = logging.getLogger("uvicorn")

DEFAULT_LOGGER = server_logger


def get_logger():
    return DEFAULT_LOGGER


def get_server_logger():
    return server_logger
