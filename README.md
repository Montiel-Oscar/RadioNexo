# RadioNexo — ¿Dónde está el hallazgo?

**Extracción espacial de entidades en informes radiológicos mediante reglas y modelos secuenciales.** Proyecto final de Lenguaje y Procesamiento Inteligente de Texto. El código procesa informes **en inglés**; el reporte académico está redactado en español.

## En una frase

Dado un **indicador espacial ya marcado** en el texto de un informe de radiografía, el programa delimita el **Trajector** (entidad cuya posición se describe, a menudo un hallazgo) y el **Landmark** (lugar de referencia). Ejemplo inventado: en `opacity in the left lung`, `in` es el indicador, `opacity` el Trajector y `left lung` el Landmark. No interpretamos imágenes ni emitimos diagnósticos.

El trabajo compara tres métodos bajo el mismo protocolo: **reglas léxicas y de proximidad**, dos modelos secuenciales **CRF** (uno por rol) y un **híbrido fijo** que recurre a reglas sólo si el CRF no produjo ese rol. No usamos un LLM ni un encoder biomédico en el experimento reportado.

Puedes explorar las cifras en el [panel visual](https://montiel-oscar.github.io/RadioNexo/) y probar la [demostración interactiva](https://montiel-oscar.github.io/RadioNexo/demo.html). Ambas páginas usan sólo estadísticas agregadas o frases inventadas; el [método de los desgloses](docs/visualizaciones.md) está documentado aquí. Si GitHub Pages aún no se ha desplegado, los archivos locales están en `dashboard/`.

## Resultado principal

| Método | Precisión | Exhaustividad | F1 micro exacta |
| --- | ---: | ---: | ---: |
| Reglas | 0.699 | 0.640 | 0.668 |
| CRF | **0.885** | 0.882 | **0.883** |
| Híbrido | 0.859 | **0.883** | 0.871 |

La prueba contiene 300 informes, 281 indicadores anotados y 591 menciones de los dos roles. El CRF mejoró a las reglas en +0.215 de F1; el híbrido **no** mejoró al CRF. Estos números miden coincidencia exacta de fragmentos de texto **con el indicador verdadero proporcionado**. No miden detección del indicador desde cero, exactitud diagnóstica ni seguridad clínica. Véanse [resultados finales](results/final_test.md) y [protocolo congelado](experiments/final_protocol_v1.md). El [artículo original de Rad-SpRL](https://doi.org/10.1016/j.jbi.2020.103473) usa otro protocolo y otros roles: sus cifras no son directamente comparables con las nuestras.

## Demostración en dos minutos

Después de seguir la instalación y preparación de datos de abajo:

```bash
python src/demo.py
```

El script muestra tres **frases inventadas**, el indicador dado y la salida de cada método. Una frase contiene `No pleural effusion`: sirve para explicar un límite importante. El programa puede extraer `pleural effusion`, pero **no** determina si está presente o negado. La demostración no usa el conjunto de prueba ni calcula F1; los resultados cuantitativos proceden de la evaluación separada.

## Reproducir desde una copia limpia

Se requiere Python **3.14** (versión usada aquí; otras versiones no se han verificado), `git` y conexión para obtener el corpus y la dependencia. Los comandos siguientes se ejecutan desde la raíz del repositorio. En Linux/macOS:

```bash
git clone https://github.com/Montiel-Oscar/RadioNexo.git
cd RadioNexo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Descarga la **misma revisión** del XML de los autores. No está incluida en este repositorio; al prepararla se verifica su SHA-256. Si la URL deja de funcionar, consulta [la ficha de datos](data/README.md) antes de sustituirla: otra versión puede cambiar los resultados.

```bash
mkdir -p data/raw
curl -fL 'https://raw.githubusercontent.com/krobertslab/datasets/20ad32e595ba12bc0c8d54ecb7fd42c358502ea1/rad-sprl/Rad-SpRL.xml' -o data/raw/Rad-SpRL.xml
sha256sum data/raw/Rad-SpRL.xml
# Esperado: d1a80e6765a6c885720fb030c51616e1b6b3b0b8540f7fcdcf9caa6cbedc173a
```

Prepara las particiones y comprueba el código. `train` y `dev` se generan por defecto; `test` se solicita explícitamente. **La prueba final ya fue observada en este proyecto:** esta repetición sirve para verificar el resultado publicado, no para ajustar métodos nuevos con ella.

```bash
python src/audit_corpus.py
python src/prepare_data.py
python -m unittest discover -s tests -v
python src/baseline_rules.py --input data/processed/dev.jsonl --output results/tmp/baseline_rules_dev.jsonl
python src/train_crf.py --input data/processed/dev.jsonl --output results/tmp/crf_dev.jsonl
python src/hybrid.py --rules results/tmp/baseline_rules_dev.jsonl --crf results/tmp/crf_dev.jsonl --output results/tmp/hybrid_dev.jsonl
python src/demo.py
```

Para reproducir **las cifras finales** con los métodos ya fijados, sigue los comandos de [experiments/final_protocol_v1.md](experiments/final_protocol_v1.md). Ese documento conserva las sumas SHA-256 de los scripts y pesos de la evaluación original; un entrenamiento nuevo puede producir pesos distintos según el entorno, por lo que **no garantizamos igualdad bit a bit**. Verifica las métricas con `src/evaluate.py` y contrástalas con [results/final_test.md](results/final_test.md). No edites modelos basándote en `test` y presentes luego esa misma prueba como independiente.

Para regenerar las estadísticas visuales y el panel autónomo después de reproducir las predicciones de prueba:

```bash
python src/visual_stats.py
python src/build_dashboard.py
```

## Datos, método y límites

El corpus [Rad-SpRL](https://doi.org/10.17632/yhb26hfz8n.1), descrito por [Datta y Roberts (2020)](https://doi.org/10.1016/j.dib.2020.106056), contiene 2 000 informes de radiografía de tórax en inglés. Esta copia local procede del [repositorio de los autores](https://github.com/krobertslab/datasets/tree/master/rad-sprl). Nuestra [auditoría](docs/auditoria_rad_sprl.md) encontró diferencias entre los conteos publicados y el XML utilizado; el SHA-256 y la partición en `data/splits/` definen exactamente el material experimental. El corpus y sus derivados no se redistribuyen aquí.

La tarea y la métrica están fijadas en [docs/definicion_tarea.md](docs/definicion_tarea.md). Un acierto exige coincidencia exacta de informe, indicador, rol y límites de tokens. Se informa F1 micro y por rol. Entrenamiento/validación/prueba: 1 400/300/300 informes, agrupando textos exactamente duplicados. No hay identificadores de paciente para asegurar separación por persona. El esquema BIO del CRF tampoco representa fielmente menciones discontinuas o superpuestas del mismo rol. `Diagnosis`, `Hedge`, negación general, detección de indicadores e imágenes quedan fuera de la evaluación principal.

## Estructura

```text
data/splits/   Partición fija (identificadores, sin texto clínico)
docs/          Fuentes, auditoría y definición de la tarea
experiments/   Protocolo y regla híbrida anteriores a la prueba
results/       Tablas y estadísticas agregadas; no predicciones individuales
src/           Lector, preparación, reglas, CRF, híbrido, evaluación y demo
tests/         Pruebas automatizadas
```

`data/raw/`, `data/processed/`, `models/`, `results/tmp/` y `.venv/` se mantienen locales mediante `.gitignore`. **No subas informes clínicos ni predicciones individuales al repositorio.** La fuente LaTeX de clase se mantiene fuera del repositorio; su [PDF compilado](Reportefinal/main.pdf) sí está aquí y contiene datos personales en la portada. El repositorio es público: revisa si deseas mantener visible ese PDF. El flujo de Pages publica **únicamente** las dos páginas de `dashboard/`, no el PDF ni otros archivos del repositorio.

## Estado y siguiente trabajo

El experimento y el reporte científico ya se completaron. La publicación de código permite una **reproducción independiente pendiente de realizar por otra persona**; no afirmamos que esa verificación externa ya ocurrió. Una extensión posible sería detectar automáticamente el indicador espacial y medir esa etapa y la cadena completa en un protocolo nuevo. Otra sería reemplazar BIO para manejar fragmentos discontinuos. Véase [plan](docs/plan.md) para contexto histórico; ante discrepancias, prevalecen la definición de tarea y el protocolo final.

**Investigación, no uso clínico.** Los resultados no deben aplicarse para tomar decisiones sobre pacientes.
