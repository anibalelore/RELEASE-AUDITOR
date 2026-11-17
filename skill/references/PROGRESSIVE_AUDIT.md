# Auditoría progresiva de perfiles — 1.4

## Propósito

Después de DISCOVER y SELECT, **cada perfil humano seleccionado recorre una escalera de cinco niveles** en el mismo flujo esencial del producto. No son cinco estereotipos ni cinco usuarios cuyo conocimiento del oficio se deduce por su ocupación: son cinco **modelos de interacción digital** configurables, con objetivos reales, limitaciones observadas o hipótesis explícitas.

El auditor hace primero **uso errático extremo** para encontrar puntos de ruptura, y termina con uso experto, pero **en todos los niveles** prueba camino erróneo y camino correcto. Simular errores deliberadamente durante QA no implica que todas las personas con poca familiaridad digital actúen así.

| Nivel | ID | Cómo actúa | ¿Qué debe encontrar? |
|---|---|---|---|
| 0 | `erratico` | Interpreta literalmente, toca elementos equivocados, envía contenido incorrecto, pierde contexto, abandona o repite; siempre en sandbox | Rechazos seguros, lenguaje claro, guía visible, prevención de datos basura y recuperación sin castigo |
| 1 | `principiante` | Entiende la tarea, no la interfaz; necesita instrucciones, confunde términos o formato | Orientación contextual, defaults seguros, pistas, explicación, navegación atrás |
| 2 | `intermedio` | Conoce tareas comunes; falla ante excepciones, flujos largos y cambios de contexto | Estados persistidos, validación coherente, errores accionables, continuidad |
| 3 | `competente` | Opera con normalidad y velocidad, multitarea y ocasionalmente se equivoca | Eficiencia y accesibilidad sin perder controles ni integridad |
| 4 | `experto` | Hace atajos, lotes, cambios rápidos, múltiples ventanas, casos límite | Lógica compleja, idempotencia, autorizaciones, concurrencia y regresiones |

**La progresión no es «entrenar a la IA hasta que aprenda a usarlo»**: se prueban cinco comportamientos independientes sobre la **misma versión del sistema** para comparar robustez. Si se modifica la aplicación, se ejecuta otra vez la matriz sobre la nueva versión. Puede documentarse el aprendizaje de un usuario real como una hipótesis distinta, pero no suponerlo a partir de la simulación.

## Algoritmo operativo obligatorio

1. **DISCOVER**: inspeccionar módulos, rutas, reglas, permisos, riesgos, dependencias, estado persistido e instrucciones UI reales.
2. **SELECT**: el propietario elige rol(es), módulo(s), objetivo(s) y nivel(es) si desea personalizar. Por defecto: cinco niveles para cada rol humano elegido y cada flujo crítico relevante.
3. **PLAN**: por cada `actor × flujo × nivel`, preparar dos escenarios identificados: `error_y_recuperacion` y `camino_correcto`. No inventar riesgos irrelevantes; derivar acciones de UI real y evidencia del negocio. La acción errónea debe ser **concreta y plausible**.
4. **BASELINE sin permiso de corrección**: ejecutar niveles 0→4 sobre una misma build, casos de error antes que correctos, aislando cuentas/datos de prueba. **Con permiso `audit-fix`**: ejecutar nivel 0, corregir si hay defectos confirmados y autorizados, revalidar ese nivel, avanzar al nivel 1, y así sucesivamente. Los cambios sucesivos generan builds distintas; **al final repetir los diez casos por flujo en una única build final** para evaluar el release. No convertir un fallo deliberado de usuario en fallo del producto si la interfaz previene el daño y logra recuperación.
5. **ORÁCULO DE PRUEBA**: validar tanto UI como estado persistido, efectos secundarios y trazabilidad. Una prueba `passed` de error significa **rechazo o contención segura + recuperación verificada**, no que la aplicación aceptó la entrada errónea.
6. **INFORME POR NIVEL**: pasos concretos, resultado esperado/observado, evidencia, severidad, causa probable, mejora propuesta y cómo revalidarla. Diferenciar `passed`, `failed`, `blocked`, `not_run` y las hipótesis no verificadas.
7. **IMPROVE** (solo con permiso `audit-fix`): arreglar hallazgos confirmados, añadir regresión, repetir el escenario fallido **y los dos casos en los cinco niveles** del flujo afectado. Comparar build anterior vs nueva. Máximo dos ciclos de autorreparación por hallazgo.
8. **RELEASE**: no dar veredicto positivo si algún escenario requerido no se ejecutó con evidencia o sigue fallando; un perfil aislado nunca certifica todos los actores. Pruebas de campo con personas reales siguen siendo necesarias cuando el riesgo lo exige.

