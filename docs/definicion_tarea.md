# Definición operacional de la tarea — versión 1

Esta definición se fijó **antes de entrenar modelos y sin examinar el conjunto de prueba**. Cualquier cambio posterior deberá registrarse con motivo y fecha.

## Entrada y salida

**Entrada principal:** texto tokenizado de un informe y la posición de un *indicador espacial* verdadero (`RadSpRLRelation`). Proporcionar ese indicador es una condición *oracle* compartida por reglas, modelo e híbrido; por tanto, las cifras obtenidas no medirán la detección de indicadores desde texto crudo.

**Salida principal:** cero o más fragmentos `Trajector` (hallazgo) y cero o más fragmentos `Landmark` (ubicación) **para ese indicador**. Se admiten varios roles del mismo tipo y roles discontinuos. No se exige crear pares hallazgo–ubicación independientes: el XML agrupa roles bajo un indicador y no resuelve necesariamente cada par posible.

Una mención se representa como:

```text
(id_informe, segmentos_del_indicador, nombre_del_rol, segmentos_del_rol)
```

Cada segmento es `[inicio_token, fin_token)` con índices de base cero. Un fragmento discontinuo conserva **todos** sus segmentos ordenados, sin rellenar los huecos. Se compara la posición, no la cadena textual ni el atributo `type`.

**Casos sin rol:** una relación anotada puede carecer de `Trajector` o `Landmark`, incluso de ambos. Se mantiene en el conjunto: para el rol ausente, la salida correcta es el conjunto vacío. Un informe sin relaciones aporta ejemplos negativos sólo para una eventual tarea de detección de indicadores; no entra en la métrica principal condicionada a indicadores verdaderos.

**Fuera de alcance inicial:** `Diagnosis`, `Hedge`, negación general, clasificación de normalidad, interpretación de imágenes, diagnóstico y detección automática del indicador. `Hedge` queda para análisis exploratorio separado.

## Métrica primaria

Para cada rol y en conjunto, sumar sobre todos los indicadores de un conjunto los verdaderos positivos (coincidencia exacta de mención), falsos positivos y falsos negativos. Informar:

- Precisión = TP / (TP + FP).
- Exhaustividad = TP / (TP + FN).
- F1 = 2 × precisión × exhaustividad / (precisión + exhaustividad).

Si un denominador es cero, el programa devuelve 0. Se reportarán **F1 por rol** y **micro-F1 conjunta**; no se interpretará una F1 alta como seguridad clínica. Un fragmento con un límite de token incorrecto, un segmento omitido o un indicador equivocado **no** es coincidencia exacta. La evaluación rechaza indicadores inventados, roles fuera de la tarea y duplicados en las predicciones.

`src/evaluate.py` implementa esta definición. Una salida de prueba sintética debe lograr F1=1 al copiar exactamente las anotaciones; otra con un fragmento continuo donde el patrón es discontinuo debe fallar la coincidencia.

## Representación local y uso

`python3 src/prepare_data.py` valida el SHA-256 del XML y escribe `data/processed/train.jsonl` y `dev.jsonl`, ignorados por Git. Se puede repetir sin cambiar el corpus original. El archivo `test.jsonl` **no se genera por defecto**; cuando se congele todo el protocolo, usar `python3 src/prepare_data.py --split test`.

Cada línea JSONL contiene un informe con `id`, `text`, `tokens`, `sentences` y `relations`; cada relación conserva el indicador y una lista de roles con sus segmentos. Para evaluar predicciones:

```bash
python3 src/evaluate.py --gold data/processed/dev.jsonl --predictions ruta/a/predicciones_dev.jsonl
```

Cada línea de predicción corresponde a un indicador y tiene `id`, `indicator` y `roles`. Se puede omitir un indicador si no se predice ningún rol; omitirlo cuenta como falsos negativos de todos sus roles verdaderos.

## Comparabilidad y límites

- Entrenamiento, validación y prueba se separan por informe y agrupan textos idénticos; no hay identificador de paciente para garantizar independencia por persona.
- Seleccionar reglas, umbrales y arquitectura usando sólo entrenamiento y validación. Prueba queda reservada para el análisis final.
- El corpus no anota exhaustivamente todos los hallazgos ni la negación. Los ejemplos no anotados no deben reinterpretarse como una verdad clínica negativa.
- Si se añade detección de indicadores, presentar sus métricas **aparte** de la extracción condicionada.
