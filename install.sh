#!/usr/bin/env bash
# Instalador para Linux, macOS y WSL; sin dependencias externas.
set -euo pipefail
usage() { echo "Uso: ./install.sh [--user | --project /ruta/repo] [--force]"; }
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/skill"
[ -f "$SOURCE/SKILL.md" ] || { echo "No existe skill/SKILL.md" >&2; exit 2; }
ROOT="$HOME"; FORCE=0
while (($#)); do
  case "$1" in
    --user) ROOT="$HOME"; shift ;;
    --project) [ "$#" -ge 2 ] || { usage; exit 2; }; ROOT="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    *) usage; exit 2 ;;
  esac
done
[ -d "$ROOT" ] || { echo "Carpeta no encontrada: $ROOT" >&2; exit 2; }
ROOT="$(cd "$ROOT" && pwd)"
for rel in .claude/skills/release-auditor .agents/skills/release-auditor; do
  target="$ROOT/$rel"
  if [ -e "$target" ] && [ "$FORCE" -ne 1 ]; then
    echo "Ya existe $target. Use --force para reemplazar ese skill." >&2
    exit 1
  fi
  if [ "$FORCE" -eq 1 ] && [ -e "$target" ]; then rm -rf -- "$target"; fi
  mkdir -p -- "$target"
  cp -R "$SOURCE"/. "$target"/
  echo "Instalado: $target"
done
printf 'Claude Code: /release-auditor | Codex: $release-auditor\nSi no aparece, reinicie la sesión.\n'
