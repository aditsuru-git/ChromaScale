import time
import os
from pathlib import Path
from queue import Queue
from threading import Thread, Lock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.upscaler import ImageUpscaler

CONFIG_PATH = Path(__file__).parent / "settings.ini"
BATCH_INTERVAL = 1.0  # seconds to batch events

class DebouncedHandler(FileSystemEventHandler):
    """Collects new files and debounces rapid events."""
    def __init__(self, queue):
        self.queue = queue
        self.lock = Lock()
        self.pending_files = {}  # path -> last event time

    def on_created(self, event):
        if event.is_directory:
            return
        if not event.src_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
            return
        with self.lock:
            self.pending_files[event.src_path] = time.time()

    def get_ready_files(self):
        """Return files that have stabilized in size."""
        ready = []
        now = time.time()
        with self.lock:
            for path, t in list(self.pending_files.items()):
                if now - t >= BATCH_INTERVAL and is_file_ready(path):
                    ready.append(path)
                    del self.pending_files[path]
        return ready

def is_file_ready(path, wait=0.5):
    """Check if file is fully written."""
    try:
        initial = os.path.getsize(path)
        time.sleep(wait)
        return os.path.exists(path) and os.path.getsize(path) == initial
    except FileNotFoundError:
        return False

def worker(queue, upscaler, replace_file, output_dir):
    """Process images from the queue."""
    while True:
        img_path = queue.get()
        try:
            input_path = Path(img_path)
            if replace_file:
                output_path = input_path
            else:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                output_path = Path(output_dir) / input_path.name

            upscaler.upscale_image(str(input_path), str(output_path))
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
        finally:
            queue.task_done()

def main():
    import configparser

    # Load settings
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    input_dir = config["paths"]["input_dir"]
    output_dir = config["paths"]["output_dir"]
    replace_file = config.getboolean("paths", "replace_file")

    # Initialize upscaler
    model_path = Path(__file__).parent / "RealESRGAN_x4plus.pth"
    upscaler = ImageUpscaler(str(model_path))

    # Queue and worker thread
    queue = Queue()
    thread = Thread(target=worker, args=(queue, upscaler, replace_file, output_dir), daemon=True)
    thread.start()

    # Watch folder
    event_handler = DebouncedHandler(queue)
    observer = Observer()
    observer.schedule(event_handler, input_dir, recursive=False)
    observer.start()
    print(f"Watching {input_dir} for new images...")

    try:
        while True:
            # Collect ready files and add to queue
            ready_files = event_handler.get_ready_files()
            for file in ready_files:
                queue.put(file)
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
