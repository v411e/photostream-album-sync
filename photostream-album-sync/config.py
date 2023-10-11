import os

class Config:
    def __init__(self) -> None:
        self.read_env()
        self.validate()
        

    def read_env(self) -> None:
        # read config from environment variables
        self.base_url = os.environ.get("SYNC_BASE_URL")
        self.album_path = os.environ.get("PHOTOPRISM_ALBUM_PATH")
        self.immich_album_id = os.environ.get("IMMICH_ALBUM_ID")
        self.cache_path = os.environ.get("SYNC_CACHE_PATH")
        self.username = os.environ.get("SYNC_USERNAME")
        self.password = os.environ.get("SYNC_PASSWORD")
        self.api_key = os.environ.get("SYNC_API_KEY")
        self.sync_type = os.environ.get("SYNC_TYPE", "photoprism")
        self.immich_db_host = os.environ.get("IMMICH_DB_HOST")
        self.immich_db_port = os.environ.get("IMMICH_DB_PORT", "5432")
        self.immich_db_name = os.environ.get("IMMICH_DB_NAME")
        self.immich_db_user = os.environ.get("IMMICH_DB_USER")
        self.immich_db_password = os.environ.get("IMMICH_DB_PASSWORD")

    def validate(self) -> bool:
        # check if config is valid
        if (not self.base_url or 
            not self.cache_path or 
            not self.sync_type or 
            self.sync_type == "photoprism" and (not self.album_path or
                                                not self.username or
                                                not self.password) or
            self.sync_type == "immich" and (not self.immich_album_id or
                                            not self.api_key or
                                            not self.immich_db_host or
                                            not self.immich_db_port or
                                            not self.immich_db_name or
                                            not self.immich_db_user or
                                            not self.immich_db_password)):
            raise ValueError("Please set all environment variables.")