import bpy


def update(_self, _context):
    """TODO: Implement"""


class Props(bpy.types.PropertyGroup):
    fog_start: bpy.props.FloatProperty(name="Fog Start", update=update)
    fog_length: bpy.props.FloatProperty(name="Fog Length", update=update)

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
    bl_label = "4B Globals"
    bl_idname = "OBJECT_PT_4B_GLOBALS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"

    def draw(self, _context):
        layout = self.layout
        layout.label(text="Global Settings")


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
