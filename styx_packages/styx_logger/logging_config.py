import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(name, log_dir="/var/log", level=logging.INFO):
    log_file_path = os.path.join(log_dir, f"{name}.log")
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[%(funcName)s:%(lineno)d] - %(message)s"
    )

    file_handler.setFormatter(formatter)

    # Stream handler for stdout
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stdout_handler)
    return logger
