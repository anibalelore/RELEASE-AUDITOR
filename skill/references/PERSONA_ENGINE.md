# Motor universal de perfiles, circunstancias y comportamiento — 1.2

## Regla central

El sistema no tiene un catálogo fijo de "usuarios tontos". Tiene **actores + objetivos + conocimientos + condiciones + fallos + consecuencias + recuperación**. El auditor explora al menos lo razonablemente relevante, priorizado por impacto, frecuencia y detectabilidad. Un usuario muy competente puede equivocarse; un usuario con baja familiaridad digital puede dominar su oficio.

### 1. Descubrimiento de actores (obligatorio para cualquier tipo de proyecto)

Extraer pistas de: documentación, capturas, roles y permisos reales, tablas, endpoints, rutas, ACL/RLS, manuales, términos de servicio, tickets, diseño, logs anonimizados e instrucciones del usuario. Separar **confirmado** vs **inferido**. Identificar también a quien **no usa la pantalla, pero recibe sus consecuencias**: dueño, cliente, auditor, proveedor, administración, soporte. Añadir actores no humanos.

### 2. Composición de escenarios — dimensiones independientes

- **Relación con sistema:** visitante, cliente, usuario, operador, supervisor, dueño, admin, proveedor, regulador, servicio externo.
- **Experiencia del dominio:** primer día, novato, competente, experto, experto con malos hábitos, reemplazo temporal.
- **Familiaridad digital:** primera vez, básica, intermedia, avanzada; no inferir de estudios, edad, país u oficio.
- **Objetivo real:** completar tarea, terminar rápido, corregir error, proteger datos, cobrar, controlar pérdidas, obtener visibilidad o hacer auditoría.
- **Presión/contexto:** prisa, interrupción, cansancio, ansiedad, equipo limitado, lluvia, ruido, luz solar, guantes, conducción estacionada, turnos, conexión lenta, offline.
- **Idioma/comprensión:** idioma principal, segundo idioma, traducción incompleta, instrucción confusa, abreviatura desconocida, formato regional de fecha/número.
- **Dispositivo/interfaz:** móvil pequeño, tablet, desktop, PWA, pantalla compartida, kiosk, lector de pantalla, teclado, voz, cámara dañada, lector QR.
- **Permisos/confianza:** anónimo, rol legítimo, invitado, temporal, admin, ex-empleado, sesión caducada, cuenta compartida, actor malicioso autorizado para test.
- **Datos:** completos, omitidos, contradictorios, duplicados, corruptos, expirados, desactualizados, adversariales sintéticos, imagen equivocada, documento de otro tipo.
- **Momento del ciclo:** alta, primer uso, operación diaria, excepción, cambio de titular/rol, baja, recuperación, cierre, migración.
- **Canal:** web, mobile, API, batch, webhook, importación, máquina, soporte humano, email.
- **Fallos externos:** proveedor fuera, reloj desfasado, API 429/500, OCR incierto, pago rechazado, red degradada, DB degradada, retries concurrentes.
- **Riesgo del negocio:** impacto monetario, seguridad física, exposición personal, pérdida de datos, incumplimiento contractual/regulatorio, reputación, tiempo operacional.

NO generar todos los productos cartesianos. Seleccionar **pares y tríos que revelen riesgo**, añadir rutas de extremo a extremo y compararlas con incidentes conocidos. Si 10 dimensiones tienen 5 valores, 5^10 casos serían absurdos; usar pairwise, clases de equivalencia, límites y ataques justificados.

### 3. Para cada actor aplicable: mínimo por flujo esencial

1. Comportamiento esperado con datos correctos.
2. Error plausible por malentendido o contexto (incluye la acción equivocada concreta).
3. Error adversarial de alto impacto (permiso, dato erróneo, operación repetida, caída de dependencia).
4. Reacción del sistema, trazabilidad, resultado persistido y efecto en actores posteriores.
5. Recuperación autónoma de la tarea, accesibilidad, soporte y salida si no puede continuar.
6. Escenario de cruce con al menos otro actor cuando exista transferencia de responsabilidad.

Para un flujo no visual, sustituir simulación de toques/clics por entradas API, jobs, mensajes, contratos y estados. No atribuir conducta a actores que no aplican.

### 4. Generación sistemática de pruebas

Formato por escenario:

```
ID | actor_id | rol | actor_type(person/system) | tarea real | contexto | suposición validada?
Acción correcta | acción equivocada específica | estado/efecto esperado | defensa | recuperación
Capa de prueba (unit/integration/contract/E2E/security/field) | riesgo | datos de test
Resultado observado | evidencia existente | severidad | estado ejecutado/no ejecutado
```

Ordenar por: seguridad y privacidad, imposibilidad de completar el negocio, corrupción/doble operación, impacto de error frecuente, usuarios sin salida, costos, fricción, cosmética. La severidad es proporcional al daño y recuperabilidad, no al estatus del rol.

### 5. Cobertura de stakeholder (requerida en informes v1.2)

En `audit-results.json`, `stakeholder_coverage` documenta:

- `actors[]`: `id`, `role`, `context`, `type` (`person`|`system`), `source` (`observed`|`inferred`), `critical` (`true`|`false`).
- `required_scenarios[]`: `id`, `actor_id`, `flow` (flujo crítico declarado), `expected_outcome` y `risk`.
- `tests[].stakeholder_scenario_id`: vincula evidencia de ejecución con el escenario.
- `excluded_actor_groups[]`: opcional; explicaciones de por qué grupos sugeridos del atlas no aplican.

El verificador exige al menos un escenario probado por actor **crítico**, al menos un escenario por flujo crítico y un resultado `passed` de prueba crítica con evidencia para cada escenario requerido. Si hay escenarios fallidos críticos: NO_GO. Si faltan o no se ejecutaron: INCOMPLETE. Si los tests ejecutados muestran problema no crítico, el auditor conserva ese resultado y eleva a revisión.

No hacer pasar un escenario de human_factors por uno de stakeholder automáticamente: pueden compartir un test si el test tiene ambos IDs y suficiente evidencia.

### 6. Gate de honestidad

- Simular una persona con IA no es observar una persona real. No afirmar que se hizo una entrevista o prueba de campo.
- Navegación de browser con screenshots no prueba cambios persistidos en base de datos; comprobar backend cuando aplica.
- Problemas de interpretación se resuelven en la interfaz de forma comprensible, no pidiendo al usuario "tener más cuidado".
- `READY_CANDIDATE` es un candidato para decisión humana; ningún skill puede asegurar 0 errores.

### 7. Antipatrones

- Ejecutar 100 casos triviales mientras un pago crítico queda sin probar.
- Clasificar personas por inteligencia a partir de trabajo o educación.
- Probar solo con rol administrador y dar por cubierto cliente, trabajador y proveedor.
- Dar por probada una entrega porque se creó la orden, sin verificar su recepción.
- Inventar que un usuario entiende la instrucción porque la IA la considera clara.
- Informar "no hay problemas" sin evidencia del entorno.
