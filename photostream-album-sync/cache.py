import os, logging
import image_utils
from sync_api import SyncApi

class Cache:
    def __init__(self, path: str):
        self.path = path

    def download_photo(self, uid: str, sync_api: SyncApi):
        filename = sync_api.download_photo(uid=uid, download_path=self.path)

        # Repair exif data
        filename = image_utils.repair_exif(filename)

        # Fetch taken_at from server and update exif if necessary
        taken_at_from_server = sync_api.get_taken_at(uid)
        filename = image_utils.update_exif(filename, taken_at_from_server)

        image_utils.resize_image(filename, 1920)

    def remove_photo(self, uid: str):
        # Find file in photo_set with matching UID
        match = set(filter(lambda x: x.startswith(uid), os.listdir(self.path)))
        if len(match) > 0:
            filename = os.path.join(self.path, match.pop())
            if os.path.exists(filename):
                log.info(f"Removing {filename}")
                os.remove(filename)

    def get_photos(self) -> set:
        photos_in_cache = set()
        for _, _, files in os.walk(self.path):
            for file in files:
                if "index" not in file:
                    photos_in_cache.add(os.path.splitext(file)[0])
        return photos_in_cache


log = logging.getLogger()