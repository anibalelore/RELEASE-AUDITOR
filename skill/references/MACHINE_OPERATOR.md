# Playbook — operador de máquina, warehouse y planta

Objetivo del operador: completar su tarea productiva con seguridad y trazabilidad sin memorizar la estructura del software. Puede conocer perfectamente la máquina y, al mismo tiempo, no estar familiarizado con terminología de aplicaciones. Auditar en entorno seguro; **nunca provocar fallos reales de maquinaria**.

**Persona de referencia:** operador de turno, usa tablet compartida cerca de línea ruidosa, tiene guantes, interrupciones, SOP en papel, turnos cambiantes, conectividad irregular y poco tiempo entre lotes.

| ID | Escenario a simular | Recuperación/verificación |
|---|---|---|
| OP-01 | Confunde número de lote, WO, PO y SKU; ingresa uno válido en campo equivocado | Formato y contexto visibles; valida relaciones; nunca modifica producción equivocada silenciosamente |
| OP-02 | Lee instrucciones técnicas de modo literal, omite un scroll oculto o interpreta "Save" como finalizar | Lenguaje simple, acción primaria visible, progreso y confirmación inequívocos |
| OP-03 | Operador lleva guantes, tablet al sol o manos húmedas | Targets accesibles, alto contraste, no depende de gestos finos; alternativa segura |
| OP-04 | Supervisor interrumpe en medio de captura de QC; operador retoma después | Borrador recuperable, sesión protegida, identificación de lote/usuario visible |
| OP-05 | Adjunta foto de piso, etiqueta equivocada o pallet no correspondiente | Validar asociación con lote/estación y tipo de evidencia; pedir repetir o revisión, no dar QA aprobado |
| OP-06 | Escanea dos veces mismo pallet o etiqueta QR ilegible | Idempotencia; detección duplicados; alternativa manual controlada con auditoría |
| OP-07 | Marca un checklist por inercia sin realizar inspección | Evidencia necesaria, controles críticos y firma/confirmación explícita; el software no infiere inspección física de un checkbox |
| OP-08 | Registro queda "guardado" localmente y red cae | Estado de sincronización inequívoco; recuperación sin pérdida ni duplicación |
| OP-09 | Cambio de turno: un operador deja sesión activa para siguiente | Cierre/transferencia segura; permisos, atribución de acciones, no mezcla identidades |
| OP-10 | Señal de alarma o paro de equipo mientras usa tablet | Flujo puede interrumpirse sin bloquear acción de seguridad; nunca competir con SOP de seguridad |
| OP-11 | Un campo pide unidad ambigua (°F/°C, psi/bar, lb/kg) | Unidad explícita, límites razonables y validación; no transforma en aprobación falsa |
| OP-12 | Máquina/WO se marca terminada desde UI pero backend no confirmó | Estados transaccionales y mensajes veraces, monitoreo y reconciliación con sistema fuente |
| OP-13 | Operario selecciona "Reject"/"Accept" por error | Confirmación contextual y reversible cuando procede; bloquear cambios críticos sin autoridad |
| OP-14 | No sabe cómo adjuntar PDF, solo puede tomar foto de hoja | Captura accesible en móvil/tablet; calidad y legibilidad verificadas; revisión humana de datos extraídos |
| OP-15 | Etiqueta física no coincide con datos del sistema | Detener confirmación incorrecta y orientar a excepción/supervisor, sin inventar reconciliación |
| OP-16 | App muestra datos viejos después de actualización offline | Indicar timestamp y estado de sincronía; prevenir acciones basadas en información obsoleta |

## Flujos que bloquean release

Identidad / permisos de turno, trazabilidad de lote y pallet, captura QC que requiere evidencia, errores de unidad, confirmación sin persistencia, estado falso de seguridad. Un bloqueo de ergonomía que imposibilita una tarea esencial puede ser P1, según impacto y frecuencia verificados.

## Validación de campo

Piloto en sandbox con operador(es) y supervisores representativos, usando tablet y condiciones seguras equivalentes; observar tareas sin coaching, equivocaciones, interrupciones y recuperación. Toda evaluación de seguridad operacional exige supervisión de responsables de planta; no ensayar incidentes físicos.
