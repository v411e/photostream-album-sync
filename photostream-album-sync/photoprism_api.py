import requests, logging, os


class PhotoprismApi:
    def __init__(
        self,
        username: str,
        password: str,
        base_url: str,
    ):
        self.username = username
        self.password = password
        self.base_url = base_url

    # Get session ID from API
    def get_session_id(self) -> str:
        if hasattr(self, 'session_id') and  self.session_id:
            return self.session_id

        auth_url = f"{self.base_url}/api/v1/session"
        response = requests.post(
            auth_url, json={"username": self.username, "password": self.password}
        )
        json_response = response.json()
        self.session_id = json_response.get("id")
        log.info("Got session ID.")
        return self.session_id

    # Get download token from API
    def get_download_token(self) -> str:
        if hasattr(self, 'download_token') and self.download_token:
            return self.download_token

        config_url = f"{self.base_url}/api/v1/config"
        response = requests.get(config_url, headers={"X-Session-ID": self.get_session_id()})
        json_response = response.json()
        self.download_token = json_response.get("downloadToken")
        return self.download_token

    # Get photo data from API
    def get_photo_data(self, uid: str) -> dict:
        photo_url = f"{self.base_url}/api/v1/photos/{uid}"
        headers = {"X-Session-ID": self.get_session_id()}
        response = requests.get(photo_url, headers=headers)
        json_response = response.json()
        return json_response

    def download_photo(self, uid: str, download_path: str) -> str:
        photo_url = f"{self.base_url}/api/v1/photos/{uid}/dl?t={self.get_download_token()}"
        headers = {"X-Session-ID": self.get_session_id()}
        response = requests.get(photo_url, headers=headers)
        original_filename = (
            response.headers["Content-Disposition"].split("=")[-1].strip('"')
        )
        filename = os.path.join(
            download_path, f"{uid}{os.path.splitext(original_filename)[1]}"
        )
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            f.write(response.content)
        log.info(f"Downloaded {filename}")
        return filename


log = logging.getLogger()
