# -*- coding: utf-8 -*-
import math
import clr

# Import Revit API
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

def create_beam_section(doc, beam):
    """
    Crea una vista de sección perpendicular al eje de la viga en su punto medio.
    """
    # 1. Obtener la curva de ubicación de la viga
    loc_curve = beam.Location.Curve
    if not loc_curve:
        print("La viga no tiene una curva de ubicación válida.")
        return None

    # 2. Calcular el punto medio y el vector tangente
    parameter = 0.5 # Punto medio (0.0 a 1.0)
    mid_point = loc_curve.Evaluate(parameter, True)
    tangent = loc_curve.ComputeDerivatives(parameter, True).BasisX.Normalize()

    # 3. Definir el sistema de coordenadas de la sección (Transform)
    # Para una sección perpendicular a la viga:
    # - El eje Z de la vista (hacia donde mira) debe ser el eje de la viga (tangente).
    # - El eje X de la vista (horizontal en el papel) suele ser el vector horizontal perpendicular.
    # - El eje Y de la vista (vertical en el papel) es el eje Z global (hacia arriba).

    up_vector = XYZ.BasisZ

    # Si la viga es vertical, necesitamos un vector 'up' diferente
    if abs(tangent.DotProduct(up_vector)) > 0.999:
        up_vector = XYZ.BasisX

    view_direction = tangent
    right_direction = up_vector.CrossProduct(view_direction).Normalize()
    up_direction = view_direction.CrossProduct(right_direction).Normalize()

    transform = Transform.Identity
    transform.Origin = mid_point
    transform.BasisX = right_direction
    transform.BasisY = up_direction
    transform.BasisZ = view_direction

    # 4. Definir el BoundingBoxXYZ para la sección
    # Estos valores definen el tamaño de la caja de corte (crop box)
    w = 2.0 # Ancho total
    h = 2.0 # Alto total
    d = 1.0 # Profundidad (lejos del plano de sección)

    section_box = BoundingBoxXYZ()
    section_box.Enabled = True
    section_box.Transform = transform

    # El plano de la sección está en Z=0 en coordenadas locales de la caja.
    # Min y Max definen el volumen visible en esas coordenadas locales.
    section_box.Min = XYZ(-w/2, -h/2, -d)
    section_box.Max = XYZ(w/2, h/2, 0)

    # 5. Buscar el tipo de vista de sección (ViewFamilyType)
    collector = FilteredElementCollector(doc)
    view_family_types = collector.OfClass(ViewFamilyType).ToElements()
    section_type_id = None
    for vft in view_family_types:
        if vft.ViewFamily == ViewFamily.Section:
            section_type_id = vft.Id
            break

    if not section_type_id:
        print("No se encontró un tipo de vista de sección.")
        return None

    # 6. Crear la sección dentro de una transacción
    t = Transaction(doc, "Crear Sección de Viga")
    t.Start()
    try:
        new_section = ViewSection.CreateSection(doc, section_type_id, section_box)
        t.Commit()
        return new_section
    except Exception as e:
        print("Error al crear la sección: {}".format(e))
        t.RollBack()
        return None

# --- Lógica de ejecución (pyRevit) ---
if __name__ == "__main__":
    try:
        # Intentar obtener el documento activo desde el entorno de Revit
        uidoc = __revit__.ActiveUIDocument
        doc = uidoc.Document

        # Obtener los elementos seleccionados
        selection_ids = uidoc.Selection.GetElementIds()

        if not selection_ids:
            print("Por favor, selecciona al menos una viga.")
        else:
            for el_id in selection_ids:
                element = doc.GetElement(el_id)
                # Verificar si el elemento es una viga (Structural Framing)
                # Se utiliza una comparación compatible con varias versiones de Revit (incluyendo 2024+)
                is_beam = False
                if element and element.Category:
                    if element.Category.Id == ElementId(BuiltInCategory.OST_StructuralFraming):
                        is_beam = True

                if is_beam:
                    section = create_beam_section(doc, element)
                    if section:
                        print("Sección creada: {}".format(section.Name))
                else:
                    print("El elemento {} no es una viga.".format(el_id))
    except NameError:
        print("Este script debe ejecutarse dentro de un entorno de Revit (pyRevit/Dynamo).")
