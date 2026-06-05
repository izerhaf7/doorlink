from fastapi import APIRouter

from app.schemas.radius_schema import RadiusUserCreate, RadiusUserUpdate
from app.services.radius_user_manager_service import radius_user_manager_service

router = APIRouter(prefix="/api/radius", tags=["RADIUS User Manager"])


@router.get("/status")
def radius_status():
    """Check backend connectivity to MikroTik RADIUS CHR/User Manager."""
    return radius_user_manager_service.status()


@router.get("/users")
def list_radius_users():
    """List HotSpot/RADIUS users stored in CHR User Manager."""
    return radius_user_manager_service.list_users()


@router.post("/users", status_code=201)
def create_radius_user(payload: RadiusUserCreate):
    """Create a User Manager account directly on the RADIUS CHR."""
    return radius_user_manager_service.create_user(
        username=payload.username,
        password=payload.password,
    )


@router.put("/users/{username}")
def update_radius_user(username: str, payload: RadiusUserUpdate):
    """Update password/disabled state for a CHR User Manager account."""
    return radius_user_manager_service.update_user(
        username,
        password=payload.password,
        disabled=payload.disabled,
    )


@router.delete("/users/{username}")
def delete_radius_user(username: str):
    """Delete a User Manager account directly from the RADIUS CHR."""
    return radius_user_manager_service.delete_user(username)
