import logging
from logging.handlers import RotatingFileHandler

LOGGER = logging.getLogger()  # If later on we want to ignore the default log messages, we can add a name here...
LOGGER.setLevel(logging.DEBUG)

log_file = '/code/logs/mocker-hub.log'
max_log_size = 5 * 1024 * 1024
backup_count = 3

rotating_handler = RotatingFileHandler(
    log_file, maxBytes=max_log_size, backupCount=backup_count
)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
rotating_handler.setFormatter(formatter)

LOGGER.addHandler(rotating_handler)