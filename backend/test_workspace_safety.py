from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.agent import safe_path

def test_safe_path_accepts_relative_python_file(tmp_path):
    assert safe_path(tmp_path, "src/example.py").name == "example.py"

def test_safe_path_rejects_parent_traversal(tmp_path):
    try:
        safe_path(tmp_path, "../outside.py")
    except ValueError:
        return
    assert False, "Expected traversal path to be rejected"

def test_safe_path_rejects_executable_extension(tmp_path):
    try:
        safe_path(tmp_path, "payload.exe")
    except ValueError:
        return
    assert False, "Expected unsupported extension to be rejected"
