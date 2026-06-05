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


def _hotspot_users_query():
    return select(User).join(Role, User.role_name == Role.name).where(
        Role.can_use_hotspot == True,  # noqa: E712 - SQLModel expression needs == True
        User.is_active == True,  # noqa: E712
    )


def _radius_username(item: dict) -> str | None:
    return item.get("name") or item.get("username")


def _upsert_radius_user(username: str, password: str) -> dict:
    """Create/update one User Manager account and fail loudly on errors."""
    if not radius_user_manager_service.enabled:
        raise HTTPException(status_code=503, detail="RADIUS/User Manager sync disabled")

    try:
        existing = radius_user_manager_service.get_user(username)
        if existing:
            radius_user_manager_service.update_user(username, password=password, disabled=False)
            return {"action": "updated", "username": username}
        radius_user_manager_service.create_user(username=username, password=password)
        return {"action": "created", "username": username}
    except HTTPException as exc:
        logger.warning("Strict RADIUS sync failed for %s: %s", username, exc.detail)
        raise HTTPException(
            status_code=502,
            detail=f"Gagal sync user '{username}' ke CHR User Manager: {exc.detail}",
        ) from exc


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

    Untuk mencegah data SQLite dan MikroTik User Manager tidak konsisten, user
    HotSpot ditulis ke CHR terlebih dahulu. Jika write ke CHR gagal, insert ke
    SQLite dibatalkan dan error dikembalikan ke dashboard/API.
    """
    existing = session.exec(select(User).where(User.username == username)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Username '{username}' sudah terdaftar")

    role = get_role_by_name(session, role_name)

    radius_written = False
    if role.can_use_hotspot:
        _upsert_radius_user(username=username, password=password)
        radius_written = True

    user = User(
        full_name=full_name,
        username=username,
        password=password,
        role_name=role_name,
        room_number=room_number,
    )
    try:
        session.add(user)
        session.commit()
        session.refresh(user)
    except Exception:
        session.rollback()
        if radius_written:
            try:
                radius_user_manager_service.delete_user(username)
            except Exception as cleanup_exc:
                logger.warning("Failed to roll back CHR user %s after SQLite error: %r", username, cleanup_exc)
        raise

    return user


def update_user(
    session: Session,
    username: str,
    *,
    full_name: str,
    role_name: str,
    room_number: str = None,
) -> User:
    """Update data DoorLink dan pastikan user HotSpot tetap ada di CHR."""
    user = get_user_by_username(session, username)
    role = get_role_by_name(session, role_name)

    if role.can_use_hotspot:
        _upsert_radius_user(username=user.username, password=user.password)

    user.full_name = full_name
    user.role_name = role_name
    user.room_number = room_number
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, username: str) -> dict:
    """Hapus user dari CHR User Manager lalu SQLite agar tidak tersisa inkonsistensi."""
    user = get_user_by_username(session, username)
    role = session.exec(select(Role).where(Role.name == user.role_name)).first()

    radius_result = None
    if role and role.can_use_hotspot:
        try:
            radius_result = radius_user_manager_service.delete_user(username)
        except HTTPException as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Gagal hapus user '{username}' dari CHR User Manager: {exc.detail}",
            ) from exc

    session.delete(user)
    session.commit()

    return {
        "message": f"User '{username}' berhasil dihapus",
        "radius_sync": radius_result,
    }


def sync_users_with_radius(session: Session, *, delete_extra: bool = False) -> dict:
    """Reconcile SQLite DoorLink users with MikroTik CHR User Manager.

    SQLite DoorLink menjadi source of truth untuk user HotSpot. Algoritma:
    1. Ambil semua user aktif dengan role.can_use_hotspot=True.
    2. Ambil semua user CHR User Manager.
    3. Create user yang ada di SQLite tapi belum ada di CHR.
    4. Update password/enable user yang ada di keduanya.
    5. Laporkan user CHR ekstra; hapus hanya jika delete_extra=True.
    """
    if not radius_user_manager_service.enabled:
        raise HTTPException(status_code=503, detail="RADIUS/User Manager sync disabled")

    local_users = session.exec(_hotspot_users_query()).all()
    local_by_username = {user.username: user for user in local_users}
    remote_items = radius_user_manager_service.list_users()
    remote_by_username = {
        username: item
        for item in remote_items
        if (username := _radius_username(item))
    }

    created: list[str] = []
    updated: list[str] = []
    failed: list[dict] = []

    for username, user in local_by_username.items():
        try:
            if username not in remote_by_username:
                radius_user_manager_service.create_user(username=username, password=user.password)
                created.append(username)
            else:
                radius_user_manager_service.update_user(username, password=user.password, disabled=False)
                updated.append(username)
        except HTTPException as exc:
            failed.append({"username": username, "error": exc.detail})

    extra_radius_users = sorted(set(remote_by_username) - set(local_by_username))
    deleted_extra_radius_users: list[str] = []
    if delete_extra:
        for username in extra_radius_users:
            try:
                radius_user_manager_service.delete_user(username)
                deleted_extra_radius_users.append(username)
            except HTTPException as exc:
                failed.append({"username": username, "error": exc.detail})

    return {
        "ok": not failed,
        "source_of_truth": "sqlite_doorlink_users_with_can_use_hotspot_true",
        "created_radius_users": created,
        "updated_radius_users": updated,
        "extra_radius_users": extra_radius_users,
        "deleted_extra_radius_users": deleted_extra_radius_users,
        "failed": failed,
    }
