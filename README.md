# Revit Beam Section Generator

Este repositorio contiene un script de Python diseñado para su uso en Autodesk Revit, que permite generar automáticamente vistas de secciones transversales (perpendiculares) al eje de una viga seleccionada.

## Contenido

- `create_beam_sections.py`: El script principal que contiene la lógica de la API de Revit.

## Características

- **Tipo de Vista**: Busca y utiliza automáticamente un tipo de sección llamado **"Viga"**. Si no existe, utiliza el tipo por defecto del proyecto.
- **Acotación Automática**: Identifica las caras laterales, superiores e inferiores de la viga para crear cotas de ancho y alto automáticamente.
- **Detalle de Doblado (Bending Detail)**: Para versiones de **Revit 2024 y posteriores**, el script busca los estribos asociados a la viga y crea automáticamente un detalle de doblado (`RebarBendingDetail`) en la vista de sección.
- **Gestión de Nombres**: Asegura que cada sección tenga un nombre único (ej. "Sección Viga - ID 123456 (1)").
- **Orientación Precisa**: Calcula el vector tangente en el punto medio de la viga para que la sección sea perfectamente perpendicular, incluso en vigas inclinadas.
- **Compatibilidad**: Diseñado para funcionar en versiones recientes de Revit (incluyendo 2024+).

## Cómo usar el script

El script está diseñado para ser ejecutado dentro de entornos que soporten la API de Revit con Python, como **pyRevit** o **Dynamo**.

### Requisitos

- Autodesk Revit.
- pyRevit instalado (recomendado) o Dynamo.
- (Opcional) Un tipo de vista de sección llamado "Viga" creado en el proyecto.
- (Opcional) Familias de detalles de doblado cargadas (necesario para la funcionalidad de `RebarBendingDetail` en Revit 2024+).

### Instrucciones para pyRevit

1. Selecciona una o varias vigas en el modelo de Revit.
2. Ejecuta el script.
3. Las nuevas secciones aparecerán en el Navegador de Proyectos con sus cotas y detalles de doblado aplicados.

## Lógica del Script

1. **Selección**: Filtra los elementos por la categoría `OST_StructuralFraming`.
2. **Transformación**: Crea un `Transform` basado en el punto medio y la tangente de la viga.
3. **Geometría y Cotas**: Escanea el sólido de la viga para encontrar planos paralelos a los ejes de la vista y genera las dimensiones.
4. **Armadura**: Identifica elementos `Rebar` hospedados en la viga y utiliza el nuevo método `RebarBendingDetail.Create` para añadir el detalle de doblado.

## Notas Técnicas

- La funcionalidad de `RebarBendingDetail` requiere que el proyecto tenga al menos un `RebarBendingDetailType` definido.
- La acotación funciona mejor con vigas de sección rectangular estándar.
