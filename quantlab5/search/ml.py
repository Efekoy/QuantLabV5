"""Simple-ML family (frozen with the preregistration). The identical procedure runs in every null world.

Walk-forward, anchored, strictly chronological (NO random K-fold). DISCOVERY folds (by session year):
  train <= 2012 -> test 2013-2014 ; train <= 2014 -> test 2015-2016 ; train <= 2016 -> test 2017-2018
Training rows: every 10th decision bar (reduces label overlap and cost). Purging: training rows whose
label interval [t, t+H] reaches the first test bar are removed (quantlab5.validation.purging).
Features: the causal ML subset of the feature library (WorldFeatures.F), median-imputed and
standardised with TRAINING statistics only.
Targets: fwd_H = log(c[t+H]/c[t]) / (sig1[t] sqrt(H)) within the session, clipped to +-5, H in
15/30/60/120; and 'barrier' = 1 if a long 2R-target/1x-stop trade (exit S1_R2) is profitable.
Models: ridge (alpha 10, 1000), decision tree (depth 3, min leaf 2000), HistGradientBoosting
(40 iterations, 8 leaves), logistic regression (C=0.1) for the barrier target only.
Signals: prediction above the training (1-q) quantile -> long event; below the q quantile -> short,
q in {0.05, 0.10}. Events are evaluated by the same kernel (variant cont_both, no filters, 14 exits).
"""
from __future__ import annotations

import numpy as np

from quantlab5.validation.purging import purge

FOLDS_DISCOVERY = (((2010, 2012), (2013, 2014)), ((2010, 2014), (2015, 2016)), ((2010, 2016), (2017, 2018)))
TARGETS = ("fwd15", "fwd30", "fwd60", "fwd120", "barrier")
REG_MODELS = ("ridge10", "ridge1000", "tree", "hgb")
QUANTILES = (0.05, 0.10)
SUBSAMPLE = 10
FSET_FAMILIES = {"PRICE": {"RET", "PATH", "DIST", "PERS", "JUMP", "TECH", "CAL", "BASE"},
                 "VOLUME": {"VOL", "VWAP", "XMKT", "OPEN"}, "ALL": None}


def signal_sets():
    out = []
    for fs in FSET_FAMILIES:
        for tg in TARGETS:
            models = ("logistic",) if tg == "barrier" else REG_MODELS
            for mdl in models:
                for q in QUANTILES:
                    out.append({"model": mdl, "target": tg, "fset": fs, "q": q})
    return out


def ml_spec(ss: dict, exit_id: str) -> dict:
    return {"grammar": "V4G1", "kind": "ML", "family": "ML", **ss, "exit": exit_id, "instrument": "NQ",
            "window": "rth", "folds": "anchored_2y_discovery", "subsample": SUBSAMPLE}


def _targets(m, W, pnl):
    c = np.asarray(m.nq.c, np.float64)
    g = m.gid
    dec = m.dec
    sig1 = np.asarray(W.F["sig1"], np.float64) if "sig1" in W.F else None
    out, horizon = {}, {}
    n = len(c)
    for H in (15, 30, 60, 120):
        j = np.minimum(dec + H, n - 1)
        ok = (dec + H < n) & (g[j] == g[dec])
        y = np.log(c[j] / c[dec])
        out[f"fwd{H}"] = np.where(ok, y, np.nan)
        horizon[f"fwd{H}"] = H
    out["barrier"] = np.where(np.isfinite(pnl[5, :, 0]), (pnl[5, :, 0] > 0).astype(float), np.nan)
    horizon["barrier"] = 390
    return out, horizon, sig1


