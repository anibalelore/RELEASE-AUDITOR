# RELEASE AUDITOR 1.3 — Auditoría por perfiles para Claude Code y Codex

Skill transversal en español para auditar proyectos de software antes de producción. **No aprueba un release solo por leer el código.** Exige ejecución real, resultados esperados/observados, artefactos existentes, flujos críticos y evidencia de release.

Compatible con **Claude Code** (`.claude/skills/release-auditor/SKILL.md`) y **Codex** (`.agents/skills/release-auditor/SKILL.md`). Ambos usan el mismo `skill/SKILL.md`.

## Instalación global en Windows (PowerShell)

1. Extrae `release-auditor.zip`.
2. Abre PowerShell en la carpeta extraída (donde está `install.ps1`).
3. Ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Scope User
```

Si utilizas PowerShell 7 puedes ejecutar `pwsh -File ./install.ps1 -Scope User`. La opción de política es específica de ese proceso; puedes también abrir PowerShell y ejecutar el script de la forma que admita la política de tu equipo.

En tu repositorio solamente (compartible con el equipo):

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Scope Project -ProjectPath "C:\ruta\mi-proyecto"
```

Reemplaza únicamente el skill existente si lo quieres actualizar con `-Force`.

## Instalación global en macOS, Linux y WSL

En la carpeta del paquete:

```bash
./install.sh --user
```

O solo en un proyecto:

```bash
./install.sh --project /ruta/al/repositorio
```

Para reinstalar de forma explícita: agrega `--force`.

**Importante:** Windows PowerShell y WSL tienen `$HOME` distintos. Ejecuta el instalador dentro del mismo entorno donde usas Claude Code/Codex. Reinicia su sesión si no detecta el skill.

## NUEVO v1.4: auditoría progresiva, del uso errático al experto

Para **cada perfil seleccionado**, RELEASE AUDITOR prueba cinco niveles de interacción: `erratico` → `principiante` → `intermedio` → `competente` → `experto`. En **cada uno** ejecuta una situación errónea con recuperación y una tarea correcta, utilizando **la misma versión** del software. Así detecta tanto la falta de guía para principiantes como errores de concurrencia/atajos para expertos.

Primero el skill estudia el sistema y el usuario elige el perfil. La herramienta define pruebas específicas según el módulo. El flujo predeterminado es **entender → elegir perfil → error + recuperación y uso correcto en 5 niveles → informe → corrección autorizada → regresión de los 5 niveles**.

```text
/release-auditor Estudia este sistema. Audita como cliente en los 5 niveles,
comenzando con uso errático extremo. Para cada nivel prueba entradas equivocadas,
recuperación guiada y camino correcto. Registra evidencia de UI y estado persistido.
Solo propone mejoras; no cambies el producto sin autorización. Si autorizo
correcciones, avanza nivel por nivel y al final repite toda la matriz.
```

Generar una plantilla de 10 escenarios por flujo sin ejecutarlos:

```bash
python skill/scripts/progression.py plan --actor cliente --role "Cliente" --flow registro --output plan-cliente.json
python skill/scripts/progression.py validate plan-cliente.json
```

Si ya creaste un perfil personalizado, el generador también admite `--profile .release-auditor/profiles/mi-perfil.json` y usará sus cinco comportamientos personalizados (y sus flujos definidos). La plantilla queda en `not_run`. El gate de release (`release_gate.py`) exige, cuando procede, evidencias vinculadas a los escenarios progresivos. **Ninguna simulación de perfiles equivale a pruebas observadas con usuarios reales**, y no garantiza cero errores. Lee [Auditoría progresiva](skill/references/PROGRESSIVE_AUDIT.md).

## NUEVO v1.3: elige desde qué persona auditar después de descubrir el producto

**Esta es la experiencia predeterminada:** primero el skill analiza el proyecto y explica qué hace; después propone perfiles relevantes (cliente, dueño/CEO, empleado, supervisor, administrador, tercero, agentes y sistemas), tú eliges desde cuáles probar, y solo entonces ejecuta pruebas y presenta un informe con soluciones. No empieza la ejecución masiva sin conocer el perfil elegido.

```text
Usuario: /release-auditor
Auditor: He analizado este sistema: [descripción basada en el repositorio].
         Áreas: [...]. Perfiles recomendados: [cliente, CEO, soporte, ...].
         ¿Desde cuál empezamos? (Puedes crear uno personalizado).
Usuario: Como dueño, con poca familiaridad digital y desde el celular.
Auditor: Plan por rol → pruebas ejecutadas con evidencia → fallos → cómo corregirlos.
```

**Claude Code:** `/release-auditor` para estudiar y elegir; `/release-auditor Audita como CEO` si ya sabes el rol.

**Codex:** `$release-auditor` o `$release-auditor Audita como cliente nuevo con mala conexión`.

Puedes elegir múltiples roles, un módulo, «todos los críticos» o **crear perfiles personalizados**. Define objetivo, permisos, vocabulario, nivel digital, idioma, dispositivo, entorno, presión, errores frecuentes y recorridos obligatorios; guarda los perfiles en `.release-auditor/profiles/` o en la carpeta global. Ejemplo:

