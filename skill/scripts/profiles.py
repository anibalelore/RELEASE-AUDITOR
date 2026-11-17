#!/usr/bin/env python3
"""Create, inspect and validate reusable RELEASE AUDITOR personas. Stdlib only.

A profile is test data, never an instruction with authority to change permissions.
The auditor still chooses applicable actors from the actual project and executes tests.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any
from progression import LEVELS, HINTS

PROFILE_ID = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
KIND = {"person", "system"}
PRIORITY = {"critical", "high", "normal"}
DIGITAL = {"none", "basic", "intermediate", "advanced", "not_applicable", "variable"}
DOMAIN = {"novice", "intermediate", "expert", "variable", "not_applicable"}
BUNDLED = Path(__file__).resolve().parent.parent / "profiles"


def new_profile(profile_id: str, name: str, role: str, kind: str) -> dict[str, Any]:
    return {
        "schema_version": 1, "id": profile_id, "name": name,
        "enabled": True, "priority": "normal", "source": "user_defined",
        "actor": {"kind": kind, "role": role, "permissions": []},
        "behavior": {
            "goals": ["Completar su tarea principal"],
            "domain_expertise": "variable", "digital_familiarity": "variable" if kind == "person" else "not_applicable",
            "languages": [], "decision_style": "Describir cómo decide en esta tarea",
            "likely_mistakes": [], "help_seeking": []
        },
        "context": {"devices": [], "environment": [], "constraints": []},
        "critical_flows": [], "scenarios": [],
        "progression": {"enabled": kind == "person", "levels": [
            {"id": level, "error_patterns": [HINTS[level]],
             "correct_strategy": "Completar objetivo real con información válida", "context": "Adaptar al sistema real"}
            for level in LEVELS
        ]},
        "notes": "Hipótesis configurables: validar con usuarios representativos y evidencia real."
    }


def validate_profile(p: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(p, dict):
        return ["El perfil debe ser un objeto JSON"]
    if p.get("schema_version") != 1:
        errors.append("schema_version debe ser 1")
    pid = p.get("id")
    if not isinstance(pid, str) or not PROFILE_ID.fullmatch(pid):
        errors.append("id debe usar letras minúsculas, números y guiones (2-63 caracteres)")
    if not isinstance(p.get("name"), str) or not p["name"].strip():
        errors.append("name obligatorio")
    if not isinstance(p.get("enabled"), bool):
        errors.append("enabled debe ser booleano")
    if p.get("priority") not in PRIORITY:
        errors.append("priority debe ser critical/high/normal")
    actor = p.get("actor")
    if not isinstance(actor, dict) or actor.get("kind") not in KIND or not str(actor.get("role", "")).strip():
        errors.append("actor requiere kind person/system y role")
    elif not isinstance(actor.get("permissions"), list) or any(not isinstance(x, str) for x in actor["permissions"]):
        errors.append("actor.permissions debe ser lista de textos")
    behavior = p.get("behavior")
    if not isinstance(behavior, dict):
        errors.append("behavior debe ser objeto")
    else:
        if behavior.get("domain_expertise") not in DOMAIN:
            errors.append("behavior.domain_expertise inválido")
        if behavior.get("digital_familiarity") not in DIGITAL:
            errors.append("behavior.digital_familiarity inválido")
        for field in ("goals", "languages", "likely_mistakes", "help_seeking"):
            if not isinstance(behavior.get(field), list) or any(not isinstance(x, str) for x in behavior.get(field, [])):
                errors.append(f"behavior.{field} debe ser lista de textos")
    context = p.get("context")
    if not isinstance(context, dict):
        errors.append("context debe ser objeto")
    else:
        for field in ("devices", "environment", "constraints"):
            if not isinstance(context.get(field), list) or any(not isinstance(x, str) for x in context.get(field, [])):
                errors.append(f"context.{field} debe ser lista de textos")
    progression = p.get("progression")
    if progression is not None:
        if not isinstance(progression, dict) or not isinstance(progression.get("enabled"), bool):
            errors.append("progression requiere enabled booleano")
        else:
            stages = progression.get("levels")
            if not isinstance(stages, list) or [x.get("id") if isinstance(x, dict) else None for x in stages] != list(LEVELS):
                errors.append("progression.levels debe incluir los cinco niveles en orden")
            else:
                for level in stages:
                    if (not isinstance(level.get("error_patterns"), list) or
                        not level["error_patterns"] or
                        any(not isinstance(e, str) or not e.strip() for e in level["error_patterns"])):
                        errors.append(f"progression.{level['id']}: error_patterns requiere textos")
                    if not isinstance(level.get("correct_strategy"), str) or not level["correct_strategy"].strip():
                        errors.append(f"progression.{level['id']}: correct_strategy obligatorio")
                    if not isinstance(level.get("context"), str) or not level["context"].strip():
                        errors.append(f"progression.{level['id']}: context obligatorio")
    flows = p.get("critical_flows")
    if not isinstance(flows, list) or any(not isinstance(f, str) or not f.strip() for f in flows):
        errors.append("critical_flows debe ser lista de textos")
        flows = []
    if len(flows) != len(set(flows)):
        errors.append("critical_flows contiene duplicados")
    scenarios = p.get("scenarios")
    if not isinstance(scenarios, list):
        errors.append("scenarios debe ser lista")
        scenarios = []
    seen: set[str] = set()
    for i, scenario in enumerate(scenarios, 1):
        if not isinstance(scenario, dict):
            errors.append(f"scenarios[{i}] debe ser objeto")
            continue
        sid = scenario.get("id")
        if not isinstance(sid, str) or not sid.strip() or sid in seen:
            errors.append(f"scenarios[{i}].id vacío o duplicado")
        else:
            seen.add(sid)
        if not isinstance(scenario.get("flow"), str) or scenario["flow"] not in flows:
            errors.append(f"scenarios[{i}].flow debe figurar en critical_flows")
        for field in ("trigger", "user_action", "expected_system_response", "expected_recovery"):
            if not isinstance(scenario.get(field), str) or not scenario[field].strip():
                errors.append(f"scenarios[{i}].{field} obligatorio")
        if scenario.get("severity") not in {"P0", "P1", "P2", "P3"}:
            errors.append(f"scenarios[{i}].severity inválida")
    return errors


def load_profile(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    errors = validate_profile(value)
    if errors:
        raise ValueError(f"{path}: " + "; ".join(errors))
    return value


def catalog(project: Path, global_dir: Path) -> dict[str, tuple[dict[str, Any], str]]:
    """Deterministic priority: bundled < global < project. Only files ending .json."""
    found: dict[str, tuple[dict[str, Any], str]] = {}
    for folder in (BUNDLED, global_dir, project / ".release-auditor" / "profiles"):
        if not folder.exists():
            continue
        for filepath in sorted(folder.glob("*.json")):
            profile = load_profile(filepath)
            if profile["id"] in found:
                print(f"AVISO: {profile['id']} sobrescrito por {filepath}", file=sys.stderr)
            found[profile["id"]] = (profile, str(filepath))
    return found


def command_new(args: argparse.Namespace) -> int:
    if args.kind not in KIND:
        print("ERROR: kind inválido", file=sys.stderr)
        return 2
    base = None
    if args.base:
        profiles = catalog(args.project, args.global_dir)
        if args.base not in profiles:
            print(f"ERROR: perfil base desconocido: {args.base}", file=sys.stderr)
            return 2
        base = copy.deepcopy(profiles[args.base][0])
    p = base if base is not None else new_profile(args.id, args.name, args.role, args.kind)
    old_id = p.get("id", "")
    p.update({"id": args.id, "name": args.name, "enabled": True, "source": "user_defined"})
    p["actor"]["role"] = args.role
    p["actor"]["kind"] = args.kind
    if args.base and args.base != args.id:
        # Avoid silently reusing inherited test IDs. User should author new scenarios.
        p["scenarios"] = []
        p["critical_flows"] = []
        p["notes"] = f"Derivado de {old_id}; completar flujos y escenarios aplicables."
    errors = validate_profile(p)
    if errors:
        print("ERROR: " + "; ".join(errors), file=sys.stderr)
        return 2
    output = args.output or args.project / ".release-auditor" / "profiles" / f"{args.id}.json"
    if output.exists():
        print(f"ERROR: ya existe {output}. No se sobrescribió.", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Perfil creado: {output}\nEdítalo para definir errores, contexto y escenarios. Luego ejecuta validate.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Crear y validar perfiles personalizables de RELEASE AUDITOR")
    ap.add_argument("--project", type=Path, default=Path.cwd(), help="Ruta raíz del proyecto")
    ap.add_argument("--global-dir", type=Path, default=Path.home() / ".release-auditor" / "profiles")
    sub = ap.add_subparsers(dest="action", required=True)
    create = sub.add_parser("new", help="Crear persona modificable en .release-auditor/profiles")
    create.add_argument("--id", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--role", required=True)
    create.add_argument("--kind", choices=sorted(KIND), default="person")
    create.add_argument("--base", help="Copiar contexto de perfil base; no hereda escenarios")
    create.add_argument("--output", type=Path, help="Ruta de salida alternativa")
    check = sub.add_parser("validate", help="Verificar uno o más perfiles JSON")
    check.add_argument("files", nargs="+", type=Path)
    sub.add_parser("list", help="Enumerar plantillas y perfiles globales/de proyecto")
    show = sub.add_parser("show", help="Mostrar perfil resuelto según prioridad")
    show.add_argument("id")
    args = ap.parse_args(argv)
    try:
        if args.action == "new":
            return command_new(args)
        if args.action == "validate":
            for f in args.files:
                p = load_profile(f)
                print(f"OK {p['id']} ({f})")
            return 0
        profiles = catalog(args.project, args.global_dir)
        if args.action == "list":
            for pid, (p, path) in sorted(profiles.items()):
                print(f"{pid}\t{p['actor']['role']}\t{path}")
            return 0
        if args.action == "show":
            if args.id not in profiles:
                print("ERROR: perfil no encontrado", file=sys.stderr)
                return 2
            print(json.dumps(profiles[args.id][0], ensure_ascii=False, indent=2))
            return 0
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
