import logging, psycopg
from config import Config
from immich_api import ImmichApi
from cache import Cache
import json

log = logging.getLogger()


class ImmichHandler:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def listen_for_notifications(self):
        conn = await psycopg.AsyncConnection.connect(
            f"postgresql://{self.config.immich_db_user}:{self.config.immich_db_password}@{self.config.immich_db_host}:{self.config.immich_db_port}/{self.config.immich_db_name}",
            autocommit=True,
        )
        curs = conn.cursor()
        await curs.execute("LISTEN albums;")
        while True:
            gen = conn.notifies()
            async for notify in gen:
                log.info(f"Got notification: {notify.payload}")
                self.on_notify(notify.payload)

    def on_notify(self, payload: str):
        try:
            # Check, if the id matches the album id
            record = json.loads(payload).get("record")
            if record and record.get("id") == self.config.immich_album_id:
                log.info(
                    f"Album {self.config.immich_album_id} has changed. Updating photos..."
                )

                cache = Cache(path=self.config.cache_path)
                im_api = ImmichApi(
                    username=self.config.username,
                    password=self.config.password,
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                )

                # API: Get all photos in album
                photos_in_album = im_api.get_album_asset_uids(self.config.immich_album_id)
                log.info(f"Photos in album: {photos_in_album}")

                # Cache: Get all photos in cache folder
                photos_in_cache = cache.get_photos()
                log.info(f"Photos in cache: {photos_in_cache}")

                # Download new photos
                new_photos = photos_in_album - photos_in_cache
                for uid in new_photos:
                    cache.download_photo(uid, im_api)

                # Remove deleted photos
                deleted_photos = photos_in_cache - photos_in_album
                for uid in deleted_photos:
                    cache.remove_photo(uid)

                log.info("Done updating photos.")

        except Exception as e:
            log.error(e)
