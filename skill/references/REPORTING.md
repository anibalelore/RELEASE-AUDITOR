# Esquema audit-results.json y veredictos

El gate usa solo biblioteca estándar Python. No reemplaza ejecutar tests: **valida coherencia de la evidencia declarada**.

Archivo JSON requerido, con objetos no vacíos y strings reales (sin placeholders):

```json
{
  "project": "mi-sistema",
  "environment": "staging",
  "build": "commit-o-build-identificador",
  "timestamp": "2026-11-16T20:00:00Z",
  "critical_flows": ["auth", "authorization", "persist-record"],
  "human_factors": {"applicable": false, "not_applicable_reason": "Ejemplo del contrato JSON para servicio sin interfaz operativa"},
  "full_suite_executed": true,
  "full_suite_evidence": ["artifacts/test-results/junit.xml"],
  "production_parity_verified": true,
  "production_parity_evidence": ["artifacts/release-config-check.txt"],
  "tests": [
    {
      "id": "QA-001",
      "flow": "auth",
      "critical": true,
      "status": "passed",
      "expected": "Login de usuario de prueba crea sesión",
      "observed": "Sesión de test obtenida; navegación autorizada",
      "action": "npx playwright test tests/e2e/auth.spec.ts",
      "evidence": ["artifacts/test-results/auth-trace.zip"]
    }
  ],
  "findings": [
    {
      "id": "BUG-001",
      "severity": "P2",
      "status": "open",
      "title": "Botón desalineado en móvil",
      "steps": "Abrir pantalla X a 375px y pulsar Y",
      "expected": "Botón visible",
      "observed": "Botón cortado",
      "evidence": ["artifacts/mobile-button.png"]
    }
  ],
  "limitations": ["No se probó la API de producción; solo sandbox"]
}
```

Valores `tests[].status`: `passed`, `failed`, `blocked`, `not_run`. `findings[].status`: `open`, `resolved`, `unverified`. Severidades `P0`, `P1`, `P2`, `P3`. Toda evidencia debe ser una referencia a resultado o artefacto existente, comprobable al auditar; no inventes rutas ni digas que el script valida el contenido de archivos remotos. El script verifica referencias locales de archivo cuando es posible, no comprueba la calidad semántica del test.

`critical_flows` **debe proceder del inventario real**, no escogerse para esconder cobertura ausente. Todo flujo crítico requiere al menos un test `passed` con acción, esperado, observado y evidencia. Si hay casos adicionales del flujo fallidos/bloqueados, el gate no aprueba el flujo.

`full_suite_executed` y `production_parity_verified` requieren sus respectivas evidencias. Si no existe staging o la paridad no pudo comprobarse, indicar `false`.

## Severidad

- **P0**: pérdida/fuga grave de datos, operación destructiva, cobro indebido, aislamiento tenant vulnerado, caída crítica.
- **P1**: flujo esencial indisponible o incorrecto, autenticación/autorización rota, corrupción potencial de datos, integración crítica incumplida.
- **P2**: función importante rota sin mitigación satisfactoria, regresión o accesibilidad relevante.
- **P3**: inconveniente menor/cosmético o mejora no bloqueante.

## Regla de release

1. `NO_GO` si hay hallazgos P0/P1 abiertos o sin verificar; o tests críticos `failed`.
2. `INCOMPLETE` si hay flujos críticos sin cobertura aprobada, tests críticos bloqueados/no ejecutados, faltan evidencias/suite/paridad, o datos inválidos.
3. `REVIEW_REQUIRED` si hay P2/P3 abiertos o fallos no críticos.
4. `READY_CANDIDATE` si no hay impedimentos conocidos con toda la evidencia exigida. Requiere aprobación humana y no garantiza ausencia de errores.

## Plantilla de resumen al usuario

