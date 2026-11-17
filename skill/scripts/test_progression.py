"""Unit tests for the progressive persona scenarios (no application test)."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from progression import build, validate, LEVELS, KINDS, main as progression_main
from release_gate import assess


class ProgressionTests(unittest.TestCase):
    def test_matrix_generation_creates_ten_scenarios_per_flow(self):
        m = build("cliente", "Cliente", ["registro", "pago"])
        self.assertEqual(len(m["required_scenarios"]), 20)
        self.assertEqual(validate(m), [])
        self.assertEqual([x["level"] for x in m["required_scenarios"][::2]], list(LEVELS) * 2)

    def test_missing_level_blocks_plan(self):
        m = build("cliente", "Cliente", ["registro"])
        m["required_scenarios"] = [s for s in m["required_scenarios"] if s["level"] != "erratico"]
        self.assertTrue(validate(m))

    def test_duplicate_scenario_blocks_plan(self):
        m = build("cliente", "Cliente", ["registro"])
        m["required_scenarios"].append(copy.deepcopy(m["required_scenarios"][0]))
        self.assertTrue(validate(m))

    def test_cli_creates_only_not_run_plan(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "plan.json"
            self.assertEqual(progression_main(["plan", "--actor", "cliente", "--role", "Cliente",
                                               "--flow", "registro", "--output", str(target)]), 0)
            self.assertTrue(all(s["status"] == "not_run" for s in json.loads(target.read_text())["required_scenarios"]))
            self.assertEqual(progression_main(["validate", str(target)]), 0)
            self.assertEqual(progression_main(["plan", "--actor", "cliente", "--role", "Cliente",
                                               "--flow", "registro", "--output", str(target)]), 2)

    def fixture(self, directory: Path):
        (directory / "evidence.log").write_text("synthetic fixture, not application evidence", encoding="utf-8")
        matrix = build("cliente", "Cliente", ["registro"])
        report = {
            "project": "fixture", "environment": "staging", "build": "v1", "timestamp": "2026-11-16T00:00:00Z",
            "critical_flows": ["registro"], "full_suite_executed": True, "full_suite_evidence": ["evidence.log"],
            "production_parity_verified": True, "production_parity_evidence": ["evidence.log"],
            "stakeholder_coverage": {"actors": [{"id": "cliente", "role": "Cliente", "context": "web",
                                                 "type": "person", "critical": True, "source": "observed"}],
                                     "required_scenarios": [{"id": "S1", "actor_id": "cliente", "flow": "registro",
                                                             "expected_outcome": "registro válido", "risk": "alta"}]},
            "human_factors": {"applicable": False, "not_applicable_reason": "fixture artificial de API (real sería aplicable)"},
            "progressive_audit": {"applicable": True, "tracks": matrix["tracks"],
                                  "required_scenarios": [{k: s[k] for k in ("id", "actor_id", "flow", "level", "kind", "expected_recovery")}
                                                         for s in matrix["required_scenarios"]]},
            "tests": [], "findings": [], "limitations": []
        }
        for i, s in enumerate(matrix["required_scenarios"]):
            report["tests"].append({"id": f"T{i}", "flow": "registro", "critical": True, "status": "passed",
                                    "action": "fixture", "expected": "paso de fixture", "observed": "paso de fixture",
                                    "evidence": ["evidence.log"], "tested_build": "v1", "progressive_scenario_id": s["id"],
                                    "stakeholder_scenario_id": "S1"})
        return report

    def test_no_progresion_in_human_role_blocks_release(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.fixture(Path(d))
            del p["progressive_audit"]
            out = assess(p, Path(d))
            self.assertEqual(out["verdict"], "INCOMPLETE")
            self.assertTrue(any("progressive_audit" in x for x in out["incomplete"]))

    def test_five_levels_all_evidenced_are_gate_candidate_in_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.fixture(Path(d))
            self.assertEqual(assess(p, Path(d))["verdict"], "READY_CANDIDATE")

    def test_one_level_unexecuted_is_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.fixture(Path(d))
            p["tests"][3]["status"] = "not_run"
            self.assertEqual(assess(p, Path(d))["verdict"], "INCOMPLETE")

    def test_wrong_build_is_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.fixture(Path(d))
            p["tests"][5]["tested_build"] = "older"
            self.assertEqual(assess(p, Path(d))["verdict"], "INCOMPLETE")

    def test_error_scenario_failed_blocks_release(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.fixture(Path(d))
            p["tests"][0]["status"] = "failed"
            self.assertEqual(assess(p, Path(d))["verdict"], "NO_GO")

    def test_missing_positive_case_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.fixture(Path(d))
            p["progressive_audit"]["required_scenarios"].pop()
            self.assertEqual(assess(p, Path(d))["verdict"], "INCOMPLETE")

    def test_missing_test_evidence_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.fixture(Path(d))
            p["tests"][1]["evidence"] = []
            self.assertEqual(assess(p, Path(d))["verdict"], "INCOMPLETE")


if __name__ == "__main__":
    unittest.main()

# These are standalone checks in the same module; unittest discovery picks them up.
class CustomProgressionProfileTests(unittest.TestCase):
    def test_person_profile_accepts_per_level_customization(self):
        from profiles import new_profile, validate_profile
        profile = new_profile("sample-actor", "Sample", "Cliente", "person")
        profile["progression"]["levels"][0]["error_patterns"] = ["Sube documento equivocado"]
        self.assertEqual(validate_profile(profile), [])
        profile["progression"]["levels"][0]["error_patterns"] = []
        self.assertTrue(validate_profile(profile))

    def test_custom_driver_matrix_respects_custom_error_actions(self):
        from profiles import load_profile
        profile = load_profile(Path(__file__).parents[2] / "examples" / "custom-profiles" / "driver-shift-checkin.json")
        overrides = {x["id"]: x for x in profile["progression"]["levels"]}
        plan = build(profile["id"], profile["actor"]["role"], profile["critical_flows"], overrides)
        self.assertIn("Fotografía zapatos", plan["required_scenarios"][0]["proposed_action"])
        self.assertEqual(validate(plan), [])
