# CRF condicionado al indicador: primera comparación

Fecha: 2026-10-15. Datos: partición `radsprl_v1.json`; 1 400 informes de entrenamiento y 300 de validación (1 439 y 308 indicadores anotados, respectivamente). El conjunto de prueba permanece cerrado.

## Decisión de modelo

El equipo disponible tiene CPU Intel Core i5-1135G7, 19 GiB de RAM y no muestra GPU NVIDIA; el entorno inicial no tenía PyTorch ni Transformers. La [publicación original de Rad-SpRL](https://pmc.ncbi.nlm.nih.gov/articles/PMC7807990/) compara BiLSTM-CRF y representaciones BERT/XLNet, pero emplea un protocolo de validación y una métrica que **no debemos equiparar** con los nuestros. La [documentación oficial de Transformers](https://huggingface.co/docs/transformers/tasks/token_classification) ofrece el camino para ajustar un encoder en clasificación de tokens. Un encoder biomédico sigue siendo interesante, pero descargarlo y ajustarlo en CPU tiene mayor costo; antes convenía establecer una referencia aprendida rápida y capaz de devolver varias menciones. Elegimos un **CRF lineal con características de contexto**, no un LLM ni un encoder preentrenado. La biblioteca utilizada es [python-crfsuite 0.9.12](https://pypi.org/project/python-crfsuite/).

## Implementación y límites de representación

Se entrenan dos CRF independientes, uno para `Trajector` y otro para `Landmark`. Cada ejemplo es la oración que contiene un indicador verdadero. Cada token recibe `B`, `I` u `O` con respecto a **ese indicador**; se incluyen la palabra, forma ortográfica, prefijos/sufijos, vecinas ±2, texto del indicador, lado y distancia. `lbfgs`, `c1=0.1`, `c2=0.1`, máximo 100 iteraciones, sin búsqueda de hiperparámetros. Los fragmentos se convierten a los mismos índices de tokens que la línea base. El modelo sólo ve los roles de entrenamiento; en validación usa texto, oraciones e indicadores anotados.

BIO permite múltiples menciones continuas, pero no conserva que dos segmentos discontinuos pertenezcan a **una** mención. Durante entrenamiento se dividieron 27 menciones discontinuas de `Trajector` y 57 de `Landmark`; también hubo 16 y 59 segmentos del mismo rol solapados que el esquema no pudo representar simultáneamente y se descartaron en favor del tramo más largo. Estos conteos son diagnóstico de entrenamiento, no resultados de validación.

## Resultado en validación

| Método | Trajector F1 | Landmark F1 | Micro P | Micro R | Micro F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Léxico + proximidad | 0.559 | 0.760 | 0.700 | 0.620 | 0.658 |
| CRF por rol | **0.817** | **0.902** | **0.878** | **0.838** | **0.857** |

El CRF obtuvo 567 aciertos, 79 falsos positivos y 110 falsos negativos, de 677 menciones gold. La diferencia apareada de F1 micro frente a reglas es **+0.199**; un bootstrap de 2 000 remuestreos por informe (semilla 42) produce un intervalo percentil descriptivo de **[+0.162, +0.237]**. No se remuestrearon menciones como observaciones independientes. Véanse `crf_vs_rules_dev.json` y `crf_dev_analysis.json` para números completos.

La elección de probar CRF estuvo motivada por errores ya observados en esta validación. Por tanto, el intervalo y la ventaja en validación **no son evidencia confirmatoria independiente** ni garantía de que la misma mejora aparecerá en prueba.

## Qué mejoró y qué falta

- En los 54 indicadores con varias menciones de un rol, F1 subió de 0.535 a 0.825: la salida BIO ya admite enumeraciones. En las 246 relaciones de un hallazgo y un lugar continuos, subió de 0.705 a 0.882.
- En 11 casos con algún rol discontinuo, F1 sigue limitada (0.484). Son muy pocos ejemplos para sacar conclusiones amplias y el esquema BIO no recupera la mención discontinua exacta.
- De los 68 falsos negativos de hallazgo, 37 solapan una predicción sin coincidir en límites; en ubicación, 13 de 42. Persisten errores de modificadores y extensión de la frase.
- Los seis indicadores sin roles principales siguen siendo problemáticos: diez menciones predichas donde no hay mención gold. El modelo no debe interpretarse como detector de cualquier hallazgo clínico.

## Próxima decisión

No recomendaría ajustar inmediatamente un BERT biomédico sólo para buscar otra subida en **la misma** validación. La mejora del CRF es sustancial, pero aún no hay una comparación confirmatoria. Primero conviene congelar CRF y reglas, definir si el proyecto realmente necesita un tercer modelo e implementar el híbrido como ablación preespecificada; después se podría reservar una comparación de encoder general frente a biomédico si hay tiempo y cómputo. Una vez fijadas las decisiones, usar prueba **una sola vez** para la tabla final. Si el objetivo se desplaza a fragmentos discontinuos, un modelo de spans sería más congruente que BIO.

## Reproducción

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
python3 src/prepare_data.py
python3 src/baseline_rules.py
.venv/bin/python src/train_crf.py
.venv/bin/python src/evaluate.py --gold data/processed/dev.jsonl --predictions results/tmp/crf_dev.jsonl
.venv/bin/python src/analyze_errors.py --predictions results/tmp/crf_dev.jsonl --output results/crf_dev_analysis.json
.venv/bin/python src/compare_models.py
.venv/bin/python -m unittest discover -s tests -v
```

Los pesos del CRF se guardan en `models/crf_v1/` y las predicciones individuales en `results/tmp/`; ambos directorios están ignorados por Git. El XML y las conversiones también son locales y no se deben subir automáticamente.
