import logging

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.role_model import Role
from app.models.user_model import User
from app.services.radius_user_manager_service import radius_user_manager_service

logger = logging.getLogger(__name__)


def get_all_users(session: Session) -> list[User]:
    """Ambil semua user dari database."""
    return session.exec(select(User)).all()


def get_user_by_username(session: Session, username: str) -> User:
    """Ambil user berdasarkan username. Raise 404 jika tidak ditemukan."""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{username}' tidak ditemukan")
    return user


def get_role_by_name(session: Session, role_name: str) -> Role:
    """Ambil role berdasarkan nama. Raise 400 jika tidak valid."""
    role = session.exec(select(Role).where(Role.name == role_name)).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Role '{role_name}' tidak valid")
    return role


def create_user(
    session: Session,
    full_name: str,
    username: str,
    password: str,
    role_name: str,
    room_number: str = None,
) -> User:
    """
    Buat user DoorLink baru.

    Data aplikasi/role/RFID disimpan di SQLite. Jika role mengizinkan HotSpot,
    backend mencoba sync ke User Manager CHR secara best-effort. Kegagalan CHR
    tidak menggagalkan dashboard supaya demo DoorLink tetap stabil.
    """
    existing = session.exec(select(User).where(User.username == username)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Username '{username}' sudah terdaftar")

    role = get_role_by_name(session, role_name)

    user = User(
        full_name=full_name,
        username=username,
        password=password,
        role_name=role_name,
        room_number=room_number,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    if role.can_use_hotspot:
        result = radius_user_manager_service.create_user_safe(username=username, password=password)
        if not result.get("ok"):
            logger.warning("SQLite user %s created, but RADIUS sync failed: %s", username, result)

    return user


def update_user(
    session: Session,
    username: str,
    *,
    full_name: str,
    role_name: str,
    room_number: str = None,
) -> User:
    """Update data DoorLink SQLite. RADIUS password/profile sync can be added later."""
    user = get_user_by_username(session, username)
    get_role_by_name(session, role_name)

    user.full_name = full_name
    user.role_name = role_name
    user.room_number = room_number
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, username: str) -> dict:
    """Hapus user dari SQLite dan coba hapus dari CHR User Manager."""
    user = get_user_by_username(session, username)
    role = session.exec(select(Role).where(Role.name == user.role_name)).first()

    # Delete local app user first: dashboard state must be authoritative for door access.
    session.delete(user)
    session.commit()

    radius_result = None
    if role and role.can_use_hotspot:
        radius_result = radius_user_manager_service.delete_user_safe(username)
        if not radius_result.get("ok"):
            logger.warning("SQLite user %s deleted, but RADIUS delete sync failed: %s", username, radius_result)

    return {
        "message": f"User '{username}' berhasil dihapus",
        "radius_sync": radius_result,
    }
