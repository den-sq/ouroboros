import logging

server_logger = logging.getLogger("uvicorn")

# Primary export, import this from other modules
logger = server_logger
