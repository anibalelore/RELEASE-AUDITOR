# Instala RELEASE AUDITOR en Claude Code y Codex (Windows PowerShell 5.1+ / 7+)
param(
    [ValidateSet('User','Project')][string]$Scope = 'User',
    [string]$ProjectPath = (Get-Location).Path,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'skill'
if (-not (Test-Path (Join-Path $source 'SKILL.md'))) { throw 'Falta skill/SKILL.md. Extraiga el ZIP completo.' }
if ($Scope -eq 'User') { $root = $HOME } else { $root = (Resolve-Path $ProjectPath).Path }
$targets = @(
    (Join-Path $root '.claude/skills/release-auditor'),
    (Join-Path $root '.agents/skills/release-auditor')
)
foreach ($target in $targets) {
    if (Test-Path $target) {
        if (-not $Force) { throw "Ya existe $target. Reejecute con -Force para reemplazar exclusivamente ese skill." }
        Remove-Item -LiteralPath $target -Recurse -Force
    }
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Copy-Item -Path (Join-Path $source '*') -Destination $target -Recurse -Force
    Write-Host "Instalado: $target"
}
Write-Host 'Claude Code: /release-auditor  |  Codex: $release-auditor'
Write-Host 'Si no aparece, reinicie la sesion de Claude Code o Codex.'
