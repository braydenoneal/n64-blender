bl_info = {
    "name": "4B Materials",
    "author": "Brayden O'Neal",
    "version": (0, 0, 0),
    "blender": (2, 80, 0),
    "location": "Properties > Material > 4B Material",
    "description": "4B Materials (borrowing heavily from Fast64)",
    "category": "Material",
}

import os

import bpy


def link_4b_material_library():
    # TODO: Development only
    directory = "C:\\Users\\happy\\projects\\blender-addon\\4b_material_library.blend"
    # directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "4b_material_library.blend")
    prev_mode = bpy.context.mode

    if prev_mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    with bpy.data.libraries.load(directory) as (data_from, data_to):
        dir_mat = os.path.join(directory, "Material")
        dir_node = os.path.join(directory, "NodeTree")

        for mat in data_from.materials:
            if mat is not None:
                bpy.ops.wm.link(filepath=os.path.join(dir_mat, mat), directory=dir_mat, filename=mat)

        if bpy.context.scene.get("4b_lib_dir") != dir_node:
            for node_group in data_from.node_groups:
                if node_group is not None:
                    bpy.ops.wm.link(filepath=os.path.join(dir_node, node_group), directory=dir_node,
                                    filename=node_group)

            bpy.context.scene["4b_lib_dir"] = dir_node


def create_globals_node_group():
    group = bpy.data.node_groups.get("Globals")

    if group:
        return

    group = bpy.data.node_groups.new("Globals", "ShaderNodeTree")
    group.nodes.new("NodeGroupOutput")

    interface = group.interface

    interface.new_socket("Fog Start", socket_type="NodeSocketFloat", in_out="OUTPUT")
    interface.new_socket("Fog Length", socket_type="NodeSocketFloat", in_out="OUTPUT")
    interface.new_socket("Fog Color", socket_type="NodeSocketColor", in_out="OUTPUT")
    interface.new_socket("Ambient Color", socket_type="NodeSocketColor", in_out="OUTPUT")
    interface.new_socket("Light Color", socket_type="NodeSocketColor", in_out="OUTPUT")
    interface.new_socket("Light Direction", socket_type="NodeSocketVector", in_out="OUTPUT")

    # Set outputs from render settings
    # sceneOutputs: NodeGroupOutput = group.nodes["Group Output"]
    # renderSettings: "Fast64RenderSettings_Properties" = bpy.context.scene.fast64.renderSettings
    #
    # update_scene_props_from_render_settings(sceneOutputs, renderSettings)


def create_globals(material):
    tree = material.node_tree

    create_globals_node_group()

    node = tree.nodes.new(type="ShaderNodeGroup")
    node.name = "Globals"
    node.location = (-368, -41)
    node.node_tree = bpy.data.node_groups["Globals"]

    tree.links.new(node.outputs["Fog Start"], tree.nodes["Fog Start"].inputs[0])
    tree.links.new(node.outputs["Fog Length"], tree.nodes["Fog Length"].inputs[0])
    tree.links.new(node.outputs["Fog Color"], tree.nodes["Fog Color"].inputs[0])
    tree.links.new(node.outputs["Ambient Color"], tree.nodes["Ambient Color"].inputs[0])
    tree.links.new(node.outputs["Light Color"], tree.nodes["Light Color"].inputs[0])
    tree.links.new(node.outputs["Light Direction"], tree.nodes["Light Direction"].inputs[0])


def create_4b_material(obj):
    link_4b_material_library()

    mat = bpy.data.materials["4b_material_library"]
    material = mat.copy()
    material.name = "4b_material"
    bpy.data.materials.remove(mat)

    create_globals(material)

    if obj is not None:
        if "Color" not in obj.data.attributes:
            obj.data.color_attributes.new("Color", "FLOAT_COLOR", "CORNER")

        obj.data.materials.append(material)
        if bpy.context.object is not None:
            bpy.context.object.active_material_index = len(obj.material_slots) - 1

    material.is_4b = True

    return material


