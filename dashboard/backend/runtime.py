import json
import time
from pathlib import Path

RUNTIME = Path(__file__).resolve().parents[1] / "runtime"


def current_run():
    path = RUNTIME / "current_run.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return {k: data.get(k) for k in ("lab", "stage", "status", "evaluated", "total", "family", "operation", "preliminary_qualifiers", "elapsed_seconds", "eta_seconds", "last_checkpoint", "errors", "sealed", "demo")}
    except (OSError, ValueError):
        return None


def parse_events(limit=100):
    path = RUNTIME / "events.jsonl"
    if not path.exists():
        return []
    output = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            event = json.loads(line)
            if isinstance(event, dict):
                output.append({k: event.get(k) for k in ("timestamp", "ts", "kind", "event", "message", "lab", "run_id")})
        except ValueError:
            continue
    return output[::-1]


class DemoReplay:
    started = None
    duration = 45
    total = 14220360

    def start(self, duration=45):
        self.started = time.monotonic()
        self.duration = max(5, min(600, duration))

    def stop(self):
        self.started = None

    def state(self):
        if self.started is None:
            return None
        elapsed = time.monotonic() - self.started
        fraction = min(1, elapsed / self.duration)
        milestones = [0, 1000000, 5000000, 10000000, self.total]
        scaled = fraction * (len(milestones) - 1)
        index = min(int(scaled), len(milestones) - 2)
        evaluated = round(milestones[index] + (milestones[index + 1] - milestones[index]) * (scaled - index))
        return {"lab": "V5.4", "stage": "DISCOVERY", "status": "COMPLETE" if fraction == 1 else "RUNNING",
                "evaluated": evaluated, "total": self.total, "family": None, "operation": "recorded discovery replay",
                "preliminary_qualifiers": None, "elapsed_seconds": round(elapsed), "eta_seconds": max(0, round(self.duration - elapsed)),
                "last_checkpoint": evaluated, "errors": 0, "demo": True}


demo = DemoReplay()
