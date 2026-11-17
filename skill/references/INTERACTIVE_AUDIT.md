# RELEASE AUDITOR — Descubrir → Elegir → Probar 5 niveles → Mejorar

Esta es la experiencia principal del skill. El sistema NO comienza intentando cientos de pruebas ni asume que el usuario quiere auditarlo todo. **Primero entiende el producto y ofrece una elección útil**. Los perfiles son configurables y pueden construirse desde el catálogo, un JSON personalizado o directamente desde una descripción conversacional.

## Fase A. DISCOVER / ENTENDER EL SISTEMA (solo inspección, sin cambios)

Al recibir `/release-auditor` o `$release-auditor`, sin perfil ni autorización previa para ejecución:

1. Investigar el proyecto actual (código, documentación, rutas, permisos, esquemas, integraciones, workers, CI y entradas de UI/API). Identificar el producto **por su función**, no por el nombre del repositorio.
2. Entregar una **ficha comprensible para el propietario**, con: qué problema resuelve, usuarios reales, módulos y flujos principales, recorrido de información extremo a extremo, integraciones, qué datos sensibles toca, qué efectos reales produce, lo que se vio directamente y lo que es hipótesis.
3. Generar un **mapa de actores sugeridos por contexto**, no un listado genérico. Para cada actor indicar objetivo, permisos, tareas, fricciones/error humano plausible, flujos críticos e impacto si falla.
4. Proponer **3 a 8 perfiles relevantes** (o menos para un proyecto pequeño), con prioridad sugerida. Incluir opciones «Todos los perfiles críticos», «Crear mi propio perfil», «Combinar dos perfiles» y «Elegir un módulo». Evitar un menú interminable de 100 actores irrelevantes.
5. Mostrar un resumen de cobertura potencial y las incógnitas. **Preguntar una sola cosa**: «¿Desde qué perfil quieres que lo audite primero?» (o aceptar si el usuario lo indicó de antemano). Después **detenerse**; no correr pruebas E2E de perfiles no seleccionados ni modificar el producto sin autorización.
6. El inventario puede guardarse en `.release-auditor/discovery.json` si el usuario autoriza archivos de auditoría; no generar ni publicar secretos. `scripts/audit_session.py validate-discovery` comprueba referencias y estructura, no certifica su veracidad.

La fase A NO emite un veredicto de lanzamiento. Puede informar hallazgos estáticos como **sospechas por comprobar**. Si hay una brecha de seguridad clara identificable desde código, señalarla con cuidado, sin convertir esa observación en una prueba de explotación.

### Formato resumido de respuesta al usuario (fase A)

**Qué hace este sistema:** ...
**Cómo funciona:** A → B → C; entre módulos ...
**Áreas identificadas:** ...
**Perfiles sugeridos (basados en el sistema):**

| Perfil | Qué intenta lograr | Riesgo dominante | Prioridad |
| --- | --- | --- | --- |
| Cliente | ... | ... | alta |
| Supervisor | ... | ... | media |
| CEO/propietario | ... | ... | alta |

**Elige:** uno, varios, todos los críticos, o un perfil personalizado. Puedes indicar también «auditar como [perfil] en [módulo]». **No anunciar un porcentaje de calidad ni aprobación antes de probar.**

## Regla v1.4: escalera de dificultad por perfil

Después de seleccionar actor y flujo(s), ejecutar **nivel 0 uso errático → 1 principiante → 2 intermedio → 3 competente → 4 experto**. **En cada nivel**: (a) fallo provocado específico + recuperación probada y (b) flujo correcto hasta efecto persistido. El auditor informa hallazgos por nivel, no asume que el usuario aprende porque el agente pasa de nivel. Consulta `PROGRESSIVE_AUDIT.md`; si se aprueba un fix, repite la matriz de los cinco niveles sobre el nuevo build. La experiencia digital no es inteligencia ni competencia laboral.

## Fase B. SELECT / CONFIGURAR LA AUDITORÍA

Cuando el usuario elige un perfil (p. ej. «como dueño»):

1. Resolver ese perfil contra roles y permisos reales, sin confundir rol de simulación con elevación de privilegios. Si no existen credenciales del rol, buscar un entorno de prueba apropiado; no pedir ni imprimir contraseñas.
2. Ofrecer personalización mediante lenguaje normal: «dueño nuevo, con poca experiencia digital, en celular, revisa ventas a diario», «cliente impaciente con internet inestable», etc. `scripts/profiles.py new --id ... --name ... --role ... [--base ...]` crea JSON editable; validar con `profiles.py validate`. No editar los perfiles globales sin pedirlo. Las preferencias de contexto son hipótesis de prueba, no verdades sobre personas reales.
3. Diseñar **escenarios por rol y objetivo**, incluyendo camino feliz, errores plausibles, extremos, permisos cruzados, recuperación, integración y estado persistido. Preguntarse: ¿qué haría realmente para lograr su trabajo?, ¿cómo lo interpretaría incorrectamente?, ¿puede recuperarse sin ayuda?
4. Registrar **alcance seleccionado** en `.release-auditor/selection.json` con actor/es, flujos, modo, entorno y fingerprint SHA-256 de `discovery.json`; validar con `audit_session.py validate-selection`.
5. Si el usuario indica explícitamente el perfil en la primera solicitud, realizar igualmente el reconocimiento breve y continuar con dicho perfil en un entorno seguro. Si falta autorización para una acción sensible, detener esa acción y registrar bloqueo. «Audita y corrige» debe ser explícito para cambiar la lógica de producto.

