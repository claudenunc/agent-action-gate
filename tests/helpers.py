"""Test helpers — neutral runtime fixtures, no family/ tree."""
import shutil
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def make_runtime_root() -> Path:
    """Create a fresh runtime root in a temp dir with skills/ and data/.

    Returns the new root. Caller is responsible for cleanup if desired;
    pytest/unittest will let the OS reclaim it eventually.
    """
    root = Path(tempfile.mkdtemp(prefix="action_gate_test_"))
    (root / "data" / "pending_actions").mkdir(parents=True, exist_ok=True)
    (root / "skills").mkdir(parents=True, exist_ok=True)
    registry = (PROJECT_ROOT / "skills" / "registry.json").read_text(encoding="utf-8")
    (root / "skills" / "registry.json").write_text(registry, encoding="utf-8")
    return root
