import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(name, log_dir="/var/log", level=logging.INFO):
    # environment = os.getenv("ENVIRONMENT", "prod")
    # default_log_dir = "/var/log/logs"
    # log_dir = os.getenv("LOG_DIR", default_log_dir)
    # log_dir = default_log_dir if environment != "test" else f"{default_log_dir}_test"
    log_file_path = os.path.join(log_dir, f"{name}.log")
    handler = RotatingFileHandler(
        log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger
