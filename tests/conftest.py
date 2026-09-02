import os
import sys
import tempfile
from pathlib import Path

import bcrypt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault(
    "DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}"
)
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault(
    "ADMIN_PASSWORD_HASH",
    bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8"),
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-com-pelo-menos-32-bytes")
