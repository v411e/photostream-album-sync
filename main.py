import logging, os, yaml, time
from photoprism_api import PhotoprismApi
import image_utils

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class AlbumHandler(FileSystemEventHandler):
    def __init__(
        self,
        base_url: str,
        album_path: str,
        cache_path: str,
        username: str,
        password: str,
    ):
        self.base_url = base_url
        self.album_path = album_path
        self.cache_path = cache_path
        self.username = username
        self.password = password
        self.pp_api = PhotoprismApi(self.username, self.password, self.base_url)

    def on_modified(self, event) -> None:
        log.debug(f"File {event.src_path} modified.")
        log.debug(f"Event type: {event.event_type}")
        try:
            if not event.is_directory and event.src_path == self.album_path:
                log.info("Album file changed, updating photos...")
                with open(self.album_path) as f:
                    album_data = yaml.safe_load(f)

                # Get current set of photo UIDs from album data only if 'Hidden' is false
                current_photos = {
                    photo["UID"]
                    for photo in album_data["Photos"]
                    if not photo.get("Hidden", False)
                }

                # Get list of all photos in cache folder
                photo_set = set()
                for _, _, files in os.walk(self.cache_path):
                    for file in files:
                        if "index" not in file:
                            photo_set.add(os.path.splitext(file)[0])

                # Download new photos
                new_photos = current_photos - photo_set
                for uid in new_photos:
                    filename = self.pp_api.download_photo(uid=uid, cache_path=self.cache_path)
                    filename = image_utils.repair_exif(filename)

                    # Fetch taken_at from server and update exif if necessary
                    photo_data = self.pp_api.get_photo_data(uid)
                    taken_at_from_server = photo_data.get("TakenAt", "")
                    filename = image_utils.update_exif(filename, taken_at_from_server)

                    image_utils.resize_image(filename, 1920)

                # Remove deleted photos
                deleted_photos = photo_set - current_photos
                for uid in deleted_photos:
                    # Find file in photo_set with matching UID
                    match = set(
                        filter(lambda x: x.startswith(uid), os.listdir(cache_path))
                    )
                    if len(match) > 0:
                        filename = os.path.join(cache_path, match.pop())
                        if os.path.exists(filename):
                            log.info(f"Removing {filename}")
                            os.remove(filename)

        except Exception as e:
            log.error(e)


if __name__ == "__main__":
    # read config from environment variables
    base_url = os.environ.get("PPSYNC_BASE_URL")
    album_path = os.environ.get("PPSYNC_ALBUM_PATH", "")
    cache_path = os.environ.get("PPSYNC_CACHE_PATH", "")
    username = os.environ.get("PPSYNC_USERNAME")
    password = os.environ.get("PPSYNC_PASSWORD")

    # check if config is valid
    if not base_url or not album_path or not cache_path or not username or not password:
        raise ValueError("Please set all environment variables.")

    # setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log = logging.getLogger()

    # start watching album file for changes
    event_handler = AlbumHandler(base_url, album_path, cache_path, username, password)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(album_path), recursive=False)
    observer.start()
    log.info(f"Watching album file {album_path} for changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
