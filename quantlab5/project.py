"""Project context: where things are and what the configuration says.

A `Project` is passed to every guarded API (load_view, stage transitions, forward
ingestion). Tests build a throw-away Project over a synthetic root + synthetic vault;
research uses `default_project()`. Nothing here reads market data.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_FILES = ("partitions.json", "costs.yaml", "sessions.yaml", "stage_policy.yaml", "search.yaml",
                "nulls.yaml", "prop_profiles.yaml", "execution.yaml", "paths.yaml")


@dataclass
class Project:
    root: Path
    vault: Path
    _cache: dict = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------ config
    def config_path(self, name: str) -> Path:
        return self.root / "config" / name

    def yaml(self, name: str) -> dict:
        p = self.config_path(name)
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    def partitions(self) -> dict:
        """Re-read on every call: the registry must never be served from a stale copy."""
        return json.loads(self.config_path("partitions.json").read_text(encoding="utf-8"))

    @property
    def stage_policy(self) -> dict:
        if "stage_policy" not in self._cache:
            self._cache["stage_policy"] = self.yaml("stage_policy.yaml")
        return self._cache["stage_policy"]

    @property
    def sessions(self) -> dict:
        return self.yaml("sessions.yaml")

    @property
    def costs(self) -> dict:
        return self.yaml("costs.yaml")

    @property
    def paths(self) -> dict:
        return self.yaml("paths.yaml")

    # ------------------------------------------------------------------ locations
    @property
    def ledger_path(self) -> Path:
        return self.root / self.stage_policy["ledger"]

    @property
    def stage_state_path(self) -> Path:
        return self.root / self.stage_policy["stage_state"]

    @property
    def freezes_dir(self) -> Path:
        return self.root / "freezes"

    def freeze_path(self, kind: str) -> Path:
        return self.root / self.stage_policy["freezes"][kind]

    @property
    def discovery_dir(self) -> Path:
        return self.root / self.paths.get("discovery_dir", "data/discovery")

    @property
    def forward_inbox(self) -> Path:
        return self.vault / "LIVE_FORWARD" / "inbox"

    @property
    def forward_accepted(self) -> Path:
        return self.vault / "LIVE_FORWARD" / "accepted"

    def raw_sources(self) -> dict[str, Path]:
        return {k: Path(v) for k, v in (self.paths.get("raw_sources") or {}).items()}


def default_project() -> Project:
    paths = yaml.safe_load((ROOT / "config" / "paths.yaml").read_text(encoding="utf-8"))
    return Project(root=ROOT, vault=Path(paths["vault"]))
