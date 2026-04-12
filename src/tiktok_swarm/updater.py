"""Self-update — pulls latest code and reinstalls dependencies."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def check_for_updates() -> str:
    try:
        subprocess.run(["git", "fetch"], cwd=ROOT, capture_output=True, timeout=30)
        result = subprocess.run(
            ["git", "log", "HEAD..origin/master", "--oneline"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        commits = result.stdout.strip()
        if commits:
            count = len(commits.splitlines())
            return f"{count} update(s) available:\n{commits}\n\nRun: tt self-update"
        return "Already up to date."
    except FileNotFoundError:
        return "[ERROR] git not found. Install git to enable updates."
    except Exception as e:
        return f"[ERROR] Could not check for updates: {e}"


def apply_update() -> str:
    steps = []
    try:
        result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            return f"[ERROR] git pull failed:\n{result.stderr}\n\nTry: cd {ROOT} && git pull manually"
        steps.append(f"Code updated: {result.stdout.strip()}")
    except Exception as e:
        return f"[ERROR] git pull failed: {e}"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", ".", "-q"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            steps.append("Dependencies reinstalled.")
        else:
            steps.append(f"[WARN] pip install had issues: {result.stderr[:200]}")
    except Exception as e:
        steps.append(f"[WARN] Could not reinstall: {e}")

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h %s (%cr)"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        steps.append(f"Current version: {result.stdout.strip()}")
    except Exception:
        pass

    return "\n".join(steps)
