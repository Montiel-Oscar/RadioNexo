# Híbrido v1: protocolo fijado antes de medirlo

Fecha: 2026-10-15. Entrada: predicciones de la línea base léxica y del CRF v1, ambos entrenados únicamente con `train` y condicionados a los mismos indicadores verdaderos. Métrica: F1 de fragmentos exactos definida en `docs/definicion_tarea.md`.

Regla única, sin umbrales: para cada indicador y cada rol por separado, conservar **todas** las menciones del CRF si propone al menos una. Sólo si el CRF no propone ninguna mención de ese rol, copiar la propuesta de las reglas (si existe). No se modifican límites, no se añaden roles de ambos métodos cuando CRF ya emitió alguno y no se mira el texto gold en la combinación.

Motivo: aprovechar la mayor precisión del CRF sin borrar su capacidad de emitir varias menciones, y comprobar si el léxico rescata omisiones completas. Riesgo previsible: la regla puede añadir falsos positivos en indicadores sin roles anotados. Evaluaremos este riesgo sin reajustar el híbrido en función de la validación.

Se compararán **los tres sistemas** en validación y, tras congelar el código y las configuraciones, **una vez** en prueba. Si el híbrido pierde frente al CRF, se reportará ese resultado: la hipótesis H2 no se rescata cambiando la combinación después de ver prueba.
