"""Copy proven INFRASTRUCTURE from QuantLabV4 into QuantLabV5 and rename it to `quantlab5` (run once).

    python tools/copy_v4_infra.py

Step 1 (copy): every file in COPIES is copied byte-for-byte from V4 (git HEAD of the V4 working tree;
          each source is checked to be git-tracked and unmodified there) and its SHA-256 is recorded.
Step 2 (mechanical port): the package is renamed quantlab4 -> quantlab5 and the V4 campaign sub-package
          `quantlab4.v4` is re-homed into the V5 layout (IMPORT_MAP). Only import paths / package names
          change in this step; the hash after it is recorded too.
Step 3 (manual adaptation, later): V5-specific changes (partition/stage names, vault, candidate-ID prefix,
          no-cap rule). The final hashes are written by tools/write_provenance.py into
          provenance/V4_COPIED_FILES_FINAL.json, with a flag for every file changed after step 2.

Nothing from V4's strategy survivors, results, cohorts, freezes, ledgers, preregistration numbers or
research scripts (s03..s12, p01..p09) is copied into the active V5 tree. V4's reports and catalogs go
to docs/prior_labs/ via tools/collect_prior_labs.py, as reference material only.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

V5 = Path(__file__).resolve().parents[1]
V4 = V5.parent / "QuantLabV4"

# The V4 campaign sub-package quantlab4/v4/* is split into the V5 layout.
V4SUB = {
    "ops": ("features/ops.py", "quantlab5.features.ops"),
    "featurelib": ("features/library.py", "quantlab5.features.library"),
    "market": ("data/market.py", "quantlab5.data.market"),
    "synth": ("synthetic/market_builders.py", "quantlab5.synthetic.market_builders"),
    "outcomes": ("engine/outcomes.py", "quantlab5.engine.outcomes"),
    "kernel": ("search/kernel.py", "quantlab5.search.kernel"),
    "grammar": ("search/reference_grammar.py", "quantlab5.search.reference_grammar"),
    "screen": ("search/reference_screen.py", "quantlab5.search.reference_screen"),
    "world": ("search/world.py", "quantlab5.search.world"),
    "ml": ("search/ml.py", "quantlab5.search.ml"),
    "analysis": ("search/analysis.py", "quantlab5.search.analysis"),
    "inference": ("nulls/inference.py", "quantlab5.nulls.inference"),
    "propsim": ("prop/propsim.py", "quantlab5.prop.propsim"),
}

PKG_DIRS = ("bootstrap", "data", "diagnostics", "engine", "features", "isolation", "nulls", "prop", "risk",
            "search", "synthetic", "util", "validation")

TESTS_RENAMED = {"test_v4_pipeline.py": "test_search_pipeline.py",
                 "test_v4_optimizations.py": "test_performance_optimizations.py",
                 "test_v4_propsim.py": "test_propsim.py"}

OTHER = [
    ("pyproject.toml", "pyproject.toml", "package metadata"),
    (".gitignore", ".gitignore", "git ignore rules (market data never enters git)"),
    ("config/costs.yaml", "config/costs.yaml", "trading costs (inherited V3/V4 values)"),
    ("config/execution.yaml", "config/execution.yaml", "execution policy"),
    ("config/nulls.yaml", "config/nulls.yaml", "null generator settings"),
    ("config/paths.yaml", "config/paths.yaml", "physical locations (rewritten for V5)"),
    ("config/prop_profiles.yaml", "config/prop_profiles.yaml", "generic prop profiles"),
    ("config/search.yaml", "config/search.yaml", "candidate-ID / enumeration settings"),
    ("config/sessions.yaml", "config/sessions.yaml", "sessions / DST / windows"),
    ("config/stage_policy.yaml", "config/stage_policy.yaml", "stage machine (rewritten for V5 stages)"),
    ("research/s00_bootstrap.py", "research/s00_bootstrap.py", "privileged one-time partitioner run"),
    ("research/s01_discovery_data_audit.py", "research/s01_discovery_structural_check.py",
     "DISCOVERY structural counts (schema/volume/rolls)"),
    ("research/s02_bootstrap_freeze.py", "research/s02_bootstrap_freeze.py", "bootstrap freeze"),
    ("research/run_worlds.py", "research/run_worlds.py", "resumable world runner (checkpoint/resume)"),
    ("tools/check_isolation.py", "tools/check_isolation.py", "OS isolation probe"),
    ("tools/write_provenance.py", "tools/write_provenance.py", "provenance writer"),
    ("tools/harden_isolation.ps1", "tools/harden_isolation.ps1", "OS isolation hardening (manual)"),
    ("tools/ingest_live_forward.py", "tools/ingest_live_forward.py", "LIVE_FORWARD ingestion command"),
    ("docs/ARCHITECTURE.md", "docs/ARCHITECTURE.md", "architecture notes (rewritten for V5)"),
    ("docs/OS_ISOLATION.md", "docs/OS_ISOLATION.md", "OS isolation notes (rewritten for V5)"),
]

NOT_COPIED = [
    "quantlab4 is copied in full (re-homed); nothing in the package was left out",
    "config/prereg_v4.yaml (V4 campaign-1 preregistered numbers) -> docs/prior_labs/V4 only",
    "config/partitions.json (V4 registry/hashes) -> V5 writes its own registry at bootstrap",
    "research/s03..s12, p01..p09 (V4 campaign research/post-hoc scripts)",
    "results/**, freezes/**, ledgers/**, provenance/** (V4 campaign state and outputs)",
    "V4_*.md / V4_*.json reports -> docs/prior_labs/V4 only (reference, never an input)",
    "tools/copy_v3_engine.py, bench_*.py, profile_world.py, verify_world.py, dump_world_hashes.py "
    "(one-off V4 tools tied to V4 result files)",
    "data/discovery/*.parquet (V5 re-partitions from the original source files)",
    "output/pdf/* (V4 report PDF) -> docs/prior_labs/V4 only",
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(root: Path, *a) -> str:
    return subprocess.check_output(["git", "-C", str(root), *a], text=True).strip()


def build_copies() -> list[tuple[str, str, str]]:
    out = []
    for f in sorted((V4 / "quantlab4").glob("*.py")):
        out.append((f"quantlab4/{f.name}", f"quantlab5/{f.name}", "package root"))
    for d in PKG_DIRS:
        for f in sorted((V4 / "quantlab4" / d).glob("*.py")):
            out.append((f"quantlab4/{d}/{f.name}", f"quantlab5/{d}/{f.name}", f"infrastructure: {d}"))
    for mod, (dst, _imp) in V4SUB.items():
        out.append((f"quantlab4/v4/{mod}.py", f"quantlab5/{dst}", f"V4 campaign module re-homed: {mod}"))
    for f in sorted((V4 / "tests").glob("*.py")):
        out.append((f"tests/{f.name}", f"tests/{TESTS_RENAMED.get(f.name, f.name)}", "inherited test"))
    for f in sorted((V4 / "tests" / "fixtures").glob("*")) if (V4 / "tests" / "fixtures").exists() else []:
        if f.is_file():
            out.append((f"tests/fixtures/{f.name}", f"tests/fixtures/{f.name}", "test fixture"))
    out += OTHER
    return out


_V4_IMPORT = re.compile(r"from quantlab4\.v4 import (\w+)( as \w+)?")
_V4_DOTTED = re.compile(r"quantlab4\.v4\.(\w+)")


def mechanical_port(text: str) -> str:
    def _imp(m):
        mod = m.group(1)
        pkg, name = V4SUB[mod][1].rsplit(".", 1)
        return f"from {pkg} import {name}{m.group(2) or f' as {mod}'}"
    text = _V4_IMPORT.sub(_imp, text)
    text = _V4_DOTTED.sub(lambda m: V4SUB[m.group(1)][1], text)
    return text.replace("quantlab4", "quantlab5")


def main() -> None:
    out = V5 / "provenance" / "V4_COPIED_FILES.json"
    if out.exists():
        raise SystemExit(f"{out} exists; the copy is a one-time step")
    head = git(V4, "rev-parse", "HEAD")
    dirty = set(x[3:] for x in git(V4, "status", "--porcelain").splitlines())
    tracked = set(git(V4, "ls-files").splitlines())
    recs = []
    for src_rel, dst_rel, why in build_copies():
        src, dst = V4 / src_rel, V5 / dst_rel
        if src_rel not in tracked or src_rel in dirty:
            raise SystemExit(f"{src_rel} is not a clean, committed V4 file")
        if dst.exists():
            raise SystemExit(f"refusing to overwrite {dst}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        at_copy = sha(dst)
        assert at_copy == sha(src)
        ported = False
        if dst.suffix in (".py", ".toml", ".ps1", ".md", ".yaml") and dst_rel != ".gitignore":
            t = dst.read_text(encoding="utf-8")
            t2 = mechanical_port(t)
            if t2 != t:
                dst.write_text(t2, encoding="utf-8", newline="")
                ported = True
        recs.append({"source": src_rel, "source_sha256": sha(src), "destination": dst_rel,
                     "destination_sha256_at_copy": at_copy, "destination_sha256_after_rename": sha(dst),
                     "renamed": ported, "purpose": why})
    for d in ("quantlab5",) + tuple(f"quantlab5/{d}" for d in PKG_DIRS):
        init = V5 / d / "__init__.py"
        if not init.exists():
            init.write_text("", encoding="utf-8")
    doc = {"copied_utc": datetime.now(timezone.utc).isoformat(), "v4_root": str(V4), "v4_git_head": head,
           "v4_working_tree_note": "V4 had uncommitted files (post-hoc reports, ledgers); none of them was copied "
                                   "into the active tree -- every copied source is committed and unmodified at HEAD",
           "import_map_v4_subpackage": {k: v[1] for k, v in V4SUB.items()}, "files": recs,
           "not_copied": NOT_COPIED}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"copied {len(recs)} files from V4 {head[:12]}; {sum(r['renamed'] for r in recs)} renamed; -> {out}")


if __name__ == "__main__":
    main()
