import time
import os
import configparser
import logging
import shutil
import cv2
from logging.handlers import RotatingFileHandler
from pathlib import Path
from queue import Queue
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.upscaler import ImageUpscaler

# --- (All functions up to 'worker' are the same) ---
WORK_DIR = Path.home() / ".chromascale_home"
CONFIG_PATH = WORK_DIR / "src" / "settings.ini"
LOG_FILE_PATH = WORK_DIR / "chromascale.log"
BATCH_INTERVAL = 1.0

def setup_logging():
    file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=5 * 1024 * 1024, backupCount=3)
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers(): logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

class DebouncedHandler(FileSystemEventHandler):
    def __init__(self, queue): self.queue = queue; self.pending_files = {}
    def on_created(self, event):
        if event.is_directory: return
        src_path_str = event.src_path.lower()
        if not src_path_str.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")): return
        self.pending_files[event.src_path] = time.time()
    def get_ready_files(self):
        ready = []; now = time.time()
        for path, t in list(self.pending_files.items()):
            if now - t >= BATCH_INTERVAL and is_file_ready(path):
                ready.append(path); del self.pending_files[path]
        return ready

def is_file_ready(path, wait=0.5):
    try:
        initial_size = os.path.getsize(path); time.sleep(wait)
        return os.path.exists(path) and os.path.getsize(path) == initial_size
    except FileNotFoundError: return False

# --- CORRECTED WORKER FUNCTION ---
def worker(queue, upscaler, replace_file, output_dir, skip_threshold):
    """Processes images from the queue with robust replace and skip logic."""
    while True:
        img_path = queue.get()
        try:
            input_path = Path(img_path)
            
            image = cv2.imread(str(input_path))
            if image is None:
                logging.warning(f"Could not read image file, skipping: {input_path.name}")
                continue
            
            height, width, _ = image.shape
            
            if width > skip_threshold or height > skip_threshold:
                logging.info(f"Skipping upscale for '{input_path.name}' (resolution {width}x{height} exceeds threshold of {skip_threshold}px).")
                if not replace_file:
                    new_stem = f"{input_path.stem}(already_high_res)"
                    new_name = f"{new_stem}{input_path.suffix}"
                    destination_path = Path(output_dir) / new_name
                    Path(output_dir).mkdir(parents=True, exist_ok=True)
                    shutil.move(img_path, destination_path)
                    logging.info(f"Moved original file to: {destination_path}")
                else:
                    logging.info("Leaving original file in place due to replace_file=True setting.")
                continue

            # --- ROBUST UPSCALING LOGIC ---
            if replace_file:
                # Use a temporary file for the output to avoid race conditions
                temp_output_path = input_path.parent / f"{input_path.stem}.tmp{input_path.suffix}"
                try:
                    logging.info(f"Processing started (in-place): {input_path.name}")
                    upscaler.upscale_image(str(input_path), str(temp_output_path))
                    # Atomically replace the original with the upscaled version
                    shutil.move(str(temp_output_path), str(input_path))
                    logging.info(f"Job finished (in-place): {input_path.name}")
                finally:
                    # Ensure the temp file is cleaned up if it still exists
                    if temp_output_path.exists():
                        os.remove(temp_output_path)
            else:
                # Standard behavior: save to output directory
                output_path = Path(output_dir) / input_path.name
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                logging.info(f"Processing started: {output_path.name}")
                upscaler.upscale_image(str(input_path), str(output_path))
                logging.info(f"Job finished: {output_path.name}")

        except Exception as e:
            logging.error(f"Job failed for '{img_path}': {e}", exc_info=True)
        finally:
            queue.task_done()

# --- (main function remains the same) ---
def main():
    setup_logging()
    logging.info("--- ChromaScale Watcher Service Starting ---")
    config = configparser.ConfigParser()
    if not CONFIG_PATH.exists():
        logging.error(f"CRITICAL: Configuration file not found at {CONFIG_PATH}"); return
    config.read(CONFIG_PATH)
    try:
        input_dir = config["paths"]["input_dir"]
        output_dir = config["paths"]["output_dir"]
        replace_file = config.getboolean("paths", "replace_file", fallback=False)
        device_mode = config.get("paths", "device_mode", fallback="auto")
        skip_threshold = config.getint("paths", "skip_resolution_threshold", fallback=2000)
    except KeyError as e:
        logging.error(f"CRITICAL: Missing key in settings.ini: {e}."); return
    if not input_dir or not Path(input_dir).is_dir():
        logging.error(f"CRITICAL: Input directory '{input_dir}' does not exist or is not set."); return
    model_path = WORK_DIR / "RealESRGAN_x4plus.pth"
    upscaler = ImageUpscaler(str(model_path), device_mode)
    queue = Queue()
    Thread(target=worker, args=(queue, upscaler, replace_file, output_dir, skip_threshold), daemon=True).start()
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
    try: main()
    except Exception as e: logging.critical("A fatal exception occurred in main", exc_info=True)