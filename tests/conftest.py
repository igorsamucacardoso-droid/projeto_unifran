import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault(
    "DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}"
)
