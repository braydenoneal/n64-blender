import json
from typing import Any

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper


def rgb(obj_color):
    return {
        'r': obj_color[0],
        'g': obj_color[1],
        'b': obj_color[2],
    }


def rgba(obj_color):
    return {
        'r': obj_color[0],
        'g': obj_color[1],
        'b': obj_color[2],
        'a': obj_color[3],
    }


def xyz(obj_color):
    return {
        'x': obj_color[0],
        'y': obj_color[1],
        'z': obj_color[2],
    }


def write_file(filepath):
    scene_materials = {}

    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH':
            continue

        material_slots = []

        for slot in ob.material_slots:
            material_slots.append(slot.name)

            if not slot.material.is_4b or slot.name in scene_materials.keys():
                continue

            p = slot.material.props_4b
            j = {}

            if p.enable_solid_color:
                j['solid_color'] = rgb(p.solid_color)
            else:
                j['texture'] = {
                    'name': '.'.join(p.texture.name.split('.')[:-1]),
                    'bounds': {'x': p.x_bounds, 'y': p.y_bounds},
                    'scale': {'x': p.x_scale, 'y': p.y_scale},
                    'shift': {'x': p.x_shift, 'y': p.y_shift},
                }

            j['backface_culling'] = p.enable_backface_culling

            if p.enable_transparency:
                j['transparency'] = {
                    'mode': p.transparency_mode,
                    'translucency': p.translucency,
                }

            j['vertex_colors'] = p.enable_vertex_colors

            if p.enable_overlay_color:
                j['overlay_color'] = rgb(p.overlay_color)

            if p.enable_ambient_color:
                j['ambient_color'] = True if p.override_ambient_color == 'override' else rgb(p.ambient_color)

            if p.enable_light_color:
                j['light_color'] = True if p.override_light_color == 'override' else {
                    'color': rgb(p.light_color),
                    'direction': xyz(p.light_direction),
                }

            if p.enable_fog:
                j['fog'] = True if p.override_fog == 'override' else {
                    'start': p.fog_start,
                    'length': p.fog_length,
                    'color': rgb(p.fog_color),
                }

            j['faces'] = []

            scene_materials[slot.name] = j

        vertices = ob.data.vertices
        uvs = ob.data.uv_layers['UVMap'].data

        if 'Color' not in ob.data.color_attributes.keys():
            continue

        color = ob.data.color_attributes['Color'].data

        for face in ob.data.polygons:
            if len(face.vertices) != 3:
                continue

            material_name = material_slots[face.material_index]

            if material_name not in scene_materials.keys():
                continue

            material = scene_materials[material_name]
            face_json = {}

            for vertex_name, vertex_index, loop_index in zip(('a', 'b', 'c'), face.vertices, face.loop_indices):
                vertex = vertices[vertex_index].co

                vertex_json: dict[str, Any] = {
                    'x': vertex.x,
                    'y': vertex.y,
                    'z': vertex.z,
                }

                if 'texture' in material.keys():
                    uv = uvs[loop_index].uv

                    vertex_json['u'] = uv.x
                    vertex_json['v'] = uv.y

                if material['vertex_colors']:
                    if 'transparency' in material.keys():
                        vertex_json['color'] = rgba(color[loop_index].color)
                    else:
                        vertex_json['color'] = rgb(color[loop_index].color)

                face_json[vertex_name] = vertex_json

            normal = face.normal
            face_json['normal'] = {
                'x': normal.x,
                'y': normal.y,
                'z': normal.z,
            }

            material['faces'].append(face_json)

    with open(filepath, 'w') as file:
        file.write(json.dumps(scene_materials, indent=2))

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


def menu_func_export(self, context):
    self.layout.operator(ExportSomeData.bl_idname, text="4B Materials model (.json)")


def register():
    bpy.utils.register_class(ExportSomeData)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportSomeData)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
