"""Self-tests for report assessment logic. Run: python -m unittest discover -s scripts -p 'test_*.py'"""
import json
import tempfile
import unittest
from pathlib import Path
from release_gate import assess
from profiles import new_profile, validate_profile, load_profile, main as profiles_main


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        (self.dir / "evidence.log").write_text("sample test evidence", encoding="utf-8")
        self.report = {
            "project": "sample", "environment": "staging", "build": "abc123",
            "timestamp": "2026-11-16T00:00:00Z", "critical_flows": ["auth"],
            "full_suite_executed": True, "full_suite_evidence": ["evidence.log"],
            "production_parity_verified": True, "production_parity_evidence": ["evidence.log"],
            "tests": [{"id": "T1", "flow": "auth", "critical": True, "status": "passed",
                       "expected": "login success", "observed": "login success", "action": "playwright auth", "evidence": ["evidence.log"],
                       "stakeholder_scenario_id": "STA-01"}],
            "findings": [], "limitations": [],
            "stakeholder_coverage": {
                "actors": [{"id": "api-client", "role": "Consumidor API",
                            "context": "Cliente de API legítimo", "type": "system",
                            "source": "observed", "critical": True}],
                "required_scenarios": [{"id": "STA-01", "actor_id": "api-client", "flow": "auth",
                                        "expected_outcome": "Acceso con token válido",
                                        "risk": "Fallo de sesión"}]},
            "human_factors": {"applicable": False, "not_applicable_reason": "API sin UI: unidad de prueba"}}

    def test_candidate_when_all_evidenced(self):
        self.assertEqual(assess(self.report, self.dir)["verdict"], "READY_CANDIDATE")

    def test_missing_evidence_never_passes(self):
        self.report["tests"][0]["evidence"] = ["does-not-exist.png"]
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_failed_critical_blocks_release(self):
        self.report["tests"][0]["status"] = "failed"
        self.assertEqual(assess(self.report, self.dir)["verdict"], "NO_GO")

    def test_p1_open_blocks_release(self):
        self.report["findings"] = [{"id":"B1", "severity":"P1", "status":"open", "title":"Login bypass",
                                    "steps":"try", "expected":"deny", "observed":"allowed", "evidence":["evidence.log"]}]
        self.assertEqual(assess(self.report, self.dir)["verdict"], "NO_GO")

    def test_p2_requires_review(self):
        self.report["findings"] = [{"id":"B2", "severity":"P2", "status":"open", "title":"Style mismatch",
                                    "steps":"visit", "expected":"aligned", "observed":"offset", "evidence":["evidence.log"]}]
        self.assertEqual(assess(self.report, self.dir)["verdict"], "REVIEW_REQUIRED")

    def test_critical_flow_without_coverage(self):
        self.report["critical_flows"].append("payments")
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_unverified_environment(self):
        self.report["production_parity_verified"] = False
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_human_factors_missing_fails_closed(self):
        del self.report["human_factors"]
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def human_report(self):
        self.report["human_factors"] = {
            "applicable": True,
            "personas": [{"id": "driver", "context": "Primer uso de formulario en teléfono bajo sol"}],
            "required_scenarios": [{"id": "DR-01", "flow": "auth", "persona_id": "driver",
                                    "expected_recovery": "Rechazar fotografía incorrecta y ofrecer otra captura"}],
            "field_validation_required": True,
            "field_validation_completed": True,
            "field_validation_summary": "Piloto representativo en staging, resultados agregados",
            "field_validation_evidence": ["evidence.log"]
        }
        self.report["tests"][0]["scenario_id"] = "DR-01"

    def test_human_factor_all_evidenced_candidate(self):
        self.human_report()
        self.assertEqual(assess(self.report, self.dir)["verdict"], "READY_CANDIDATE")

    def test_human_scenario_missing_blocks_candidate(self):
        self.human_report()
        del self.report["tests"][0]["scenario_id"]
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_human_scenario_failed_blocks_release(self):
        self.human_report()
        self.report["tests"][0]["status"] = "failed"
        self.assertEqual(assess(self.report, self.dir)["verdict"], "NO_GO")

    def test_field_validation_missing_blocks_candidate(self):
        self.human_report()
        self.report["human_factors"]["field_validation_completed"] = False
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_field_validation_waiver_requires_review(self):
        self.human_report()
        hf = self.report["human_factors"]
        hf["field_validation_required"] = False
        hf["field_validation_waiver_reason"] = "Aplazado por condiciones extraordinarias"
        hf["field_validation_waiver_approver"] = "Responsable QA"
        self.assertEqual(assess(self.report, self.dir)["verdict"], "REVIEW_REQUIRED")

    def test_human_scenario_must_match_declared_persona(self):
        self.human_report()
        self.report["human_factors"]["required_scenarios"][0]["persona_id"] = "nonexistent"
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_stakeholder_coverage_missing_fails_closed(self):
        self.report.pop("stakeholder_coverage")
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_stakeholder_required_actor_without_scenario_fails(self):
        self.report["stakeholder_coverage"]["actors"].append({
            "id": "owner", "role": "Dueño", "context": "Supervisión de operación",
            "type": "person", "source": "inferred", "critical": True})
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_stakeholder_without_test_is_incomplete(self):
        self.report["tests"][0].pop("stakeholder_scenario_id")
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_stakeholder_wrong_actor_is_incomplete(self):
        self.report["stakeholder_coverage"]["required_scenarios"][0]["actor_id"] = "unknown"
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_stakeholder_failed_case_blocks(self):
        self.report["tests"][0]["status"] = "failed"
        self.assertEqual(assess(self.report, self.dir)["verdict"], "NO_GO")

    def with_custom_profile(self):
        p = new_profile("custom-api", "Consumidor API personalizado", "API cliente", "system")
        p["priority"] = "critical"
        p["critical_flows"] = ["auth"]
        p["scenarios"] = [{
            "id": "STA-01", "flow": "auth", "trigger": "Se necesita autenticar",
            "user_action": "Envía token válido", "expected_system_response": "Crea sesión válida",
            "expected_recovery": "Permite renovar token", "severity": "P1"
        }]
        (self.dir / "custom-api.json").write_text(json.dumps(p), encoding="utf-8")
        self.report["custom_profiles"] = [{"id": "custom-api", "source_file": "custom-api.json", "critical": True}]
        self.report["stakeholder_coverage"]["actors"][0]["profile_id"] = "custom-api"
        return p

    def test_custom_profile_valid_candidate(self):
        self.with_custom_profile()
        self.assertEqual(assess(self.report, self.dir)["verdict"], "READY_CANDIDATE")

    def test_custom_profile_missing_file_incomplete(self):
        self.with_custom_profile()
        self.report["custom_profiles"][0]["source_file"] = "no-such-profile.json"
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_custom_profile_wrong_id_incomplete(self):
        self.with_custom_profile()
        self.report["custom_profiles"][0]["id"] = "different-profile"
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_custom_profile_missing_actor_incomplete(self):
        self.with_custom_profile()
        self.report["stakeholder_coverage"]["actors"][0].pop("profile_id")
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_custom_profile_scenario_cannot_be_ignored(self):
        p = self.with_custom_profile()
        p["scenarios"].append({
            "id": "STA-02", "flow": "auth", "trigger": "Expira la sesión",
            "user_action": "Reintenta con token vencido", "expected_system_response": "401",
            "expected_recovery": "Refresca credencial de manera autorizada", "severity": "P1"
        })
        (self.dir / "custom-api.json").write_text(json.dumps(p), encoding="utf-8")
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_custom_profile_invalid_format_incomplete(self):
        self.with_custom_profile()
        (self.dir / "custom-api.json").write_text("{}", encoding="utf-8")
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_custom_profile_traversal_denied(self):
        self.with_custom_profile()
        self.report["custom_profiles"][0]["source_file"] = "../custom-api.json"
        self.assertEqual(assess(self.report, self.dir)["verdict"], "INCOMPLETE")

    def test_validate_profile_rejects_bad_scenario(self):
        p = self.with_custom_profile()
        p["scenarios"][0]["expected_recovery"] = ""
        self.assertTrue(validate_profile(p))

    def test_profile_cli_creates_and_validates(self):
        path = self.dir / "my-persona.json"
        self.assertEqual(profiles_main(["new", "--id", "my-persona", "--name", "Persona test", "--role", "Tester", "--output", str(path)]), 0)
        self.assertEqual(load_profile(path)["id"], "my-persona")
        self.assertEqual(profiles_main(["validate", str(path)]), 0)

    def test_example_remains_incomplete(self):
        example = Path(__file__).parents[2] / "examples" / "audit-results.example.json"
        if example.exists():
            self.assertEqual(assess(json.loads(example.read_text()), self.dir)["verdict"], "INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
