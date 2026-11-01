# Primera línea base: léxico + proximidad (validación)

Fecha de ejecución: 2026-10-15. Corpus: Rad-SpRL XML auditado, partición `radsprl_v1.json`. Entrenamiento: 1 400 informes. Validación: 300 informes, 308 indicadores anotados. **Prueba no utilizada.**

## Método

Para cada indicador verdadero, el programa busca dentro de su oración y una ventana de 12 tokens a cada lado. Aprende de entrenamiento las expresiones anotadas (hasta seis tokens, continuas) y la dirección más frecuente de cada rol por indicador. Elige como máximo un `Trajector` y un `Landmark`, priorizando lado, proximidad, longitud y frecuencia. No consulta los roles de validación al predecir. No detecta indicadores ni fragmentos discontinuos; un término no visto no puede ser propuesto.

Código: `src/baseline_rules.py`. Evaluación exacta: `src/evaluate.py`. Diagnóstico agregado: `src/analyze_errors.py`; conteos completos en `baseline_rules_dev_analysis.json`. Las predicciones individuales quedan en `results/tmp/`, ignorado por Git.

## Resultados

| Rol | Precisión | Exhaustividad | F1 | TP / FP / FN |
| --- | ---: | ---: | ---: | ---: |
| Trajector (hallazgo) | 0.616 | 0.511 | 0.559 | 181 / 113 / 173 |
| Landmark (ubicación) | 0.781 | 0.740 | 0.760 | 239 / 67 / 84 |
| Micro conjunto | 0.700 | 0.620 | **0.658** | 420 / 180 / 257 |

La coincidencia exige exactamente los mismos índices de tokens, asociados al indicador correcto. Estos números **no** miden rendimiento clínico ni extracción de texto sin indicadores anotados. Tampoco representan prueba final: son una primera referencia en validación.

## Análisis de errores

- Entre los 173 falsos negativos de `Trajector`, 86 solapan una predicción pero tienen límites distintos; 87 ni siquiera solapan. En `Landmark`, los números son 45 y 39, respectivamente. Los modificadores no vistos son un patrón observado en los ejemplos: *“minimal early degenerative change”* frente a *“degenerative change”*; el fallo cuenta como falso positivo y falso negativo bajo coincidencia exacta.
- Hay 54 indicadores con más de una mención principal de algún rol. Su F1 micro es 0.535, frente a 0.705 en 246 indicadores con exactamente un hallazgo y un lugar continuos. El límite de una predicción por rol impone un techo de exhaustividad en enumeraciones.
- En 11 indicadores con un rol principal discontinuo, F1 es 0.296. El método sólo propone tramos continuos.
- En seis indicadores sin roles principales anotados, la línea base generó 11 menciones espurias. El léxico y la proximidad no bastan para decidir que una relación está vacía.
- Por indicador frecuente, F1: *of* 0.716 (122 casos), *in* 0.604 (71), *without* 0.711 (32), *with* 0.648 (26), *within* 0.564 (18). Estos subgrupos son pequeños y descriptivos; no se emplearon para ajustar retrospectivamente las reglas.

Las categorías estructurales se superponen; no sumar sus conteos. El análisis de validación es exploratorio y no autoriza volver a diseñar esta misma línea base para maximizar su puntuación.

## Decisión experimental siguiente

Entrenar un etiquetador contextual condicionado al indicador, que pueda delimitar frases no vistas y emitir **varias** menciones por rol. Mantener esta línea base congelada para la comparación; diseñar el etiquetador en entrenamiento y escoger hiperparámetros sólo con validación. Conservar prueba cerrada hasta fijar métodos y métricas.

## Reproducción

Desde la raíz del proyecto, tras ejecutar `python3 src/prepare_data.py`:

```bash
python3 src/baseline_rules.py
python3 src/evaluate.py --gold data/processed/dev.jsonl --predictions results/tmp/baseline_rules_dev.jsonl
python3 src/analyze_errors.py
python3 -m unittest discover -s tests -v
```
