from fastapi import APIRouter
from app.services.mikrotik_service import mikrotik_service

router = APIRouter(prefix="/mikrotik", tags=["MikroTik"])


@router.get("/resource")
def get_resource():
    """Ambil informasi system resource MikroTik (CPU, RAM, uptime, dll)."""
    return mikrotik_service.get_system_resource()
