import logging, os, yaml
from photoprism_api import PhotoprismApi
import image_utils
from config import Config

from watchdog.events import FileSystemEventHandler

class AlbumHandler(FileSystemEventHandler):
    def __init__(self, config: Config):
        self.config = config
        self.pp_api = PhotoprismApi(config.username, config.password, config.base_url)

    def on_modified(self, event) -> None:
        log.debug(f"File {event.src_path} modified.")
        log.debug(f"Event type: {event.event_type}")
        try:
            album_file_has_changed = not event.is_directory and event.src_path == self.album_path;
            if album_file_has_changed:
                log.info("Album file changed, updating photos...")

                # Get current set of photo UIDs from album data only if 'Hidden' is false
                photos_in_album = get_photos_in_album_yaml(self.config.album_path)

                # Get all photos in cache folder
                photos_in_cache = get_photos_in_cache(self.config.cache_path)

                # Download new photos
                new_photos = photos_in_album - photos_in_cache
                for uid in new_photos:
                    download_photo_in_cache(uid, self.pp_api, self.config.cache_path)

                # Remove deleted photos
                deleted_photos = photos_in_cache - photos_in_album
                for uid in deleted_photos:
                    remove_photo_from_cache(uid, self.config.cache_path)

        except Exception as e:
            log.error(e)
    
    
def load_album_yaml(album_path: str) -> dict:
    with open(album_path) as f:
        album_data = yaml.safe_load(f)
    return album_data

def get_photos_in_cache(cache_path: str) -> set:
    photos_in_cache = set()
    for _, _, files in os.walk(cache_path):
        for file in files:
            if "index" not in file:
                photos_in_cache.add(os.path.splitext(file)[0])

def get_photos_in_album_yaml(album_path: str) -> set:
    album_data = load_album_yaml(album_path)              

    # Get current set of photo UIDs from album data only if 'Hidden' is false
    return {
        photo["UID"]
        for photo in album_data["Photos"]
        if not photo.get("Hidden", False)
    }

def download_photo_in_cache(uid: str, pp_api: PhotoprismApi, path: str):  
    filename = pp_api.download_photo(uid=uid, download_path=path)

    # Repair exif data
    filename = image_utils.repair_exif(filename)

    # Fetch taken_at from server and update exif if necessary
    photo_data = pp_api.get_photo_data(uid)
    taken_at_from_server = photo_data.get("TakenAt", "")
    filename = image_utils.update_exif(filename, taken_at_from_server)

    image_utils.resize_image(filename, 1920)

def remove_photo_from_cache(uid: str, cache_path: str):
    # Find file in photo_set with matching UID
    match = set(
        filter(lambda x: x.startswith(uid), os.listdir(cache_path))
    )
    if len(match) > 0:
        filename = os.path.join(cache_path, match.pop())
        if os.path.exists(filename):
            log.info(f"Removing {filename}")
            os.remove(filename)

log = logging.getLogger()