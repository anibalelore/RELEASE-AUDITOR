# Auditoría de factores humanos — usuarios reales, no usuarios ideales

## Objetivo y límites

El agente adopta **el modelo mental, conocimientos tecnológicos, idioma, entorno físico y objetivos operativos de cada usuario**. No se limita a probar el happy path. Busca activamente confusiones previsibles, equivocaciones y bloqueos causados por el diseño, mediante escenarios ejecutables y observables.

**Principio de respeto:** baja alfabetización digital, bajo dominio del idioma, edad, estrés o formación formal limitada **no implican baja inteligencia** ni incapacidad profesional. Un conductor puede operar un vehículo complejo y no distinguir un selector de documentos. Evita caricaturas y estereotipos. Construye supuestos a partir del contexto del puesto, evidencias de campo y datos de uso; marca las hipótesis no validadas.

**Pruebas sintéticas ≠ pruebas con seres humanos.** Un agente puede simular caminos de error en un navegador, pero no certificar comprensión, carga cognitiva, tiempo real de aprendizaje ni accesibilidad funcional sin estudios con participantes representativos. En los flujos operativos críticos requiere una validación de campo observada antes de una decisión READY_CANDIDATE; documenta muestra, tareas, criterios y resultados agregados sin identificar participantes.

## Mentalidad y método: HUMAN FIRST / WORST PLAUSIBLE CASE

1. **Descubrir perfiles por tarea**: objetivos del puesto, contexto físico, vocabulario cotidiano, motivación, frecuencia de uso, idiomas, dispositivos reales y posible nivel de experiencia digital. No presumas que el usuario conoce la navegación del producto.
2. **Deconstruir cada instrucción**: ¿Qué entendería alguien que nunca ha visto este formulario? ¿Qué acción literal podría realizar? ¿Qué ocurre al leerla deprisa o interpretarla en otro idioma? ¿Dónde buscaría ayuda?
3. **Construir una matriz de combinaciones de fallos**: usuario novel + sol + cámara vertical + red mala + prisa + documento dañado; rotar los factores sin generar combinaciones arbitrarias imposibles. Priorizar gravedad y probabilidad.
4. **Actuar, no imaginar**: ejecutar la acción en UI real con viewport/dispositivo representativo y fixtures sintéticos. Verificar respuesta del sistema, persistencia y progreso. Si no hay navegador/credenciales/fixtures, marcar NOT_RUN y elaborar scripts reproducibles para la siguiente ejecución.
5. **Comprobar recuperación**: detectar error pronto; explicar sin culpar; mostrar un siguiente paso claro; permitir reintentar, guardar progreso, volver atrás; no perder datos anteriores; evitar estados sin salida. Validar tanto error como recuperación exitosa.
6. **Rediseñar el contrato de interacción**: si la pregunta no es estrictamente necesaria, eliminarla, inferirla con confirmación, hacerla opcional o añadir una alternativa "No sé / Más de un color". No agregues pantallas para encubrir un flujo confuso.
7. **Auditar al agente**: verificar que no confunda simulación con conducta humana comprobada y que no invente una observación de campo.

## Catálogo de factores

**Capacidades/experiencia:** primera vez usando smartphone; solo WhatsApp y llamadas; poca lectura; desconocimiento de términos "upload", "PDF", "anverso", "horizontal" o "trailer"; dificultad con permisos de cámara; presionar iconos en vez de texto; confundir guardar con enviar; desconocer scroll y notificaciones del navegador.

**Entorno:** sol directo y reflejos; pantalla rota; guantes/manos mojadas o grasosas; ruido y vibraciones; poca iluminación nocturna; clima frío/lluvia; teclado virtual tapando CTA; vehículo parado en fila; operador junto a máquina; interrupciones por supervisor/radio; batería baja; una mano disponible; 3G intermitente.

**Variación humana:** español, inglés u otro idioma y mezclas; cansancio, presión de tiempo, ansiedad por una entrega tardía; diferencia entre lo que pide el sistema y cómo el usuario nombra los objetos; multisesión, cambios de teléfono, rotación de personal.

**Errores previsibles:** tocar lo primero disponible; usar cámara frontal accidentalmente; foto del suelo/pies/tablero; documento equivocado; foto girada, oscura, cortada, duplicada o de baja resolución; aceptar cualquier opción por seguir; firmar en campo incorrecto; pulsar enviar repetidamente; alejarse sin completar; usar datos de otra persona; omitir campos que no comprende; responder literalmente una pregunta innecesaria y quedar bloqueado.

## Exigencia por cada escenario crítico

- Persona/contexto **plausible y explícito**: no usar atributos protegidos como una supuesta explicación de capacidad.
- Pasos reproducibles en interfaz, no solo "pensaría que se confunde".
- Intento inicial, acción errónea, sistema esperado, sistema observado, estado persistido, recuperación, tiempo/interacciones cuando son medibles, riesgo operativo.
- Clasificar `BUG` confirmado vs `RIESGO` hipotético vs `INSIGHT` de usabilidad vs `NOT_RUN`.
- Capturar evidencia con **datos sintéticos y documentos de prueba**; nunca subir documentos personales de terceros a servicios de IA ni incluir PII en traces.
- Dos capas: **protección del sistema** (bloquear o marcar contenido incorrecto) y **asistencia de tarea** (instrucción comprensible, ejemplo visual, reintento sencillo).
- Preguntar: "¿Un usuario puede completar la tarea sin asistencia externa?" y "¿Qué hará si no entiende la siguiente pantalla?".

## Métricas objetivas orientativas (acordar umbrales con el equipo)

- Tasa de finalización sin ayuda de tareas críticas por persona y escenario.
- Tiempo real de tarea y de recuperación (medianas y percentiles, no inventar objetivos universales).
- Número de errores prevenibles, bloqueos de navegación y toques innecesarios.
- Tasa de falso positivo/falso negativo en validación documental (según fixtures marcados manualmente).
- Porcentaje de sesiones que conservan datos tras interrupción/red caída.
- Proporción de solicitudes de ayuda y abandonos con causa observada.

## Severidad de UX operativa

- **P1 release blocker** cuando un error humano razonablemente frecuente permite registrar documento inválido como verificado, vincula firma al sujeto equivocado, genera autorización equivocada o deja a un usuario operativo sin salida para completar una tarea esencial.
- **P2** cuando la tarea puede recuperarse, pero hay fricción considerable, repetición injustificada, datos ambiguos o falta de guía; elevar a P1 si el impacto operacional observado es alto.
- **P3** para detalles menores sin impacto significativo.

## Evidencia de campo

Para check-in, floor operations o flujos equivalentes, realizar pilotaje supervisado en ambiente de prueba con personas representativas (con consentimiento, no recolectar documentos reales sin autorización): tareas sin coaching inicial, guion neutral, observación de intentos, errores y recuperaciones, resultados agregados. Un agente NO puede declararlo `completed` solo por generar historias o hacer clic en el navegador.