def reset_material(context, material):
    nodes = material.node_tree.nodes

    shader_settings = nodes["Shader"]
    shader_inputs = shader_settings.inputs

    shader_inputs["Enable Solid Color"].default_value = context.scene.props.enable_solid_color

    shader_inputs["Enable Transparency"].default_value = (context.scene.props.transparency_mode != "opaque" and
                                                          not context.scene.props.enable_solid_color)

    transparency_mode_to_blend_method = {
        "opaque": "OPAQUE",
        "cutout": "CLIP",
        "transparent": "BLEND"
    }

    material.blend_method = transparency_mode_to_blend_method[context.scene.props.transparency_mode]

    material.use_backface_culling = context.scene.props.enable_backface_culling

    shader_inputs["Enable Fog"].default_value = context.scene.props.enable_fog
    shader_inputs["Enable Vertex Colors"].default_value = context.scene.props.enable_vertex_colors

    shader_inputs["Enable Overlay Color"].default_value = context.scene.props.enable_overlay_color

    shader_inputs["Solid Color"].default_value = context.scene.props.solid_color
    shader_inputs["Overlay Color"].default_value = context.scene.props.overlay_color

    for i in ["0, 0", "0, 1", "1, 0", "1, 1"]:
        texture = nodes[f"Texture {i}"]
        texture.image = context.scene.props.texture

    filter_settings = nodes["Bilinear UV"]
    filter_inputs = filter_settings.inputs

    width, height = context.scene.props.texture.size
    filter_inputs["Width"].default_value = width
    filter_inputs["Height"].default_value = height

    x_bounds = context.scene.props.x_bounds

    filter_inputs["Clamp X"].default_value = x_bounds == "extend"
    filter_inputs["Repeat X"].default_value = x_bounds == "repeat"
    filter_inputs["Mirror X"].default_value = x_bounds == "mirror"

    y_bounds = context.scene.props.y_bounds

    filter_inputs["Clamp Y"].default_value = y_bounds == "extend"
    filter_inputs["Repeat Y"].default_value = y_bounds == "repeat"
    filter_inputs["Mirror Y"].default_value = y_bounds == "mirror"


class Create4BMaterial(bpy.types.Operator):
    bl_idname = "object.create_4b_mat"
    bl_label = "Create 4B Material"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    def execute(self, context):
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, "No active object selected.")
        else:
            material = create_4b_material(obj)
            reset_material(context, material)
            self.report({"INFO"}, "Created new 4B material.")
        return {"FINISHED"}


def update(_self, context):
    reset_material(context, context.material)


class Props(bpy.types.PropertyGroup):
    enable_solid_color: bpy.props.BoolProperty(name="Enable Solid Color", default=False, update=update)
    solid_color: bpy.props.FloatVectorProperty(
        name="Solid Color",
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(1, 1, 1, 1),
        update=update
    )

    texture: bpy.props.PointerProperty(name="Texture", type=bpy.types.Image, update=update)

    bound_options = [
        ("repeat", "Repeat", ""),
        ("extend", "Extend", ""),
        ("clip", "Clip", ""),
        ("mirror", "Mirror", "")
    ]

    x_bounds: bpy.props.EnumProperty(name="X Bounds", items=bound_options, default="repeat", update=update)
    y_bounds: bpy.props.EnumProperty(name="Y Bounds", items=bound_options, default="repeat", update=update)

    transparency_options = [
        ("opaque", "Opaque", ""),
        ("cutout", "Cutout", ""),
        ("transparent", "Transparent", ""),
    ]

    transparency_mode: bpy.props.EnumProperty(name="Transparency Mode", items=transparency_options, default="opaque",
                                              update=update)
    enable_backface_culling: bpy.props.BoolProperty(name="Enable Backface Culling", default=True, update=update)

    enable_fog: bpy.props.BoolProperty(name="Enable Fog", default=True, update=update)
    enable_vertex_colors: bpy.props.BoolProperty(name="Enable Vertex Colors", default=True, update=update)

    enable_overlay_color: bpy.props.BoolProperty(name="Enable Overlay Color", default=False, update=update)
    overlay_color: bpy.props.FloatVectorProperty(
        name="Overlay Color",
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(1, 1, 1, 1),
        update=update
    )


class Panel(bpy.types.Panel):
    bl_label = "4B Material"
    bl_idname = "MATERIAL_PT_4B_Inspector"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        props = context.scene.props

        layout.operator(Create4BMaterial.bl_idname)

        if not context.material or not context.material.is_4b:
            layout.label(text="This is not a 4B material.")
            return

        layout.prop(props, "enable_solid_color")
        if props.enable_solid_color:
            layout.prop(props, "solid_color")

        if not props.enable_solid_color:
            layout.template_ID(props, "texture", open="image.open", new="image.new")

            if props.texture is not None:
                width, height = props.texture.size
                layout.label(text=f"Size: {width}x{height}")

            layout.prop(props, "x_bounds")
            layout.prop(props, "y_bounds")

            layout.prop(props, "transparency_mode")

        layout.prop(props, "enable_backface_culling")

        layout.prop(props, "enable_fog")
        layout.prop(props, "enable_vertex_colors")

        layout.prop(props, "enable_overlay_color")
        if props.enable_overlay_color:
            layout.prop(props, "overlay_color")


def register():
    bpy.types.Material.is_4b = bpy.props.BoolProperty()
    bpy.utils.register_class(Panel)
    bpy.utils.register_class(Props)
    bpy.utils.register_class(Create4BMaterial)
    bpy.types.Scene.props = bpy.props.PointerProperty(type=Props)


def unregister():
    del bpy.types.Material.is_4b
    bpy.utils.unregister_class(Panel)
    bpy.utils.unregister_class(Props)
    bpy.utils.unregister_class(Create4BMaterial)
    del bpy.types.Scene.props


if __name__ == "__main__":
    register()
