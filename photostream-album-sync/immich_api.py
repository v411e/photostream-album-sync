import requests, logging
from sync_api import SyncApi

log = logging.getLogger()


class ImmichApi(SyncApi):
    def _get_album_info(self, album_id: str) -> dict:
        url = f"{self.base_url}/api/album/{album_id}"
        headers = {"Accept": "application/json", "x-api-key": self.api_key}
        response = requests.request("GET", url, headers=headers)
        json_response = response.json()
        log.debug(f"Got album info for {album_id}: {json_response}")
        return json_response

    def _get_album_assets(self, album_id: str) -> dict:
        album_info = self._get_album_info(album_id)
        assets = album_info.get("assets")
        log.debug(f"Got assets for album {album_id}: {assets}")
        return assets

    def get_album_asset_uids(self, album_id: str) -> set:
        assets = self._get_album_assets(album_id)
        asset_uids = [asset.get("id") for asset in assets]
        log.debug(f"Got asset uids for album {album_id}: {asset_uids}")
        return set(asset_uids)

    def download_photo(self, uid: str, download_path: str) -> str:
        url = f"{self.base_url}/api/asset/download/{uid}"
        headers = {"Accept": "application/octet-stream", "x-api-key": self.api_key}
        response = requests.request("POST", url, headers=headers)
        filename = super()._save_file(
            response=response, download_path=download_path, uid=uid
        )
        log.info(f"Downloaded {filename}")
        return filename

    def get_taken_at(self, uid: str) -> str:
        url = f"{self.base_url}/api/asset/assetById/{uid}"
        headers = {"Accept": "application/json", "x-api-key": self.api_key}
        response = requests.request("GET", url, headers=headers)
        json_response = response.json()
        exif_info = json_response.get("exifInfo")
        if exif_info:
            log.info(f"Got exif info for {uid}: {exif_info}")
            return exif_info.get("dateTimeOriginal")
        else:
            localDateTime = json_response.get("localDateTime")
            log.info(
                f"No exif info for {uid}, using localDateTime instead: {localDateTime}"
            )
            return localDateTime