```md
# Informe QA — [proyecto] — [fecha]
**Veredicto**: NO_GO | INCOMPLETE | REVIEW_REQUIRED | READY_CANDIDATE
**Alcance**: [módulos], [ambiente], [build/commit], [navegadores]
**Pruebas reales**: X passed / Y failed / Z blocked / W not_run
**Flujos críticos**: completados / totales, con evidencia
**Riesgos abiertos**: P0: X, P1: X, P2: X, P3: X

## Hallazgos principales
[ID] [Prioridad] Módulo — reproducción — esperado vs observado — evidencia — fix — regression test

## No probado
[Limitaciones, credenciales, sandbox, permisos, prod]

## Recomendación
[Orden concreto: 1, 2, 3 + rollback + decisión humana]
```

## Gate de factores humanos v1.1

`human_factors` es obligatorio incluso si la aplicación es solo backend. Si no hay interacción humana directa, indicar `{"applicable": false, "not_applicable_reason": "..."}` con razón precisa. En toda UI de usuarios de campo, se requiere `applicable: true`. Ejemplo mínimo **de estructura, no resultado real**:

```json
{
  "human_factors": {
    "applicable": true,
    "personas": [{"id": "driver", "context": "Chofer con poca familiaridad digital; móvil bajo sol y red irregular"}],
    "required_scenarios": [
      {"id": "DR-01", "flow": "driver-checkin", "persona_id": "driver",
       "expected_recovery": "Rechazar foto de pies sin certificar documento y guiar nuevo intento"}
    ],
    "field_validation_required": true,
    "field_validation_completed": false,
    "field_validation_summary": "",
    "field_validation_evidence": []
  },
  "tests": [
    {"id": "QA-DR-01", "flow": "driver-checkin", "scenario_id": "DR-01", "critical": true,
     "status": "not_run", "action": "", "expected": "", "observed": "", "evidence": []}
  ]
}
```

Cada escenario humano requerido debe vincularse a un flujo crítico declarado y a una persona declarada; su `tests[].scenario_id` debe tener al menos un test **passed, critical=true, ejecutado y con evidencia real**; cualquier fallido bloquea release, cualquier bloqueado o no ejecutado causa INCOMPLETE. No cuentes escenarios imaginados como tests.

`field_validation_required: true` exige `field_validation_completed: true`, resumen anonimizado y archivo de evidencia existente de piloto observado con usuarios representativos (no fotos de documentos ni datos privados). Si es inviable y el dueño del producto asume el riesgo excepcional, puede declararse `field_validation_required: false` junto a `field_validation_waiver_reason` y `field_validation_waiver_approver`; el gate devuelve como máximo `REVIEW_REQUIRED`, nunca READY_CANDIDATE. No escribas una exención para sortear el gate.

**Importante**: este script solo comprueba referencias locales y coherencia declarada: **no verifica la honestidad, la calidad ni el origen de un piloto**. Un auditor humano debe corroborar las pruebas de campo.

## Gate de cobertura de actores v1.2

`stakeholder_coverage` es obligatorio en todo informe v1.2, incluso para productos sin interfaz. No implica probar roles inaplicables. Ejemplo **estructural**, no evidencia:

```json
{
  "stakeholder_coverage": {
    "actors": [
      {"id":"cliente","role":"Cliente final","context":"Hace pedido por primera vez", "type":"person", "source":"observed", "critical":true},
      {"id":"pagos","role":"Proveedor de pagos","context":"Webhook reintentado", "type":"system", "source":"observed", "critical":true}
    ],
    "required_scenarios": [
      {"id":"STA-001","actor_id":"cliente","flow":"checkout","expected_outcome":"Una sola orden y un solo cobro","risk":"Doble pago"},
      {"id":"STA-002","actor_id":"pagos","flow":"checkout","expected_outcome":"Webhook idempotente","risk":"Duplicación de confirmación"}
    ],
    "excluded_actor_groups": [{"group":"produccion","reason":"No existen operarios ni maquinaria en este software"}]
  },
  "tests": [{"id":"QA-001","flow":"checkout","stakeholder_scenario_id":"STA-001","critical":true,"status":"not_run"}]
}
```

Cada actor crítico necesita al menos un escenario y cada flujo crítico al menos uno vinculado a un actor. Cada escenario debe tener una ejecución crítica `passed` y evidencia de archivo existente, sin fallos ni escenarios incompletos. La auditoría no debe incluir roles ajenos solo para inflar cobertura.
