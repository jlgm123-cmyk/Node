# -*- coding: utf-8 -*-
import math
import clr

# Import Revit API
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

def find_section_type_by_name(doc, name="Viga"):
    """
    Busca un tipo de vista de sección por nombre.
    Si no lo encuentra, devuelve el primero disponible.
    """
    collector = FilteredElementCollector(doc).OfClass(ViewFamilyType)
    first_type = None
    for vft in collector:
        if vft.ViewFamily == ViewFamily.Section:
            if not first_type:
                first_type = vft
            type_name = vft.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
            if name.lower() in type_name.lower():
                return vft
    return first_type

def get_unique_view_name(doc, base_name):
    """
    Asegura que el nombre de la vista sea único en el documento.
    """
    collector = FilteredElementCollector(doc).OfClass(View)
    existing_names = set([v.Name for v in collector])

    if base_name not in existing_names:
        return base_name

    suffix = 1
    new_name = "{} ({})".format(base_name, suffix)
    while new_name in existing_names:
        suffix += 1
        new_name = "{} ({})".format(base_name, suffix)
    return new_name

def add_beam_dimensions(doc, view, beam, transform):
    """
    Intenta acotar el ancho y alto de la viga en la vista de sección.
    Funciona mejor con vigas de sección rectangular estándar.
    """
    try:
        opt = Options()
        opt.ComputeReferences = True
        opt.IncludeNonVisibleObjects = True
        opt.View = view

        geometry = beam.get_Geometry(opt)

        # Recolectar planos/caras que sean paralelos a los ejes locales de la sección
        horizontal_refs = ReferenceArray()
        vertical_refs = ReferenceArray()

        # En una sección transversal, buscamos planos cuyas normales sean
        # paralelas a los ejes Right (BasisX) o Up (BasisY) de la sección.
        view_right = transform.BasisX
        view_up = transform.BasisY

        for obj in geometry:
            if isinstance(obj, Solid):
                for face in obj.Faces:
                    normal = face.ComputeNormal(UV(0.5, 0.5))
                    # Normal paralela al eje horizontal de la vista (BasisX) -> Referencia para ancho
                    if abs(normal.DotProduct(view_right)) > 0.99:
                        vertical_refs.Append(face.Reference)
                    # Normal paralela al eje vertical de la vista (BasisY) -> Referencia para alto
                    elif abs(normal.DotProduct(view_up)) > 0.99:
                        horizontal_refs.Append(face.Reference)
            elif isinstance(obj, GeometryInstance):
                inst_geom = obj.GetInstanceGeometry()
                for inst_obj in inst_geom:
                    if isinstance(inst_obj, Solid):
                        for face in inst_obj.Faces:
                            normal = face.ComputeNormal(UV(0.5, 0.5))
                            if abs(normal.DotProduct(view_right)) > 0.99:
                                vertical_refs.Append(face.Reference)
                            elif abs(normal.DotProduct(view_up)) > 0.99:
                                horizontal_refs.Append(face.Reference)

        # Crear cota de ancho (Horizontal)
        if vertical_refs.Size >= 2:
            # Línea de cota horizontal (desplazada un poco arriba del centro)
            line_p1 = transform.Origin + view_up * 0.5
            line_p2 = line_p1 + view_right
            dim_line = Line.CreateBound(line_p1, line_p2)
            doc.Create.NewDimension(view, dim_line, vertical_refs)

        # Crear cota de alto (Vertical)
        if horizontal_refs.Size >= 2:
            # Línea de cota vertical (desplazada un poco al lado del centro)
            line_p1 = transform.Origin + view_right * 0.5
            line_p2 = line_p1 + view_up
            dim_line = Line.CreateBound(line_p1, line_p2)
            doc.Create.NewDimension(view, dim_line, horizontal_refs)

    except Exception as e:
        print("Aviso: No se pudieron generar todas las cotas automáticas ({}).".format(e))

def create_beam_section(doc, beam):
    """
    Crea una vista de sección perpendicular al eje de la viga en su punto medio y la acota.
    """
    # 1. Obtener la curva de ubicación de la viga
    loc_curve = beam.Location.Curve
    if not loc_curve:
        print("La viga no tiene una curva de ubicación válida.")
        return None

    # 2. Calcular el punto medio y el vector tangente
    parameter = 0.5
    mid_point = loc_curve.Evaluate(parameter, True)
    tangent = loc_curve.ComputeDerivatives(parameter, True).BasisX.Normalize()

    # 3. Definir el sistema de coordenadas de la sección (Transform)
    up_vector = XYZ.BasisZ
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

    # 4. Configurar el BoundingBoxXYZ (Crop Box)
    w, h, d = 3.0, 3.0, 1.0
    section_box = BoundingBoxXYZ()
    section_box.Enabled = True
    section_box.Transform = transform
    section_box.Min = XYZ(-w/2, -h/2, -d)
    section_box.Max = XYZ(w/2, h/2, 0)

    # 5. Buscar tipo de sección "Viga"
    section_type = find_section_type_by_name(doc, "Viga")
    if not section_type:
        print("No se encontró un tipo de vista de sección adecuado.")
        return None

    # 6. Crear la sección y acotar dentro de una transacción
    t = Transaction(doc, "Crear Sección Acotada de Viga")
    t.Start()
    try:
        new_section = ViewSection.CreateSection(doc, section_type.Id, section_box)

        # Asignar nombre único
        base_name = "Sección Viga - ID {}".format(beam.Id)
        new_section.Name = get_unique_view_name(doc, base_name)

        # Configurar escala (ej. 1:10)
        new_section.Scale = 10

        # Añadir cotas automáticas
        add_beam_dimensions(doc, new_section, beam, transform)

        t.Commit()
        return new_section
    except Exception as e:
        print("Error al procesar la sección para el ID {}: {}".format(beam.Id, e))
        t.RollBack()
        return None

# --- Lógica de ejecución ---
if __name__ == "__main__":
    try:
        uidoc = __revit__.ActiveUIDocument
        doc = uidoc.Document
        selection_ids = uidoc.Selection.GetElementIds()

        if not selection_ids:
            print("Por favor, selecciona al menos una viga.")
        else:
            for el_id in selection_ids:
                element = doc.GetElement(el_id)
                if element and element.Category and \
                   element.Category.Id == ElementId(BuiltInCategory.OST_StructuralFraming):
                    section = create_beam_section(doc, element)
                    if section:
                        print("Éxito: Se ha generado la sección '{}'.".format(section.Name))
    except NameError:
        print("Este script debe ejecutarse dentro de un entorno de Revit (pyRevit/Dynamo).")