**Principio de elección:** un usuario puede auditar solo «CEO» hoy y «cliente» mañana. La auditoría por perfil no debe atribuirse a perfiles no elegidos. El historial puede agregarse por versión/commit para una auditoría general, siempre que la evidencia siga vigente.

## Fase C. TEST / EJECUCIÓN COMO ESE PERFIL

- Utilizar la interfaz real (cuando existe) en staging o un entorno local aislado, cuentas sintéticas, datos de prueba, y comprobar resultados en backend; para sistemas headless usar contratos y consumer flows.
- Probar la secuencia de tareas desde las expectativas del perfil, no solo botones. Simular errores representativos y recuperación verificable. Alternar escenario normal, límite, extremo, excepción y transición entre actores.
- No confundir un escenario redactado con uno ejecutado. Log, resultado esperado/observado y evidencia ligada a build/entorno para cada prueba.
- Cuando los recursos son insuficientes, registrar `BLOCKED/NOT_RUN` con requisito concreto en vez de inventar éxito. No tocar producción sin autorización específica.
- Puede utilizar pruebas existentes y generar nuevas pruebas en workspace aislado (audit mode). Corregir código solo si el usuario eligió `audit-fix`.

## Fase D. REPORT / INFORME FINAL SEGÚN PERFIL

Mostrar primero los hallazgos más importantes con relación explícita al actor y su tarea:

| Prioridad | Flujo y fallo | Qué hizo el perfil | Resultado real | Corrección concreta | Verificación posterior |
| --- | --- | --- | --- | --- | --- |
| P1 | ... | ... | ... | ... | ... |

Cada finding indica `ID`, impacto de negocio, pasos de reproducción, evidencia, causa raíz confirmada o hipótesis, solución propuesta (UX/proceso/datos/código/permiso), esfuerzo estimado sin falsa precisión, prueba de regresión, y estado. Distinguir **bug demostrado** de **recomendación de diseño** y **riesgo no probado**. Dar *quick wins*, bloqueantes y deuda de mejora con orden recomendado.

**Veredicto por perfil**: `BLOQUEADO`, `INCOMPLETO`, `REQUIERE_REVISION`, `SIN_BLOQUEANTES_OBSERVADOS` (nunca «perfecto»). Reportar número ejecutado/fallido/bloqueado sin deducir porcentajes de un universo desconocido. Explicitar que las demás perspectivas permanecen pendientes.

**Veredicto de lanzamiento global**: solo al pedir «auditoría release integral» o «todos los perfiles críticos», después de cobertura verificable de todos los perfiles/flujos críticos y condiciones de campo/integración aplicables. Usar `release_gate.py`; si falta uno de esos elementos, el máximo veredicto global es `INCOMPLETE`. No prometer ausencia total de errores.

## Fase E. IMPROVE / CORREGIR Y REPROBAR (opcional)

Preguntar si desea «solo informe» o «aplicar correcciones» si no estaba indicado, sin hacer cambios automáticamente. Con `audit-fix`, priorizar P0/P1, escribir test que reproduzca, corregir de forma mínima, probar regresiones y reemitir informe con **antes/después**. Nunca confundir una corrección aplicada con una corrección probada.

## Orden recomendado de comandos naturales

- `/release-auditor` → descubrir y presentar menú de perfiles.
- `/release-auditor Estudia este proyecto y recomiéndame perfiles; aún no ejecutes pruebas` → discovery solo.
- `/release-auditor Audita como CEO` → discovery breve, seleccionar CEO, ejecutar pruebas autorizadas, informe scoped.
- `/release-auditor Audita como cliente nuevo, poca experiencia digital, en móvil y con red intermitente` → persona personalizada temporal.
- `/release-auditor Enfócate en la facturación y el rol administrativo. Solo informe` → módulo + perfil.
- `/release-auditor Audita todos los roles críticos antes del release` → cobertura integral y gate global, no fingir ejecución donde falte acceso.
- `/release-auditor Corrige los P1 confirmados y repite pruebas` → solo con autorización de modificación y con entorno seguro.

En Codex sustituir `/release-auditor` por `$release-auditor`.