```bash
python skill/scripts/profiles.py new --id mi-ceo --name "Dueño de operación" --role CEO
python skill/scripts/profiles.py validate .release-auditor/profiles/mi-ceo.json
```

El motor usa `skill/references/INTERACTIVE_AUDIT.md`. El inventario (`discovery.json`) y la elección (`selection.json`) pueden verificarse así:

```bash
python skill/scripts/audit_session.py validate-discovery .release-auditor/discovery.json
python skill/scripts/audit_session.py fingerprint .release-auditor/discovery.json
python skill/scripts/audit_session.py validate-selection .release-auditor/discovery.json .release-auditor/selection.json
```

**Diferencia crítica:** auditar como CEO y no encontrar problemas NO aprueba toda la aplicación. El informe indica claramente perspectivas pendientes; un veredicto global solo se evalúa al cubrir con evidencia todos los actores y flujos críticos. Las pruebas no disponibles permanecen `NOT_RUN/BLOCKED`.

### Qué verás en el informe por perfil

| Encontrado | Evidencia | Cómo corregir | Verificación posterior |
| --- | --- | --- | --- |
| Error o fricción en un flujo | Pasos reproducibles y resultado real | Ajuste concreto de experiencia, reglas, permisos o código | Prueba de regresión y recuperación de usuario |

Primero ofrece informe y mejoras; **no modifica tu aplicación salvo que pidas `audit-fix`**. Para requisitos y formatos, consulta [el proceso interactivo](skill/references/INTERACTIVE_AUDIT.md).

## Cómo invocarlo

**Claude Code** (en la carpeta del repositorio):

```text
/release-auditor Audita este sistema en modo release. Revisa flujos críticos de extremo a extremo, permisos, DB, APIs, UI, fallos de red, integraciones y build. Usa staging y datos de prueba; no modifiques producción. Ejecuta tests reales, presenta evidencia y bloquea el release si hay fallos. No afirmes que está listo si algo quedó sin verificar.
```

**Codex** (en el repositorio):

```text
$release-auditor Audita este repo en modo audit (sin alterar código funcional). Construye una matriz de pruebas por riesgo; ejecuta todo lo que puedas realmente, registra los bloqueos e informa fallos con pasos de reproducción y evidencias. Evalúa release gate.
```

**Para auditar y corregir**: `Modo audit-fix: corrige solo los defectos confirmados, agrega regresión y vuelve a ejecutar suite; no despliegues.`

**Para un módulo**: `Modo module: audita el módulo de check-in e integraciones de punta a punta; no certifiques módulos que no se probaron.`

## NUEVO v1.2: atlas universal de actores

**El auditor ya no se limita a conductores y operadores.** Utiliza `skill/references/PERSONA_ATLAS.md` (18 familias, perfiles externos, internos, directivos, terceros y actores no humanos) y `skill/references/PERSONA_ENGINE.md` para reconocer los roles que realmente participan en un proyecto.

Combina **rol + objetivo + experiencia digital + conocimiento del oficio + dispositivo + contexto + permisos + datos + interrupciones + riesgo + recuperación**. Selecciona combinaciones representativas basadas en riesgo, no todos los posibles productos cartesianos. Prueba desde un cliente que abandona el registro hasta un dueño que revisa el dashboard y un worker que reintenta un pago duplicado. Nunca asume que poca alfabetización digital significa baja inteligencia.

Para el veredicto, el nuevo `stakeholder_coverage` en `audit-results.json` exige inventario de actores, escenarios críticos por actor/flujo y resultados ejecutados con evidencia. El mecanismo no inventa pruebas ni valida campo por IA. Revisa `skill/references/REPORTING.md`.

**Comando universal en Claude Code:**

```text
/release-auditor Audita este proyecto de extremo a extremo como cliente, operador,
supervisor, dueño, administrador, proveedor, soporte, auditor y servicios externos
solo en los roles que realmente apliquen. Cruza perspectivas, privilegios,
condiciones difíciles, malentendidos, escenarios extremos y recuperación.
Ejecuta pruebas y evidencia, informa personas/actores no cubiertos. No certifiques
si falta algún escenario crítico y no modifiques producción.
```

**En Codex:**

```text
$release-auditor Modo release universal: descubre todos los actores relevantes,
genera pruebas adaptativas por riesgo y valida handoffs entre roles con evidencia.
No confundas hipótesis con pruebas y bloquea el release incompleto.
```

## NUEVO: simulación extrema de personas reales (Human First)

El auditor se coloca en el lugar de un conductor o un operador de máquina con poca familiaridad **digital** y trabajo complejo fuera de la pantalla. No confunde habilidades informáticas con inteligencia. Simula decisiones humanas equivocadas, interpretaciones literales, fotos de objetos incorrectos, licencias giradas o cortadas, firmas en lugares incorrectos, respuestas como "mi camión tiene dos colores", fallas de red, guantes, pantallas en el sol, interrupciones y cambio de turnos.

