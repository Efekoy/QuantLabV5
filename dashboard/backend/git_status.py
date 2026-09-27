import subprocess
from dashboard.adapters.v54 import ROOT


def run_git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=5, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def parse_porcelain(text):
    files = []
    for line in text.splitlines():
        if len(line) >= 4:
            files.append({"status": line[:2].strip() or "M", "path": line[3:]})
    return files


def git_status():
    files = parse_porcelain(run_git("status", "--short", "--untracked-files=normal"))
    return {"branch": run_git("branch", "--show-current"), "latest": run_git("log", "-1", "--format=%h %s"),
            "clean": not files, "count": len(files), "files": files[:100]}
