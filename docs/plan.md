# Plan de investigación (versión 0; archivo histórico)

Este documento conserva las ideas y decisiones de la etapa de planificación. **No es la descripción actual del experimento.** La comparación final fue reglas–CRF–híbrido fijo; no se entrenó un encoder ni se evaluó `Hedge`. Véanse el [README](../README.md), el [protocolo final](../experiments/final_protocol_v1.md) y los [resultados de prueba](../results/final_test.md).

## 1. Problema

Los informes radiológicos contienen observaciones expresadas en texto libre. Extraer una palabra como *opacity* no basta: hay que saber **dónde** se observa. El corpus Rad-SpRL representa relaciones espaciales mediante un indicador (a menudo una preposición), un *Trajector* (hallazgo) y un *Landmark* (lugar anatómico). Algunas relaciones incluyen un diagnóstico sugerido o una expresión de incertidumbre. Nuestro objeto de estudio es **procesamiento de lenguaje**, no visión médica.

## 2. Pregunta científica

Con el indicador espacial proporcionado, ¿mejora un método híbrido la identificación de los fragmentos de hallazgo (*Trajector*) y ubicación (*Landmark*) asociados a él respecto de reglas y de un modelo secuencial por separado?

Subpreguntas:

- ¿En qué construcciones lingüísticas falla más cada método: *of/in/with/without*, coordinación, distancia entre menciones y múltiples lugares?
- Si hay tiempo, ¿cuánto cambia el resultado al detectar también el indicador desde texto sin marcar? Sería un experimento distinto.
- De forma exploratoria, ¿qué proporción de las expresiones *Hedge* se detecta y qué errores aparecen? No presentarlo como evaluación exhaustiva de incertidumbre.

## 3. Hipótesis y posibles resultados

- H1: el método secuencial tendrá mayor exhaustividad que reglas simples para expresiones poco frecuentes.
- H2: el híbrido tendrá mayor F1 exacta de roles que cada componente en el conjunto de prueba.
- H3 exploratoria: las reglas mostrarán precisión relativamente alta en algunos patrones frecuentes y serán útiles para analizar errores.

Las hipótesis se rechazarán o matizarán si los datos no las respaldan. No confundir mejoras numéricas pequeñas con diferencias sólidas; estimar incertidumbre mediante remuestreo por **informe**, no por mención aislada.

## 4. Datos y unidad de análisis

