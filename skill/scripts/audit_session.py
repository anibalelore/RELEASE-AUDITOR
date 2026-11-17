#!/usr/bin/env python3
"""Validate staged interactive audit metadata, not the truth of a real-world audit.

Discovery is a non-executing description of an application. Selection references
its exact contents to prevent accidental scope/role drift after a code change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"No se pudo leer {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: se requiere un objeto JSON")
    return data


def good_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def unique_ids(data: object, label: str, errors: list[str]) -> set[str]:
    if not isinstance(data, list):
        errors.append(f"{label}: lista requerida")
        return set()
    ids: set[str] = set()
    for index, item in enumerate(data):
        if not isinstance(item, dict) or not good_text(item.get("id")):
            errors.append(f"{label}[{index}]: id requerido")
            continue
        val = item["id"]
        if val in ids:
            errors.append(f"{label}: id duplicado: {val}")
        ids.add(val)
    return ids


def validate_discovery(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version debe ser 1")
    project = data.get("project")
    if not isinstance(project, dict) or not good_text(project.get("name")) or not good_text(project.get("purpose")):
        errors.append("project requiere name y purpose")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources or any(not good_text(s) for s in sources):
        errors.append("sources requiere al menos un origen inspeccionado")
    modules = unique_ids(data.get("modules"), "modules", errors)
    flows = unique_ids(data.get("flows"), "flows", errors)
    actors = unique_ids(data.get("actors"), "actors", errors)
    if not modules:
        errors.append("se necesita al menos un módulo real observado o inferido")
    if not flows:
        errors.append("se necesita al menos un flujo real observado o inferido")
    if not actors:
        errors.append("se necesita al menos un actor sugerido")
    for item in data.get("modules", []) if isinstance(data.get("modules"), list) else []:
        if isinstance(item, dict) and (not good_text(item.get("name")) or not good_text(item.get("purpose"))):
            errors.append(f"módulo {item.get('id')}: name y purpose requeridos")
    for item in data.get("flows", []) if isinstance(data.get("flows"), list) else []:
        if not isinstance(item, dict):
            continue
        if not good_text(item.get("name")) or not isinstance(item.get("critical"), bool):
            errors.append(f"flujo {item.get('id')}: name y critical requeridos")
        m = item.get("modules")
        if not isinstance(m, list) or not m or any(mid not in modules for mid in m):
            errors.append(f"flujo {item.get('id')}: módulos inexistentes o vacíos")
    for item in data.get("actors", []) if isinstance(data.get("actors"), list) else []:
        if not isinstance(item, dict):
            continue
        if not good_text(item.get("role")) or not isinstance(item.get("critical"), bool):
            errors.append(f"actor {item.get('id')}: role y critical requeridos")
        if item.get("source") not in ("observed", "inferred", "custom"):
            errors.append(f"actor {item.get('id')}: source inválido")
        f = item.get("recommended_flows")
        if not isinstance(f, list) or any(fid not in flows for fid in f):
            errors.append(f"actor {item.get('id')}: recommended_flows inválidos")
    return errors


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_selection(data: dict, discovery: dict, discovery_path: Path) -> list[str]:
    errors = validate_discovery(discovery)
    if errors:
        return ["discovery inválido: " + e for e in errors]
    if data.get("schema_version") != 1:
        errors.append("schema_version debe ser 1")
    if data.get("discovery_sha256") != sha256(discovery_path):
        errors.append("discovery_sha256 no coincide: volver a estudiar o actualizar selección")
    if data.get("mode") not in ("audit", "audit-fix", "release"):
        errors.append("mode debe ser audit, audit-fix o release")
    if data.get("scope") not in ("profiles", "all-critical"):
        errors.append("scope debe ser profiles o all-critical")
    if data.get("execution_environment") not in ("local", "staging", "sandbox", "none"):
        errors.append("execution_environment debe ser local/staging/sandbox/none")
    if data.get("user_selected") is not True:
        errors.append("user_selected debe ser true solo después de una selección explícita")
    available_actors = {a["id"] for a in discovery["actors"]}
    selected = data.get("selected_actor_ids")
    if not isinstance(selected, list) or not selected or len(selected) != len(set(selected)) or any(i not in available_actors for i in selected):
        errors.append("selected_actor_ids debe ser una lista única de actores existentes")
        selected = []
    available_flows = {f["id"] for f in discovery["flows"]}
    selected_flows = data.get("selected_flow_ids")
    if not isinstance(selected_flows, list) or not selected_flows or len(selected_flows) != len(set(selected_flows)) or any(i not in available_flows for i in selected_flows):
        errors.append("selected_flow_ids debe ser una lista única de flujos existentes")
        selected_flows = []
    if data.get("mode") == "release" and data.get("scope") != "all-critical":
        errors.append("release integral requiere scope all-critical; para perfil único usa audit")
    if data.get("scope") == "all-critical":
        missing_actors = {a["id"] for a in discovery["actors"] if a["critical"]} - set(selected)
        missing_flows = {f["id"] for f in discovery["flows"] if f["critical"]} - set(selected_flows)
        if missing_actors:
            errors.append("faltan actores críticos: " + ", ".join(sorted(missing_actors)))
        if missing_flows:
            errors.append("faltan flujos críticos: " + ", ".join(sorted(missing_flows)))
    if data.get("mode") == "audit-fix" and data.get("permission_to_modify_product") is not True:
        errors.append("audit-fix requiere permission_to_modify_product true y autorización real")
    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Valida el flujo interactivo de RELEASE AUDITOR")
    sub = p.add_subparsers(dest="action", required=True)
    d = sub.add_parser("validate-discovery", help="Validar inventario sin ejecutar pruebas")
    d.add_argument("discovery", type=Path)
    f = sub.add_parser("fingerprint", help="Huella SHA-256 para selection.json")
    f.add_argument("discovery", type=Path)
    s = sub.add_parser("validate-selection", help="Validar selección después de elegir perfil")
    s.add_argument("discovery", type=Path)
    s.add_argument("selection", type=Path)
    args = p.parse_args(argv)
    try:
        disc = load(args.discovery)
        if args.action == "fingerprint":
            print(sha256(args.discovery))
            return 0
        errors = validate_discovery(disc)
        if args.action == "validate-selection":
            sel = load(args.selection)
            errors = validate_selection(sel, disc, args.discovery)
        if errors:
            for error in errors:
                print("ERROR:", error, file=sys.stderr)
            return 1
        print("OK: esquema de fase validado. No confirma pruebas ni evidencia de producción.")
        return 0
    except ValueError as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
