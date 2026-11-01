# Datos de RadioNexo

Se descargó `raw/Rad-SpRL.xml` del repositorio de los autores el **15 de octubre de 2026**. El antiguo corpus NUBes permanece fuera de este directorio, en el archivo `ClinNeg-archivo`.

## Fuente prevista

- Conjunto: [Rad-SpRL en Mendeley Data](https://doi.org/10.17632/yhb26hfz8n.1), con alternativa en [GitHub de Roberts Lab](https://github.com/krobertslab/datasets/tree/master/rad-sprl).
- Procedencia: informes de radiografías de tórax de la colección [Open-i](https://openi.nlm.nih.gov/).
- Idioma y formato publicados: inglés, XML. Verificar el esquema real antes de construir el conversor.
- URL exacta de esta copia: `https://raw.githubusercontent.com/krobertslab/datasets/20ad32e595ba12bc0c8d54ecb7fd42c358502ea1/rad-sprl/Rad-SpRL.xml`.
- Tamaño: 9 609 066 bytes. SHA-256: `d1a80e6765a6c885720fb030c51616e1b6b3b0b8540f7fcdcf9caa6cbedc173a`.
- La página de Mendeley indica **CC BY 4.0** para su conjunto; antes de distribuir esta copia desde GitHub, comprobar si la atribución y las condiciones son equivalentes.

## Organización local

- `raw/`: archivo original intacto, versión y comprobación de integridad. No subir al repositorio.
- `processed/`: conversiones JSONL locales con texto y anotaciones; no subir al repositorio. El conversor genera sólo entrenamiento y validación por defecto; `test.jsonl` requiere `--split test` y ya fue usado para la evaluación final registrada.
- `splits/radsprl_v1.json`: identificadores de entrenamiento, validación y prueba; no contiene texto clínico. Regenerar con `python3 src/make_splits.py`.
- En Git podrán publicarse instrucciones, código, configuraciones, conteos agregados y, cuando se permita, identificadores de partición.

## Controles al descargar

1. [Hecho] Registrar URL exacta, fecha, versión, tamaño y SHA-256.
2. [Pendiente] Confirmar las condiciones precisas de redistribución de la copia de GitHub.
3. [Hecho] Contar documentos, relaciones y cada rol; se encontraron diferencias frente al artículo. Véase `docs/auditoria_rad_sprl.md`.
4. [Hecho] Agrupar textos exactamente duplicados al particionar; revisar manualmente si existen duplicados cercanos.
5. [Hecho] Reservar prueba mediante lista fija de identificadores; no usarla para diseñar reglas.

No introducir informes de pacientes identificables ni cargar textos clínicos sensibles en servicios externos.
