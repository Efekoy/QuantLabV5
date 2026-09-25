"""Static guard: research code never opens market-data files directly.
(Ported from QuantLabV4; V5 adds the V2-V5 vaults, earlier labs' data folders and docs/prior_labs.)

Only two modules may read parquet/CSV market data:
  quantlab5/isolation/load_view.py      (the single guarded entry point)
  quantlab5/bootstrap/partitioner.py    (privileged one-time bootstrap)
plus quantlab5/isolation/forward.py (privileged forward ingestion). Everything under
research/ and the rest of quantlab5/ must go through load_view.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"quantlab5/isolation/load_view.py", "quantlab5/bootstrap/partitioner.py", "quantlab5/isolation/forward.py",
           "research/s00_bootstrap.py"}
PATTERNS = [r"read_parquet", r"read_csv", r"pyarrow\.parquet", r"pyarrow\.dataset", r"\bpq\.", r"\bpads\.",
            r"ParquetFile", r"read_table", r"\.parquet['\"]", r"nq_continuous_front", r"es_continuous_front",
            r"QuantLabV[2-5]_Vault", r"Quant[\\/]+data", r"QuantLabV[2-4][\\/]+data", r"docs[\\/]+prior_labs", r"[\\/]prior_labs\b", r"['\"]prior_labs['\"]"]


def _files():
    for base in ("research", "quantlab5"):
        for p in (ROOT / base).rglob("*.py"):
            yield p.relative_to(ROOT).as_posix(), p.read_text(encoding="utf-8")


def test_no_module_outside_the_allow_list_reads_market_files():
    offenders = []
    for rel, text in _files():
        if rel in ALLOWED:
            continue
        for pat in PATTERNS:
            if re.search(pat, text):
                offenders.append(f"{rel}: {pat}")
    assert offenders == []


def test_research_scripts_use_load_view_or_declare_no_data():
    """Every research script (except the privileged s00) either uses load_view / load_bars or declares
    READS_MARKET_DATA = False. (Direct file access is separately forbidden above.)"""
    for p in sorted((ROOT / "research").glob("s[0-9]*.py")):
        if p.name.startswith("s00_"):
            continue
        t = p.read_text(encoding="utf-8")
        assert ("load_view" in t or "load_bars" in t or "load_market" in t
                or "READS_MARKET_DATA = False" in t), p.name


def test_raw_source_paths_appear_only_in_config():
    hits = [rel for rel, text in _files() if "nq_continuous_front_1m" in text and rel not in ALLOWED]
    assert hits == []
