# Evaluación final congelada — Rad-SpRL

Fecha de apertura y evaluación de prueba: 2026-10-15. El [protocolo](../experiments/final_protocol_v1.md) se escribió antes de generar `test.jsonl`; sus sumas SHA-256 de código, XML, partición y pesos se comprobaron sin cambios después de evaluar. No se reajustaron modelos con prueba. La prueba contiene 300 informes, 281 indicadores espaciales anotados y 591 menciones principales (`Trajector` + `Landmark`).

## Tarea y métrica

La entrada de cada método incluye el **indicador espacial verdadero**. Se predicen cero o más fragmentos de hallazgo (`Trajector`) y ubicación (`Landmark`) asociados al indicador. Una mención sólo cuenta como acierto si coincide exactamente en rol, indicador y segmentos de tokens. No se evalúa detectar indicadores desde texto libre ni se juzga si un informe es clínicamente correcto.

## Resultados de prueba

| Método | Precisión micro | Exhaustividad micro | F1 micro | TP / FP / FN |
| --- | ---: | ---: | ---: | ---: |
| Léxico + proximidad | 0.699 | 0.640 | 0.668 | 378 / 163 / 213 |
| CRF BIO por rol | **0.885** | 0.882 | **0.883** | 521 / 68 / 70 |
| Híbrido fijo | 0.859 | **0.883** | 0.871 | 522 / 86 / 69 |

| Método | Trajector F1 | Landmark F1 |
| --- | ---: | ---: |
| Léxico + proximidad | 0.640 | 0.697 |
| CRF BIO por rol | **0.888** | **0.878** |
| Híbrido fijo | 0.868 | 0.873 |

Frente a reglas, el CRF mejora F1 micro **+0.215**. El intervalo percentil de un bootstrap apareado de 2 000 remuestreos por **informe** (semilla 42) es **[+0.175, +0.257]**. La salida JSON está en `crf_vs_rules_test.json`.

Frente al CRF, el híbrido cambia F1 **−0.0123**, con intervalo descriptivo **[−0.0191, −0.0065]**; véase `hybrid_vs_crf_test.json`. El híbrido añadió 19 menciones cuando el CRF estaba vacío para un rol: sólo una fue acierto exacto adicional y 18 fueron falsos positivos. La pequeña ganancia de exhaustividad no compensó la pérdida de precisión.

## Interpretación de hipótesis

- La evidencia respalda que el modelo secuencial supera a esta línea base léxica bajo el protocolo de extracción condicionado al indicador. El CRF recupera varias menciones y límites no presentes literalmente en el vocabulario de entrenamiento.
- **H2, “el híbrido tendrá mayor F1 que cada componente”, no se apoyó.** La regla de rescate fija empeoró tanto validación (0.853 frente a 0.857) como prueba (0.871 frente a 0.883). No se cambia el híbrido retrospectivamente para rescatar la hipótesis.
- La parte de H1 referente a expresiones *poco frecuentes* no se probó todavía por frecuencia estratificada; sólo podemos afirmar que la exhaustividad **global** del CRF superó la de reglas (0.882 frente a 0.640 en prueba).

## Limitaciones y lectura correcta

Las F1 de validación y prueba no deben interpretarse como una mejora temporal del mismo sistema: son subconjuntos distintos y la prueba tiene menos indicadores (281 frente a 308). La elección de CRF surgió tras observar errores de validación; la evaluación de prueba, aunque se hizo una sola vez tras congelar métodos, sigue siendo una evaluación en **un corpus y una partición**, no una demostración de generalización a otro hospital o idioma.

El esquema BIO no representa exactamente menciones discontinuas ni dos menciones del mismo rol que se solapan. Los indicadores son dados (*oracle*), así que un despliegue real exigiría medir su detección. El corpus no anota exhaustivamente toda la información clínica, y estas métricas no califican la seguridad de un sistema médico. El XML y las predicciones individuales no se incluyen por defecto en un repositorio público.

El análisis descriptivo posterior a la evaluación (sin reajustar el modelo) concreta esa limitación: el CRF obtuvo F1 0.940 en 233 indicadores con exactamente un hallazgo y una ubicación continuos, pero 0.760 en 35 indicadores con menciones múltiples y 0.465 en 17 con algún rol discontinuo. En diez indicadores sin roles principales anotados produjo 16 menciones falsas. Los subgrupos pueden solaparse y son demasiado pequeños para afirmar diferencias generales; los conteos completos están en `crf_test_analysis.json`.

## Reproducibilidad

Los scripts y la versión de dependencias están en `src/`, `requirements.txt` y `experiments/final_protocol_v1.md`. Los 18 tests automatizados pasan. El XML, datos derivados, pesos y predicciones permanecen localmente en rutas ignoradas por Git. Las tablas y JSON agregados de este directorio son los resultados que se pueden citar en el artículo.

**Siguiente trabajo académico:** solicitar una reproducción independiente siguiendo el README y revisar cualquier discrepancia. El artículo científico ya fue redactado fuera de este repositorio; su portada contiene datos personales y no se publica aquí. Como extensiones verdaderas —no ajustes retroactivos a esta prueba— quedan un modelo de spans para discontinuidad, la detección automática de indicadores y una comparación de encoder general frente a biomédico en una partición nueva o validación cruzada.
