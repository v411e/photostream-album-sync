from abc import ABC, abstractmethod
import requests, os, logging

log = logging.getLogger()

def _get_file_extension(response_header: str):
    content_type = response_header.get('Content-Type')
    content_disposition = response_header.get('Content-Disposition')

    if content_disposition:
        file_extension = content_disposition.split('=')[-1].strip('"')
        return '.' + file_extension

    if content_type:
        file_extension = content_type.split('/')[1]
        return '.' + file_extension

    return None

class SyncApi(ABC):
    def __init__(
        self,
        username: str,
        password: str,
        api_key: str,
        base_url: str,
    ):
        self.username = username
        self.password = password
        self.api_key = api_key
        self.base_url = base_url

    @staticmethod
    def _save_file(response: requests.Response, download_path: str, uid: str) -> str:
        log.debug(f"_save_file called. Response headers: {response.headers}")
        filename = os.path.join(
            download_path, f"{uid}{_get_file_extension(response.headers)}"
        )
        log.debug(f"Creating dirs...")
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        log.info(f"Saving file to {filename}...")
        with open(filename, "wb") as f:
            f.write(response.content)
        return filename

    @abstractmethod
    def download_photo(self, uid: str, download_path: str) -> str:
        pass

    @abstractmethod
    def get_taken_at(self, uid: str) -> str:
        pass