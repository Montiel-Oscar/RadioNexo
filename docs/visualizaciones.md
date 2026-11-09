# Visualizaciones y desgloses de la prueba final

Estas figuras y el [panel local](../dashboard/index.html) describen la **misma prueba final congelada**. Se calcularon después de ver los resultados, sin reentrenar ni cambiar reglas. Son análisis descriptivos, no nuevas hipótesis confirmadas. Ningún archivo publicado contiene texto de informes, identificadores de pacientes ni predicciones individuales.

## Regenerar

Después de seguir el README para preparar `data/processed/test.jsonl` y generar las tres predicciones `results/tmp/*_test.jsonl`:

```bash
python src/visual_stats.py
python src/build_dashboard.py
```

Abre `dashboard/index.html` en un navegador. Es un archivo autónomo: no carga datos clínicos ni usa un servicio externo. El archivo generado [visualization_stats.json](../results/visualization_stats.json) contiene sólo conteos y métricas agregados; el script valida que el CRF reproduce 521 aciertos, 68 falsos positivos y 70 omisiones antes de escribirlo.

## Qué muestran los nuevos desgloses

- **Por indicador espacial:** F1 exacta para palabras con al menos seis indicadores en prueba. Por ejemplo, `of` aparece 130 veces y el CRF obtiene 0.914; `with` aparece sólo 11 veces y obtiene 0.591. Los tamaños son insuficientes para afirmar que la palabra por sí sola cause el rendimiento.
- **Por longitud:** la categoría se asigna según las menciones de referencia, no según lo predicho. Se muestra **exhaustividad exacta**, no F1. Hay 183 menciones de un token, 220 de dos, 125 de tres, 42 continuas de cuatro o más y 21 discontinuas. Las discontinuas tienen exhaustividad 0 en los tres métodos porque ninguno reconstruyó sus segmentos como una sola mención.
- **Por informe:** sólo 158 informes tienen al menos una mención principal anotada. La F1 del CRF supera a reglas en 91, pierde en 6 y empata en 61; frente al híbrido, 13/1/144. Un empate de F1 no implica predicciones idénticas. La prueba principal sigue siendo la **F1 micro global y el bootstrap apareado por informe** del protocolo original.

Los gráficos del artículo se dibujan directamente en su `main.tex` con TikZ para que compilen sin depender del HTML. Sus números provienen de `visualization_stats.json` y de los resultados finales ya publicados.
