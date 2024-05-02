
import logging
from dotenv import load_dotenv
import os

def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # setting the log file
    load_dotenv()
    LOG_FILE = os.getenv("LOG_FILE_PATH")
    f_handler = logging.FileHandler(LOG_FILE)
    f_handler.setLevel(logging.INFO)  # set log level to INFO
    # setting the format of logs
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)
    return logger