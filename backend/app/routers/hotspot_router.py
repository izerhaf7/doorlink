from fastapi import APIRouter
from app.services.mikrotik_service import mikrotik_service
from app.schemas.hotspot_schema import HotspotUserCreate

router = APIRouter(prefix="/hotspot", tags=["Hotspot"])


@router.get("/users")
def get_hotspot_users():
    """Ambil daftar semua user hotspot dari MikroTik."""
    return mikrotik_service.get_hotspot_users()


@router.post("/users")
def create_hotspot_user(user: HotspotUserCreate):
    """Buat user hotspot baru di MikroTik."""
    return mikrotik_service.create_hotspot_user(
        name=user.name,
        password=user.password,
        profile=user.profile,
    )


@router.get("/active")
def get_hotspot_active():
    """Ambil daftar session hotspot yang sedang aktif."""
    return mikrotik_service.get_hotspot_active()
