"""Resumable sequential world runner (one process, bounded memory). (Ported unchanged from QuantLabV4.)

    python research/run_worlds.py <jobfile.json>

A job file lists jobs {"id", "world": {...}, "out": relpath}. Each job runs the COMPLETE inherited (V4 reference) search
(quantlab5.search.world.run_world) on one world and writes its summary JSON (with a sha256 of the summary).
Jobs whose output already exists and verifies are skipped, so an interrupted run resumes exactly.
World kinds:
  {"kind": "synthetic", "plant": P, "seed": S}
  {"kind": "synthetic_null", "plant": P, "world_seed": S, "null": A|B|C, "null_seed": N}
  {"kind": "real_null", "partition": "DISCOVERY", "null": A|B|C, "null_seed": N}
  {"kind": "real", "partition": "DISCOVERY", "save_dir": relpath}   (only after the preregistration freeze)
"""
from __future__ import annotations

import gc
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quantlab5.nulls.base import MinuteSignFlipNull, TodBlockResampleNull  # noqa: E402
from quantlab5.data.market import build_market, load_market  # noqa: E402
from quantlab5.synthetic.market_builders import calibration_world  # noqa: E402
from quantlab5.search.world import run_world  # noqa: E402

NULLS = {"A": lambda: MinuteSignFlipNull(joint=False), "C": lambda: MinuteSignFlipNull(joint=True),
         "B": lambda: TodBlockResampleNull(30, joint=True)}
_REAL_CACHE: dict = {}


def _null_of(m, kind, seed):
    w = NULLS[kind]().generate({"NQ": m.nq, "ES": m.es}, int(seed))
    return build_market(w["NQ"], w["ES"], m.nq_symbols, m.es_symbols)


def make_world(spec):
    k = spec["kind"]
    if k == "synthetic":
        return calibration_world(spec["plant"], int(spec["seed"]))
    if k == "synthetic_null":
        return _null_of(calibration_world(spec["plant"], int(spec["world_seed"])), spec["null"], spec["null_seed"])
    if k in ("real_null", "real"):
        # The real market is re-loaded per world (ledgered read, ~6 s) instead of being cached next to the null
        # world: that keeps ~0.6 GB less resident (performance audit 2026-09-24; identical data and results).
        part = spec.get("partition", "DISCOVERY")
        m = load_market(part, purpose=f"run_worlds: {k} ({spec.get('null', '')})")
        if k == "real":
            return m
        out = _null_of(m, spec["null"], spec["null_seed"])
        del m
        return out
    raise ValueError(k)


def _ok(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        body = {k: v for k, v in d.items() if k != "summary_sha256"}
        return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() == d.get("summary_sha256")
    except Exception:          # noqa: BLE001
        return False


def main():
    jobs = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for job in jobs:
        out = ROOT / job["out"]
        if _ok(out):
            continue
        t0 = time.time()
        try:
            m = make_world(job["world"])
            save = job["world"].get("save_dir")
            s = run_world(m, first_year=2010, save_dir=(ROOT / save) if save else None)
        except Exception:      # noqa: BLE001
            print(f"JOB FAILED {job['id']}\n{traceback.format_exc()}", flush=True)
            raise
        s["job"] = job
        s["summary_sha256"] = hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(s, indent=1), encoding="utf-8")
        print(f"JOB DONE {job['id']} global_max_t={s['global_max_t']} n_pass={s['global_n_pass']} "
              f"{time.time() - t0:.0f}s", flush=True)
        del m
        gc.collect()
    print("ALL JOBS DONE", flush=True)


if __name__ == "__main__":
    main()
