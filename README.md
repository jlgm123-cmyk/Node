# Revit Beam Section Generator

Este repositorio contiene un script de Python diseñado para su uso en Autodesk Revit, que permite generar automáticamente vistas de secciones transversales (perpendiculares) al eje de una viga seleccionada.

## Contenido

- `create_beam_sections.py`: El script principal que contiene la lógica de la API de Revit.

## Cómo usar el script

El script está diseñado para ser ejecutado dentro de entornos que soporten la API de Revit con Python, como **pyRevit** o **Dynamo**.

### Requisitos

- Autodesk Revit.
- pyRevit instalado (recomendado) o Dynamo.

### Instrucciones para pyRevit

1. Abre un proyecto de Revit que contenga vigas.
2. Copia el contenido de `create_beam_sections.py` en un nuevo botón de pyRevit o ejecútalo a través de la consola de pyRevit.
3. Asegúrate de tener una viga seleccionada en el modelo antes de ejecutar el script.
4. El script creará una nueva sección en el punto medio de la viga seleccionada, orientada perpendicularmente a su eje.

### Lógica del Script

1. **Selección**: Identifica la viga seleccionada por el usuario.
2. **Geometría**: Obtiene la curva de ubicación (`LocationCurve`) de la viga.
3. **Cálculo de Plano**: Calcula el vector tangente en el punto medio de la viga para definir la dirección de la vista.
4. **Transformación**: Crea un objeto `Transform` y un `BoundingBoxXYZ` orientados para que el plano de la sección sea perpendicular a la viga.
5. **Creación**: Utiliza `ViewSection.CreateSection` para generar la vista dentro de una transacción de Revit.

## Personalización

Puedes ajustar las variables `w` (ancho), `h` (alto) y `d` (profundidad) en la función `create_beam_section` para cambiar el tamaño de la caja de sección generada.
