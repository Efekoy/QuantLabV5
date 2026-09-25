"""Search-adjusted inference from world summaries (frozen with the preregistration).

For each family f: T_f = max t over ELIGIBLE candidates of that family (None -> -inf), P_f = number of
PASSING candidates. Global: T_G = max_f T_f, P_G = sum_f P_f.
p-value of an observed statistic against N null worlds of one kind:  p = (1 + #{null >= observed}) / (1 + N).
Decision (preregistered): family / global evidence if max(p_A, p_C) <= 0.05 (the conservative of the two
primary, edge-free nulls). Null B (path-preserving) is reported as secondary.
Resolution: the smallest attainable p is 1/(1+N); nothing finer is reported.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

FAMILIES = ("RET", "VOL", "VWAP", "PATH", "DIST", "JUMP", "PERS", "OPEN", "XMKT", "CAL", "TECH", "REOPEN", "SYM", "ML")


def _t(v):
    return -np.inf if v is None else float(v)


def stats(summary: dict) -> dict:
    fam = summary["families"]
    out = {f"T_{f}": _t(fam[f]["max_t"]) for f in FAMILIES if f in fam}
    out.update({f"P_{f}": int(fam[f]["n_pass"]) for f in FAMILIES if f in fam})
    out["T_G"] = max(out[f"T_{f}"] for f in FAMILIES if f in fam)
    out["P_G"] = sum(out[f"P_{f}"] for f in FAMILIES if f in fam)
    return out


def pvalue(obs: float, null_vals) -> float:
    nv = np.asarray(list(null_vals), dtype=float)
    return float((1 + np.sum(nv >= obs)) / (1 + len(nv)))


def load_summaries(paths) -> list[dict]:
    return [json.loads(Path(p).read_text(encoding="utf-8")) for p in paths]


def compare(real: dict, nulls_by_kind: dict[str, list[dict]]) -> dict:
    rs = stats(real)
    res = {"real": rs, "n_null": {k: len(v) for k, v in nulls_by_kind.items()}, "p": {}, "null_quantiles": {}}
    for k, lst in nulls_by_kind.items():
        ns = [stats(s) for s in lst]
        res["p"][k] = {key: pvalue(rs[key], [x[key] for x in ns]) for key in rs}
        res["null_quantiles"][k] = {key: {q: float(np.quantile([x[key] for x in ns], q)) if ns else None
                                          for q in (0.5, 0.9, 0.95, 0.99)} for key in rs}
    prim = [k for k in ("A", "C") if k in res["p"] and res["n_null"][k] > 0]
    res["decision_p"] = {key: max(res["p"][k][key] for k in prim) for key in rs} if prim else {}
    res["resolution"] = {k: 1.0 / (1 + n) for k, n in res["n_null"].items()}
    return res
