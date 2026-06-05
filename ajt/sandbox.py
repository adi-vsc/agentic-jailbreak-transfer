import os
import subprocess
import sys
import tempfile


def run_python(code: str, stdin: str = "", timeout: float = 5.0) -> tuple[str, bool]:
    """Run code in a fresh subprocess. Returns (stdout, ok). ok=False on
    non-zero exit, timeout, or crash."""
    fd, path = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(code)
        proc = subprocess.run(
            [sys.executable, path],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.stdout, proc.returncode == 0
    except subprocess.TimeoutExpired:
        return "", False
    except Exception:
        return "", False
    finally:
        os.unlink(path)
