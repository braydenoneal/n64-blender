import json
import math
from typing import Any

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from mathutils import Matrix


def matrix_to_glm(matrix: Matrix):
    return [col[:] for col in matrix.col]


def write_file(filepath):
    scene = bpy.context.scene

    bones = {}

    for ob in scene.objects:
        if ob.type != 'ARMATURE':
            continue

        for bone in ob.data.bones:
            bones[bone.name] = {
                'parent': bone.parent.name,
            } if bone.parent is not None else {}

            head = bone.head_local - ob.location

            bones[bone.name] |= {
                'head': [head[:3]],
                'frames': [],
            }

        for curve in ob.animation_data.action.fcurves:
            if not curve.data_path.startswith('pose.bones['):
                continue

            bone_name = curve.data_path.split('"')[1]

            if bone_name not in bones.keys():
                continue

            frames = [frame['frame'] for frame in bones[bone_name]['frames']]

            for index, keyframe in curve.keyframe_points.items():
                frame = keyframe.co.x

                if frame not in frames:
                    scene.frame_set(math.floor(frame), subframe=frame % 1)
                    pose_bone = ob.pose.bones[bone_name]

                    # axis, roll = pose_bone.bone.AxisRollFromMatrix(pose_bone.matrix.to_3x3())
                    # roll_matrix = Matrix.Rotation(roll, 4, axis)
                    # print(pose_bone.matrix_channel)
                    # matrix = pose_bone.matrix_channel @ roll_matrix
                    # print(matrix)
                    #
                    # matrix = pose_bone.bone.matrix.to_4x4().inverted() @ pose_bone.matrix
                    # matrix = pose_bone.bone.matrix_local.inverted() @ pose_bone.matrix
                    # matrix = pose_bone.matrix_basis  # _channel

                    matrix_channel_no_parent = pose_bone.matrix_channel

                    if pose_bone.parent is not None:
                        matrix_channel_no_parent = pose_bone.parent.matrix_channel.inverted() @ matrix_channel_no_parent

                    bones[bone_name]['frames'].append({
                        'frame': frame,
                        'matrix': matrix_to_glm(pose_bone.matrix),
                        'matrix_basis': matrix_to_glm(pose_bone.matrix_basis),
                        'matrix_channel': matrix_to_glm(pose_bone.matrix_channel),
                        'matrix_channel_no_parent': matrix_to_glm(matrix_channel_no_parent),
                        'bone_matrix': matrix_to_glm(pose_bone.bone.matrix),
                        'bone_matrix_local': matrix_to_glm(pose_bone.bone.matrix_local),
                    })

    faces = []

    for ob in scene.objects:
        if ob.type != 'MESH':
            continue

        vertices = ob.data.vertices

        for face in ob.data.polygons:
            if len(face.vertices) != 3:
                continue

            face_json = {}

            for vertex_name, vertex_index, loop_index in zip(('a', 'b', 'c'), face.vertices, face.loop_indices):
                vertex = vertices[vertex_index].co

                vertex_json: dict[str, Any] = {
                    'x': vertex.x,
                    'y': vertex.y,
                    'z': vertex.z,
                }

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

            normal = face.normal

            face_json['normal'] = {
                'x': normal.x,
                'y': normal.y,
                'z': normal.z,
            }

            faces.append(face_json)

    json_data = {
        'faces': faces,
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
