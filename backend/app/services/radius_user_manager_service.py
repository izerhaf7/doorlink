import logging
from typing import Any

from fastapi import HTTPException

from app.config import (
    MIKROTIK_RADIUS_HOST,
    MIKROTIK_RADIUS_PASSWORD,
    MIKROTIK_RADIUS_REST_SCHEME,
    MIKROTIK_RADIUS_SYNC_ENABLED,
    MIKROTIK_RADIUS_TIMEOUT,
    MIKROTIK_RADIUS_USER,
)
from app.services.routeros_rest_client import RouterOSRestClient

logger = logging.getLogger(__name__)


class RadiusUserManagerService:
    """Backend adapter for MikroTik RADIUS CHR/User Manager.

    The current DoorLink topology uses MASTER only as RADIUS client. User CRUD
    must target CHR directly. After the CHR upgrade to RouterOS v7, User Manager
    lives under /user-manager and is exposed through REST as /rest/user-manager/*.
    """

    def __init__(self):
        self.enabled = MIKROTIK_RADIUS_SYNC_ENABLED
        self.client = RouterOSRestClient(
            host=MIKROTIK_RADIUS_HOST,
            username=MIKROTIK_RADIUS_USER,
            password=MIKROTIK_RADIUS_PASSWORD,
            scheme=MIKROTIK_RADIUS_REST_SCHEME,
            timeout=MIKROTIK_RADIUS_TIMEOUT,
            label="MikroTik RADIUS CHR",
        )

    def status(self) -> dict[str, Any]:
        if not self.enabled:
            return {
                "enabled": False,
                "host": MIKROTIK_RADIUS_HOST,
                "online": False,
                "message": "RADIUS sync disabled by MIKROTIK_RADIUS_SYNC_ENABLED=false",
            }

        try:
            resource = self.client.get("/rest/system/resource")
            um = self.client.get("/rest/user-manager")
            return {
                "enabled": True,
                "host": MIKROTIK_RADIUS_HOST,
                "online": True,
                "routeros_version": resource.get("version"),
                "user_manager": um,
            }
        except HTTPException as exc:
            return {
                "enabled": True,
                "host": MIKROTIK_RADIUS_HOST,
                "online": False,
                "message": exc.detail,
            }

    def list_users(self) -> list:
        self._ensure_enabled()
        return self.client.get("/rest/user-manager/user")

    def get_user(self, username: str) -> dict | None:
        for item in self.list_users():
            if item.get("name") == username or item.get("username") == username:
                return item
        return None

    def create_user(self, username: str, password: str) -> dict:
        self._ensure_enabled()
        payload = {
            "name": username,
            "password": password,
        }
        return self.client.put("/rest/user-manager/user", payload)

    def update_user(
        self,
        username: str,
        *,
        password: str | None = None,
        disabled: bool | None = None,
    ) -> dict:
        self._ensure_enabled()
        existing = self.get_user(username)
        if not existing:
            raise HTTPException(status_code=404, detail=f"User Manager user '{username}' tidak ditemukan")

        item_id = existing.get(".id")
        if not item_id:
            raise HTTPException(status_code=500, detail="User Manager item tidak punya .id")

        payload: dict[str, Any] = {}
        if password is not None:
            payload["password"] = password
        if disabled is not None:
            payload["disabled"] = "yes" if disabled else "no"
        if not payload:
            return existing
        return self.client.patch(f"/rest/user-manager/user/{item_id}", payload)

    def delete_user(self, username: str) -> dict:
        self._ensure_enabled()
        existing = self.get_user(username)
        if not existing:
            return {"message": f"User Manager user '{username}' sudah tidak ada"}

        item_id = existing.get(".id")
        if not item_id:
            raise HTTPException(status_code=500, detail="User Manager item tidak punya .id")
        return self.client.delete(f"/rest/user-manager/user/{item_id}")

    def create_user_safe(self, username: str, password: str) -> dict:
        """Best-effort sync used by SQLite user creation.

        DoorLink dashboard must keep working even if CHR is temporarily offline.
        Return a structured warning instead of raising to the caller.
        """
        if not self.enabled:
            return {"ok": False, "skipped": True, "message": "RADIUS sync disabled"}
        try:
            existing = self.get_user(username)
            if existing:
                return {"ok": True, "skipped": True, "message": "User already exists in User Manager"}
            self.create_user(username=username, password=password)
            return {"ok": True, "skipped": False, "message": "User synced to User Manager"}
        except HTTPException as exc:
            logger.warning("RADIUS create sync failed for %s: %s", username, exc.detail)
            return {"ok": False, "skipped": False, "message": exc.detail}
        except Exception as exc:
            logger.exception("Unexpected RADIUS create sync failure for %s", username)
            return {"ok": False, "skipped": False, "message": repr(exc)}

    def delete_user_safe(self, username: str) -> dict:
        if not self.enabled:
            return {"ok": False, "skipped": True, "message": "RADIUS sync disabled"}
        try:
            self.delete_user(username)
            return {"ok": True, "skipped": False, "message": "User removed from User Manager"}
        except HTTPException as exc:
            logger.warning("RADIUS delete sync failed for %s: %s", username, exc.detail)
            return {"ok": False, "skipped": False, "message": exc.detail}
        except Exception as exc:
            logger.exception("Unexpected RADIUS delete sync failure for %s", username)
            return {"ok": False, "skipped": False, "message": repr(exc)}

    def _ensure_enabled(self) -> None:
        if not self.enabled:
            raise HTTPException(status_code=503, detail="RADIUS sync disabled")


radius_user_manager_service = RadiusUserManagerService()
