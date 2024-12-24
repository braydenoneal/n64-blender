import bpy


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
    fog_start: bpy.props.FloatProperty(name="Start", min=0, step=100, default=16, update=update)

    fog_length: bpy.props.FloatProperty(name="Length", min=0, step=100, default=32, update=update)

    fog_color: bpy.props.FloatVectorProperty(
        name="Color",
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(1, 1, 1, 1),
        update=update
    )

    ambient_color: bpy.props.FloatVectorProperty(
        name="Color",
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(0.5, 0.5, 0.5, 1),
        update=update
    )

    light_color: bpy.props.FloatVectorProperty(
        name="Color",
        subtype="COLOR",
        size=4,
        min=0,
        max=1,
        default=(1, 1, 1, 1),
        update=update
    )

    light_direction: bpy.props.FloatVectorProperty(
        name="Direction",
        size=3,
        min=-1,
        max=1,
        default=(0, 0, 1),
        update=update
    )


class Panel(bpy.types.Panel):
    bl_label = "4B Settings"
    bl_idname = "OBJECT_PT_4B_GLOBALS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"

    def draw(self, context):
        layout = self.layout
        props = context.scene.globals_4b

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.label(text="Ambient Light")
        layout.prop(props, "ambient_color")
        layout.label()

        layout.label(text="Directional Light")

        layout.prop(props, "light_color")
        layout.prop(props, "light_direction")

        layout.label(text="Fog")
        col = layout.column(align=True)
        col.prop(props, "fog_start")
        col.prop(props, "fog_length")
        layout.prop(props, "fog_color")
        layout.label()



def draw_globals_panel(self, _context):
    layout = self.layout
    layout.popover(Panel.bl_idname)


def register():
    bpy.utils.register_class(Panel)
    bpy.utils.register_class(Props)
    bpy.types.VIEW3D_HT_header.append(draw_globals_panel)
    bpy.types.Scene.globals_4b = bpy.props.PointerProperty(type=Props)


def unregister():
    bpy.utils.unregister_class(Panel)
    bpy.utils.unregister_class(Props)
    bpy.types.VIEW3D_HT_header.remove(draw_globals_panel)
    del bpy.types.Scene.globals_4b
