import os
from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# Backend runtime configuration
BACKEND_HOST = _env("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(_env("BACKEND_PORT", "8000"))

# MikroTik MASTER RouterOS REST API configuration.
# Backward compatibility: old MIKROTIK_* variables still point to MASTER.
MIKROTIK_MASTER_HOST = _env("MIKROTIK_MASTER_HOST", _env("MIKROTIK_HOST", "10.10.13.10"))
MIKROTIK_MASTER_USER = _env("MIKROTIK_MASTER_USER", _env("MIKROTIK_USER", "admin"))
MIKROTIK_MASTER_PASSWORD = _env("MIKROTIK_MASTER_PASSWORD", _env("MIKROTIK_PASSWORD", ""))
MIKROTIK_MASTER_REST_SCHEME = _env("MIKROTIK_MASTER_REST_SCHEME", "http")
MIKROTIK_MASTER_TIMEOUT = float(_env("MIKROTIK_MASTER_TIMEOUT", "10"))

# Legacy names used by older code paths. Keep these as aliases for MASTER.
MIKROTIK_HOST = MIKROTIK_MASTER_HOST
MIKROTIK_USER = MIKROTIK_MASTER_USER
MIKROTIK_PASSWORD = MIKROTIK_MASTER_PASSWORD

# MikroTik RADIUS CHR / User Manager configuration.
# RouterOS v7 User Manager is accessed via REST at /rest/user-manager/*.
MIKROTIK_RADIUS_HOST = _env("MIKROTIK_RADIUS_HOST", "10.10.13.6")
MIKROTIK_RADIUS_USER = _env("MIKROTIK_RADIUS_USER", "admin")
MIKROTIK_RADIUS_PASSWORD = _env("MIKROTIK_RADIUS_PASSWORD", "")
MIKROTIK_RADIUS_REST_SCHEME = _env("MIKROTIK_RADIUS_REST_SCHEME", "http")
MIKROTIK_RADIUS_TIMEOUT = float(_env("MIKROTIK_RADIUS_TIMEOUT", "10"))
MIKROTIK_RADIUS_SYNC_ENABLED = _env("MIKROTIK_RADIUS_SYNC_ENABLED", "true").lower() in {
    "1", "true", "yes", "on"
}

# Database Configuration
DATABASE_URL = _env("DATABASE_URL", "sqlite:///doorlink.db")
