# Playbook — conductor/driver, check-in y carga documental

Objetivo real del conductor: entrar a la instalación, identificar camión/remolque/carga, presentar documentos válidos, obtener instrucciones de andén y seguir su ruta. No está ahí para aprender tecnología. El sistema debe hablar su idioma, reconocer su situación, prevenir datos falsos y permitir ayuda excepcional sin trabar la fila.

**Persona sintética de referencia:** conductor profesional competente, primera visita a esta planta, usa móvil mayormente para llamadas/mapas/mensajes, tiene prisa moderada, está al sol, con ruido, pantalla pequeña y red irregular. Estas hipótesis se personalizan por instalación/idioma y requieren validación con usuarios reales.

| ID | Situación adversarial a ejecutar con fixtures no sensibles | Resultado aceptable / recuperación |
|---|---|---|
| DR-01 | Al pedir "subir licencia", abre cámara y fotografía zapatos/suelo | Detecta que no es una licencia; NO la marca verificada; muestra ejemplo visual y opción "Tomar otra foto" |
| DR-02 | Fotografía licencia en vertical cuando la interfaz dice "horizontal"; contenido queda cortado | Comprueba cuatro bordes/campos esenciales o confianza suficiente; rechaza **solo si el contenido no es utilizable** y guía cómo encuadrar; no penaliza orientación por sí misma |
| DR-03 | Toma la licencia correcta pero borrosa, deslumbrada, oscura o con reflejos | No inventa ni completa datos faltantes; solicita foto nueva con instrucción concreta, preserva formulario |
| DR-04 | Sube seguro, tarjeta del camión, ticket de lavado o pasaporte en campo de licencia | Contrasta tipo de documento con el esperado; permite cambiar tipo si legítimo; evita aprobación silenciosa |
| DR-05 | Sube licencia de otra persona o lado reverso sin frente requerido | No lo considera verificado automáticamente; fuerza conciliación de identidad/revisión autorizada, sin mostrar datos sensibles innecesarios |
| DR-06 | Reutiliza foto vieja o duplica el mismo archivo en diferentes campos | Detecta duplicación inapropiada cuando aplica; informa qué falta sin eliminar información válida |
| DR-07 | Firma donde indica "initials", en caja equivocada o sin comprender a qué consiente | Firma se muestra asociada a documento/declarante correcto; confirmación clara; no se aplican firmas a documentos incorrectos; reintento permitido |
| DR-08 | Dibuja línea/punto accidentalmente y pulsa continuar | Regla de suficiencia sin falso rechazo indiscriminado; previsualización, posibilidad de limpiar, confirmación y trazabilidad |
| DR-09 | Pregunta "Color del camión" y responde "dos colores" o no sabe cómo nombrarlo | Campo opcional o "Más de un color / No sé" salvo justificación operacional documentada; nunca deja la fila bloqueada por detalle irrelevante |
| DR-10 | Confunde color tractor con color remolque, truck number con trailer number | Labels con ejemplos y ayuda visual; valida identificador adecuado, explica términos locales, permite corregir |
| DR-11 | Toca "Continuar" cinco veces por lentitud; cambia a otra app | Un solo registro; idempotencia; estado guardado y feedback claro al retomar |
| DR-12 | Pierde red al cargar la foto o justo antes de enviar | No declara éxito hasta confirmar guardado; recupera reintento seguro, sin duplicar check-in |
| DR-13 | Abre QR/link desde un teléfono con idioma distinto y niega permisos de cámara | Instrucción traducida y alternativa de carga/ayuda; no crea un callejón sin salida |
| DR-14 | Abandona a mitad del registro porque lo llaman desde andén | Reanuda sin perder datos dentro de política definida; sesión y datos personales protegidos |
| DR-15 | Usa pantalla bajo sol brillante, con guantes o teclado superpuesto | CTA legible y alcanzable, objetivos táctiles cómodos; tareas prioritarias completables en móvil real |
| DR-16 | Selecciona cliente/equipo/andén equivocado | Mensajes muestran consecuencia; validación backend previene asignación errónea, ofrece corrección antes de confirmar |
| DR-17 | Documento expirado o wash ticket fuera de vigencia | No permite verificar/autorizar; mensaje que explica vigencia, ruta a recepción/revisión manual autorizada |
| DR-18 | Un conductor ayuda a otro y quedan mezclados números/fotos | La sesión y el registro mantienen identidad clara; evita asociar documentos o firmas al conductor equivocado |
| DR-19 | Pulsa atrás, refresh, cierra pestaña o vuelve desde notificación | Sin duplicados, con estado coherente y mensajes de recuperación; no invalida autenticación silenciosamente |
| DR-20 | Intenta saltarse fotos/documentos con archivo vacío, irrelevante o extensión disfrazada | Validación de tipo, contenido, tamaño, integridad y revisión humana cuando OCR/IA no está seguro |

## Aceptación operativa mínima antes de candidato a release

1. **Prueba de documentación:** DR-01/02/03/04 y un caso correcto; comparar esperado vs resultado observado en UI real, backend y estado final. Si el sistema acepta pies como licencia verificada: P1, NO_GO.
2. **Pregunta bloqueante:** DR-09; distinguir requisito legal/operacional esencial de decoración. Una respuesta plausible no puede bloquear check-in durante una hora.
3. **Firma:** DR-07/08 + caso exitoso; comprobar asociación firma-documento-persona en DB/audit trail. Si asocia mal: P1.
4. **Red y duplicados:** DR-11/12 + recuperación; no generar dobles registros ni prometer éxito falso.
5. **Idioma, móvil y entorno:** DR-13/15 + al menos el idioma y dispositivo representativos reales.
6. **Validación humana de campo:** personal de conducción/recepción representativo completa tareas de prueba sin instrucciones externas; registrar resultados agregados, bloqueos y decisiones de rediseño. Una simulación automatizada jamás sustituye esta prueba.

## Diseño recomendado, no asumir implementación presente

- Preguntar solo datos esenciales; recuperar automáticamente los demás cuando sea seguro y solicitar confirmación.
- Cámara integrada con marco dinámico, ejemplo de lo que debe verse y texto conciso, no instrucciones abstractas como "horizontal" sin apoyo visual.
- Clasificación y calidad documental antes de dar "Listo"; si el OCR tiene baja confianza, estado pendiente de revisión, nunca validado ficticiamente.
- Un paso principal por pantalla, botones claros, lenguaje cotidiano, progreso visible, volver/corregir sin borrar todo, alternativa de ayuda a personal autorizado.
- Guardar borradores con límites de privacidad; validaciones server-side, auditoría y estado explícito de pendiente/aprobado/rechazado.
- Traducción auténtica y revisada, no traducir literalmente términos técnicos ni discriminar al usuario por idioma.
