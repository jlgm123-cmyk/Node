# -*- coding: utf-8 -*-
import math
import clr

# Import Revit API
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *
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
        horizontal_refs = ReferenceArray()
        vertical_refs = ReferenceArray()

        view_right = transform.BasisX
        view_up = transform.BasisY

        for obj in geometry:
            if isinstance(obj, Solid):
                for face in obj.Faces:
                    normal = face.ComputeNormal(UV(0.5, 0.5))
                    if abs(normal.DotProduct(view_right)) > 0.99:
                        vertical_refs.Append(face.Reference)
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

        if vertical_refs.Size >= 2:
            line_p1 = transform.Origin + view_up * 0.5
            line_p2 = line_p1 + view_right
            dim_line = Line.CreateBound(line_p1, line_p2)
            doc.Create.NewDimension(view, dim_line, vertical_refs)

        if horizontal_refs.Size >= 2:
            line_p1 = transform.Origin + view_right * 0.5
            line_p2 = line_p1 + view_up
            dim_line = Line.CreateBound(line_p1, line_p2)
            doc.Create.NewDimension(view, dim_line, horizontal_refs)

    except Exception as e:
        print("Aviso: No se pudieron generar todas las cotas automáticas ({}).".format(e))

def find_rebar_bending_detail_type(doc):
    """
    Busca el primer tipo de detalle de doblado de armadura disponible.
    """
    try:
        collector = FilteredElementCollector(doc).OfClass(RebarBendingDetailType)
        return collector.FirstElement()
    except:
        return None

def add_stirrup_bending_detail(doc, view, beam, transform):
    """
    Busca estribos asociados a la viga y crea un detalle de doblado en la vista.
    Revit 2024+
    """
    # Verificar versión de Revit (RebarBendingDetail es 2024+)
    revit_version = int(doc.Application.VersionNumber)
    if revit_version < 2024:
        print("Aviso: Los Bending Details de armadura requieren Revit 2024 o superior.")
        return

    try:
        # Buscar el tipo de detalle de doblado
        detail_type = find_rebar_bending_detail_type(doc)
        if not detail_type:
            print("Aviso: No se encontró ningún 'RebarBendingDetailType' en el proyecto.")
            return

        # Buscar estribos (rebars) hospedados en la viga
        # Se utiliza RebarHostData para una búsqueda más fiable
        host_data = RebarHostData.GetRebarHostData(beam)
        rebars_in_host = host_data.GetRebarsInHost()

        stirrup = None
        print("Buscando estribos (shape: M_T1) en la viga ID {} ({} armaduras encontradas)...".format(beam.Id, len(rebars_in_host)))

        for r in rebars_in_host:
            try:
                # 0. Filtrar por Estilo de Armadura (Stirrup/Tie)
                if r.RebarStyle != RebarStyle.StirrupTie:
                    continue

                # 1. Verificar por Nombre de Forma (RebarShape)
                shape_id = r.GetShapeId()
                shape = doc.GetElement(shape_id) if shape_id != ElementId.InvalidElementId else None
                # Se usa SYMBOL_NAME_PARAM para evitar errores de acceso directo a Name
                shape_name = shape.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() if shape else "Desconocida"

                # 2. Verificar por Nombre de Tipo (RebarBarType)
                rebar_type = doc.GetElement(r.GetTypeId())
                type_name = rebar_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() if rebar_type else "Desconocido"

                # 3. Verificar por parámetro de forma (REBAR_SHAPE)
                param_shape = r.get_Parameter(BuiltInParameter.REBAR_SHAPE)
                param_shape_str = param_shape.AsValueString() if param_shape else "N/A"

                print("- Rebar ID: {} | Shape: {} | Type: {} | ParamShape: {}".format(r.Id, shape_name, type_name, param_shape_str))

                search_term = "M_T1"
                match_found = False

                if search_term.upper() in shape_name.upper():
                    match_found = True
                    print("  [!] Coincidencia encontrada por Shape Name.")
                elif search_term.upper() in type_name.upper():
                    match_found = True
                    print("  [!] Coincidencia encontrada por Type Name.")
                elif search_term.upper() in param_shape_str.upper():
                    match_found = True
                    print("  [!] Coincidencia encontrada por Parameter Value String.")

                if match_found:
                    stirrup = r
                    break
            except Exception as ex:
                print("  [!] Error analizando armadura {}: {}".format(r.Id, str(ex)))
                continue

        if stirrup:
            # Posición relativa para el detalle (un poco alejado de la viga en el plano de la sección)
            # transform.Origin es el centro de la viga.
            # Desplazamos en BasisX (derecha de la vista) y BasisY (arriba de la vista).
            offset_x = 2.0
            offset_y = 1.0
            position = transform.Origin + (transform.BasisX * offset_x) + (transform.BasisY * offset_y)

            # Crear el detalle de doblado
            # Nota: El método Create requiere el OBJETO RebarBendingDetailType, no solo su ElementId.
            RebarBendingDetail.Create(doc, view.Id, stirrup.Id, 0, detail_type, position, 0.0)
            print("Éxito: Detalle de doblado (bending detail) creado para la armadura ID {}.".format(stirrup.Id))
        else:
            print("Aviso: No se encontraron estribos (Rebar) hospedados en la viga ID {}.".format(beam.Id))

    except Exception as e:
        print("Error al crear el detalle de doblado: {}".format(e))

def create_beam_section(doc, beam):
    """
    Crea una vista de sección perpendicular, la acota y añade detalles de doblado.
    """
    loc_curve = beam.Location.Curve
    if not loc_curve:
        print("La viga no tiene una curva de ubicación válida.")
        return None

    parameter = 0.5
    mid_point = loc_curve.Evaluate(parameter, True)
    tangent = loc_curve.ComputeDerivatives(parameter, True).BasisX.Normalize()

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

    # Bounding Box (Ajustado para que el bending detail sea visible)
    w, h, d = 6.0, 4.0, 1.0
    section_box = BoundingBoxXYZ()
    section_box.Enabled = True
    section_box.Transform = transform
    section_box.Min = XYZ(-w/2, -h/2, -d)
    section_box.Max = XYZ(w/2, h/2, 0)

    section_type = find_section_type_by_name(doc, "Viga")
    if not section_type:
        print("No se encontró un tipo de vista de sección adecuado.")
        return None

    t = Transaction(doc, "Crear Sección con Detalles de Viga")
    t.Start()
    try:
        new_section = ViewSection.CreateSection(doc, section_type.Id, section_box)
        base_name = "Sección Viga - ID {}".format(beam.Id)
        new_section.Name = get_unique_view_name(doc, base_name)
        new_section.Scale = 10

        # 1. Añadir cotas
        add_beam_dimensions(doc, new_section, beam, transform)

        # 2. Añadir detalle de doblado (Revit 2024+)
        add_stirrup_bending_detail(doc, new_section, beam, transform)

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
                        print("Sección completa generada: '{}'.".format(section.Name))
    except NameError:
        print("Este script debe ejecutarse dentro de un entorno de Revit (pyRevit/Dynamo).")
