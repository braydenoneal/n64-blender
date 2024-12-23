import os

import bpy

from .globals_panel import update_globals_node_group


def link_4b_material_library():
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "4b_material_library.blend")
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

    update_globals_node_group()


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


def update_material(material):
    nodes = material.node_tree.nodes
    props = material.props_4b

    for i in ["0, 0", "0, 1", "1, 0", "1, 1"]:
        texture = nodes[f"Texture {i}"]
        texture.image = props.texture if not props.enable_solid_color else None

    filter_settings = nodes["Bilinear UV"]
    filter_inputs = filter_settings.inputs

    if props.texture and not props.enable_solid_color:
        width, height = props.texture.size
        filter_inputs["Width"].default_value = width
        filter_inputs["Height"].default_value = height
    else:
        filter_inputs["Width"].default_value = 0
        filter_inputs["Height"].default_value = 0

    x_bounds = props.x_bounds

    filter_inputs["Clamp X"].default_value = x_bounds == "extend"
    filter_inputs["Repeat X"].default_value = x_bounds == "repeat"
    filter_inputs["Mirror X"].default_value = x_bounds == "mirror"

    y_bounds = props.y_bounds

    filter_inputs["Clamp Y"].default_value = y_bounds == "extend"
    filter_inputs["Repeat Y"].default_value = y_bounds == "repeat"
    filter_inputs["Mirror Y"].default_value = y_bounds == "mirror"

    shader_settings = nodes["Shader"]
    shader_inputs = shader_settings.inputs

    shader_inputs["Enable Transparency"].default_value = props.transparency_mode != "opaque"

    transparency_mode_to_blend_method = {
        "opaque": "OPAQUE",
        "cutout": "CLIP",
        "transparent": "BLEND"
    }

    material.blend_method = transparency_mode_to_blend_method[props.transparency_mode]

    material.use_backface_culling = props.enable_backface_culling

    shader_inputs["Translucency"].default_value = props.translucency

    shader_inputs["Solid Color"].default_value = props.solid_color

    shader_inputs["Enable Solid Color"].default_value = props.enable_solid_color

    shader_inputs["Enable Vertex Colors"].default_value = props.enable_vertex_colors

    shader_inputs["Overlay Color"].default_value = props.overlay_color

    shader_inputs["Enable Overlay Color"].default_value = props.enable_overlay_color

    shader_inputs["Enable Ambient Color"].default_value = props.enable_ambient_color

    shader_inputs["Enable Light Color"].default_value = props.enable_light_color

    shader_inputs["Override Ambient Color"].default_value = props.ambient_color

    shader_inputs["Enable Override Ambient Color"].default_value = props.override_ambient_color

    shader_inputs["Override Light Color"].default_value = props.light_color

    shader_inputs["Override Light Direction"].default_value = props.light_direction

    shader_inputs["Enable Override Light Color"].default_value = props.override_light_color

    shader_inputs["Enable Fog"].default_value = props.enable_fog

    shader_inputs["Override Fog Start"].default_value = props.fog_start

    shader_inputs["Override Fog Length"].default_value = props.fog_length

    shader_inputs["Override Fog Color"].default_value = props.fog_color

    shader_inputs["Enable Override Fog"].default_value = props.override_fog


class Create4BMaterial(bpy.types.Operator):
    bl_idname = "object.create_4b_mat"
    bl_label = "Create 4B Material"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    def execute(self, _context):
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, "No active object selected.")
        else:
            material = create_4b_material(obj)
            update_material(material)
        return {"FINISHED"}


def update(_self, context):
    update_material(context.material)


