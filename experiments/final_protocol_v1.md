# Protocolo congelado antes de abrir prueba

Fecha: 2026-10-15. Estado al escribir este archivo: **`data/processed/test.jsonl` no existe y no se han calculado métricas de prueba**.

## Modelos que se evaluarán

1. Reglas léxicas y de proximidad v1, ajustadas sólo con `train`; máximo una mención continua por rol.
2. CRF BIO v1, dos modelos por rol entrenados sólo con `train`; configuración fija `c1=0.1`, `c2=0.1`, 100 iteraciones máximas. Se reutilizan los pesos ya entrenados mediante `--predict-only`.
3. Híbrido v1: para cada rol e indicador, todas las menciones del CRF si existe alguna; si no, copiar la propuesta de reglas. Regla fijada antes de medir el híbrido en validación; se mantiene aunque su F1 de validación (0.853) sea levemente inferior a la del CRF (0.857).

La pregunta principal se responde con **micro-F1 de fragmentos exactos condicionados al indicador verdadero**; también se informarán precisión, exhaustividad, F1 por rol y TP/FP/FN. Comparar CRF–reglas e híbrido–CRF con bootstrap apareado de 2 000 remuestreos por informe, semilla 42. Los intervalos son descriptivos; no equivalen por sí solos a validez externa. No habrá cambios de algoritmo o hiperparámetros después de observar prueba. Si el híbrido no mejora, H2 se considerará no apoyada.

## Datos y artefactos congelados

- XML: SHA-256 `d1a80e6765a6c885720fb030c51616e1b6b3b0b8540f7fcdcf9caa6cbedc173a`.
- Partición: SHA-256 `5216db5f7a7f4b152017de54331b512794911063e33fe11d4bab503de92997f6`.
- `src/baseline_rules.py`: `b1d49111d7242868f580dd8ef4285f0528a647a3abfb0e23520c630532863f78`.
- `src/train_crf.py`: `5b18f612f50a71124513f25c8a47e02ef2d10f667ba041ce64489d4fb047cedd`.
- `src/hybrid.py`: `11938fd5e4039cb62957c0091da95d3f488424428d8f1111cf8ca290d0121d08`.
- `src/evaluate.py`: `2875abbde6153601e071748eae5ebd321fdf0ba50679a676ba0a59095c20c316`.
- Pesos CRF `Trajector`: `ca042a4ac42bf1468845d56a6a069e67a5604e83a3346a5970613dfe7f04af4e`.
- Pesos CRF `Landmark`: `dbed1fd9e1ed875a5a4702462150c8992e554c94827d4695cb72e833a32e7f7d`.

## Ejecución única prevista

Desde la raíz del proyecto:

```bash
python3 src/prepare_data.py --split test
python3 src/baseline_rules.py --input data/processed/test.jsonl --output results/tmp/baseline_rules_test.jsonl
.venv/bin/python src/train_crf.py --predict-only --input data/processed/test.jsonl --output results/tmp/crf_test.jsonl
python3 src/hybrid.py --rules results/tmp/baseline_rules_test.jsonl --crf results/tmp/crf_test.jsonl --output results/tmp/hybrid_test.jsonl
python3 src/evaluate.py --gold data/processed/test.jsonl --predictions results/tmp/baseline_rules_test.jsonl
python3 src/evaluate.py --gold data/processed/test.jsonl --predictions results/tmp/crf_test.jsonl
python3 src/evaluate.py --gold data/processed/test.jsonl --predictions results/tmp/hybrid_test.jsonl
python3 src/compare_models.py --gold data/processed/test.jsonl --first results/tmp/baseline_rules_test.jsonl --second results/tmp/crf_test.jsonl --output results/crf_vs_rules_test.json
python3 src/compare_models.py --gold data/processed/test.jsonl --first results/tmp/crf_test.jsonl --second results/tmp/hybrid_test.jsonl --output results/hybrid_vs_crf_test.json
```

Los JSONL individuales y pesos permanecen fuera de Git. El informe final resumirá los números, sin copiar texto de pacientes. Después de esta ejecución, los análisis de error pueden explicar resultados, pero no justificar cambios retroactivos a los modelos reportados.
