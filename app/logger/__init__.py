import logging
import sys
import datetime
import os

from app.architecture.singleton import Singleton


class CustomLogger(metaclass=Singleton):
    """logger class which creates logging class object"""

    def __init__(self, enable_file_logging: bool = False):
        log_formatter = logging.Formatter(
            "[%(asctime)s] - [%(levelname)s] - [%(filename)s:%(lineno)d] - %(message)s"
        )
        self.custom_logger = logging.getLogger(__name__)
        self.custom_logger.setLevel(logging.DEBUG)
        # Create a stream handler for printing logs to the console
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(log_formatter)
        self.custom_logger.addHandler(stream_handler)
        self.file_logging() if enable_file_logging else None

    def file_logging(self):
        # Useful to save logs in log file when log stream is not available

        now = datetime.datetime.now()
        current_datetime = now.strftime("%Y_%m_%d_%H_%M_%S")
        # Create a file handler with log file name including current date and time
        log_file = f"log/app_{current_datetime}.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_formatter)
        # Add both handlers to the logger
        self.custom_logger.addHandler(file_handler)


logger = CustomLogger().custom_logger

if __name__ == "__main__":
    logger.debug("debug log")
    logger.info("info log")
    logger.warning("warn log")
    logger.error("error log")
    logger.exception("exception log")
