from datetime import datetime
import time
import os
import logging
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver
from elasticsearch_dsl import connections
from event import Event, EventLevel

# Configure logging.

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

polling_interval = 5

# Connect to ElasticSearch.

logging.info("Connecting to ElasticSearch...")
try:
    hostname = os.getenv("ES_HOST", "elasticsearch:9200")
    connections.create_connection(hosts=[f"http://{hostname}"])
    Event.init()
    logging.info("Connected to ElasticSearch!")
except Exception as e:
    logging.error(f"Failed to connect to ElasticSearch: {str(e)}", exc_info=False)
    exit(1)

def send_log_to_es(log_line: str):
    """
    Send a single log entry (a single line) to ElasticSearch.
    The line should have the following format:
            `{datetime} - {level} - {text}`
    """

    parts = log_line.split(" - ", 2)
    if len(parts) < 3:
        # logging.warning(f"Incorrect log format for line: {log_line}")
        return
    
    date_time = parts[0].strip()
    level = parts[1].strip().lower()
    text = parts[2].strip()

    try:
        date_time = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S,%f')
        level = EventLevel(level)
    except ValueError as e:
        # logging.error(f"Error parsing log line: {log_line} - {e}")
        return

    logging.info(f"Sending log to Elasticsearch: {log_line}")
    event = Event(date_time=date_time, log_level=level.value, text_content=text)
    event.save()

def send_new_logs_to_es(new_content: str):
    lines = new_content.split('\n')
    for line in lines:
        l = line.strip()
        if len(l) == 0:
            continue
        
        send_log_to_es(line)

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, file_path):
        self.file_path = file_path
        self.size_file_path = self.file_path + '.meta'
        self.previous_size = self.load_previous_size()

    def load_previous_size(self):
        if os.path.exists(self.size_file_path):
            try:
                with open(self.size_file_path, 'r') as size_file:
                    val = int(size_file.read().strip())
                    logging.info(f"Continuing file {self.file_path} from {val}")
                    return val
            except Exception as e:
                logging.error(f"Error reading size file: {e}. Starting from 0.")
        return 0

    def save_previous_size(self):
        try:
            with open(self.size_file_path, 'w') as size_file:
                size_file.write(str(self.previous_size))
        except Exception as e:
            logging.error(f"Error writing size file: {e}")

    def on_modified(self, event):
        if event.src_path == self.file_path:
            current_size = os.path.getsize(self.file_path)

            if self.previous_size > current_size:
                logging.warning(f"Irregularity in log size: want ({self.previous_size}) but ({current_size}). Rewinding...")
                self.previous_size = 0
                self.save_previous_size()
                
            if current_size >= self.previous_size:
                with open(self.file_path, 'r') as file:
                    file.seek(self.previous_size)
                    new_content = file.read()
                    send_new_logs_to_es(new_content)
                self.previous_size = current_size
                self.save_previous_size()

def monitor_file(file_path):
    event_handler = FileChangeHandler(file_path)
    observer = PollingObserver(timeout=polling_interval)
    observer.schedule(event_handler, os.path.dirname(file_path), recursive=False)
    observer.start()
    
    logging.info(f"Monitoring changes in {file_path}...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    except Exception as e:
        logging.error(f"Error in monitoring file: {e}")
    
    observer.join()

if __name__ == "__main__":
    file_path_to_monitor = '/logs/mocker-hub.log'
    
    if not os.path.exists(file_path_to_monitor):
        logging.error(f"File {file_path_to_monitor} does not exist. Exiting.")
        exit(1)

    monitor_file(file_path_to_monitor)