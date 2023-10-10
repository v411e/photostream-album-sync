from abc import ABC, abstractmethod

class SyncApi(ABC):
    def __init__(
        self,
        username: str,
        password: str,
        base_url: str,
    ):
        self.username = username
        self.password = password
        self.base_url = base_url

    @abstractmethod
    def download_photo(self, uid: str, download_path: str) -> str:
        pass

    @abstractmethod
    def get_taken_at(self, uid: str) -> str:
        pass