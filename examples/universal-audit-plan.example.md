# Plan ilustrativo UNIVERSAL AUDIT — sin pruebas ejecutadas

Este ejemplo enseña cómo generar nuevos perfiles y situaciones para **el sistema encontrado**, sin atar el skill a un sector.

1. Detectar actividades, actores (humanos y máquina), estados y efectos reales de cada flujo crítico.
2. Para cada flujo, construir pruebas `happy_path`, `plausible_misuse`, `boundary` y `recovery`.
3. Registrar y justificar una por una las categorías de `references/UNIVERSAL_AUDIT.md` como aplicables o no aplicables; vincular las aplicables a flujos y escenarios.
4. Generar 2–5 combinaciones de alto riesgo por flujo cuando el contexto lo justifique: actor + dispositivo/red + estado + dependencia externa + tiempo.
5. Ejecutar realmente, sin tocar producción destructivamente. Separar **simulación** de **observación con personas reales**.
6. Comprobar que la tarea termina, el estado persistido es correcto, no hay efectos duplicados o no autorizados, y la recuperación no hace perder trabajo.
7. Entregar evidencia por escenario, bugs reproducibles, cobertura no ejecutada y veredicto del gate.

Ejemplos breves de situaciones que se adaptan al producto:

| Sistema | Actor | Acción adversarial plausible | Comportamiento seguro esperado |
| --- | --- | --- | --- |
| Portal de clientes | persona que entra por primera vez | intenta confirmar dos veces y vuelve con Back | una sola operación, estado consistente y mensaje claro |
| B2B/API | cliente automatizado | repite webhook con mismo ID tras timeout | idempotencia, sin doble cargo o evento |
| IA con herramientas | agente ejecutor | contenido externo intenta activar una acción no autorizada | ignora instrucción no confiable, pide permisos, registra bloqueo |
| Gestión industrial | supervisor de turno | edita registro mientras operador lo finaliza | política de concurrencia coherente y auditada |
| App móvil | usuario con conexión mala | sube imagen, cierra y regresa | progreso recuperable o fallo claro, sin aceptar archivo inválido |
| Marketplace | vendedor | cancela después de parcial settlement | saldo, comisiones y reembolso conciliados |

No generes un archivo `audit-results.json` positivo con estas frases: son un catálogo de posibles tests, no evidencia.
