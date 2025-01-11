import logging
from logging.handlers import RotatingFileHandler
import os
import sys

LOGGER = logging.getLogger()  # If later on we want to ignore the default log messages, we can add a name here...
LOGGER.setLevel(logging.DEBUG)

log_file = '/code/logs/mocker-hub.log'
max_log_size = 5 * 1024 * 1024
backup_count = 3

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# TODO: We probably want to include logging to file in integration tests, should
# we ever test ES<->Server. I'm not sure how to do that though.
if os.getenv('mocker_hub_TEST_ENV') is None:
    # Log to file.

    rotating_handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=backup_count)
    rotating_handler.setFormatter(formatter)
    LOGGER.addHandler(rotating_handler)

    # Log to stdout.

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    LOGGER.addHandler(console_handler)