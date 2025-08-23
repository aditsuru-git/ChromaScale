import time
import os
import configparser
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from queue import Queue
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.upscaler import ImageUpscaler

# --- Configuration ---
WORK_DIR = Path.home() / ".chromascale_home"
CONFIG_PATH = WORK_DIR / "src" / "settings.ini"
LOG_FILE_PATH = WORK_DIR / "chromascale.log"
BATCH_INTERVAL = 1.0  # seconds

def setup_logging():
    """Configures logging to a rotating file and to the console."""
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    stream_handler = logging.StreamHandler()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


class DebouncedHandler(FileSystemEventHandler):
    """Waits for file writes to stabilize before queuing."""
    def __init__(self, queue):
        self.queue = queue
        self.pending_files = {}

    def on_created(self, event):
        if event.is_directory:
            return
        src_path_str = event.src_path.lower()
        if not src_path_str.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
            return
        self.pending_files[event.src_path] = time.time()

    def get_ready_files(self):
        ready = []
        now = time.time()
        for path, t in list(self.pending_files.items()):
            if now - t >= BATCH_INTERVAL and is_file_ready(path):
                ready.append(path)
                del self.pending_files[path]
        return ready

def is_file_ready(path, wait=0.5):
    """Checks if a file has stopped growing in size."""
    try:
        initial_size = os.path.getsize(path)
        time.sleep(wait)
        return os.path.exists(path) and os.path.getsize(path) == initial_size
    except FileNotFoundError:
        return False

def worker(queue, upscaler, replace_file, output_dir):
    """Processes images from the queue."""
    while True:
        img_path = queue.get()
        try:
            input_path = Path(img_path)
            if replace_file:
                output_path = input_path
            else:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                output_path = Path(output_dir) / input_path.name
            
            logging.info(f"Processing started: {output_path.name}")
            upscaler.upscale_image(str(input_path), str(output_path))
            logging.info(f"Job finished: {output_path.name}")

        except Exception as e:
            logging.error(f"Job failed for '{img_path}': {e}", exc_info=True)
        finally:
            queue.task_done()

def main():
    setup_logging()
    logging.info("--- ChromaScale Watcher Service Starting ---")
    
    config = configparser.ConfigParser()
    if not CONFIG_PATH.exists():
        logging.error(f"CRITICAL: Configuration file not found at {CONFIG_PATH}")
        return
    config.read(CONFIG_PATH)

    try:
        input_dir = config["paths"]["input_dir"]
        output_dir = config["paths"]["output_dir"]
        replace_file = config.getboolean("paths", "replace_file")
    except KeyError as e:
        logging.error(f"CRITICAL: Missing key in settings.ini: {e}.")
        return

    if not input_dir or not Path(input_dir).is_dir():
        logging.error(f"CRITICAL: Input directory '{input_dir}' does not exist or is not set.")
        return

    # CORRECTED: The model path is in the WORK_DIR root, not inside src.
    model_path = WORK_DIR / "RealESRGAN_x4plus.pth"
    upscaler = ImageUpscaler(str(model_path))
    
    queue = Queue()
    Thread(target=worker, args=(queue, upscaler, replace_file, output_dir), daemon=True).start()

    event_handler = DebouncedHandler(queue)
    observer = Observer()
    observer.schedule(event_handler, input_dir, recursive=False)
    observer.start()
    logging.info(f"--- Watching '{input_dir}' for new images ---")

    try:
        while True:
            ready_files = event_handler.get_ready_files()
            for file in ready_files:
                logging.info(f"Job accepted: {Path(file).name}")
                queue.put(file)
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical("A fatal exception occurred in main", exc_info=True)