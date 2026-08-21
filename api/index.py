import sys
from pathlib import Path

# Add project root and backend path to sys.path
root_path = Path(__file__).resolve().parent.parent
backend_path = root_path / "backend"

if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from backend.app.main import app
