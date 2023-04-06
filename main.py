import datetime
import logging
import os
import yaml
import requests
import time
from PIL import Image
import exiftool

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

        self.session_id = self.get_session_id()
        self.download_token = self.get_download_token()

    # Get session ID from API
    def get_session_id(self) -> str:
        auth_url = f"{self.base_url}/api/v1/session"
        response = requests.post(
            auth_url, json={"username": self.username, "password": self.password}
        )
        json_response = response.json()
        session_id = json_response.get("id")
        log.info("Got session ID.")
        return session_id

    # Get download token from API
    def get_download_token(self) -> str:
        config_url = f"{self.base_url}/api/v1/config"
        response = requests.get(config_url, headers={"X-Session-ID": self.session_id})
        json_response = response.json()
        return json_response.get("downloadToken")

    # Get photo data from API
    def get_photo_data(self, uid: str) -> dict:
        photo_url = f"{self.base_url}/api/v1/photos/{uid}"
        headers = {"X-Session-ID": self.session_id}
        response = requests.get(photo_url, headers=headers)
        json_response = response.json()
        return json_response

    # Resize image with PIL to fit inside max_size
    def resize_image(self, filename: str, max_size: int) -> None:
        im = Image.open(filename)
        exif = im.info["exif"]
        width, height = im.size
        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int(max_size * height / width)
            else:
                new_height = max_size
                new_width = int(max_size * width / height)
            log.info(f"Resizing {filename} to {new_width}x{new_height}")
            im = im.resize((new_width, new_height), Image.LANCZOS)
            im.save(filename, exif=exif)

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
                    photo_url = f"{self.base_url}/api/v1/photos/{uid}/dl?t={self.download_token}"
                    headers = {"X-Session-ID": self.session_id}
                    response = requests.get(photo_url, headers=headers)
                    original_filename = (
                        response.headers["Content-Disposition"]
                        .split("=")[-1]
                        .strip('"')
                    )
                    filename = os.path.join(
                        cache_path, f"{uid}{os.path.splitext(original_filename)[1]}"
                    )
                    os.makedirs(os.path.dirname(filename), exist_ok=True)
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    log.info(f"Downloaded {filename}")
                    self.repair_exif(filename)
                    self.update_exif(filename)
                    self.resize_image(filename, 1920)

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

    def iso_to_yyyymmddhhmmss(self, iso_string: str):
        # date_time_obj = datetime.datetime.fromisoformat(iso_string)
        date_time_obj = datetime.datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%SZ")
        return date_time_obj.strftime("%Y:%m:%d %H:%M:%S")

    # Check file for exif date and update if necessary
    def update_exif(self, filename: str) -> None:
        uid = os.path.splitext(os.path.basename(filename))[0]
        with exiftool.ExifToolHelper() as et:
            metadata = et.get_metadata(filename)[0]
            if not metadata.get("EXIF:DateTimeOriginal"):
                log.info(f"No exif date found for {filename}.")
                photo_data = self.get_photo_data(uid)
                if photo_data.get("TakenAt"):
                    log.info(f"Updating exif date for {filename}.")
                    et.execute(
                        "-overwrite_original",
                        "-P",
                        "-AllDates="
                        + self.iso_to_yyyymmddhhmmss(photo_data.get("TakenAt", "")),
                        filename,
                    )
                else:
                    log.warn(f"Could not find any date information for {filename}.")

    # Repair exif data
    def repair_exif(self, filename: str) -> None:
        with exiftool.ExifTool() as et:
            et.execute(
                        "-overwrite_original",
                        "-all=",
                        "-tagsfromfile",
                        "@",
                        "-all:all",
                        "-unsafe",
                        "-icc_profile",
                        filename,
                    )

    # Check file for exif date and update if necessary
    # pillow seems to not support datetimeoriginal
    def update_exif_pillow(self, filename: str) -> None:
        uid = os.path.splitext(os.path.basename(filename))[0]
        im = Image.open(filename)
        exif = im.getexif()
        log.info(exif)
        if not exif.get(306):
            log.info(f"No exif date found for {filename}.")
            photo_data = self.get_photo_data(uid)
            if photo_data.get("TakenAt"):
                log.info(f"Updating exif date for {filename}.")
                exif[306] = exif[36867] = self.iso_to_yyyymmddhhmmss(
                    photo_data.get("TakenAt", "")
                )
                im.save(filename, exif=exif)
            else:
                log.warn(f"Could not find any date information for {filename}.")
        log.info(exif.get(306))


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
