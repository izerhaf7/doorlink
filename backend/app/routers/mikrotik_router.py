from fastapi import APIRouter

from app.services.mikrotik_service import mikrotik_master_service, mikrotik_service

# New one-door API wrapper paths recommended by the DoorLink brief.
api_router = APIRouter(prefix="/api/mikrotik/master", tags=["MikroTik MASTER"])


@api_router.get("/resource")
def api_master_resource():
    """System resource from MASTER RouterOS REST API."""
    return mikrotik_master_service.get_system_resource()


@api_router.get("/hotspot/active")
def api_master_hotspot_active():
    """Currently active HotSpot sessions on MASTER."""
    return mikrotik_master_service.get_hotspot_active()


@api_router.get("/hotspot/users")
def api_master_hotspot_users():
    """Local HotSpot users on MASTER, for monitoring only."""
    return mikrotik_master_service.get_hotspot_users()


@api_router.get("/hotspot/hosts")
def api_master_hotspot_hosts():
    """HotSpot host table on MASTER."""
    return mikrotik_master_service.get_hotspot_hosts()


@api_router.get("/radius")
def api_master_radius_clients():
    """RADIUS client configuration on MASTER."""
    return mikrotik_master_service.get_radius_clients()


@api_router.get("/hotspot/ip-bindings")
def api_master_ip_bindings():
    """HotSpot IP bindings/bypass list on MASTER."""
    return mikrotik_master_service.get_ip_bindings()


# Legacy route retained so existing clients keep working.
legacy_router = APIRouter(prefix="/mikrotik", tags=["MikroTik Legacy"])


@legacy_router.get("/resource")
def get_resource():
    """Backward compatible alias for /api/mikrotik/master/resource."""
    return mikrotik_service.get_system_resource()


router = APIRouter()
router.include_router(api_router)
router.include_router(legacy_router)
