import os
from dotenv import load_dotenv

load_dotenv()

# MikroTik RouterOS REST API Configuration
MIKROTIK_HOST = os.getenv("MIKROTIK_HOST", "192.168.88.1")
MIKROTIK_USER = os.getenv("MIKROTIK_USER", "admin")
MIKROTIK_PASSWORD = os.getenv("MIKROTIK_PASSWORD", "")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///doorlink.db")
