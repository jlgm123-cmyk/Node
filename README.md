# Revit Beam Section Generator

Este repositorio contiene un script de Python diseñado para su uso en Autodesk Revit, que permite generar automáticamente vistas de secciones transversales (perpendiculares) al eje de una viga seleccionada.

## Contenido

- `create_beam_sections.py`: El script principal que contiene la lógica de la API de Revit.

## Características

- **Tipo de Vista**: Busca y utiliza automáticamente un tipo de sección llamado **"Viga"**. Si no existe, utiliza el tipo de sección por defecto del proyecto.
- **Acotación Automática**: El script intenta identificar las caras laterales, superiores e inferiores de la viga para crear cotas de ancho y alto automáticamente en la nueva vista.
- **Gestión de Nombres**: Asegura que cada sección tenga un nombre único (ej. "Sección Viga - ID 123456 (1)").
- **Orientación Precisa**: Calcula el vector tangente en el punto medio de la viga para que la sección sea perfectamente perpendicular, incluso en vigas inclinadas o verticales.
- **Compatibilidad**: Diseñado para funcionar en versiones recientes de Revit (incluyendo 2024+).

## Cómo usar el script

El script está diseñado para ser ejecutado dentro de entornos que soporten la API de Revit con Python, como **pyRevit** o **Dynamo**.

### Requisitos

- Autodesk Revit.
- pyRevit instalado (recomendado) o Dynamo.
- (Opcional) Un tipo de vista de sección llamado "Viga" creado en el proyecto para una mejor organización.

### Instrucciones para pyRevit

1. Abre un proyecto de Revit que contenga vigas (Structural Framing).
2. Selecciona una o varias vigas en el modelo.
3. Ejecuta el script.
4. Las nuevas secciones aparecerán en el Navegador de Proyectos bajo el tipo correspondiente, con cotas de dimensiones aplicadas.

## Lógica del Script

1. **Filtro**: Solo procesa elementos de la categoría `OST_StructuralFraming`.
2. **Transformación**: Crea un objeto `Transform` basado en el punto medio y la tangente de la viga.
3. **Geometría**: Escanea el sólido de la viga en busca de caras cuyas normales coincidan con los ejes de la vista de sección.
4. **Dimensionamiento**: Utiliza `doc.Create.NewDimension` para colocar las cotas de base y altura.

## Notas Técnicas

La acotación automática funciona de manera óptima con familias de vigas de sección rectangular estándar. En familias con geometrías muy complejas o irregulares, es posible que el script no encuentre referencias válidas para todas las cotas.
