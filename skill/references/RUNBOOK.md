# Runbook de pruebas reales

## Descubrimiento

Inspeccionar archivos antes de elegir comandos; algunos proyectos no usan Node. Identificar `package.json`, `pnpm-lock.yaml`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `.github/workflows`, `supabase/`, `prisma/`, `playwright.config.*`, `docker-compose*` y documentación de tests. Capturar `git rev-parse HEAD` si aplica; `git status --short` antes/después. No imprimir `.env` ni credenciales.

## Comandos, solo cuando encajan con el stack

- Node: ejecutar scripts **existentes** de `package.json`: `npm run build`, `npm run typecheck`, `npm test` / equivalentes con pnpm/yarn/bun. Revisar scripts antes de invocarlos; podrían mutar DB o producción.
- Python: `pytest` con entorno virtual y base de tests, no con credenciales productivas.
- Playwright (si ya instalado): `npx playwright test --reporter=list`, `npx playwright show-report`, `npx playwright show-trace path/to/trace.zip`. Generar o adaptar tests a rutas reales y locators resilientes (`getByRole`, `getByLabel`) con assertions de resultado, no solo screenshots.
- Si no hay suite E2E: proponer/configurar Playwright en rama o carpeta de test autorizada. Evitar instalar dependencias sin evaluar impacto, riesgo y permisos. La auditoría queda incompleta hasta ejecutar tests.
- Integraciones externas: usar sandbox/fixtures verídicos y mostrar por separado qué no pudo verificarse contra tercero real.

## Evidencia mínima por test

Incluir ID, flujo, criticidad, entorno, commit/build, timestamp, precondiciones, comando/acciones ejecutadas, resultado esperado, resultado observado, status, evidencia (log/trace/screenshot/response sanitizados) y limpieza realizada. Guardar screenshots/traces solo en rutas permitidas; no incluir secretos, documentos de clientes ni datos personales.

## Controles para evitar falsos positivos

- Tests que simplemente hagan `expect(true).toBe(true)` no cuentan.
- Un stub 200 no prueba una API externa.
- Una tabla que se ve llena no demuestra que se guardó en DB.
- Un `console.log('success')` sin verificación no prueba nada.
- Un bypass de autenticación en test no prueba las reglas de autorización.
- El código que el propio asistente creó debe ser auditado con los mismos criterios; preferir proceso revisor separado si hay otro agente disponible.
- Si existe CI, ejecutar también allí y comprobar que la pipeline efectivamente impida deploy cuando fallan tests críticos; un badge verde antiguo no cuenta como validación actual.

## Ciclo de corrección

Defecto real -> test reproductor FAIL -> fix mínimo -> test PASS -> pruebas de vecinos -> suite amplia -> verificación en build de producción/staging -> actualizar reporte. Máximo dos iteraciones automáticas por defecto. Si no se puede verificar el fix, estado es `unverified`, no `resolved`.

## Pruebas HUMAN FIRST

Lee `HUMAN_FACTORS.md`, `DRIVER_CHECKIN.md`, `MACHINE_OPERATOR.md` según el uso. Usa Playwright para interactuar con la aplicación real cuando hay permiso. Ejecuta casos desde cada persona: comenzar sin formación previa, intentar subir una foto incorrecta, no saber un término, dar una respuesta literal, firmar en el lugar equivocado, perder red, y recuperar el flujo. No basta inspeccionar un componente de validación; confirma persistencia/rechazo y mensajes al usuario.

Etiqueta cada prueba de persona con `tests[].scenario_id`, ligado a `human_factors.required_scenarios[].id`. Recolecta fixtures de prueba sintéticos (no datos de conductores reales). Para flujos críticos, un piloto controlado observado con operadores o conductores representativos es un requisito aparte; nunca atribuir al agente un estudio de campo no realizado.