def _fit_predict(model, Xtr, ytr, Xte, is_cls):
    if model.startswith("ridge"):
        a = float(model[5:])
        Xa = np.c_[np.ones(len(Xtr)), Xtr]
        A = Xa.T @ Xa + a * np.diag(np.r_[0.0, np.ones(Xtr.shape[1])])
        w = np.linalg.solve(A, Xa.T @ ytr)
        return w[0] + Xte @ w[1:], w[0] + Xtr @ w[1:]
    if model == "tree":
        from sklearn.tree import DecisionTreeRegressor
        mdl = DecisionTreeRegressor(max_depth=3, min_samples_leaf=2000, random_state=0).fit(Xtr, ytr)
    elif model == "hgb":
        from sklearn.ensemble import HistGradientBoostingRegressor
        mdl = HistGradientBoostingRegressor(max_iter=40, max_leaf_nodes=8, learning_rate=0.1,
                                            early_stopping=False, random_state=0).fit(Xtr, ytr)
    elif model == "logistic":
        from sklearn.linear_model import LogisticRegression
        mdl = LogisticRegression(C=0.1, max_iter=300).fit(Xtr, ytr.astype(int))
        return mdl.predict_proba(Xte)[:, 1], mdl.predict_proba(Xtr)[:, 1]
    else:
        raise ValueError(model)
    return mdl.predict(Xte), mdl.predict(Xtr)


def ml_events(m, W, pnl, years_dec, folds=FOLDS_DISCOVERY):
    """Returns list of (signal_set_dict, pos int64 sorted, sign int64)."""
    names = [r["name"] for r in W.catalog if r["name"] in W.F and r["name"] != "sig1"]
    fam = {r["name"]: r["family"] for r in W.catalog}
    X_all = np.column_stack([W.F[nm].astype(np.float64) for nm in names])
    Y, Hor, _ = _targets(m, W, pnl)
    sig1 = np.asarray(W.F["sig1"], np.float64)
    events = {}
    for (tr0, tr1), (te0, te1) in folds:
        tr_mask = (years_dec >= tr0) & (years_dec <= tr1)
        te_mask = (years_dec >= te0) & (years_dec <= te1)
        te_idx = np.nonzero(te_mask)[0]
        if len(te_idx) == 0:
            continue
        tr_idx = np.nonzero(tr_mask)[0][::SUBSAMPLE]
        first_test_bar = int(m.dec[te_idx[0]])
        for fs, fams in FSET_FAMILIES.items():
            cols = [i for i, nm in enumerate(names) if fams is None or fam[nm] in fams]
            Xtr_raw, Xte_raw = X_all[np.ix_(tr_idx, cols)], X_all[np.ix_(te_idx, cols)]
            med = np.nanmedian(Xtr_raw, axis=0)
            med = np.where(np.isfinite(med), med, 0.0)
            Xtr = np.where(np.isfinite(Xtr_raw), Xtr_raw, med)
            Xte = np.where(np.isfinite(Xte_raw), Xte_raw, med)
            mu, sd = Xtr.mean(0), Xtr.std(0)
            sd = np.where(sd > 0, sd, 1.0)
            Xtr, Xte = np.clip((Xtr - mu) / sd, -10, 10), np.clip((Xte - mu) / sd, -10, 10)
            for tg in TARGETS:
                y = Y[tg][tr_idx]
                if tg != "barrier":
                    H = Hor[tg]
                    y = np.clip(y / (sig1[tr_idx] * np.sqrt(H)), -5, 5)
                ok = np.isfinite(y)
                t_bar = m.dec[tr_idx]
                keep = purge(np.arange(len(tr_idx)), t_bar, t_bar + Hor[tg], [(first_test_bar, 10 ** 12)])
                ok &= np.isin(np.arange(len(tr_idx)), keep)
                if ok.sum() < 500:
                    continue
                models = ("logistic",) if tg == "barrier" else REG_MODELS
                for mdl in models:
                    p_te, p_tr = _fit_predict(mdl, Xtr[ok], y[ok], Xte, tg == "barrier")
                    for q in QUANTILES:
                        hi, lo = np.quantile(p_tr, 1 - q), np.quantile(p_tr, q)
                        key = (mdl, tg, fs, q)
                        sg = np.where(p_te > hi, 1, np.where(p_te < lo, -1, 0))
                        sel = sg != 0
                        prev = events.get(key, (np.zeros(0, np.int64), np.zeros(0, np.int64)))
                        events[key] = (np.r_[prev[0], te_idx[sel]], np.r_[prev[1], sg[sel]])
    out = []
    for ss in signal_sets():
        key = (ss["model"], ss["target"], ss["fset"], ss["q"])
        pos, sg = events.get(key, (np.zeros(0, np.int64), np.zeros(0, np.int64)))
        o = np.argsort(pos, kind="stable")
        out.append((ss, pos[o].astype(np.int64), sg[o].astype(np.int64)))
    return out


