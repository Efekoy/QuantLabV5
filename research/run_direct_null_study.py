"""Restricted direct-null diagnostic worker; never emits original OHLCV."""
from __future__ import annotations

import json
import subprocess

import numpy as np

from quantlab5.direct_null.access import FREEZE, LEDGER, close, scope
from quantlab5.direct_null.methods import METHODS, transform
from quantlab5.isolation import ledger
from quantlab5.isolation.load_view import load_view
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import file_sha256
from research.check_v5_1_nuisance import _corr, _lag, diagnose

READS_MARKET_DATA = True
OUT = ROOT / "reports/V5_DIRECT_NULL_DIAGNOSTICS.json"
START, END = "2010-06-08", "2018-12-31"
COLUMNS = ["open", "high", "low", "close", "volume", "symbol"]
SEEDS = (9101, 9102, 9103)


class _DirectWorld:
    def __init__(self, source, tape, artifact, method):
        self.source, self.tape, self.artifact, self.mode = source, tape, artifact, method

    def generate_seed(self, seed):
        return transform(self.source, self.mode, seed)


def _structural(world, source):
    result = {}
    for inst in ("NQ", "ES"):
        b, r = world[inst], source[inst]
        arrays = [np.asarray(getattr(b, x)) for x in ("o", "h", "l", "c", "v")]
        result[inst] = bool(
            all(np.isfinite(x).all() for x in arrays)
            and all(np.min(x) > 0 for x in arrays[:4])
            and np.min(b.v) >= 0
            and np.all(b.h >= np.maximum(b.o, b.c))
            and np.all(b.l <= np.minimum(b.o, b.c))
            and np.all(np.diff(b.ts) > 0)
            and np.array_equal(b.ts, r.ts)
            and np.array_equal(b.seg, r.seg))
    return result


def _directional(world):
    """Frozen extra close-close/gap directional checks absent from V5.1."""
    out = {}
    signs = {}
    for inst in ("NQ", "ES"):
        b = world[inst]
        cc = np.asarray(b.c)-np.r_[b.o[0], b.c[:-1]]
        gap = np.asarray(b.o)-np.r_[b.o[0], b.c[:-1]]
        s = np.sign(cc)
        signs[inst] = s
        valid = s != 0
        prior = np.abs(cc[:-1])
        cut = np.median(prior)
        same = (b.sday[:-1] == b.sday[1:]) & (b.seg[:-1] == b.seg[1:])
        metrics = {f"cc_sign_autocorr_{k}": abs(_lag(s, b.sday, b.seg, k))
                   for k in (1, 2, 5, 30)}
        metrics.update({f"gap_sign_autocorr_{k}": abs(_lag(np.sign(gap), b.sday, b.seg, k))
                        for k in (1, 5)})
        metrics["cc_sign_bias"] = float(abs(np.mean(s[valid]))) if np.any(valid) else 0.0
        for label, mask in (("low", prior <= cut), ("high", prior > cut)):
            x = s[1:][same & mask]
            metrics[f"next_cc_sign_given_prior_magnitude_{label}"] = (
                float(abs(np.mean(x))) if len(x) else 0.0)
        out[inst] = metrics
    n, e = world["NQ"], world["ES"]
    pos = np.searchsorted(e.ts, n.ts)
    valid = pos < len(e.ts)
    valid[valid] &= e.ts[pos[valid]] == n.ts[valid]
    ni = np.flatnonzero(valid)
    ei = pos[ni]
    cross = {
        "NQ_to_ES_next_cc_sign": abs(_corr(signs["NQ"][ni[:-1]], signs["ES"][ei[1:]])),
        "ES_to_NQ_next_cc_sign": abs(_corr(signs["ES"][ei[:-1]], signs["NQ"][ni[1:]])),
    }
    return {"instruments": out, "cross_market": cross,
            "maximum": float(max(*[max(x.values()) for x in out.values()], *cross.values()))}


def main():
    if OUT.exists():
        raise RuntimeError("direct-null diagnostic output already exists")
    frozen = subprocess.run(["git", "show", "HEAD:V5_DIRECT_NULL_PROTOCOL_FREEZE.json"],
                            cwd=ROOT, capture_output=True, check=True).stdout
    if frozen != FREEZE.read_bytes():
        raise RuntimeError("direct-null protocol must be committed unchanged before access")
    project = default_project()
    with scope():
        ledger.append(LEDGER, "DIRECT_NULL_STUDY_OPEN", reason="frozen restricted worker")
        source = {}
        accesses = []
        for inst in ("NQ", "ES"):
            md = load_view(inst, "DISCOVERY", START, END, COLUMNS, project=project,
                           purpose="DIRECT_NULL_STRUCTURE_ACCESS")
            rec = ledger.append(LEDGER, "DATA_READ", ledger.ALLOWED,
                                "DIRECT_NULL_STRUCTURE_ACCESS", instrument=inst,
                                partition="DISCOVERY", start=START, end=END,
                                columns=COLUMNS, rows=len(md.frame),
                                partition_sha256=md.partition_sha256,
                                parent_v5_ledger_sequence=md.ledger_seq)
            accesses.append({"instrument": inst, "main_ledger_sequence": md.ledger_seq,
                             "study_ledger_sequence": rec["seq"]})
            source[inst] = md.bars()
        with np.load(ROOT / "reports/V5_1_NUISANCE_TAPE.npz", allow_pickle=False) as z:
            tape = {k: z[k] for k in z.files}
        artifact = json.loads((ROOT / "V5_1_DISCOVERY_NUISANCE_CALIBRATION.json").read_text())
        methods = {}
        for method in METHODS:
            rows = []
            model = _DirectWorld(source, tape, artifact, method)
            for seed in SEEDS:
                try:
                    world = model.generate_seed(seed)
                    structural = _structural(world, source)
                    nuisance = diagnose(model, seed)
                    extra = _directional(world)
                    zero_edge = bool(nuisance["zero_edge_pass"] and extra["maximum"] <= .01)
                    rows.append({"seed": seed, "structural": structural,
                                 "nuisance": nuisance, "extra_directional": extra,
                                 "zero_edge_pass": zero_edge,
                                 "pass": bool(all(structural.values()) and nuisance["nuisance_pass"]
                                              and zero_edge)})
                except (ValueError, FloatingPointError, OverflowError) as exc:
                    rows.append({"seed": seed, "pass": False, "generation_error": str(exc)})
            methods[method] = rows
        passing = [m for m in METHODS if all(x["pass"] for x in methods[m])]
        selected = passing[0] if passing else None
        report = {"kind": "V5_DIRECT_NULL_FROZEN_DIAGNOSTICS",
                  "protocol_freeze_sha256": file_sha256(FREEZE),
                  "methods_in_frozen_priority": list(METHODS), "seeds": list(SEEDS),
                  "methods": methods, "selected_method": selected,
                  "status": "PASS" if selected else "FAIL_DIRECT_NULL_DIAGNOSTICS",
                  "accesses": accesses, "original_discovery_strategy_outcomes_calculated": 0,
                  "raw_discovery_bars_exported": 0}
        OUT.write_text(json.dumps(report, sort_keys=True, indent=2)+"\n", encoding="utf-8")
        ledger.append(LEDGER, "DIRECT_NULL_STUDY_CLOSED", reason=report["status"],
                      report_sha256=file_sha256(OUT))
        close()
    if selected is None:
        raise SystemExit("No frozen direct-null method passed all gates; STOP")


if __name__ == "__main__":
    main()
