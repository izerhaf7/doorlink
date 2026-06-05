import logging

import requests
from fastapi import HTTPException
from app.config import MIKROTIK_HOST, MIKROTIK_USER, MIKROTIK_PASSWORD


logger = logging.getLogger(__name__)


class MikroTikService:
    def __init__(self):
        self.base_url = f"http://{MIKROTIK_HOST}".rstrip("/")
        self.auth = (MIKROTIK_USER, MIKROTIK_PASSWORD)
        self.session = requests.Session()
        self.session.trust_env = False

    def _request(self, method: str, path: str, json_data: dict = None) -> dict | list:
        url = f"{self.base_url}{path}"
        method = method.upper()
        logger.info("MikroTik request method=%s url=%s", method, url)

        try:
            response = self.session.request(
                method=method,
                url=url,
                auth=self.auth,
                json=json_data,
                timeout=10,
            )
        except requests.exceptions.ConnectionError as e:
            logger.exception("MikroTik connection error method=%s url=%s", method, url)
            raise HTTPException(
                status_code=503,
                detail=f"Tidak dapat terhubung ke MikroTik di {MIKROTIK_HOST}: {repr(e)}",
            )
        except requests.exceptions.Timeout as e:
            logger.exception("MikroTik timeout method=%s url=%s", method, url)
            raise HTTPException(
                status_code=504,
                detail=f"Request ke MikroTik timeout: {repr(e)}",
            )
        except Exception as e:
            logger.exception("MikroTik unknown error method=%s url=%s", method, url)
            raise HTTPException(
                status_code=500,
                detail=f"Error MikroTik tidak dikenal: {repr(e)}",
            )

        logger.info(
            "MikroTik response method=%s url=%s status_code=%s",
            method,
            url,
            response.status_code,
        )

        if not response.ok:
            error_text = response.text[:300]
            logger.warning(
                "MikroTik API error method=%s url=%s status_code=%s response=%s",
                method,
                url,
                response.status_code,
                error_text,
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=f"MikroTik API error: {error_text}",
            )

        if not response.text.strip():
            return {}

        try:
            return response.json()
        except ValueError as e:
            logger.exception(
                "MikroTik invalid JSON method=%s url=%s status_code=%s response=%s",
                method,
                url,
                response.status_code,
                response.text[:300],
            )
            raise HTTPException(
                status_code=500,
                detail=f"Response MikroTik bukan JSON valid: {response.text[:300]}",
            ) from e

    def get_system_resource(self) -> dict:
        return self._request("GET", "/rest/system/resource")

    def get_hotspot_users(self) -> list:
        return self._request("GET", "/rest/ip/hotspot/user")

    def create_hotspot_user(self, name: str, password: str, profile: str = "default") -> dict:
        payload = {
            "name": name,
            "password": password,
            "profile": profile,
        }
        # RouterOS v7 REST creates new resources by sending the payload to the
        # collection endpoint, not to the console-style /add path.
        return self._request("PUT", "/rest/ip/hotspot/user", json_data=payload)

    def get_hotspot_active(self) -> list:
        return self._request("GET", "/rest/ip/hotspot/active")


mikrotik_service = MikroTikService()