# ---------------------------------------------------------------- frozen models for later periods
def _design(W, fams):
    fam = {r["name"]: r["family"] for r in W.catalog}
    names = [r["name"] for r in W.catalog if r["name"] in W.F and r["name"] != "sig1"
             and (fams is None or fam[r["name"]] in fams)]
    return names, np.column_stack([W.F[nm].astype(np.float64) for nm in names])


def fit_frozen(m, W, pnl, ss: dict, years_dec, train_years=(2010, 2018)) -> dict:
    """Fit ONE signal set on all DISCOVERY decision bars (every SUBSAMPLE-th), same hyperparameters.
    Returns a picklable dict with preprocessing, model and the training-prediction quantile thresholds."""
    import pickle
    names, X = _design(W, FSET_FAMILIES[ss["fset"]])
    idx = np.nonzero((years_dec >= train_years[0]) & (years_dec <= train_years[1]))[0][::SUBSAMPLE]
    Y, Hor, _ = _targets(m, W, pnl)
    sig1 = np.asarray(W.F["sig1"], np.float64)
    y = Y[ss["target"]][idx]
    if ss["target"] != "barrier":
        y = np.clip(y / (sig1[idx] * np.sqrt(Hor[ss["target"]])), -5, 5)
    Xtr_raw = X[idx]
    med = np.nanmedian(Xtr_raw, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    Xtr = np.where(np.isfinite(Xtr_raw), Xtr_raw, med)
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd = np.where(sd > 0, sd, 1.0)
    Xtr = np.clip((Xtr - mu) / sd, -10, 10)
    ok = np.isfinite(y)
    model = _fit_model(ss["model"], Xtr[ok], y[ok])
    p_tr = _predict(model, Xtr[ok])
    return {"ss": ss, "names": names, "med": med, "mu": mu, "sd": sd, "model": pickle.dumps(model),
            "hi": float(np.quantile(p_tr, 1 - ss["q"])), "lo": float(np.quantile(p_tr, ss["q"]))}


def _fit_model(model, X, y):
    if model.startswith("ridge"):
        a = float(model[5:])
        Xa = np.c_[np.ones(len(X)), X]
        A = Xa.T @ Xa + a * np.diag(np.r_[0.0, np.ones(X.shape[1])])
        return ("ridge", np.linalg.solve(A, Xa.T @ y))
    if model == "tree":
        from sklearn.tree import DecisionTreeRegressor
        return DecisionTreeRegressor(max_depth=3, min_samples_leaf=2000, random_state=0).fit(X, y)
    if model == "hgb":
        from sklearn.ensemble import HistGradientBoostingRegressor
        return HistGradientBoostingRegressor(max_iter=40, max_leaf_nodes=8, learning_rate=0.1,
                                             early_stopping=False, random_state=0).fit(X, y)
    if model == "logistic":
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression(C=0.1, max_iter=300).fit(X, y.astype(int))
    raise ValueError(model)


def _predict(model, X):
    if isinstance(model, tuple) and model[0] == "ridge":
        w = model[1]
        return w[0] + X @ w[1:]
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    return model.predict(X)


def apply_frozen(frozen: dict, W, mask_dec=None):
    """Events (pos, sign) of a frozen model on any world W (optionally restricted to decision bars in mask)."""
    import pickle
    X = np.column_stack([W.F[nm].astype(np.float64) for nm in frozen["names"]])
    X = np.where(np.isfinite(X), X, frozen["med"])
    X = np.clip((X - frozen["mu"]) / frozen["sd"], -10, 10)
    p = _predict(pickle.loads(frozen["model"]), X)
    sg = np.where(p > frozen["hi"], 1, np.where(p < frozen["lo"], -1, 0))
    if mask_dec is not None:
        sg = np.where(mask_dec, sg, 0)
    pos = np.nonzero(sg)[0].astype(np.int64)
    return pos, sg[pos].astype(np.int64)
