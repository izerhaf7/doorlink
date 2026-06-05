import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.role_model import Role
from app.models.user_model import User
from app.services import user_service
from app.services.radius_user_manager_service import radius_user_manager_service


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for role_name in ["owner", "tenant", "guest", "trusted_guest", "technician"]:
            session.add(Role(name=role_name, can_use_hotspot=True))
        session.commit()
        yield session


@pytest.fixture
def fake_radius(monkeypatch):
    calls = []
    remote_users = {}

    monkeypatch.setattr(radius_user_manager_service, "enabled", True)

    def get_user(username):
        item = remote_users.get(username)
        return dict(item) if item else None

    def create_user(username, password):
        calls.append(("create", username, password))
        remote_users[username] = {".id": f"*{len(remote_users)+1}", "name": username, "password": password}
        return {"ret": "ok"}

    def update_user(username, *, password=None, disabled=None):
        calls.append(("update", username, password, disabled))
        remote_users.setdefault(username, {".id": f"*{len(remote_users)+1}", "name": username})
        if password is not None:
            remote_users[username]["password"] = password
        if disabled is not None:
            remote_users[username]["disabled"] = "yes" if disabled else "no"
        return {"ret": "ok"}

    def delete_user(username):
        calls.append(("delete", username))
        remote_users.pop(username, None)
        return {"ret": "ok"}

    def list_users():
        return [dict(v) for v in remote_users.values()]

    monkeypatch.setattr(radius_user_manager_service, "get_user", get_user)
    monkeypatch.setattr(radius_user_manager_service, "create_user", create_user)
    monkeypatch.setattr(radius_user_manager_service, "update_user", update_user)
    monkeypatch.setattr(radius_user_manager_service, "delete_user", delete_user)
    monkeypatch.setattr(radius_user_manager_service, "list_users", list_users)
    return calls, remote_users


def test_create_user_writes_to_user_manager_before_sqlite_commit(session, fake_radius):
    calls, remote_users = fake_radius

    user = user_service.create_user(
        session=session,
        full_name="Tenant One",
        username="tenant1",
        password="secret123",
        role_name="tenant",
    )

    assert user.username == "tenant1"
    assert calls == [("create", "tenant1", "secret123")]
    assert remote_users["tenant1"]["password"] == "secret123"
    assert session.exec(select(User).where(User.username == "tenant1")).first() is not None


def test_create_user_fails_without_sqlite_inconsistency_when_user_manager_write_fails(session, monkeypatch):
    monkeypatch.setattr(radius_user_manager_service, "enabled", True)

    def fail_create_user(username, password):
        raise HTTPException(status_code=401, detail="Unauthorized")

    monkeypatch.setattr(radius_user_manager_service, "get_user", lambda username: None)
    monkeypatch.setattr(radius_user_manager_service, "create_user", fail_create_user)

    with pytest.raises(HTTPException) as exc:
        user_service.create_user(
            session=session,
            full_name="Tenant Broken",
            username="broken",
            password="secret123",
            role_name="tenant",
        )

    assert exc.value.status_code == 502
    assert session.exec(select(User).where(User.username == "broken")).first() is None


def test_reconcile_users_creates_missing_updates_drift_and_reports_extra(session, fake_radius):
    calls, remote_users = fake_radius
    session.add(User(full_name="Owner", username="owner1", password="newpass", role_name="owner"))
    session.add(User(full_name="Guest", username="guest1", password="guestpass", role_name="guest"))
    session.commit()
    remote_users["owner1"] = {".id": "*1", "name": "owner1", "password": "oldpass"}
    remote_users["legacy"] = {".id": "*2", "name": "legacy", "password": "legacy"}

    result = user_service.sync_users_with_radius(session=session, delete_extra=False)

    assert ("update", "owner1", "newpass", False) in calls
    assert ("create", "guest1", "guestpass") in calls
    assert remote_users["owner1"]["password"] == "newpass"
    assert remote_users["guest1"]["password"] == "guestpass"
    assert "legacy" in result["extra_radius_users"]
    assert result["ok"] is True


def test_reconcile_users_can_delete_extra_radius_users_when_requested(session, fake_radius):
    calls, remote_users = fake_radius
    remote_users["legacy"] = {".id": "*2", "name": "legacy", "password": "legacy"}

    result = user_service.sync_users_with_radius(session=session, delete_extra=True)

    assert ("delete", "legacy") in calls
    assert "legacy" not in remote_users
    assert result["deleted_extra_radius_users"] == ["legacy"]
