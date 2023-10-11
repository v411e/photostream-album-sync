import logging, yaml
from photoprism_api import PhotoprismApi
from config import Config
from cache import Cache

from watchdog.events import FileSystemEventHandler


class AlbumHandler(FileSystemEventHandler):
    def __init__(self, config: Config):
        self.config = config

    def on_modified(self, event) -> None:
        log.debug(f"File {event.src_path} modified.")
        log.debug(f"Event type: {event.event_type}")
        try:
            album_file_has_changed = (
                not event.is_directory and event.src_path == self.config.album_path
            )
            if album_file_has_changed:
                log.info("Album file changed, updating photos...")
                pp_api = PhotoprismApi(
                    username=self.config.username,
                    password=self.config.password,
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                )
                cache = Cache(path=self.config.cache_path)

                # Get current set of photo UIDs from album data only if 'Hidden' is false
                photos_in_album = get_photos_in_album_yaml(self.config.album_path)

                # Get all photos in cache folder
                photos_in_cache = cache.get_photos()

                # Download new photos
                new_photos = photos_in_album - photos_in_cache
                for uid in new_photos:
                    cache.download_photo(uid, pp_api)

                # Remove deleted photos
                deleted_photos = photos_in_cache - photos_in_album
                for uid in deleted_photos:
                    cache.remove_photo(uid)

                log.info("Done updating photos.")

        except Exception as e:
            log.error(e)


def load_album_yaml(album_path: str) -> dict:
    with open(album_path) as f:
        album_data = yaml.safe_load(f)
    return album_data


def get_photos_in_album_yaml(album_path: str) -> set:
    album_data = load_album_yaml(album_path)

    # Get current set of photo UIDs from album data only if 'Hidden' is false
    return {
        photo["UID"] for photo in album_data["Photos"] if not photo.get("Hidden", False)
    }


log = logging.getLogger()
