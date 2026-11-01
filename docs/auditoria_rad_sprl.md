# Auditoría inicial de Rad-SpRL — 15 de octubre de 2026

## Alcance y procedencia

Se descargó el archivo `Rad-SpRL.xml` del [repositorio de los autores](https://github.com/krobertslab/datasets/tree/master/rad-sprl), revisión `20ad32e595ba12bc0c8d54ecb7fd42c358502ea1`. El [artículo descriptivo](https://pmc.ncbi.nlm.nih.gov/articles/PMC7451761/) remite también a [Mendeley Data, versión 1](https://doi.org/10.17632/yhb26hfz8n.1). En esa página se anuncia la licencia **CC BY 4.0**. Aún no se ha comprobado byte a byte si el archivo de Mendeley coincide con esta copia de GitHub.

- Archivo local: `data/raw/Rad-SpRL.xml` (ignorado por Git).
- Tamaño: **9 609 066 bytes**.
- SHA-256: `d1a80e6765a6c885720fb030c51616e1b6b3b0b8540f7fcdcf9caa6cbedc173a`.
- Auditor reproducible: `python3 src/audit_corpus.py`.

## Lo que realmente hay en el XML

| Elemento | Conteo local |
| --- | ---: |
| Informes | 2 000 |
| Oraciones | 33 530 |
| Tokens | 201 572 |
| `RadSpRLRelation` / indicadores espaciales | 2 028 |
| Menciones `Trajector` | 2 254 |
| Menciones `Landmark` | 2 084 |
| Menciones `Diagnosis` | 448 |
| Menciones `Hedge` | 388 |
| Informes sin relación espacial anotada | 938 |
| Relaciones con ambos roles principales | 1 971 |
| Relaciones con varios `Trajector` o `Landmark` | 303 |
| Menciones discontinuas, codificadas con comas | 126 |
| Informes adicionales con texto exactamente duplicado | 16, en 8 grupos |
| Errores estructurales detectados tras interpretar fragmentos discontinuos | 0 |

Las etiquetas de tipo dentro de `Trajector` son `Disorder` (2 081) y `Anatomy` (173). Todos los `Landmark` tienen tipo `Anatomy` en esta copia. Hay 56 relaciones sin `Trajector` y 56 sin `Landmark`; 57 relaciones carecen de al menos uno de los dos roles. Estos casos no deben forzarse artificialmente a tener un par.

**Diferencia frente al artículo:** allí se publican 1 962 indicadores, 2 293 *Trajector*, 2 167 *Landmark*, 455 *Diagnosis* y 388 *Hedge*. El XML de GitHub conserva el número de informes y el conteo de *Hedge*, pero no todos los demás. No se conoce aún la causa; puede haber diferencias de versión o de criterio de conteo. Los experimentos deberán citar el SHA-256 y los conteos locales, no mezclar métricas entre versiones sin comprobar equivalencia.

## Convenciones del formato que afectan al experimento

1. Los `<Token>` tienen inicio y longitud de caracteres (`cs`, `cl`); las oraciones y los roles referencian rangos de **tokens** mediante `ts`, `tl`.
2. Algunos roles son **discontinuos**: `ts="118,121" tl="1,1"` representa dos segmentos. El primer auditor interpretó eso como error; tras adaptarlo, los 126 casos se validan.
3. Cada `RadSpRLRelation` tiene un indicador espacial y puede contener **varios** hallazgos y/o ubicaciones. El XML no expresa necesariamente qué pares individuales del producto cartesiano corresponden; por eso la tarea primaria será **extraer roles vinculados al indicador dado**, no generar automáticamente todos los pares posibles.
4. El indicador espacial está anotado. Usarlo como entrada en el experimento principal es una simplificación explícita; medir la detección del indicador desde texto crudo será un experimento separado si hay tiempo.
5. La ausencia de una relación espacial no implica que el informe sea normal. Aunque el artículo describe selección de informes no normales, el informe `00001` contiene literalmente una impresión de radiografía normal. Debe evitarse presentar la muestra como una selección perfectamente filtrada o representativa.
6. La negación general no está anotada exhaustivamente en Rad-SpRL. En particular, `without` puede ser un indicador espacial y no una etiqueta universal de negación.

## Partición v1

El repositorio consultado ofrece un XML único, no particiones oficiales. `python3 src/make_splits.py` genera `data/splits/radsprl_v1.json` con semilla **42**, grupos de texto exactamente idéntico indivisibles y estratificación por presencia de alguna relación anotada.

| Conjunto | Con relación | Sin relación | Total |
| --- | ---: | ---: | ---: |
| Entrenamiento | 743 | 657 | 1 400 |
| Validación | 159 | 141 | 300 |
| Prueba | 160 | 140 | 300 |

La partición usa identificadores de informe y no publica el texto. Agrupar duplicados exactos reduce una fuente de fuga, pero **no garantiza independencia por paciente**: el corpus no proporciona un identificador de paciente en la estructura inspeccionada. Antes de entrenar, revisar posibles duplicados cercanos y documentar la limitación.

## Próxima revisión antes de modelar

- [Hecho] Revisar cinco casos de **entrenamiento** con `python3 src/inspect_cases.py`:

  | Tipo | Informe | Observación |
  | --- | --- | --- |
  | Sin relaciones | `00001` | Su ausencia no debe usarse como etiqueta de normalidad. |
  | Simple | `00004` | El indicador `in` vincula una opacidad con una ubicación; `Diagnosis` y `Hedge` son roles adicionales. |
  | Roles múltiples | `00004` | El mismo indicador agrupa dos hallazgos, una ubicación y dos expresiones `Hedge`. |
  | Rol ausente | `00009` | Hay un indicador `of` sin roles hijos; se conserva como salida vacía. |
  | Discontinuo | `00075` | Un `Trajector` usa dos segmentos (`ts="118,121"`), que no deben fusionarse. |

- [Hecho] Formalizar la unidad evaluable y la métrica en [definicion_tarea.md](definicion_tarea.md). El parser `src/corpus.py` preserva segmentos y roles múltiples; `src/evaluate.py` calcula F1 exacta.
- [Hecho] No excluir relaciones sin ambos roles: cada rol se evalúa independientemente y su ausencia es un conjunto vacío, no un error del conversor.
- [Hecho] Convertir sólo entrenamiento y validación. El conjunto de prueba permanece sin convertir hasta el análisis final.
- [Pendiente] Examinar posibles duplicados **cercanos**, más allá de textos exactamente iguales.
- Confirmar, si es posible, si Mendeley versión 1 contiene el mismo XML y registrar los términos de uso aplicables al archivo concreto.
