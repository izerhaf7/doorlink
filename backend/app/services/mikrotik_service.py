import requests
from fastapi import HTTPException
from app.config import MIKROTIK_HOST, MIKROTIK_USER, MIKROTIK_PASSWORD


class MikroTikService:
    """Service class untuk komunikasi dengan MikroTik RouterOS REST API."""

    def __init__(self):
        self.base_url = f"http://{MIKROTIK_HOST}"
        self.auth = (MIKROTIK_USER, MIKROTIK_PASSWORD)

    def _request(self, method: str, path: str, json_data: dict = None) -> dict | list:
        """
        Helper method untuk mengirim HTTP request ke MikroTik REST API.
        Menangani error koneksi dan response non-2xx.
        """
        url = f"{self.base_url}{path}"

        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                json=json_data,
                timeout=10,
            )
        except requests.ConnectionError:
            raise HTTPException(
                status_code=503,
                detail=f"Tidak dapat terhubung ke MikroTik di {MIKROTIK_HOST}",
            )
        except requests.Timeout:
            raise HTTPException(
                status_code=504,
                detail="Request ke MikroTik timeout",
            )

        if not response.ok:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"MikroTik API error: {response.text}",
            )

        return response.json()

    # ── System ──────────────────────────────────────────────

    def get_system_resource(self) -> dict:
        """GET /rest/system/resource — info CPU, RAM, uptime, dsb."""
        return self._request("GET", "/rest/system/resource")

    # ── Hotspot Users ───────────────────────────────────────

    def get_hotspot_users(self) -> list:
        """GET /rest/ip/hotspot/user — daftar semua user hotspot."""
        return self._request("GET", "/rest/ip/hotspot/user")

    def create_hotspot_user(self, name: str, password: str, profile: str = "default") -> dict:
        """POST /rest/ip/hotspot/user — buat user hotspot baru."""
        payload = {
            "name": name,
            "password": password,
            "profile": profile,
        }
        return self._request("POST", "/rest/ip/hotspot/user/add", json_data=payload)

    # ── Hotspot Active ──────────────────────────────────────

    def get_hotspot_active(self) -> list:
        """GET /rest/ip/hotspot/active — daftar session aktif."""
        return self._request("GET", "/rest/ip/hotspot/active")


# Singleton instance agar tidak perlu inisialisasi ulang di setiap router
mikrotik_service = MikroTikService()