## Personalización

El usuario puede definir perfiles propios (p. ej. «cliente de primera compra, habla español, móvil básico, con prisa») y además modificar el comportamiento de **cada nivel** sin cambiar el rol. Configurar sobre el proyecto, no desde atributos demográficos presumidos. Puedes ajustar comportamientos individuales de cada nivel editando `progression.levels[].error_patterns`, `.correct_strategy` y `.context` en el JSON del perfil. Cada actor conserva los cinco niveles obligatorios, pero sus condiciones y pruebas son personalizables. Documenta las diferencias y no etiquetes cinco niveles con un mismo comportamiento.

Ejemplos de errores que dependen del contexto:

- **Documentos**: foto del objeto incorrecto, documento parcialmente fuera del encuadre, OCR erróneo, carga duplicada. La app debe guiar, no solo rechazar.
- **Pagos**: dirección de facturación ambigua, doble toque, abandono durante red lenta, reembolso y cambios entre pestañas. Usar sandbox.
- **Panel del dueño**: interpretar datos desactualizados como actuales, comparar métricas incompatibles, aprobar el lote equivocado, filtrar sin darse cuenta.
- **API/servicio** (sin persona humana): reemplazar la escalera por cinco grados de entrada/servicio degradado (`normal`, `incompleto`, `malformado`, `intermitente`, `adversarial autorizado`). No simular clics humanos en servicios no visuales.

## Gate con evidencia

`audit-results.json` agrega `progressive_audit` cuando es aplicable:

```json
{
  "progressive_audit": {
    "applicable": true,
    "tracks": [
      {"actor_id":"driver","flow":"checkin","levels":["erratico","principiante","intermedio","competente","experto"]}
    ],
    "required_scenarios": [
      {"id":"driver-checkin-erratico-error_y_recuperacion", "actor_id":"driver", "flow":"checkin", "level":"erratico", "kind":"error_y_recuperacion", "expected_recovery":"El sistema rechaza documento incorrecto y permite repetir sin perder avance"},
      {"id":"driver-checkin-erratico-camino_correcto", "actor_id":"driver", "flow":"checkin", "level":"erratico", "kind":"camino_correcto", "expected_recovery":"Termina correctamente con guía visible"}
    ]
  }
}
```

Ejemplo ilustrativo abreviado: **para aprobar un track real se requieren los 10 escenarios** (dos por nivel), cada uno asociado a un `tests[]` con `progressive_scenario_id`, `status`, `critical`, `action`, `expected`, `observed` y `evidence` local verificable. No rellenar observaciones inventadas para hacer pasar el gate. En modo release, la ausencia del bloque para interfaces humanas significa `INCOMPLETE`; si no aplica, `applicable: false` y `not_applicable_reason` obligatorio.

El generador `scripts/progression.py` admite `--profile ruta/al/perfil.json` para utilizar esos comportamientos personalizados, además de `--actor`, `--role` y `--flow`. Permite crear una plantilla de los 10 escenarios por flujo. Solo construye el **plan**: nunca ejecuta la aplicación ni adjudica PASS.