class Props(bpy.types.PropertyGroup):
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

    translucency: bpy.props.FloatProperty(name="Translucency",
                                          description="How much light passes through. 0 is fully opaque and 1 is fully transparent. Transparency mode must be set to \"Transparent\"",
                                          min=0, max=1, step=1, update=update)

    enable_backface_culling: bpy.props.BoolProperty(name="Enable Backface Culling", default=True, update=update)

    enable_solid_color: bpy.props.BoolProperty(name="Enable Solid Color", default=False, update=update)
    solid_color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(1, 1, 1, 1),
        update=update
    )

    enable_vertex_colors: bpy.props.BoolProperty(name="Enable Vertex Colors", default=True, update=update)

    enable_overlay_color: bpy.props.BoolProperty(name="Enable Overlay Color", default=False, update=update)
    overlay_color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(1, 1, 1, 1),
        update=update
    )

    enable_ambient_color: bpy.props.BoolProperty(name="Enable Ambient Color", default=True, update=update)
    override_ambient_color: bpy.props.BoolProperty(name="Override Ambient Color", default=False, update=update)
    ambient_color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(1, 1, 1, 1),
        update=update
    )

    enable_light_color: bpy.props.BoolProperty(name="Enable Light Color", default=True, update=update)
    override_light_color: bpy.props.BoolProperty(name="Override Light Color", default=False, update=update)
    light_color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(1, 1, 1, 1),
        update=update
    )
    light_direction: bpy.props.FloatVectorProperty(
        size=3,
        min=-1,
        max=1,
        default=(0, 0, 1),
        update=update
    )

    enable_fog: bpy.props.BoolProperty(name="Enable Fog", default=True, update=update)
    override_fog: bpy.props.BoolProperty(name="Override Fog", default=False, update=update)
    fog_start: bpy.props.FloatProperty(name="Fog Start", min=0, step=100, default=16, update=update)
    fog_length: bpy.props.FloatProperty(name="Fog Length", min=0, step=100, default=32, update=update)
    fog_color: bpy.props.FloatVectorProperty(
        name="Fog Color",
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(1, 1, 1, 1),
        update=update
    )


class Panel(bpy.types.Panel):
    bl_label = "4B Material"
    bl_idname = "MATERIAL_PT_4B_INSPECTOR"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        layout = self.layout

        layout.operator(Create4BMaterial.bl_idname)

        if not context.material:
            return

        if not context.material.is_4b:
            layout.label(text="This is not a 4B material.")
            return

        props = context.material.props_4b

        box = layout.box()
        box.enabled = not props.enable_solid_color

        box.template_ID(props, "texture", open="image.open", new="image.new")

        if props.texture is not None:
            width, height = props.texture.size
            box.label(text=f"Size: {width}x{height}")
        else:
            box.label(text="Size:")

        box.prop(props, "x_bounds")
        box.prop(props, "y_bounds")

        split = layout.split()
        col = split.column()
        col.prop(props, "enable_solid_color")
        col = split.column()
        col.enabled = props.enable_solid_color
        col.prop(props, "solid_color", text="")

        box = layout.box()

        box.label(text="Transparency Mode")
        box.prop(props, "transparency_mode", expand=True)

        box.prop(props, "enable_backface_culling")

        row = box.row()
        row.enabled = props.transparency_mode == "transparent"
        row.prop(props, "translucency", slider=True)

        layout.prop(props, "enable_vertex_colors")

        split = layout.split()
        col = split.column()
        col.prop(props, "enable_overlay_color")
        col = split.column()
        col.enabled = props.enable_overlay_color
        col.prop(props, "overlay_color", text="")

        box = layout.box()

        box.prop(props, "enable_ambient_color")
        split = box.split()
        split.enabled = props.enable_ambient_color
        col = split.column()
        col.prop(props, "override_ambient_color")
        col = split.column()
        col.enabled = props.override_ambient_color
        col.prop(props, "ambient_color", text="")

        box = layout.box()

        box.prop(props, "enable_light_color")
        split = box.split()
        split.enabled = props.enable_light_color
        col = split.column()
        col.prop(props, "override_light_color")
        col = split.column()
        col.enabled = props.override_light_color
        col.prop(props, "light_color", text="")
        row = box.row()
        row.enabled = props.override_light_color and props.enable_light_color
        row.prop(props, "light_direction", text="")

        box = layout.box()

        box.prop(props, "enable_fog")
        split = box.split()
        split.enabled = props.enable_fog
        col = split.column()
        col.prop(props, "override_fog")
        col = split.column()
        col.enabled = props.override_fog
        col.prop(props, "fog_color", text="")
        row = box.row()
        row.enabled = props.override_fog and props.enable_fog
        row.prop(props, "fog_start")
        row = box.row()
        row.enabled = props.override_fog and props.enable_fog
        row.prop(props, "fog_length")


def register():
    bpy.types.Material.is_4b = bpy.props.BoolProperty()
    bpy.utils.register_class(Panel)
    bpy.utils.register_class(Props)
    bpy.utils.register_class(Create4BMaterial)
    bpy.types.Material.props_4b = bpy.props.PointerProperty(type=Props)


def unregister():
    del bpy.types.Material.is_4b
    bpy.utils.unregister_class(Panel)
    bpy.utils.unregister_class(Props)
    bpy.utils.unregister_class(Create4BMaterial)
    del bpy.types.Material.props_4b
