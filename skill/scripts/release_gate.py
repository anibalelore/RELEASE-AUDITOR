#!/usr/bin/env python3
"""Release Auditor evidence gate. Standard library only.

Assesses the *supplied* audit report; does not execute a test suite or certify an app.
Every evidence item must point to an existing file INSIDE the report directory.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from profiles import load_profile

VALID_TEST = {"passed", "failed", "blocked", "not_run"}
VALID_SEVERITY = {"P0", "P1", "P2", "P3"}
VALID_FINDING = {"open", "resolved", "unverified"}


def nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def evidence_errors(items: Any, basedir: Path, owner: str) -> list[str]:
    if not isinstance(items, list) or not items:
        return [f"{owner}: evidencia ausente"]
    errors: list[str] = []
    base = basedir.resolve()
    for i, item in enumerate(items):
        if not nonblank(item):
            errors.append(f"{owner}: referencia de evidencia {i + 1} vacía")
            continue
        if "\x00" in item:
            errors.append(f"{owner}: referencia inválida")
            continue
        p = Path(item)
        path = (base / p).resolve()
        if p.is_absolute() or not path.is_relative_to(base):
            errors.append(f"{owner}: evidencia debe estar dentro del directorio del informe: {item}")
        elif not path.is_file():
            errors.append(f"{owner}: evidencia no encontrada: {item}")
    return errors


def assess(report: Any, basedir: Path) -> dict[str, Any]:
    errors: list[str] = []
    blockers: list[str] = []
    incomplete: list[str] = []
    reviews: list[str] = []
    counts = Counter()
    severity_counts = Counter()
    covered_flows: list[str] = []

    if not isinstance(report, dict):
        return {"verdict": "INCOMPLETE", "errors": ["El reporte debe ser un objeto JSON"],
                "blockers": [], "incomplete": [], "reviews": [], "counts": {},
                "severity_counts": {}, "covered_flows": [], "critical_flows": []}

    for k in ("project", "environment", "build", "timestamp"):
        if not nonblank(report.get(k)):
            incomplete.append(f"Campo obligatorio ausente: {k}")
    if nonblank(report.get("timestamp")):
        try:
            datetime.fromisoformat(report["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            incomplete.append("Timestamp sin formato ISO 8601 válido")

    flows = report.get("critical_flows", [])
    if not isinstance(flows, list) or not flows or any(not nonblank(x) for x in flows):
        incomplete.append("Declarar flujos críticos reales en critical_flows")
        flows = []
    elif len(set(flows)) != len(flows):
        incomplete.append("critical_flows contiene duplicados")

    tests = report.get("tests", [])
    if not isinstance(tests, list) or not tests:
        incomplete.append("No se registraron pruebas ejecutadas")
        tests = []
    seen_ids: set[str] = set()
    valid_tests = []
    for index, test in enumerate(tests, 1):
        if not isinstance(test, dict):
            incomplete.append(f"Prueba {index}: debe ser objeto")
            continue
        test_id = test.get("id")
        if not nonblank(test_id) or test_id in seen_ids:
            incomplete.append(f"Prueba {index}: ID ausente o duplicado")
            test_id = f"test-{index}"
        seen_ids.add(test_id)
        flow = test.get("flow")
        status = test.get("status")
        if not nonblank(flow):
            incomplete.append(f"{test_id}: flow ausente")
        if status not in VALID_TEST:
            incomplete.append(f"{test_id}: status inválido")
            continue
        counts[status] += 1
        critical = test.get("critical")
        if not isinstance(critical, bool):
            incomplete.append(f"{test_id}: critical debe ser booleano")
            critical = True  # fail closed
        if status in ("passed", "failed"):
            for field in ("expected", "observed", "action"):
                if not nonblank(test.get(field)):
                    incomplete.append(f"{test_id}: sin {field} verificable")
            incomplete.extend(evidence_errors(test.get("evidence"), basedir, test_id))
        if status == "passed" and not any(
            s.startswith(f"{test_id}:") for s in incomplete
        ):
            valid_tests.append(test)
        if critical and status == "failed":
            blockers.append(f"Prueba crítica fallida: {test_id} ({flow})")
        elif critical and status in ("blocked", "not_run"):
            incomplete.append(f"Prueba crítica no completada: {test_id} ({status})")
        elif not critical and status == "failed":
            reviews.append(f"Prueba no crítica fallida: {test_id}")
        elif not critical and status in ("blocked", "not_run"):
            incomplete.append(f"Prueba planificada sin ejecutar: {test_id} ({status})")

    for flow in flows:
        matching = [t for t in tests if isinstance(t, dict) and t.get("flow") == flow]
        if not matching:
            incomplete.append(f"Flujo crítico sin pruebas registradas: {flow}")
            continue
        if any(t.get("status") == "failed" for t in matching):
            blockers.append(f"Flujo crítico con prueba fallida: {flow}")
            continue
        if any(t.get("status") in ("blocked", "not_run") for t in matching):
            incomplete.append(f"Flujo crítico con pruebas sin completar: {flow}")
            continue
        if not any(t.get("flow") == flow and t.get("status") == "passed" and t.get("critical") is True for t in valid_tests):
            incomplete.append(f"Flujo crítico no verificado con evidencia: {flow}")
            continue
        covered_flows.append(flow)

    # Human factors are a distinct release gate. The file's existence alone
    # does not prove that a test ran, or that a representative pilot occurred.
    hf = report.get("human_factors")
    if not isinstance(hf, dict):
        incomplete.append("Declarar human_factors y su aplicabilidad (no asumir que la UX fue probada)")
    elif not isinstance(hf.get("applicable"), bool):
        incomplete.append("human_factors.applicable debe ser booleano")
    elif hf["applicable"] is False:
        if not nonblank(hf.get("not_applicable_reason")):
            incomplete.append("Explicar por qué factores humanos no aplican")
    else:
        personas = hf.get("personas")
        ids = set()
        if not isinstance(personas, list) or not personas:
            incomplete.append("human_factors.personas: declarar al menos un perfil operativo")
            personas = []
        for persona in personas:
            if not isinstance(persona, dict) or not nonblank(persona.get("id")) or not nonblank(persona.get("context")):
                incomplete.append("human_factors.personas: cada persona necesita id y context")
            elif persona["id"] in ids:
                incomplete.append(f"Persona duplicada: {persona['id']}")
            else:
                ids.add(persona["id"])

        scenarios = hf.get("required_scenarios")
        if not isinstance(scenarios, list) or not scenarios:
            incomplete.append("human_factors.required_scenarios: listar casos críticos personalizados")
            scenarios = []
        seen_scenario_ids: set[str] = set()
        for i, scenario in enumerate(scenarios, 1):
            if not isinstance(scenario, dict):
                incomplete.append(f"Escenario humano {i}: debe ser objeto")
                continue
            sid = scenario.get("id")
            flow = scenario.get("flow")
            pid = scenario.get("persona_id")
            if not nonblank(sid) or sid in seen_scenario_ids:
                incomplete.append(f"Escenario humano {i}: ID ausente o duplicado")
                continue
            seen_scenario_ids.add(sid)
            if not nonblank(flow) or flow not in flows:
                incomplete.append(f"{sid}: escenario debe vincularse a flujo crítico declarado")
            if pid not in ids:
                incomplete.append(f"{sid}: persona_id inexistente o inválido")
            if not nonblank(scenario.get("expected_recovery")):
                incomplete.append(f"{sid}: sin recuperación esperada del usuario")
            candidates = [t for t in tests if isinstance(t, dict) and
                          t.get("scenario_id") == sid and t.get("flow") == flow]
            if not candidates:
                incomplete.append(f"Escenario humano sin pruebas: {sid}")
            elif any(t.get("status") == "failed" for t in candidates):
                blockers.append(f"Escenario humano crítico fallido: {sid}")
            elif any(t.get("status") in ("blocked", "not_run") for t in candidates):
                incomplete.append(f"Escenario humano no ejecutado completamente: {sid}")
            elif not any(t in valid_tests and t.get("critical") is True for t in candidates):
                incomplete.append(f"Escenario humano sin PASS crítico evidenciado: {sid}")

        for test in tests:
            if isinstance(test, dict) and nonblank(test.get("scenario_id")) and test["scenario_id"] not in seen_scenario_ids:
                incomplete.append(f"{test.get('id', 'Test')}: scenario_id no declarado: {test['scenario_id']}")

        required = hf.get("field_validation_required")
        if not isinstance(required, bool):
            incomplete.append("human_factors.field_validation_required debe ser booleano")
        elif required:
            if hf.get("field_validation_completed") is not True:
                incomplete.append("Validación de campo con usuarios representativos no demostrada")
            else:
                if not nonblank(hf.get("field_validation_summary")):
                    incomplete.append("Falta resumen anonimizado del piloto de campo")
                incomplete.extend(evidence_errors(hf.get("field_validation_evidence"), basedir,
                                                  "human_factors.field_validation"))
        else:
            if (not nonblank(hf.get("field_validation_waiver_reason")) or
                    not nonblank(hf.get("field_validation_waiver_approver"))):
                incomplete.append("Exención de prueba de campo sin justificación y responsable")
            else:
                reviews.append("Validación de campo dispensada: requiere aprobación humana explícita")

    # Universal actor coverage covers *all* relevant stakeholders, including
    # business owners, customers, administrators, service actors and handoffs.
    # Human-factors UI testing is complementary, not a substitute.
    stakeholder = report.get("stakeholder_coverage")
    if not isinstance(stakeholder, dict):
        incomplete.append("Declarar stakeholder_coverage con actores reales y escenarios por riesgo")
    else:
        actors = stakeholder.get("actors")
        actor_ids: set[str] = set()
        critical_actor_ids: set[str] = set()
        if not isinstance(actors, list) or not actors:
            incomplete.append("stakeholder_coverage.actors: falta inventario de actores aplicables")
            actors = []
        for actor in actors:
            if not isinstance(actor, dict) or not nonblank(actor.get("id")):
                incomplete.append("stakeholder_coverage.actors: ID de actor obligatorio")
                continue
            aid = actor["id"]
            if aid in actor_ids:
                incomplete.append(f"Actor duplicado: {aid}")
            actor_ids.add(aid)
            if not all(nonblank(actor.get(k)) for k in ("role", "context")):
                incomplete.append(f"{aid}: rol y contexto obligatorios")
            if actor.get("type") not in ("person", "system"):
                incomplete.append(f"{aid}: type debe ser person/system")
            if actor.get("source") not in ("observed", "inferred"):
                incomplete.append(f"{aid}: source debe ser observed/inferred")
            if not isinstance(actor.get("critical"), bool):
                incomplete.append(f"{aid}: critical debe ser booleano")
            elif actor["critical"]:
                critical_actor_ids.add(aid)

        scenarios = stakeholder.get("required_scenarios")
        if not isinstance(scenarios, list) or not scenarios:
            incomplete.append("stakeholder_coverage.required_scenarios: faltan escenarios aplicables")
            scenarios = []
        scenario_ids: set[str] = set()
        scenarios_by_actor: set[str] = set()
        scenarios_by_flow: set[str] = set()
        for idx, scenario in enumerate(scenarios, 1):
            if not isinstance(scenario, dict):
                incomplete.append(f"Escenario stakeholder {idx}: objeto requerido")
                continue
            sid, aid, flow = scenario.get("id"), scenario.get("actor_id"), scenario.get("flow")
            if not nonblank(sid) or sid in scenario_ids:
                incomplete.append(f"Escenario stakeholder {idx}: ID ausente o duplicado")
                continue
            scenario_ids.add(sid)
            if aid not in actor_ids:
                incomplete.append(f"{sid}: actor_id no declarado")
            else:
                scenarios_by_actor.add(aid)
            if flow not in flows:
                incomplete.append(f"{sid}: flow no declarado como crítico")
            else:
                scenarios_by_flow.add(flow)
            if not nonblank(scenario.get("expected_outcome")) or not nonblank(scenario.get("risk")):
                incomplete.append(f"{sid}: resultado esperado y riesgo deben ser explícitos")
            matching = [t for t in tests if isinstance(t, dict) and
                        t.get("stakeholder_scenario_id") == sid and t.get("flow") == flow]
            if not matching:
                incomplete.append(f"Escenario stakeholder sin pruebas: {sid}")
            elif any(t.get("status") == "failed" and t.get("critical") is True for t in matching):
                blockers.append(f"Escenario stakeholder crítico fallido: {sid}")
            elif any(t.get("status") in ("blocked", "not_run") for t in matching):
                incomplete.append(f"Escenario stakeholder no completado: {sid}")
            elif not any(t in valid_tests and t.get("critical") is True for t in matching):
                incomplete.append(f"Escenario stakeholder sin PASS crítico evidenciado: {sid}")

        for aid in critical_actor_ids - scenarios_by_actor:
            incomplete.append(f"Actor crítico sin escenarios: {aid}")
        for flow in set(flows) - scenarios_by_flow:
            incomplete.append(f"Flujo crítico sin escenarios stakeholder: {flow}")
        for test in tests:
            if isinstance(test, dict) and nonblank(test.get("stakeholder_scenario_id")) and \
                    test["stakeholder_scenario_id"] not in scenario_ids:
                incomplete.append(f"{test.get('id', 'Test')}: stakeholder_scenario_id no declarado")

    # Progressive five-level audit is a release requirement for each critical
    # human actor/critical flow pair (other actors have non-human failure modes).
    # A scenario is satisfied ONLY by a corresponding executed test with evidence.
    from progression import LEVELS as PROGRESSIVE_LEVELS, KINDS as PROGRESSIVE_KINDS
    # Read from the existing actor/scenario inventory. This does not broaden the
    # scope to all possible human roles, only those declared as applicable.
    observed_actors = stakeholder.get("actors", []) if isinstance(stakeholder, dict) else []
    observed_scenarios = stakeholder.get("required_scenarios", []) if isinstance(stakeholder, dict) else []
    critical_human_actors = {
        a["id"] for a in observed_actors if isinstance(a, dict) and nonblank(a.get("id"))
        and a.get("type") == "person" and a.get("critical") is True
    }
    required_pairs = {
        (s.get("actor_id"), s.get("flow")) for s in observed_scenarios
        if isinstance(s, dict) and s.get("actor_id") in critical_human_actors
        and s.get("flow") in flows
    }
    progressive = report.get("progressive_audit")
    if progressive is None and required_pairs:
        incomplete.append("Falta progressive_audit para los perfiles humanos críticos")
    elif progressive is not None:
        if not isinstance(progressive, dict) or not isinstance(progressive.get("applicable"), bool):
            incomplete.append("progressive_audit debe declarar applicable booleano")
        elif progressive["applicable"] is False:
            if required_pairs:
                incomplete.append("progressive_audit deshabilitado para actores humanos críticos")
            if not nonblank(progressive.get("not_applicable_reason")):
                incomplete.append("progressive_audit: falta justificación de no aplicabilidad")
        else:
            tracks = progressive.get("tracks")
            prog_scenarios = progressive.get("required_scenarios")
            if not isinstance(tracks, list) or not tracks:
                incomplete.append("progressive_audit.tracks: se requiere al menos un track")
                tracks = []
            if not isinstance(prog_scenarios, list) or not prog_scenarios:
                incomplete.append("progressive_audit.required_scenarios: se requieren escenarios")
                prog_scenarios = []
            track_keys = set()
            scenario_keys: set[tuple[str, str, str, str]] = set()
            progressive_ids = set()
            for t in tracks:
                if not isinstance(t, dict) or not nonblank(t.get("actor_id")) or not nonblank(t.get("flow")):
                    incomplete.append("Track progresivo sin actor_id/flow")
                    continue
                key = (t["actor_id"], t["flow"])
                if key in track_keys:
                    incomplete.append(f"Track progresivo duplicado: {key}")
                track_keys.add(key)
                if key not in required_pairs:
                    incomplete.append(f"Track progresivo fuera de actores/flujos críticos: {key}")
                if t.get("levels") != list(PROGRESSIVE_LEVELS):
                    incomplete.append(f"Track {key}: se requieren cinco niveles en orden")
            for pair in required_pairs - track_keys:
                incomplete.append(f"Falta track progresivo para actor/flujo crítico: {pair}")
            for s in prog_scenarios:
                if not isinstance(s, dict) or not nonblank(s.get("id")):
                    incomplete.append("Escenario progresivo sin ID")
                    continue
                sid, aid, flow, level, kind = (s.get(k) for k in ("id", "actor_id", "flow", "level", "kind"))
                if sid in progressive_ids:
                    incomplete.append(f"Escenario progresivo duplicado: {sid}")
                progressive_ids.add(sid)
                key = (aid, flow, level, kind)
                if (aid, flow) not in track_keys or level not in PROGRESSIVE_LEVELS or kind not in PROGRESSIVE_KINDS:
                    incomplete.append(f"Escenario progresivo {sid}: nivel, clase, actor o flujo inválidos")
                    continue
                if key in scenario_keys:
                    incomplete.append(f"Escenario progresivo repetido: {key}")
                scenario_keys.add(key)
                if not nonblank(s.get("expected_recovery")):
                    incomplete.append(f"Escenario progresivo {sid}: falta expectativa de salida y consistencia")
                related = [t for t in tests if isinstance(t, dict) and
                           t.get("progressive_scenario_id") == sid and t.get("flow") == flow]
                if not related:
                    incomplete.append(f"Escenario progresivo sin prueba: {sid}")
                elif any(t.get("status") == "failed" and t.get("critical") is True for t in related):
                    blockers.append(f"Escenario progresivo crítico fallido: {sid}")
                elif any(t.get("status") in ("blocked", "not_run") for t in related):
                    incomplete.append(f"Escenario progresivo no terminado: {sid}")
                elif not any(t in valid_tests and t.get("critical") is True for t in related):
                    incomplete.append(f"Escenario progresivo sin PASS evidenciado: {sid}")
                for t in related:
                    if t.get("tested_build") != report.get("build"):
                        incomplete.append(f"{t.get('id', sid)}: prueba progresiva no corresponde a build auditada")
            for aid, flow in track_keys:
                for level in PROGRESSIVE_LEVELS:
                    for kind in PROGRESSIVE_KINDS:
                        if (aid, flow, level, kind) not in scenario_keys:
                            incomplete.append(f"Falta caso progresivo {aid}/{flow}/{level}/{kind}")
            for t in tests:
                if isinstance(t, dict) and nonblank(t.get("progressive_scenario_id")) and \
                        t["progressive_scenario_id"] not in progressive_ids:
                    incomplete.append(f"{t.get('id', 'Test')}: progressive_scenario_id no declarado")

    # Custom persona profiles are optional, but once declared they MUST be
    # applied to the actual actor/scenario matrix. Check a local snapshot of
    # each profile so the gate cannot silently ignore the user's customization.
    custom_profiles = report.get("custom_profiles", [])
    if not isinstance(custom_profiles, list):
        incomplete.append("custom_profiles debe ser una lista")
        custom_profiles = []
    seen_profile_ids: set[str] = set()
    stakeholder_actors = stakeholder.get("actors", []) if isinstance(stakeholder, dict) else []
    stakeholder_scenarios = stakeholder.get("required_scenarios", []) if isinstance(stakeholder, dict) else []
    for index, entry in enumerate(custom_profiles, 1):
        if not isinstance(entry, dict) or not nonblank(entry.get("id")) or not nonblank(entry.get("source_file")):
            incomplete.append(f"Perfil personalizado {index}: id y source_file obligatorios")
            continue
        pid = entry["id"]
        if pid in seen_profile_ids:
            incomplete.append(f"Perfil personalizado duplicado: {pid}")
            continue
        seen_profile_ids.add(pid)
        if not isinstance(entry.get("critical"), bool):
            incomplete.append(f"{pid}: critical debe ser booleano")
        rel = Path(entry["source_file"])
        base = basedir.resolve()
        file_path = (base / rel).resolve()
        if rel.is_absolute() or not file_path.is_relative_to(base) or not file_path.is_file():
            incomplete.append(f"{pid}: archivo de perfil ausente o fuera del informe")
            continue
        try:
            profile = load_profile(file_path)
        except ValueError as exc:
            incomplete.append(f"{pid}: perfil inválido: {exc}")
            continue
        if profile["id"] != pid:
            incomplete.append(f"{pid}: id no coincide con el archivo del perfil")
        if profile["enabled"] is not True:
            incomplete.append(f"{pid}: perfil deshabilitado no puede declararse ejecutado")
        if profile["priority"] == "critical" and entry.get("critical") is not True:
            incomplete.append(f"{pid}: prioridad crítica desactivada en el reporte")
        actor_matches = [a for a in stakeholder_actors if isinstance(a, dict) and a.get("profile_id") == pid]
        if not actor_matches:
            incomplete.append(f"{pid}: perfil personalizado sin actor vinculado en stakeholder_coverage")
        if entry.get("critical") is True and not any(a.get("critical") is True for a in actor_matches):
            incomplete.append(f"{pid}: perfil crítico sin actor crítico")
        if entry.get("critical") is True and (not profile["critical_flows"] or not profile["scenarios"]):
            incomplete.append(f"{pid}: faltan flujos o escenarios críticos personalizados")
        for flow in profile["critical_flows"]:
            if flow not in flows:
                incomplete.append(f"{pid}: flujo personalizado fuera de critical_flows: {flow}")
        for scenario in profile["scenarios"]:
            matches = [s for s in stakeholder_scenarios if isinstance(s, dict)
                       and s.get("id") == scenario["id"] and s.get("flow") == scenario["flow"]
                       and any(s.get("actor_id") == a.get("id") for a in actor_matches)]
            if not matches:
                incomplete.append(f"{pid}: escenario personalizado no incorporado a stakeholder_coverage: {scenario['id']}")
    if custom_profiles:
        for actor in stakeholder_actors:
            if isinstance(actor, dict) and nonblank(actor.get("profile_id")) and actor["profile_id"] not in seen_profile_ids:
                incomplete.append(f"Actor {actor.get('id')}: profile_id no declarado en custom_profiles")

    findings = report.get("findings", [])
    if not isinstance(findings, list):
        incomplete.append("findings debe ser lista")
        findings = []
    seen_finding_ids = set()
    for index, finding in enumerate(findings, 1):
        if not isinstance(finding, dict):
            incomplete.append(f"Hallazgo {index}: debe ser objeto")
            continue
        fid = finding.get("id")
        sev = finding.get("severity")
        status = finding.get("status")
        if not nonblank(fid) or fid in seen_finding_ids:
            incomplete.append(f"Hallazgo {index}: ID ausente o duplicado")
            fid = f"finding-{index}"
        seen_finding_ids.add(fid)
        if sev not in VALID_SEVERITY or status not in VALID_FINDING:
            incomplete.append(f"{fid}: severidad o estado inválido")
            continue
        severity_counts[f"{sev}_{status}"] += 1
        if not nonblank(finding.get("title")):
            incomplete.append(f"{fid}: título ausente")
        if status in ("open", "unverified"):
            for k in ("steps", "expected", "observed"):
                if not nonblank(finding.get(k)):
                    incomplete.append(f"{fid}: falta {k}")
            incomplete.extend(evidence_errors(finding.get("evidence"), basedir, fid))
            if sev in ("P0", "P1"):
                blockers.append(f"Hallazgo bloqueante {sev}: {fid} — {finding.get('title', '')}")
            else:
                reviews.append(f"Hallazgo abierto {sev}: {fid} — {finding.get('title', '')}")
        if status == "resolved":
            rid = finding.get("regression_test_id")
            if not nonblank(rid) or not any(t.get("id") == rid for t in valid_tests):
                incomplete.append(f"{fid}: fix 'resolved' sin prueba de regresión passed con evidencia")

    for field, field_evidence in (
        ("full_suite_executed", "full_suite_evidence"),
        ("production_parity_verified", "production_parity_evidence"),
    ):
        value = report.get(field)
        if value is not True:
            incomplete.append(f"No demostrado: {field}")
        else:
            incomplete.extend(evidence_errors(report.get(field_evidence), basedir, field))

    limitations = report.get("limitations", [])
    if not isinstance(limitations, list):
        incomplete.append("limitations debe ser una lista")
    elif limitations:
        for limit in limitations:
            incomplete.append(f"Limitación abierta: {limit}")

    verdict = ("NO_GO" if blockers else "INCOMPLETE" if incomplete or errors
               else "REVIEW_REQUIRED" if reviews else "READY_CANDIDATE")
    return {"verdict": verdict, "errors": errors, "blockers": blockers,
            "incomplete": incomplete, "reviews": reviews, "counts": dict(counts),
            "severity_counts": dict(severity_counts), "covered_flows": covered_flows,
            "critical_flows": flows}


def to_markdown(report: dict[str, Any], result: dict[str, Any]) -> str:
    lines = [f"# Auditoría de release — {report.get('project', 'Proyecto sin identificar')}",
             "", f"**Veredicto: {result['verdict']}**",
             "", f"**Entorno:** {report.get('environment', 'no verificado')}",
             f"**Build:** {report.get('build', 'no verificado')}",
             f"**Fecha:** {report.get('timestamp', 'no verificado')}",
             "", "## Ejecución", ""]
    counts = result["counts"]
    lines.append(" | ".join(f"{k}: {counts.get(k, 0)}" for k in ("passed", "failed", "blocked", "not_run")))
    lines.append(f"Flujos críticos verificados: {len(result['covered_flows'])}/{len(result['critical_flows'])}")
    for title, key in (("Bloqueantes", "blockers"), ("Cobertura o evidencia incompleta", "incomplete"),
                       ("Riesgos para revisión", "reviews"), ("Problemas de formato", "errors")):
        lines.extend(["", f"## {title}", ""])
        lines.extend(f"- {entry}" for entry in result[key]) if result[key] else lines.append("- Ninguno registrado.")
    lines.extend(["", "**Nota:** este gate valida el informe, no ejecuta ni certifica el software.", ""])
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Verifica evidencia y riesgos antes de release")
    ap.add_argument("report", type=Path, help="audit-results.json")
    ap.add_argument("--output", type=Path, help="Guardar resumen en Markdown")
    args = ap.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ERROR al leer JSON: {exc}", file=sys.stderr)
        return 2
    result = assess(report, args.report.parent)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(to_markdown(report, result), encoding="utf-8")
        print(f"Informe guardado: {args.output}")
    return 0 if result["verdict"] == "READY_CANDIDATE" else 1


if __name__ == "__main__":
    sys.exit(main())
