import bpy


class ResetGlobals(bpy.types.Operator):
    bl_idname = "object.reset_4b_globals"
    bl_label = "Reset 4B Global Settings"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    def execute(self, _context):
        del bpy.context.scene["globals_4b"]
        update_globals_node_group()
        self.report({"INFO"}, "Reset 4B global settings.")
        return {"FINISHED"}


def update_globals_node_group():
    outputs = bpy.data.node_groups.get("Globals").nodes["Group Output"]
    global_settings = bpy.context.scene.globals_4b

    outputs.inputs["Fog Start"].default_value = global_settings.fog_start

    outputs.inputs["Fog Length"].default_value = global_settings.fog_length

    outputs.inputs["Fog Color"].default_value = global_settings.fog_color

    outputs.inputs["Ambient Color"].default_value = global_settings.ambient_color

    outputs.inputs["Light Color"].default_value = global_settings.light_color

    outputs.inputs["Light Direction"].default_value = global_settings.light_direction


def update(_self, _context):
    update_globals_node_group()


class Props(bpy.types.PropertyGroup):
    fog_start: bpy.props.FloatProperty(name="Fog Start", min=0, default=16, update=update)

    fog_length: bpy.props.FloatProperty(name="Fog Length", min=0, default=32, update=update)

    fog_color: bpy.props.FloatVectorProperty(
        name="Fog Color",
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(1, 1, 1, 1),
        update=update
    )

    ambient_color: bpy.props.FloatVectorProperty(
        name="Ambient Color",
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(0.5, 0.5, 0.5, 1),
        update=update
    )

    light_color: bpy.props.FloatVectorProperty(
        name="Light Color",
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(1, 1, 1, 1),
        update=update
    )

    light_direction: bpy.props.FloatVectorProperty(
        name="Light Direction",
        size=3,
        min=-1,
        max=1,
        default=(0, 0, 1),
        update=update
    )


class Panel(bpy.types.Panel):
    bl_label = "4B Globals"
    bl_idname = "OBJECT_PT_4B_GLOBALS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"

    def draw(self, context):
        layout = self.layout
        props = context.scene.globals_4b

        layout.label(text="4B Global Settings")

        layout.prop(props, "fog_start")

        layout.prop(props, "fog_length")

        layout.prop(props, "fog_color")

        layout.prop(props, "ambient_color")

        layout.prop(props, "light_color")

        layout.label(text="Light Direction")
        layout.prop(props, "light_direction", text="")

        layout.operator(ResetGlobals.bl_idname)


def draw_globals_panel(self, _context):
    layout = self.layout
    layout.popover(Panel.bl_idname)


def register():
    bpy.utils.register_class(Panel)
    bpy.utils.register_class(Props)
    bpy.utils.register_class(ResetGlobals)
    bpy.types.VIEW3D_HT_header.append(draw_globals_panel)
    bpy.types.Scene.globals_4b = bpy.props.PointerProperty(type=Props)


def unregister():
    bpy.utils.unregister_class(Panel)
    bpy.utils.unregister_class(Props)
    bpy.utils.unregister_class(ResetGlobals)
    bpy.types.VIEW3D_HT_header.remove(draw_globals_panel)
    del bpy.types.Scene.globals_4b
