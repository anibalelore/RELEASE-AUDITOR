# Ejemplo de misión de auditoría humana — check-in de drivers

**NO SE HAN EJECUTADO ESTAS PRUEBAS.** Esta es una matriz de aceptación para adaptar a la app real. Nunca uses este documento como evidencia de un sistema ya auditado.

## Contexto y personaje

Persona sintética: conductor profesional que visita la planta por primera vez. Está apurado por cumplir ventana de carga, usa teléfono económico con brillo alto, entiende las instrucciones de patio pero no el vocabulario de aplicaciones. La prueba debe verificar si puede llegar desde el QR a una confirmación confiable por sí mismo. No presupongas su edad ni inteligencia.

Entorno: staging + cuenta synthetic-driver-A, fixture de licencia de fantasía visiblemente marcado `TEST ONLY`, fotos sintéticas de suelo/zapatos, seguro sintético, red simulada lenta, viewport real, idioma seleccionado. Nunca subir licencia real ni usar identidad de persona real.

## Secuencia realista / fallos compuestos

### Misión 1 — Foto incorrecta que parece haber sido aceptada

- Entrar desde QR y seleccionar "licencia".
- Adjuntar imagen del suelo/zapatos.
- **Esperado:** NO aparece estado `verified`; sistema indica "Esta foto no parece una licencia. Coloque la licencia dentro del marco y vuelva a tomarla", con opción clara de retomar y sin eliminar otros datos correctos.
- **Verificar:** UI, respuesta API, registro DB, estado OCR, bitácora, tiempo de recuperación. Si queda `verified`, clasificar P1.

### Misión 2 — Orientación inesperada + recorte

- Hacer foto de licencia de prueba en vertical: variante A legible y completa, variante B con borde/nombre cortado.
- **Esperado A:** aceptar si calidad/contenido son suficientes; la orientación no debe ser una regla artificial.
- **Esperado B:** no completar datos inexistentes, pedir recaptura con guía visual basada en lo faltante.
- Verificar que OCR no introdujo letras o fechas fabricadas y que el driver puede rehacer solo esa foto.

### Misión 3 — Pregunta ambigua bloquea a una persona

- Llegar a "¿De qué color es el camión?" y responder "blanco y azul" o "tengo dos colores".
- **Esperado:** si el color no es requisito operativo/legal, no pedir precisión ni frenar el check-in; si sí es imprescindible, admitir multicolor u ofrecer selección múltiple/"Otro" y asistencia.
- Medir si se bloquea por falta de opción y por cuánto tiempo en una prueba real; no inventar duración a partir de simulación.

### Misión 4 — Firma en lugar incorrecto

- Dibujar una firma en un campo ajeno o comenzar en cuadro incorrecto, retroceder y cambiar documento.
- **Esperado:** la firma está inequívocamente ligada a conductor/documento/versión; ningún consentimiento se presume, y se requiere confirmación final contextual. No hay asociación cruzada tras retroceder.
- Verificar relación real en backend y auditoría. Firma en sujeto o documento incorrecto = P1.

### Misión 5 — Guantes, sol, red y reintento

- Activar throttling/loss en entorno de pruebas; enviar formulario, tocar continuar dos veces, salir por llamada, volver.
- **Esperado:** sin duplicados, estado guardado solo cuando el servidor confirma, mensajes simples, reanudación segura sin pérdida. Probar también en hardware móvil representativo con supervisión.

## Ampliación de riesgo

Después de cada misión, combinar un segundo factor sin cambiar la regla de negocio: otro idioma, dispositivo pequeño, teclado tapando botón, permisos de cámara denegados, otro driver que ayuda, documento vencido, cambiar de aplicación. Usar equivalence classes y pairwise en vez de hacer todas las permutaciones imposibles. Cada variante debe tener acción, expected, observed y evidence. No escribir un PASS ficticio.

## Piloto supervisado de campo (independiente del agente)

- Preparar tareas neutrales con datos sintéticos, teléfonos reales y ambiente seguro.
- Observar a usuarios del puesto sin guiarlos inicialmente; obtener consentimiento y no capturar identidad/documentación real en la evidencia.
- Medir finalización sin ayuda, obstáculos, errores y recuperación; anotar citas anónimas si están autorizadas.
- Registrar cambios de diseño, volver a probar y adjuntar un acta agregada antes de firmar un release.
- **Sin piloto observado, una auditoría simulada no equivale a validación humana.**

## Criterio de salida

`READY_CANDIDATE` requiere que los escenarios críticos estén declarados y probados con evidencia real, que no haya bugs P0/P1 ni pruebas críticas fallidas, que el field pilot esté documentado y que la suite técnica, paridad y mecanismos de rollback aplicables estén comprobados. Nunca significa software libre de bugs.
