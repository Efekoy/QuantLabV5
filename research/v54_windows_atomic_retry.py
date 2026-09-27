"""Operational wrapper for transient Windows sharing locks during checkpoint replace.

The v5.4-prereg scientific modules remain byte-for-byte unchanged. A retry
repeats only the same atomic os.replace operation after WinError 5. It never
changes an evaluated specification, row, checkpoint boundary, or decision.
"""
from __future__ import annotations

from pathlib import Path
import time


_ORIGINAL_REPLACE = Path.replace


def _retry_replace(self: Path, target):
    for attempt in range(12):
        try:
            return _ORIGINAL_REPLACE(self, target)
        except PermissionError as exc:
            if getattr(exc, "winerror", None) != 5 or attempt == 11:
                raise
            time.sleep(min(0.1 * (attempt + 1), 0.75))
    raise AssertionError("unreachable replace retry state")


def main():
    Path.replace = _retry_replace
    from research.run_v54_discovery import main as discovery_main
    discovery_main()


if __name__ == "__main__":
    main()
