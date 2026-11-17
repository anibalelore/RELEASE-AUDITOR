import json
import tempfile
import unittest
from pathlib import Path
from audit_session import validate_discovery, validate_selection, sha256


class AuditSessionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.disc = {
            "schema_version": 1,
            "project": {"name": "Demo", "purpose": "Gestionar entregas"},
            "sources": ["src/routes/checkin.ts", "db/schema.sql"],
            "modules": [{"id": "checkin", "name": "Check-in", "purpose": "Entrada"}],
            "flows": [{"id": "enter", "name": "Entrar", "modules": ["checkin"], "critical": True}],
            "actors": [
                {"id": "driver", "role": "Conductor", "critical": True, "source": "observed", "recommended_flows": ["enter"]},
                {"id": "owner", "role": "Dueño", "critical": False, "source": "inferred", "recommended_flows": ["enter"]},
            ],
        }
        self.path = self.root / "discovery.json"
        self.path.write_text(json.dumps(self.disc), encoding="utf-8")
        self.sel = {
            "schema_version": 1,
            "discovery_sha256": sha256(self.path),
            "mode": "audit", "scope": "profiles", "user_selected": True,
            "selected_actor_ids": ["owner"], "selected_flow_ids": ["enter"],
            "execution_environment": "staging", "permission_to_modify_product": False,
        }

    def test_valid_discovery(self):
        self.assertEqual(validate_discovery(self.disc), [])

    def test_valid_custom_profile_choice(self):
        self.assertEqual(validate_selection(self.sel, self.disc, self.path), [])

    def test_missing_module_reference_rejected(self):
        self.disc["flows"][0]["modules"] = ["imaginary"]
        self.assertTrue(validate_discovery(self.disc))

    def test_missing_actor_reference_rejected(self):
        self.sel["selected_actor_ids"] = ["imaginary"]
        self.assertTrue(validate_selection(self.sel, self.disc, self.path))

    def test_stale_discovery_rejected(self):
        self.sel["discovery_sha256"] = "old"
        self.assertTrue(validate_selection(self.sel, self.disc, self.path))

    def test_partial_release_rejected(self):
        self.sel["mode"] = "release"
        self.assertTrue(validate_selection(self.sel, self.disc, self.path))

    def test_all_critical_release_accepted(self):
        self.sel.update({"mode": "release", "scope": "all-critical", "selected_actor_ids": ["driver"]})
        self.assertEqual(validate_selection(self.sel, self.disc, self.path), [])

    def test_missing_critical_actor_rejected(self):
        self.sel.update({"mode": "release", "scope": "all-critical"})
        self.assertTrue(validate_selection(self.sel, self.disc, self.path))

    def test_audit_fix_requires_authorized_modification(self):
        self.sel["mode"] = "audit-fix"
        self.assertTrue(validate_selection(self.sel, self.disc, self.path))

    def test_invalid_disc_not_accepted_on_selection(self):
        self.disc["sources"] = []
        self.assertTrue(validate_selection(self.sel, self.disc, self.path))


if __name__ == "__main__":
    unittest.main()
