import logging
import sys
import datetime

from architecture.singleton import Singleton


class CustomLogger(metaclass=Singleton):
    """logger class which creates logging class object"""

    def __init__(self):
        self.custom_logger = logging.getLogger(__name__)
        self.custom_logger.setLevel(logging.DEBUG)

        # Get the current date and time
        now = datetime.datetime.now()
        current_datetime = now.strftime("%Y_%m_%d_%H_%M_%S")

        # Create a file handler with log file name including current date and time
        log_file = f"log/app_{current_datetime}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        log_formatter = logging.Formatter(
            "[%(asctime)s] - [%(levelname)s] - [%(filename)s:%(lineno)d] - %(message)s"
        )
        file_handler.setFormatter(log_formatter)

        # Create a stream handler for printing logs to the console
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(log_formatter)

        # Add both handlers to the logger
        self.custom_logger.addHandler(file_handler)
        self.custom_logger.addHandler(stream_handler)


logger = CustomLogger().custom_logger

if __name__ == "__main__":
    logger.debug("debug log")
    logger.info("info log")
    logger.warning("warn log")
    logger.error("error log")
    logger.exception("exception log")
