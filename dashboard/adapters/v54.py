import json
from pathlib import Path
from .base import LabAdapter

ROOT = Path(__file__).resolve().parents[2]


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def rows(relative):
    with (ROOT / relative).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


class V54Adapter(LabAdapter):
    id = "v5.4"

    def __init__(self):
        self._audits = None
        self._cohort_validation = {}

    def get_lab_metadata(self):
        complete = read_json("V5_4_COMPLETE_RESEARCH_FREEZE.json")
        validation = read_json("V5_4_VALIDATION_FREEZE.json")
        return {"id": self.id, "name": "V5.4 Broad Search", "version": "V5.4", "root_path": str(ROOT),
                "status": "COMPLETE", "current_stage": "HISTORICAL AUDITS COMPLETE",
                "searched": complete["specifications_evaluated"], "discovery": complete["discovery_qualifiers"],
                "supported": validation["supported_count"], "dual_supported": len(complete["dual_audit_supported_ids"]),
                "live_forward_sealed": complete["live_forward_sealed"]}

    def get_run_status(self):
        progress = read_json("reports/v54/progress.json")
        return {"id": "v54-discovery", "lab_id": self.id, "name": "V5.4 Broad Discovery", "stage": "DISCOVERY",
                "status": "COMPLETE", "evaluated": progress["completed_rows"], "total": progress["total_specs"],
                "checkpoint": progress["completed_rows"], "source": "reports/v54/progress.json"}

    def get_strategies(self):
        cohort = set(read_json("V5_4_SCIENTIFIC_COHORT_FREEZE.json")["candidate_ids"])
        for record in rows("reports/V5_4_VALIDATION_RESULTS.jsonl"):
            if record["candidate_id"] in cohort:
                self._cohort_validation[record["candidate_id"]] = record
            yield record

    def get_stage_results(self, candidate_id):
        if self._audits is None:
            self._audits = read_json("reports/V5_4_HISTORICAL_AUDIT_RESULTS.json")["audits"]
        audits = self._audits
        return {"audit_1": audits["phase1"].get(candidate_id), "audit_2": audits["phase2"].get(candidate_id)}

    def get_equity_curves(self, candidate_id):
        if candidate_id not in self._cohort_validation:
            for record in rows("reports/V5_4_VALIDATION_RESULTS.jsonl"):
                if record["candidate_id"] == candidate_id:
                    self._cohort_validation[candidate_id] = record
                    break
        record = self._cohort_validation.get(candidate_id)
        if not record:
            return {}
        curves = {"validation": record["validation"]["daily_net_r"]}
        for stage, path in (("discovery", "reports/v54/qualifier_details.jsonl"),
                            ("audit_1", "reports/v54/phase1_sealed.jsonl"),
                            ("audit_2", "reports/v54/phase2_sealed.jsonl")):
            for result in rows(path):
                if result["candidate_id"] == candidate_id:
                    curves[stage] = result["trade_net_r" if stage == "discovery" else "daily_net_r"]
                    break
        return curves

    def get_relationships(self, candidate_id):
        specs = read_json("V5_4_SCIENTIFIC_COHORT_FREEZE.json")["specs"]
        if candidate_id not in specs:
            return []
        return [{"related_id": other, "kind": "same_family"} for other, spec in specs.items()
                if other != candidate_id and spec["family"] == specs[candidate_id]["family"]]

    def get_protocol_state(self):
        complete = read_json("V5_4_COMPLETE_RESEARCH_FREEZE.json")
        return {"audits_revealed": read_json("V5_4_BOTH_HISTORICAL_AUDITS_COMPLETE.json")["simultaneous_reveal"],
                "live_forward_sealed": complete["live_forward_sealed"], "stage_frozen": True}
