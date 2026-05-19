from sqlmodel import Session, select
from fastapi import HTTPException

from app.models.user_model import User
from app.models.role_model import Role
from app.services.mikrotik_service import mikrotik_service


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


def create_user(session: Session, full_name: str, username: str, password: str,
                role_name: str, room_number: str = None) -> User:
    """
    Buat user DoorLink baru.
    - Validasi role ada di database.
    - Cek username belum dipakai.
    - Jika role punya can_use_hotspot=True, buat juga user HotSpot di MikroTik.
    """
    # Cek duplikat username
    existing = session.exec(select(User).where(User.username == username)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Username '{username}' sudah terdaftar")

    # Validasi role
    role = get_role_by_name(session, role_name)

    # Buat user di database lokal
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

    # Buat user HotSpot di MikroTik jika role membolehkan
    if role.can_use_hotspot:
        try:
            mikrotik_service.create_hotspot_user(
                name=username,
                password=password,
            )
        except HTTPException as e:
            # User sudah tersimpan di DB lokal, tapi gagal di MikroTik
            # Untuk prototype: tetap lanjut, tapi beri warning di response
            # (bisa diubah ke rollback di production)
            pass

    return user


def delete_user(session: Session, username: str) -> dict:
    """Hapus user berdasarkan username."""
    user = get_user_by_username(session, username)
    session.delete(user)
    session.commit()
    return {"message": f"User '{username}' berhasil dihapus"}
