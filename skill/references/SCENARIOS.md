# Catálogo de escenarios adversariales (seleccionar por riesgo, no aplicar ciegamente)

## Matriz universal

| Área | Camino feliz | Camino alterno / ataque controlado | Evidencia exigida |
|---|---|---|---|
| Login | credenciales válidas y retorno a ruta | credenciales incorrectas; sesión expirada; logout en otra pestaña | respuesta UI, cookies sanitizadas, sesión realmente inválida |
| Roles y tenants | usuario correcto accede a sus datos | rol sin permiso; URL directa; ID de otra empresa; consulta API sin UI | 403 / ausencia de datos / política backend |
| Formularios | envío y confirmación | vacío, campo largo, caracteres Unicode, doble clic, refresh, reenvío | registros DB, no duplicados, errores visibles |
| DB/CRUD | crear, buscar, editar y recuperar | conexión caída; validación, transacciones, FK, migración, concurrencia | estado DB antes/después (sin PII) |
| APIs | request válido con schema | invalid payload, 401, 403, 404, 409, 429, 5xx, timeout | response, schema y side effects |
| Integraciones | callback real de sandbox | tercero lento o caído, webhooks duplicados, out-of-order, firma inválida | idempotencia, cola, estado final |
| Pagos | checkout de prueba | cobro rechazado, cancelación, retry, duplicado, webhook tardío | estados sandbox, conciliación sin cobro real |
| Upload/OCR/IA | archivo correcto y campos extraídos | archivo equivocado, corrupto, extensiones falsificadas, prompt injection en documento, baja calidad | validación humana, trazabilidad, no inventar datos |
| Notificaciones | envío a buzón de test | email inexistente, proveedor caído, plantilla vacía, repetición | estado real y retry, no mails a clientes reales |
| Mobile/responsive | navega y guarda | pequeño viewport, teclado abierto, red lenta, cambio orientación | screenshot/trace, usabilidad |
| Rendimiento | carga típica | datos voluminosos, paginado, consultas N+1, picos controlados | presupuesto definido, latencias medidas |
| Timezones | creación/lectura uniforme | DST, medianoche, zonas cruzadas, formato de fecha | timestamps y reglas de negocio |
| Seguridad | acceso autorizado | inyección, XSS, CSRF, IDOR, exposición de logs, RLS mal configurada | checks seguros y pruebas autorizadas |
| Operaciones | build y deployment staging | env ausente, migración fallida, rollback, colas estancadas | logs, health probes y plan rollback |
| A11y | navegación por mouse | teclado-only, foco, etiquetas, mensajes screen-reader | resultado comprobado con herramienta/inspección |
| Observabilidad | evento normal | error de tercero, caída de job, alerta no dispara | log/trace/alert y correlación real |

## Escenarios transversales obligatorios según funcionalidades presentes

1. Dejar el formulario a medias, volver atrás y recargar: ¿se pierde/duplica el estado?
2. Crear desde un módulo, consultar desde otro, editar y verificar sincronización real.
3. Dos usuarios actualizando simultáneamente la misma entidad: política de conflicto definida.
4. Doble clic en submit + reintento por red: exactamente una operación de negocio cuando corresponde.
5. Pérdida de conexión a mitad de grabación: ¿UI miente diciendo «guardado»?
6. Reutilización de token vencido; acceso a recurso de empresa distinta; permiso revocado a mitad de sesión.
7. Cambiar nombre, zona horaria o idioma; probar Unicode, espacios, null, fechas límite.
8. Error del servicio externo tras éxito parcial del servicio principal: compensación/recovery.
9. Limites de cuota API, latencia, rate limits, bulk import y paginación.
10. Backups y restauración demostrados en entorno seguro cuando forman parte de la política operativa.

## Por dominio (cuando aplique)

- **RR.HH. / fiscal / datos sensibles:** PII cifrada y autorización por campo, retención, auditoría de acceso, documentos equivocados, OCR ambiguo que debe requerir verificación humana, exportaciones, firmas; compliance específico sujeto a revisión legal.
- **Logística / planta / warehouse:** estados ordenados, IDs duplicados, QR corrupto, check-in sin conectividad, documentos vencidos, cargas a muelle equivocado, turnos, procesos concurrentes, bitácora.
- **GPS / transporte:** latencia y pérdida GPS, stale traffic data, throttling API, rutas entre estados, timezone, notificaciones mientras se conduce; no realizar acciones peligrosas en conducción real.
- **SaaS multi-tenant:** aislamiento de empresa, roles, planes y límites, facturación, trial expired, downgrade, API keys, tenants creados/eliminados.
- **IA / agentes:** prompt injection, respuestas inconsistentes, salida estructurada inválida, alucinaciones, fugas entre tenants, falta de human-in-the-loop, pérdida de contexto, tool failure, costo y latencia.

## Rol humano / error operativo extremo (obligatorio para interfaces de campo)

Los casos anteriores no sustituyen pruebas desde las necesidades, el lenguaje y la realidad del operador. Usar `HUMAN_FACTORS.md`, `DRIVER_CHECKIN.md` y `MACHINE_OPERATOR.md`. Incluir fotos equivocadas y orientaciones imprevistas, firmas incorrectas, preguntas irrelevantes bloqueantes, desconexión, interrupciones, guantes, brillo solar, dispositivos económicos, localización, idioma y ayuda de compañeros. Evaluar si puede recuperarse y terminar por sí solo. Para un release crítico, documentar también pruebas observadas con personas representativas; sin ellas no declarar candidato listo.
