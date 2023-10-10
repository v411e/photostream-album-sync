import logging, os, time
from photoprism_album_handler import AlbumHandler
from config import Config
from watchdog.observers import Observer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger()

if __name__ == "__main__":
    config = Config()

    match config.sync_type:
        case "photoprism":
            # start watching album file for changes
            event_handler = AlbumHandler(config)
            observer = Observer()
            observer.schedule(event_handler, path=os.path.dirname(config.album_path), recursive=False)
            observer.start()
            log.info(f"Watching album file {config.album_path} for changes...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()
