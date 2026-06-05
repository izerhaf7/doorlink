from app.config import (
    MIKROTIK_MASTER_HOST,
    MIKROTIK_MASTER_PASSWORD,
    MIKROTIK_MASTER_REST_SCHEME,
    MIKROTIK_MASTER_TIMEOUT,
    MIKROTIK_MASTER_USER,
)
from app.services.routeros_rest_client import RouterOSRestClient


class MikroTikMasterService:
    """Wrapper khusus MikroTik MASTER.

    MASTER dipakai untuk monitoring router, HotSpot active/users, dan status
    jaringan. CRUD User Manager tidak dilakukan lewat MASTER.
    """

    def __init__(self):
        self.client = RouterOSRestClient(
            host=MIKROTIK_MASTER_HOST,
            username=MIKROTIK_MASTER_USER,
            password=MIKROTIK_MASTER_PASSWORD,
            scheme=MIKROTIK_MASTER_REST_SCHEME,
            timeout=MIKROTIK_MASTER_TIMEOUT,
            label="MikroTik MASTER",
        )

    def get_system_resource(self) -> dict:
        return self.client.get("/rest/system/resource")

    def get_hotspot_active(self) -> list:
        return self.client.get("/rest/ip/hotspot/active")

    def get_hotspot_users(self) -> list:
        return self.client.get("/rest/ip/hotspot/user")

    def get_hotspot_hosts(self) -> list:
        return self.client.get("/rest/ip/hotspot/host")

    def get_radius_clients(self) -> list:
        return self.client.get("/rest/radius")

    def get_ip_bindings(self) -> list:
        return self.client.get("/rest/ip/hotspot/ip-binding")

    def create_hotspot_user(self, name: str, password: str, profile: str = "default") -> dict:
        """Legacy helper retained for compatibility.

        DoorLink's desired architecture creates HotSpot/RADIUS users on the
        RADIUS CHR User Manager, not on MASTER's local /ip hotspot user table.
        New code should use radius_user_manager_service instead.
        """
        payload = {"name": name, "password": password, "profile": profile}
        return self.client.put("/rest/ip/hotspot/user", payload)


mikrotik_master_service = MikroTikMasterService()

# Backward-compatible object name used by existing dashboard code.
mikrotik_service = mikrotik_master_service
