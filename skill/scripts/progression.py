#!/usr/bin/env python3
"""Generate/validate persona × workflow × proficiency-level scenario matrices.

Produces a PLAN, not proof that tests ran. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LEVELS = ("erratico", "principiante", "intermedio", "competente", "experto")
KINDS = ("error_y_recuperacion", "camino_correcto")
ID = re.compile(r"^[a-z][a-z0-9-]{1,62}$")

HINTS = {
    "erratico": "Acciones equivocadas extremas: elemento/documento equivocado, respuesta literal, varios toques, retroceso o abandono",
    "principiante": "No entiende términos o instrucciones; intenta orientación básica y corrección tras feedback",
    "intermedio": "Domina el camino normal; confunde excepción, estado intermedio o reintento",
    "competente": "Completa rápido en condiciones reales; interrupción, distracción y datos correctos",
    "experto": "Atajos, cambios rápidos, datos límite, múltiples pestañas, concurrencia o volumen"
}


def build(actor: str, role: str, flows: list[str], level_overrides: dict | None = None) -> dict:
    tracks = []
    scenarios = []
    for flow in flows:
        tracks.append({"actor_id": actor, "flow": flow, "levels": list(LEVELS)})
        for lvl in LEVELS:
            custom = (level_overrides or {}).get(lvl, {})
            for kind in KINDS:
                scenarios.append({
                    "id": f"{actor}-{flow}-{lvl}-{kind}",
                    "actor_id": actor, "flow": flow, "level": lvl, "kind": kind,
                    "proposed_action": ("; ".join(custom.get("error_patterns", [HINTS[lvl]])) if kind == KINDS[0]
                                        else custom.get("correct_strategy", "Completar el objetivo real con información correcta")),
                    "context": custom.get("context", "Adaptar al sistema real"),
                    "expected_recovery": "Definir resultado verificable: contención segura, guía y recuperación" if kind == KINDS[0] else "Definir resultado verificable: tarea completa y datos consistentes",
                    "status": "not_run",
                })
    return {"schema_version": 1, "actor_id": actor, "role": role, "flows": flows,
            "levels": list(LEVELS), "tracks": tracks, "required_scenarios": scenarios,
            "note": "Plantilla de planificación; cada caso requiere datos, expectativa concreta y evidencia posterior. No ejecuta pruebas."}


def validate(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["El plan debe ser un objeto"]
    if data.get("schema_version") != 1:
        errors.append("schema_version debe ser 1")
    actor, role, flows = data.get("actor_id"), data.get("role"), data.get("flows")
    if not isinstance(actor, str) or not ID.fullmatch(actor):
        errors.append("actor_id inválido")
    if not isinstance(role, str) or not role.strip():
        errors.append("role obligatorio")
    if (not isinstance(flows, list) or not flows or any(not isinstance(f, str) or not ID.fullmatch(f) for f in flows)
            or len(flows) != len(set(flows))):
        errors.append("flows inválidos o duplicados")
        flows = []
    if data.get("levels") != list(LEVELS):
        errors.append("Se requieren los cinco niveles en orden")
    tracks, scenarios = data.get("tracks"), data.get("required_scenarios")
    if not isinstance(tracks, list) or not isinstance(scenarios, list):
        return errors + ["tracks y required_scenarios deben ser listas"]
    combos: set[tuple[str, str, str]] = set()
    seen_ids: set[str] = set()
    for i, item in enumerate(scenarios):
        if not isinstance(item, dict):
            errors.append(f"escenario {i} no es objeto")
            continue
        sid = item.get("id")
        if not isinstance(sid, str) or not sid or sid in seen_ids:
            errors.append(f"escenario {i}: id ausente o duplicado")
        else:
            seen_ids.add(sid)
        if item.get("actor_id") != actor or item.get("flow") not in flows or item.get("level") not in LEVELS or item.get("kind") not in KINDS:
            errors.append(f"escenario {i}: actor/flow/level/kind inválido")
            continue
        k = item["flow"], item["level"], item["kind"]
        if k in combos:
            errors.append(f"escenario duplicado: {k}")
        combos.add(k)
        if not isinstance(item.get("expected_recovery"), str) or not item["expected_recovery"].strip():
            errors.append(f"escenario {i}: resultado esperado obligatorio")
    for flow in flows:
        for level in LEVELS:
            for kind in KINDS:
                if (flow, level, kind) not in combos:
                    errors.append(f"falta {flow}/{level}/{kind}")
    by_flow = {x.get("flow"): x for x in tracks if isinstance(x, dict)}
    if len(by_flow) != len(tracks) or set(by_flow) != set(flows):
        errors.append("tracks no coincide con los flujos")
    for flow, track in by_flow.items():
        if track.get("actor_id") != actor or track.get("levels") != list(LEVELS):
            errors.append(f"track {flow}: actor o niveles inválidos")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generar y verificar matriz progresiva para un rol")
    sub = parser.add_subparsers(dest="cmd", required=True)
    create = sub.add_parser("plan")
    create.add_argument("--actor")
    create.add_argument("--role")
    create.add_argument("--profile", type=Path, help="Perfil JSON personalizable de profiles.py")
    create.add_argument("--flow", action="append", dest="flows")
    create.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("validate")
    check.add_argument("file", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.cmd == "plan":
            profile = None
            overrides = None
            if args.profile:
                from profiles import load_profile
                profile = load_profile(args.profile)
                if profile.get("actor", {}).get("kind") != "person":
                    raise ValueError("La escalera de personas requiere actor humano; use resiliencia de servicio para API")
                overrides = {x["id"]: x for x in profile.get("progression", {}).get("levels", [])}
            actor = args.actor or (profile["id"] if profile else None)
            role = args.role or (profile["actor"]["role"] if profile else None)
            flows = args.flows or (profile.get("critical_flows") if profile else None)
            d = build(actor, role, flows or [], overrides)
            errors = validate(d)
            if errors:
                raise ValueError("; ".join(errors))
            if args.output.exists():
                raise ValueError(f"No sobrescribo {args.output} sin revisión")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Plan creado: {args.output}. {len(d['required_scenarios'])} casos NOT_RUN; no ejecuta la aplicación.")
        else:
            d = json.loads(args.file.read_text(encoding="utf-8"))
            errors = validate(d)
            if errors:
                raise ValueError("; ".join(errors))
            print("OK: plan estructural válido; NO demuestra pruebas ejecutadas.")
    except (OSError, ValueError) as e:
        print("ERROR:", e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