- Fuente primaria: [Rad-SpRL](https://doi.org/10.17632/yhb26hfz8n.1) / [artículo de datos](https://pmc.ncbi.nlm.nih.gov/articles/PMC7451761/).
- Idioma: inglés; modalidad: informes de radiografía de tórax, seleccionados entre informes no normales de Open-i.
- Unidad de partición: informe. Unidad de predicción principal: roles asociados a un indicador espacial anotado. Una relación XML puede contener varios hallazgos o ubicaciones; no asumir que todos los pares posibles son relaciones independientes.
- Etiquetas principales: *Spatial Indicator*, *Trajector*, *Landmark*. *Diagnosis* y *Hedge* quedan como extensión; no hacer pasar ausencia de anotación por hallazgo negativo.
- Los números publicados describen el corpus; deben verificarse tras descarga, sin asumir que todas las relaciones sirven exactamente al mismo experimento.

## 5. Protocolo previsto

### Fase A: auditoría (obligatoria antes de modelar)

1. [Hecho] Descargar desde el repositorio de los autores y conservar archivo original localmente; registrar URL y SHA-256.
2. [Hecho parcialmente] Comprobar términos de uso; Mendeley anuncia CC BY 4.0, pero verificar condiciones de cualquier archivo que se redistribuya.
3. [Hecho] Comprobar XML, reconstrucción de texto y posiciones, identificadores, duplicados y distribución de roles. Ver [auditoría](auditoria_rad_sprl.md).
4. [Hecho] Leer manualmente cinco casos de entrenamiento: simple, múltiple, discontinuo, sin rol y sin relación. Se fijó la [definición operacional](definicion_tarea.md), sin excluir roles ausentes.
5. [Hecho] Fijar semilla 42 y partición entrenamiento/validación/prueba a nivel de informe; el repositorio consultado sólo ofrece un XML, sin particiones oficiales. La [partición](../data/splits/radsprl_v1.json) agrupa textos idénticos y contiene sólo identificadores.

### Fase B: comparación

1. **Reglas [hecho]:** dado un indicador espacial, proponer fragmentos de hallazgo y ubicación con vocabulario aprendido sólo de entrenamiento y ventana de tokens. La implementación `src/baseline_rules.py` y el [análisis en validación](../results/baseline_rules_dev.md) quedan congelados como referencia; no rehacer sus decisiones tras consultar validación o prueba.
2. **Modelo secuencial [hecho]:** CRF independiente por rol, condicionado al mismo indicador. Etiqueta BIO con rasgos léxicos y contexto ±2, admite varias menciones continuas. Véase [resultado en validación](../results/crf_dev.md). Un encoder general o biomédico queda como comparación opcional y separada.
3. **Híbrido:** unir o filtrar propuestas de reglas con puntuación del modelo. Ajustar umbrales sólo en validación.
4. **Ablación:** comparar con y sin reglas para identificar qué componente aporta cualquier mejora. Si los recursos lo permiten, comparar encoder general y biomédico como análisis adicional, no como condición para terminar el proyecto.

### Fase C: evaluación

- **Métrica primaria:** precisión, exhaustividad y F1 de fragmentos `Trajector` y `Landmark` con coincidencia exacta de posiciones de tokens, ligados al indicador conocido. Los fragmentos discontinuos se representan como una tupla ordenada de segmentos. Reportar cada rol y micro-F1 conjunto.
- **Diagnóstico de errores:** falsos positivos/negativos por tipo de indicador, distancia entre menciones, pluralidad de hallazgos/lugares y longitud del informe.
- **Separación de tareas:** puntuación condicionada a indicadores verdaderos (experimento principal) y puntuación *end-to-end* con indicadores predichos (extensión). No compararlas como si fueran el mismo experimento.
- **Estabilidad:** semillas y remuestreo por informe para intervalos de confianza si el tiempo lo permite.
- **Ceguera:** reservar prueba hasta que datos, reglas, hiperparámetros y métricas estén fijados.

La primera línea base obtuvo F1 micro exacta 0.658 en validación, sin evaluar prueba. Su error principal en `Trajector` combina límites de frase no vistos y menciones múltiples. El CRF obtuvo 0.857 en la misma validación y recupera varias menciones. Estas cifras son exploratorias porque la elección del segundo método estuvo informada por errores de validación; la confirmación se reserva para prueba.

El [híbrido v1](../experiments/hybrid_v1.md) se fijó antes de evaluarlo y no mejoró al CRF en validación. Después se congelaron código, pesos, datos y métrica en el [protocolo final](../experiments/final_protocol_v1.md). La [prueba única](../results/final_test.md) confirmó la ventaja del CRF sobre reglas (F1 0.883 frente a 0.668) y no respaldó H2 para el híbrido estudiado (F1 0.871). Cualquier modelo posterior requerirá presentarse como nuevo experimento; no se reutilizará esta prueba para seleccionar hiperparámetros.

## 6. Riesgos y límites

- **Sesgo de selección:** los 2 000 informes proceden de casos no normales; no generalizar a todos los estudios radiológicos.
- **Pocos ejemplos de Hedge:** 388 menciones publicadas; análisis secundario, no promesa de detector clínico de incertidumbre.
- **Esquema específico:** hay relaciones espaciales que el corpus no representa; no interpretar todo lo no anotado como negativo auténtico.
- **Fuga de datos:** particionar por informe y buscar textos duplicados; no elegir patrones tras mirar prueba.
- **Validez externa:** resultados en Open-i no demuestran desempeño en otros hospitales, idiomas, tomografías o resonancias.
- **Seguridad:** el repositorio es académico; ninguna salida debe emplearse para atención o diagnóstico.

## 7. Entregables del equipo

1. Auditoría reproducible de datos y definición final de la tarea.
2. Conversor y particiones reproducibles, con pruebas básicas de integridad.
3. Tres enfoques comparables y configuración registrada.
4. Tabla de resultados, intervalos o variación, y ejemplos de errores.
5. Artículo: Introducción, estado de la cuestión, marco teórico, estructura experimental, resultados, análisis, conclusión, trabajo futuro y bibliografía.

## 8. Reparto sugerido (ajustable)

- Integrante A: corpus, anotaciones y evaluación.
- Integrante B: reglas y análisis lingüístico.
- Integrante C: modelo contextual y reproducibilidad.
- Integrante D, si existe: revisión bibliográfica, estadística y redacción integradora.

Todos deben revisar ejemplos y participar en el análisis final; el reparto no separa el trabajo científico en silos.

## 9. Decisiones por cerrar después de la auditoría

- ¿Es idéntica la copia GitHub del XML a la versión de Mendeley? Sus conteos no coinciden exactamente con los del artículo.
- [Resuelto] La tarea principal extrae roles vinculados a un indicador verdadero; no fuerza pares independientes.
- [Resuelto] El indicador forma parte de la clave de coincidencia exacta y es compartido como entrada *oracle*.
- ¿Qué encoder cabe en el equipo disponible?
- ¿Qué términos de distribución rigen el corpus descargado?
