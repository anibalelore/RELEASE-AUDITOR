# UNIVERSAL AUDIT — descubrir actores, estados, fallos y límites de cualquier sistema

> **No es una lista de perfiles fijos.** El sistema bajo prueba determina las funciones, los actores, el contexto y las variantes. Los ejemplos de conductores y operadores son solamente playbooks especializados cuando corresponda.

## 1. Descubrir qué es el producto antes de imaginar escenarios

Inspeccionar código, configuración, permisos, rutas, interfaces, APIs, esquemas, pruebas existentes, despliegues y documentación. Delimitar **entorno autorizado** y reglas de negocio corroboradas. Crear un mapa de:

- **Actores:** usuarios finales y ocasionales, administradores, supervisores, personal de soporte, terceros, sistemas integrados, tareas programadas, bots, procesos asíncronos y actores adversariales *solo en entorno autorizado*. Una misma persona puede cambiar de rol en una sesión.
- **Objetivos reales:** qué trabajo intenta completar, qué resultado significa éxito desde su perspectiva y qué datos/efectos deben persistir. Incluir casos donde el usuario quiere terminar rápido, abandonar, corregir, delegar o revertir.
- **Journey/estados:** antes, durante y después de cada acción, estados intermedios, transiciones permitidas, reingresos, errores, cancelación y recuperación; incluir datos, logs, notificaciones, pagos y servicios downstream.
- **Condiciones:** frecuencia de uso, conocimientos del dominio vs experiencia digital, edad **solo si afecta una necesidad de diseño documentada**, idioma, capacidades de acceso, dispositivo, ancho de banda, condiciones ambientales, presión de tiempo, confianza, colaboración y carga cognitiva. No asumir que profesión o estudios miden inteligencia.
- **Criticidad:** consecuencias de acciones equivocadas (seguridad física, salud, datos, dinero, privacidad, cumplimiento, pérdida operativa, reputación, accesibilidad y tiempo humano).

Si falta información, formular hipótesis etiquetadas `SUPUESTO`; no presentarlas como hallazgos observados ni inventar entrevistas con usuarios.

## 2. Generador de escenarios por flujo: mínimo obligatorio

Para **cada flujo crítico**, define escenarios ejecutables con precondición, actor/contexto, acción, resultado esperado, respuesta observada, datos persistidos, recuperación y evidencia. Cubrir como mínimo estas cuatro dimensiones:

1. `happy_path`: uso esperado; completar un objetivo verificando efectos reales.
2. `plausible_misuse`: confusión razonable, acto equivocado, uso fuera del orden ideal, intento literal, error de API cliente o automatización; demostrar contención, ayuda y corrección.
3. `boundary`: entrada límite, regla límite, estado raro o ciclo de vida extremo (vencido, vacío, duplicado, valor máximo, redondeo, DST, etc.).
4. `recovery`: interrupción o fallo a mitad de tarea y reanudación/reintento/cancelación sin daño, pérdida ni duplicación.

No basta con escribir escenarios: cada uno se vincula a test real con `scenario_id`, resultado y evidencia. Cuando no se puede ejecutar, `NOT_RUN` o `BLOCKED` y gate **INCOMPLETE**.

## 3. Taxonomía universal: dimensiones que hay que evaluar explícitamente

Para **cada categoría** anota si es aplicable, por qué, a qué flujos afecta y cuál es el escenario ejecutado más peligroso/probable. Una categoría puede no aplicar; explica **por qué**. Ninguna puede desaparecer silenciosamente del inventario. Incluye las cuatro dimensiones mínimas anteriores y las siguientes:

- `business_rule`: reglas implícitas, unidades, excepciones, decisiones innecesarias, estados prohibidos, operaciones parciales.
- `human_factors`: comprensión de instrucciones, errores inocentes, tareas reales, ayudas, abandono y recuperación; aplica cuando hay interacción humana.
- `security`: abuso autorizado, escalada de privilegios, acceso entre tenants, credenciales, inyección, sesión y manipulación de parámetros.
- `privacy`: PII, consentimiento, retención, exposición involuntaria, descargas, permisos y borrado conforme a políticas.
- `authorization`: matriz de permisos por rol, recurso, organización, estatus y transición.
- `data_integrity`: escrituras parciales, fuentes de verdad, operaciones compensatorias, reconciliación, duplicados y consistencia.
- `integration`: terceros, versiones, contratos, webhooks, 429/500/timeouts, mocks vs servicios realmente conectados.
- `concurrency`: dos actores, dos pestañas, colas, carrera, bloqueo, idempotencia y orden variable.
- `time`: husos horarios, horario de verano, caducidad, fechas futuras, turnos, cierres y fronteras temporales.
- `network`: latencia, sin conexión, reconexión, reintentos, subida interrumpida y conexiones degradadas.
- `environment`: móviles antiguos, guantes, ruido, iluminación, hardware dañado, dispositivos especiales o condiciones de trabajo.
- `accessibility`: teclado, lectores de pantalla, foco, contraste, voz, texto alternativo, movilidad y sensibilidad visual cuando aplica.
- `localization`: idioma, escritura, formatos de fecha/número, traducción de conceptos, zonas, sistema de medida y textos largos.
- `performance`: carga realista autorizada, picos, formularios lentos, datasets grandes y degradación controlada.
- `compatibility`: navegadores, sistema operativo, resolución, app versions, migraciones cliente/servidor y hardware.
- `observability`: trazabilidad, errores detectables, alertas útiles, correlación de eventos, soporte y diagnósticos sin datos sensibles.
- `operations`: cambios de turno, procedimientos manuales, incidentes, soporte, reversión y excepciones de negocio.
- `deployment`: build de producción, secretos ausentes, flags, migraciones, rollback, backups y equivalencia del entorno.
- `ai_behavior`: si hay IA, alucinación, prompts maliciosos, herramientas, resultados no deterministas, OCR fallido, explicación, fallback, coste y privacidad.
- `fraud_abuse`: manipulación de sistemas de incentivos, suplantación, solicitudes automatizadas, abuso de promociones y límites.

