import os
import sys
from pathlib import Path

os.environ.setdefault("MIKROTIK_RADIUS_SYNC_ENABLED", "false")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_and_esp32_command_are_available():
    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["message"] == "DoorLink Backend Running"

    command = client.get("/esp32/door-command")
    assert command.status_code == 200
    assert "command" in command.json()


def test_dashboard_login_page_is_available():
    response = client.get("/dashboard/doorlink")
    assert response.status_code == 200
    assert "DoorLink" in response.text


def test_one_door_api_routes_are_registered():
    paths = {route.path for route in app.routes}
    assert "/api/mikrotik/master/resource" in paths
    assert "/api/mikrotik/master/hotspot/active" in paths
    assert "/api/mikrotik/master/hotspot/users" in paths
    assert "/api/radius/status" in paths
    assert "/api/radius/users" in paths


def test_radius_status_can_fallback_without_chr_connection():
    response = client.get("/api/radius/status")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is False
    assert body["online"] is False
