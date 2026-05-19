from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas.user_schema import UserCreate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/")
def list_users(session: Session = Depends(get_session)):
    """Ambil daftar semua user DoorLink."""
    users = user_service.get_all_users(session)
    return [
        UserResponse(
            id=u.id,
            full_name=u.full_name,
            username=u.username,
            role_name=u.role_name,
            room_number=u.room_number,
            is_active=u.is_active,
            created_at=str(u.created_at),
        )
        for u in users
    ]


@router.get("/{username}")
def get_user(username: str, session: Session = Depends(get_session)):
    """Ambil detail user berdasarkan username."""
    u = user_service.get_user_by_username(session, username)
    return UserResponse(
        id=u.id,
        full_name=u.full_name,
        username=u.username,
        role_name=u.role_name,
        room_number=u.room_number,
        is_active=u.is_active,
        created_at=str(u.created_at),
    )


@router.post("/", status_code=201)
def create_user(data: UserCreate, session: Session = Depends(get_session)):
    """
    Buat user DoorLink baru.
    Jika role memiliki can_use_hotspot=True, user HotSpot juga dibuat di MikroTik.
    """
    u = user_service.create_user(
        session=session,
        full_name=data.full_name,
        username=data.username,
        password=data.password,
        role_name=data.role_name,
        room_number=data.room_number,
    )
    return UserResponse(
        id=u.id,
        full_name=u.full_name,
        username=u.username,
        role_name=u.role_name,
        room_number=u.room_number,
        is_active=u.is_active,
        created_at=str(u.created_at),
    )


@router.delete("/{username}")
def delete_user(username: str, session: Session = Depends(get_session)):
    """Hapus user berdasarkan username."""
    return user_service.delete_user(session, username)
