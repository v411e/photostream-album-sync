import os

class Config:
    def __init__(self) -> None:
        self.read_env()
        self.validate()
        

    def read_env(self) -> None:
        # read config from environment variables
        self.base_url = os.environ.get("SYNC_BASE_URL")
        self.album_path = os.environ.get("PHOTOPRISM_ALBUM_PATH", "")
        self.cache_path = os.environ.get("SYNC_CACHE_PATH", "")
        self.username = os.environ.get("SYNC_USERNAME")
        self.password = os.environ.get("SYNC_PASSWORD")
        self.sync_type = os.environ.get("SYNC_TYPE", "photoprism")

    def validate(self) -> bool:
        # check if config is valid
        if not self.base_url or not self.cache_path or not self.username or not self.password or not self.sync_type or self.sync_type == "photoprism" and not self.album_path:
            raise ValueError("Please set all environment variables.")