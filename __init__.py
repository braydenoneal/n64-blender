from .module_loader import refresh

refresh()

bl_info = {
    "name": "4B Materials",
    "author": "Brayden O'Neal",
    "version": (0, 0, 0),
    "blender": (2, 80, 0),
    "location": "Properties > Material > 4B Material",
    "description": "4B Materials (borrowing heavily from Fast64)",
    "category": "Material",
}

from . import material_panel
from . import globals_panel
from . import export_operator


def register():
    material_panel.register()
    globals_panel.register()
    export_operator.register()


def unregister():
    material_panel.unregister()
    globals_panel.unregister()
    export_operator.unregister()


if __name__ == "__main__":
    register()
