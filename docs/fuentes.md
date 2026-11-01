# Fuentes iniciales y función de cada una (archivo histórico)

La bibliografía completa y el análisis final están en el artículo académico elaborado fuera de este repositorio. Aquí se conserva la selección de fuentes con que comenzó el proyecto.

## Datos principales

1. Datta, S. y Roberts, K. (2020). [A dataset of chest X-ray reports annotated with Spatial Role Labeling annotations](https://pmc.ncbi.nlm.nih.gov/articles/PMC7451761/). *Data in Brief*, 32, 106056. Define corpus, etiquetas, tamaño, procedencia y límites. DOI: [10.1016/j.dib.2020.106056](https://doi.org/10.1016/j.dib.2020.106056).
2. [Rad-SpRL en Mendeley Data](https://doi.org/10.17632/yhb26hfz8n.1). Descarga primaria indicada por los autores; verificar versión y términos antes de redistribuir.
3. [Rad-SpRL en GitHub de Roberts Lab](https://github.com/krobertslab/datasets/tree/master/rad-sprl). Copia alternativa indicada en el artículo; comparar integridad y formato con la descarga primaria.

## Método y estado de la cuestión

4. Datta, S., Si, Y., Rodriguez, L., Shooshan, S. E., Demner-Fushman, D. y Roberts, K. (2020). [Understanding spatial language in radiology: Representation framework, annotation, and spatial relation extraction from chest X-ray reports using deep learning](https://doi.org/10.1016/j.jbi.2020.103473). *Journal of Biomedical Informatics*, 108, 103473. Trabajo original que propone y evalúa el esquema: referencia imprescindible para no presentar la extracción espacial como tarea inédita.
5. Demner-Fushman, D. y otros (2016). [Preparing a collection of radiology examinations for distribution and retrieval](https://doi.org/10.1093/jamia/ocv080). *Journal of the American Medical Informatics Association*. Contexto de la colección [Open-i](https://openi.nlm.nih.gov/) de la que procede el corpus.
6. Jain, S. y otros (2021). [RadGraph: Extracting Clinical Entities and Relations from Radiology Reports](https://arxiv.org/abs/2106.14463). Marco de extracción de entidades y relaciones en radiología; **no es el mismo esquema** que Rad-SpRL. Útil para el estado de la cuestión, no combinar etiquetas sin una correspondencia justificada.
7. [Documentación oficial de Hugging Face Transformers: Token classification](https://huggingface.co/docs/transformers/tasks/token_classification). Referencia de implementación futura para un encoder contextual; no es evidencia de superioridad en este corpus.
8. [python-crfsuite 0.9.12](https://pypi.org/project/python-crfsuite/) y su [API](https://python-crfsuite.readthedocs.io/en/latest/). Implementación del CRF secuencial usado en la primera comparación aprendida.

## Notas de lectura

- La novedad propuesta es la **comparación experimental y el análisis de errores** en Rad-SpRL, no haber inventado la extracción espacial.
- Antes de cerrar la bibliografía, buscar trabajos posteriores que usen Rad-SpRL y comprobar si ya compararon exactamente reglas, modelo e híbrido. Si fuese así, reformular la contribución hacia un análisis de robustez específico.
- Registrar fecha de consulta, versión de datos y licencia exacta en la auditoría local. La licencia del artículo no implica automáticamente que todo archivo derivado pueda redistribuirse con las mismas condiciones.
