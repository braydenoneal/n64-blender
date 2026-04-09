import math

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from mathutils import Matrix, Vector

from .material_panel import link_4b_material_library, update_material


def z_up_to_y_up(item: Vector | Matrix):
    return item @ Matrix.Rotation(math.radians(90), 4, (1, 0, 0))


def vec3(vector: Vector, apply_z_up_to_y_up: bool = True):
    return (z_up_to_y_up(vector) if apply_z_up_to_y_up else vector)[:3]


def mat3(matrix: Matrix):
    return [col[:] for col in matrix.to_3x3().col]


def rgb(ob):
    return ob[:3]


def rgba(ob):
    return ob[:4]


def write_file(filepath):
    ob = bpy.context.object

    for slot in ob.material_slots:
        mat = slot.material

        if not mat.is_f3d:
            continue

        name = mat.name
        texture = mat.f3d_mat.tex0.tex
        x_clamp = mat.f3d_mat.tex0.S.clamp
        x_mirror = mat.f3d_mat.tex0.S.mirror
        y_clamp = mat.f3d_mat.tex0.T.clamp
        y_mirror = mat.f3d_mat.tex0.T.mirror

        mat.is_f3d = False

        link_4b_material_library()

        mat2 = bpy.data.materials["4b_material_library"]
        material = mat2.copy()
        material.name = name
        bpy.data.materials.remove(mat2)

        slot.material = material
        p = material.props_4b

        p.enable_vertex_colors = False
        p.texture = texture

        if x_mirror:
            p.x_bounds = 'mirror'
        elif x_clamp:
            p.x_bounds = 'extend'
        else:
            p.x_bounds = 'repeat'

        if y_mirror:
            p.y_bounds = 'mirror'
        elif y_clamp:
            p.y_bounds = 'extend'
        else:
            p.y_bounds = 'repeat'

        material.is_4b = True
        update_material(material)

    return {'FINISHED'}


class ExportSomeData(Operator, ExportHelper):
    bl_idname = "export_test.some_data"
    bl_label = "Export 4B Materials model"
    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        return write_file(self.filepath)


def menu_func_export(self, _):
    self.layout.operator(ExportSomeData.bl_idname, text="4B Materials model (.json)")


def register():
    bpy.utils.register_class(ExportSomeData)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportSomeData)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