Estas son **dimensiones de riesgo**, no promesas de que todo pueda ejecutarse en cualquier sistema. Los casos de mayor impacto deben probarse en ambiente seguro; cargas agresivas, pentest activo, transacciones reales o efectos sobre terceros requieren permiso explícito.

## 4. Mentalidad adversarial sin caricaturas

No preguntes solo «¿el usuario sabe hacerlo?». Pregunta:
- ¿Qué pasa cuando el usuario quiere lograr otra cosa, o el texto se interpreta literalmente?
- ¿Cómo falla el flujo cuando alguien se salta pasos, cambia de idea, cierra la app, comparte equipo o recibe ayuda?
- ¿Qué datos parecen correctos en la UI pero están mal en la base, en el email, en la factura o en el servicio externo?
- ¿Qué ocurre cuando un servicio confirma tarde, confirma dos veces, falla después del guardado o devuelve algo válido pero semánticamente incorrecto?
- ¿Puede el sistema bloquear operaciones legítimas por una pregunta irrelevante o aceptar resultados incorrectos por no comprobar su significado?
- ¿Puede un operador experto en su trabajo pero nuevo en esta interfaz completar la tarea sin coaching?
- ¿Puede un experto malintencionado burlar el control sin romper la UI, solo cambiando secuencia, IDs, fechas o permisos? (solo pruebas autorizadas)

**Regla de oro:** detectar → contener → explicar → recuperar → verificar resultado final y efectos laterales. Un error prevenido sin vía de recuperación puede seguir siendo un defecto crítico.

## 5. Multiplicar escenarios de forma inteligente

No intentar la combinación cartesiana infinita. Usa cobertura **basada en riesgos**, particiones de equivalencia, límites, transiciones de estado, pares (`pairwise`) y combinaciones de alto impacto. A cada escenario añade: severidad potencial, probabilidad fundamentada, reversibilidad, detectabilidad, trazabilidad y automatizabilidad. Si hay combinaciones no cubiertas, registrar riesgo residual explícito.

Reejecutar siempre al modificar un componente compartido, un permiso, una integración o una regla transversal. Comparar comportamiento real de UI/API/DB/cola/webhook y el flujo de recuperación, no limitarse a contar tests verdes.

## 6. Ejemplos de uso, NO perfiles preseleccionados

- **E-commerce:** compra, carrito duplicado, cupón incompatible, reembolso parcial, retraso de pasarela, contracargo, impuestos y devolución.
- **HR:** formularios, documentación laboral, permisos, cambios de datos, separación de funciones, cargas equivocadas, firma y trazabilidad.
- **Clínica:** cita doble, usuario con visión limitada, instrucciones mal interpretadas, resultados y permisos, integraciones clínicas; sin datos reales.
- **Finanzas:** redondeo, moneda, fechas, permisos, doble cobro, conciliación, reversos y cortes de servicio.
- **Agente IA:** tool calling, instrucciones adversariales, contenido no confiable, alucinación, costes, límites, permisos y acciones irreversibles.
- **Industrial/IoT:** sensor desconectado, descalibración, alarmas, manos ocupadas, cambio de turno, hardware, modo offline y seguridad física.
- **App logística:** dirección ambigua, GPS inexacto, documentos incorrectos, tiempos, conectividad y asignaciones duplicadas.
- **API sin UI:** cliente mal implementado, requests mal formadas, retries, idempotencia, concurrencia, permisos, errores parciales y backward compatibility.
- **Educación/atención al cliente:** instrucciones literales, múltiples idiomas, accesibilidad, niveles de experiencia, abandono, escalamiento y ayuda.

En todos los casos, descubrir los actores y reglas reales del repositorio. No asumir módulos inexistentes por leer esta lista.

## 7. Aprobación rigurosa

- `READY_CANDIDATE` **solo** cuando existen pruebas reales con evidencia para escenarios críticos declarados, análisis de dimensiones aplicables, integraciones, permisos y recuperación; pruebas de campo observadas cuando el contexto lo exige.
- `INCOMPLETE` si hay dimensiones sin evaluar, escenarios críticos no ejecutados, terceros no comprobados, ausencia de pruebas con usuarios requeridas o falta de evidencia.
- `NO_GO` si se reproduce un fallo bloqueante de seguridad, seguridad física, dinero, datos, autorización o funcionamiento esencial.
- Aun con todas las pruebas aprobadas: no afirmar «cero errores»; documentar límites del entorno, confianza y riesgo residual, sujeto a decisión humana.
