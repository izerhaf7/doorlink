from sqlmodel import Session, select
from app.models.user_model import User
from app.models.role_model import Role
from app.models.access_log_model import AccessLog


def check_door_access(session: Session, username: str) -> dict:
    """
    Cek apakah user boleh membuka pintu.
    Return dict dengan username, allowed, dan reason.
    """
    user = session.exec(select(User).where(User.username == username)).first()

    if not user:
        return {
            "username": username,
            "allowed": False,
            "reason": "User tidak ditemukan",
        }

    if not user.is_active:
        return {
            "username": username,
            "allowed": False,
            "reason": "User tidak aktif",
        }

    role = session.exec(select(Role).where(Role.name == user.role_name)).first()

    if not role:
        return {
            "username": username,
            "allowed": False,
            "reason": f"Role '{user.role_name}' tidak ditemukan",
        }

    if not role.can_open_door:
        return {
            "username": username,
            "allowed": False,
            "reason": f"Role '{role.name}' tidak memiliki izin buka pintu",
        }

    return {
        "username": username,
        "allowed": True,
        "reason": "Akses diizinkan",
    }


def open_door(session: Session, username: str) -> dict:
    """
    Simulasi buka pintu.
    - Cek akses user.
    - Buat access_log.
    - Return hasil allowed/denied.
    """
    access = check_door_access(session, username)

    if access["allowed"]:
        log = AccessLog(
            username=username,
            method="web",
            status="allowed",
            message="Pintu dibuka (simulasi)",
        )
    else:
        log = AccessLog(
            username=username,
            method="web",
            status="denied",
            message=access["reason"],
        )

    session.add(log)
    session.commit()

    return {
        "username": username,
        "allowed": access["allowed"],
        "status": log.status,
        "message": log.message,
    }


def get_access_logs(session: Session) -> list[AccessLog]:
    """Ambil semua access log, urut dari yang terbaru."""
    return session.exec(
        select(AccessLog).order_by(AccessLog.created_at.desc())
    ).all()


def esp32_check_access(session: Session, username: str) -> dict:
    """
    Endpoint khusus ESP32 Wokwi.
    - Reuse check_door_access() untuk logika permission.
    - Simpan access_log dengan method="esp32".
    - Return flat JSON: username, allowed, status, message.
      (format ringkas agar mudah di-parse ArduinoJson)
    """
    access = check_door_access(session, username)

    if access["allowed"]:
        log = AccessLog(
            username=username,
            method="esp32",
            status="allowed",
            message="ESP32 simulation access allowed",
        )
        response_message = "Access granted"
    else:
        log = AccessLog(
            username=username,
            method="esp32",
            status="denied",
            message=access["reason"],
        )
        # Pesan yang dikembalikan ke ESP32 tetap singkat
        if access["reason"] == "User tidak ditemukan":
            response_message = "User not found"
        else:
            response_message = "Access denied"

    session.add(log)
    session.commit()

    return {
        "username": username,
        "allowed": access["allowed"],
        "status": log.status,
        "message": response_message,
    }

