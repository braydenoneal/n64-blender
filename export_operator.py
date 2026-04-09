import json
import math
from typing import Any

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from mathutils import Matrix, Vector


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
    scene = bpy.context.scene

    if scene is None:
        return {'CANCELLED'}

    bones = {}

    for ob in scene.objects:
        if ob.type != 'ARMATURE':
            continue

        for bone in ob.data.bones:
            bones[bone.name] = {
                'parent': bone.parent.name,
            } if bone.parent is not None else {}

            head = bone.head_local - ob.location
            tail = bone.tail_local - ob.location

            bones[bone.name] |= {
                'head': vec3(head),
                'tail': vec3(tail),
                'frames': {},
            }

        prev_action = ob.animation_data.action
        prev_frame = scene.frame_current_final

        for action in bpy.data.actions:
            ob.animation_data.action = action

            for curve in action.fcurves:
                if not curve.data_path.startswith('pose.bones['):
                    continue

                bone_name = curve.data_path.split('"')[1]

                if bone_name not in bones.keys():
                    continue

                if action.name not in bones[bone_name]['frames']:
                    bones[bone_name]['frames'][action.name] = []

                frames = [frame['frame'] for frame in bones[bone_name]['frames'][action.name]]

                for index, keyframe in curve.keyframe_points.items():
                    frame = keyframe.co.x

                    if frame in frames:
                        continue

                    scene.frame_set(math.floor(frame), subframe=frame % 1)
                    pose_bone = ob.pose.bones[bone_name]

                    matrix = z_up_to_y_up(pose_bone.matrix_channel)

                    if pose_bone.parent is not None:
                        matrix = z_up_to_y_up(pose_bone.parent.matrix_channel).inverted() @ matrix

                    bones[bone_name]['frames'][action.name].append({
                        'frame': frame,
                        'matrix': mat3(matrix),
                        'translation': vec3(pose_bone.location, False)
                    })

        ob.animation_data.action = prev_action
        scene.frame_set(math.floor(prev_frame), subframe=prev_frame % 1)

    materials = {}

    for ob in scene.objects:
        if ob.type != 'MESH':
            continue

        material_slots = []

        for slot in ob.material_slots:
            material_slots.append(slot.name)

            if not slot.material.is_4b or slot.name in materials.keys():
                continue

            p = slot.material.props_4b
            j = {}

            if p.enable_solid_color:
                j['solid_color'] = rgb(p.solid_color)
            else:
                j['texture'] = {
                    'name': p.texture.name,
                    'bounds': {'x': p.x_bounds, 'y': p.y_bounds},
                    'scale': {'x': p.x_scale, 'y': p.y_scale},
                    'shift': {'x': p.x_shift, 'y': p.y_shift},
                }

            if p.enable_texture_b:
                j['texture_b'] = {
                    'name': p.texture_b.name,
                    'bounds': {'x': p.x_bounds_b, 'y': p.y_bounds_b},
                    'scale': {'x': p.x_scale_b, 'y': p.y_scale_b},
                    'shift': {'x': p.x_shift_b, 'y': p.y_shift_b},
                    'mix': p.texture_mix,
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
                j['ambient_color'] = True if p.override_ambient_color != 'override' else rgb(p.ambient_color)

            if p.enable_light_color:
                j['light_color'] = True if p.override_light_color != 'override' else {
                    'color': rgb(p.light_color),
                    'direction': vec3(p.light_direction),
                }

            if p.enable_fog:
                j['fog'] = True if p.override_fog != 'override' else {
                    'start': p.fog_start,
                    'length': p.fog_length,
                    'color': rgb(p.fog_color),
                }

            j['faces'] = []

            materials[slot.name] = j

        vertices = ob.data.vertices
        uvs = ob.data.uv_layers['UVMap'].data

        if 'Color' not in ob.data.color_attributes.keys():
            continue

        color = ob.data.color_attributes['Color'].data

        for face in ob.data.polygons:
            if len(face.vertices) != 3:
                continue

            material_name = material_slots[face.material_index]

            if material_name not in materials.keys():
                continue

            material = materials[material_name]
            face_json = {}

            for vertex_name, vertex_index, loop_index in zip(('a', 'b', 'c'), face.vertices, face.loop_indices):
                vertex = vertices[vertex_index]

                vertex_json: dict[str, Any] = {
                    'vertex': vec3(vertex.co),
                }

                if face.use_smooth:
                    vertex_json['normal'] = vec3(vertex.normal)

                if 'texture' in material.keys():
                    uv = uvs[loop_index].uv

                    vertex_json['u'] = uv.x
                    vertex_json['v'] = uv.y

                if material['vertex_colors']:
                    if 'transparency' in material.keys():
                        vertex_json['color'] = rgba(color[loop_index].color)
                    else:
                        vertex_json['color'] = rgb(color[loop_index].color)

                weights = []

                for group in vertices[vertex_index].groups:
                    name = ob.vertex_groups[group.group].name

                    if name not in bones.keys():
                        continue

                    if len(weights) >= 4:
                        break

                    weights.append({
                        'bone': name,
                        'weight': group.weight
                    })

                if len(weights) > 0:
                    vertex_json['weights'] = weights

                face_json[vertex_name] = vertex_json

            if not face.use_smooth:
                face_json['normal'] = vec3(face.normal)

            material['faces'].append(face_json)

    json_data = {
        'materials': materials,
        'bones': bones,
    }

    with open(filepath, 'w') as file:
        file.write(json.dumps(json_data, indent=2))

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
