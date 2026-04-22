import math
from typing import Any

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


def combiner_equals(c0, c1):
    checks = [
        c0.A == c1.A,
        c0.B == c1.B,
        c0.C == c1.C,
        c0.D == c1.D,
    ]

    return all(checks)


def tex_equals(tex0, tex1):
    if tex0 is not None:
        print(tex0.name)
    if tex1 is not None:
        print(tex1.name)
    print()

    checks = [
        (tex0.tex is None and tex1.tex is None) or
        ((tex0.tex is not None and tex1.tex is not None) and
         (tex0.tex.name == tex1.tex.name)),
        tex0.S.clamp == tex1.S.clamp,
        tex0.S.mirror == tex1.S.mirror,
        tex0.T.clamp == tex1.T.clamp,
        tex0.T.mirror == tex1.T.mirror,
    ]

    return all(checks)


def f3d_mat_equals(m0: Any, m1: Any):
    mat0 = m0.f3d_mat
    mat1 = m1.f3d_mat

    checks = [
        tex_equals(mat0.tex0, mat1.tex0),
        tex_equals(mat0.tex1, mat1.tex1),
        mat0.draw_layer.oot == mat1.draw_layer.oot,
        mat0.env_color[:] == mat1.env_color[:],
        mat0.is_multi_tex == mat1.is_multi_tex,
        mat0.prim_color[:] == mat1.prim_color[:],
        mat0.tex_scale[:] == mat1.tex_scale[:],
        mat0.use_default_lighting == mat1.use_default_lighting,
        mat0.use_global_fog == mat1.use_global_fog,
        combiner_equals(mat0.combiner1, mat1.combiner1),
        combiner_equals(mat0.combiner2, mat1.combiner2),
    ]

    print(''.join(['1' if check else '0' for check in checks]))

    return all(checks)


def write_file(filepath):
    # objs = bpy.context.scene.objects
    #
    # count = 0
    #
    # for obj in objs:
    #     for slot in obj.material_slots:
    #         mat = slot.material
    #
    #         for obj1 in objs:
    #             if obj == obj1:
    #                 continue
    #
    #             for slot1 in obj1.material_slots:
    #                 mat1 = slot1.material
    #
    #                 if mat == mat1:
    #                     continue
    #
    #                 if f3d_mat_equals(mat, mat1):
    #                     count += 1
    #                     print(count)
    #                     slot1.material = mat

    for mesh in bpy.data.meshes:
        col_layer = mesh.vertex_colors.get('Col')
        if col_layer is not None:
            col_layer.name = 'Color'

    ob = bpy.context.object

    for slot in ob.material_slots:
        mat = slot.material

        if not mat.is_f3d:
            continue

        name = mat.name

        vertex_colors = not mat.f3d_mat.rdp_settings.is_geo_mode_on("g_lighting")

        texture = mat.f3d_mat.tex0.tex
        x_clamp = mat.f3d_mat.tex0.S.clamp
        x_mirror = mat.f3d_mat.tex0.S.mirror
        y_clamp = mat.f3d_mat.tex0.T.clamp
        y_mirror = mat.f3d_mat.tex0.T.mirror

        env_color = mat.f3d_mat.env_color

        backface_culling = mat.f3d_mat.rdp_settings.g_cull_back

        transparent = mat.f3d_mat.draw_layer.oot != 'Opaque'

        cutout = mat.f3d_mat.combiner1.D_alpha == 'TEXEL0'

        mat.is_f3d = False

        link_4b_material_library()

        mat2 = bpy.data.materials["4b_material_library"]
        material = mat2.copy()
        material.name = name
        bpy.data.materials.remove(mat2)

        slot.material = material
        p = material.props_4b

        p.enable_vertex_colors = vertex_colors

        if texture is not None:
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

        p.enable_backface_culling = backface_culling
        p.transparency_mode = 'cutout' if cutout else 'transparent'

        if cutout:
            p.enable_transparency = True

        if transparent:
            p.enable_transparency = True
            p.translucency = env_color[3]

        p.enable_overlay_color = True
        p.overlay_color = env_color

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
