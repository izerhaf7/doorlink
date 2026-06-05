import logging
from typing import Any

import requests
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class RouterOSRestClient:
    """Small RouterOS v7 REST client with safe error messages.

    This client is intentionally backend-only. Dashboard/ESP32 callers never see
    MikroTik credentials; they only call FastAPI endpoints.
    """

    def __init__(
        self,
        *,
        host: str,
        username: str,
        password: str,
        scheme: str = "http",
        timeout: float = 10,
        label: str = "MikroTik",
    ):
        self.host = host
        self.username = username
        self.password = password
        self.scheme = scheme or "http"
        self.timeout = timeout
        self.label = label
        self.base_url = f"{self.scheme}://{self.host}".rstrip("/")
        self.auth = (self.username, self.password)
        self.session = requests.Session()
        # Avoid proxy env variables breaking private LAN access.
        self.session.trust_env = False

    @property
    def configured(self) -> bool:
        return bool(self.host and self.username)

    def request(self, method: str, path: str, json_data: dict | None = None) -> dict | list:
        if not self.configured:
            raise HTTPException(
                status_code=503,
                detail=f"{self.label} belum dikonfigurasi di .env",
            )

        url = f"{self.base_url}{path}"
        method = method.upper()
        logger.info("%s REST request method=%s path=%s", self.label, method, path)

        try:
            response = self.session.request(
                method=method,
                url=url,
                auth=self.auth,
                json=json_data,
                timeout=self.timeout,
            )
        except requests.exceptions.ConnectionError as e:
            logger.exception("%s connection error method=%s url=%s", self.label, method, url)
            raise HTTPException(
                status_code=503,
                detail=f"Tidak dapat terhubung ke {self.label} di {self.host}: {repr(e)}",
            ) from e
        except requests.exceptions.Timeout as e:
            logger.exception("%s timeout method=%s url=%s", self.label, method, url)
            raise HTTPException(
                status_code=504,
                detail=f"Request ke {self.label} timeout: {repr(e)}",
            ) from e
        except Exception as e:
            logger.exception("%s unknown error method=%s url=%s", self.label, method, url)
            raise HTTPException(
                status_code=500,
                detail=f"Error {self.label} tidak dikenal: {repr(e)}",
            ) from e

        if not response.ok:
            error_text = response.text[:300]
            logger.warning(
                "%s REST error method=%s path=%s status_code=%s response=%s",
                self.label,
                method,
                path,
                response.status_code,
                error_text,
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=f"{self.label} API error: {error_text}",
            )

        if not response.text.strip():
            return {}

        try:
            return response.json()
        except ValueError as e:
            logger.exception(
                "%s invalid JSON method=%s path=%s status_code=%s response=%s",
                self.label,
                method,
                path,
                response.status_code,
                response.text[:300],
            )
            raise HTTPException(
                status_code=500,
                detail=f"Response {self.label} bukan JSON valid: {response.text[:300]}",
            ) from e

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def put(self, path: str, payload: dict) -> Any:
        return self.request("PUT", path, json_data=payload)

    def patch(self, path: str, payload: dict) -> Any:
        return self.request("PATCH", path, json_data=payload)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)