Como ejemplos aplicables solo cuando el dominio corresponda, el paquete incorpora **20 escenarios de check-in de drivers** y **16 escenarios para operadores de planta**, además de una metodología transversal que combina prueba automatizada real, validación de comportamiento, recuperación y veredicto de lanzamiento. La simulación con IA no reemplaza pruebas observadas con usuarios representativos en terreno para flujos críticos.

Ejemplo Claude Code:

```text
/release-auditor Modo release: audita el check-in como un conductor profesional
con poca experiencia usando formularios. Ejecuta casos DR-01 a DR-20
con datos sintéticos, fotografías erróneas, documento cortado, firma mal puesta,
conexión caída, respuestas ambiguas y recuperación del usuario. Verifica estado
real y registro en backend. No certifiques si faltan escenarios o piloto en campo.
```

Ejemplo Codex:

```text
$release-auditor Haz una auditoría HUMAN FIRST del módulo de operadores.
Ejecuta casos OP-01 a OP-16 y tus casos adversariales propios,
con evidencias UI/backend, antes de declarar listo para producción.
```

El formato `audit-results.json` admite `human_factors` con escenarios críticos específicos, validación de campo y verificaciones de evidencia **fail-closed**; el gate declara `INCOMPLETE` si faltan.

## Ejemplo de flujo interactivo (no representa una auditoría real)

- [`examples/discovery.example.json`](examples/discovery.example.json): mapa ficticio de sistema, módulos, flujos y actores.
- [`examples/selection.example.json`](examples/selection.example.json): elección ficticia del perfil «dueño/CEO» y su flujo.

Ejecuta `python skill/scripts/audit_session.py validate-selection examples/discovery.example.json examples/selection.example.json` para verificar la consistencia de la selección; **esto no ejecuta pruebas sobre una aplicación**.

## Qué produce el auditor

- Inventario de módulos y flujos críticos.
- Matriz de escenarios positivos, negativos y adversariales.
- Pruebas reales (Playwright / tests del stack / APIs / integraciones en entorno seguro) cuando dispone de herramientas, servidor y credenciales de prueba.
- Bugs con severidad P0 a P3, reproducción, evidencia y propuesta de corrección.
- `audit-results.json` y `audit-report.md` (solo después de auditar).
- `release_gate.py` que no da luz verde cuando falta evidencia.

### Gate (para informes reales)

```bash
python /ruta/skill/scripts/release_gate.py audit-results.json --output audit-report.md
```

En el ZIP hay un **ejemplo intencionalmente INCOMPLETE** para demostrar que no fabrica éxito:

```bash
python skill/scripts/release_gate.py examples/audit-results.example.json --output /tmp/audit-example.md
```

Este comando termina con exit code **1** (no verde) por diseño. 0 = `READY_CANDIDATE`, 1 = otra decisión, 2 = JSON ilegible. `READY_CANDIDATE` significa candidato a validación humana, no garantía.

## Lo que este skill NO hace por sí solo

- No conecta automáticamente a tu app ni inicia sesión sin acceso de prueba y herramientas disponibles.
- No reemplaza un staging bien configurado, Playwright, CI ni observabilidad.
- No puede comprobar facturación real, email real o servicios externos si solo existen mocks.
- No hace pruebas masivas ni ataques a sistemas externos no autorizados.
- **No puede garantizar cero bugs**: maximiza detección y transparencia del riesgo residual.

## Estructura

```
release-auditor/
  README.md
  install.ps1            # Windows
  install.sh             # Linux/macOS/WSL
  skill/
    SKILL.md             # skill común
    references/
      SCENARIOS.md       # casos adversariales
      RUNBOOK.md         # cómo ejecutar con evidencia
      REPORTING.md       # JSON y severidades
      PROFILE.md         # plantilla de adaptación por proyecto
      PERSONA_ATLAS.md   # 18 familias de actores y ejemplos
      PERSONA_ENGINE.md  # generación adaptativa por riesgo
      INTERACTIVE_AUDIT.md # descubrir → elegir → probar → informar
    scripts/
      profiles.py         # perfiles a medida
      audit_session.py    # validador de selección
      release_gate.py     # verificador fail-closed
      test_release_gate.py
  examples/
    audit-results.example.json  # deliberadamente sin pruebas ejecutadas
```

## Diseño recomendado del equipo

1. **Agente desarrollador** implementa funcionalidad y sus unit tests.
2. **RELEASE AUDITOR en el otro asistente** prueba de forma independiente un build de staging y reporta defectos con reproducción.
3. Desarrollador corrige; auditor ejecuta regresión y confirma artefactos.
4. CI ejecuta suite y report gate por cada release. La decisión final queda en una persona responsable.

Documentación oficial: [Claude Code skills](https://code.claude.com/docs/en/skills), [Codex skills](https://learn.chatgpt.com/docs/build-skills), [Playwright](https://playwright.dev/docs/intro), [OWASP ASVS](https://asvs.owasp.org/).
