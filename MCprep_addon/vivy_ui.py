import json
import bpy
from .materials import vivy_materials

class VivyNodeToolProps(bpy.types.PropertyGroup):
    material_name: bpy.props.StringProperty(name="Material Name", 
                                            maxlen=50,
                                            default="")
    desc: bpy.props.StringProperty(name="Description", 
                                        maxlen=75,
                                        default="")
    diffuse_name: bpy.props.StringProperty(name="Diffuse Node Name", 
                                            maxlen=25,
                                            default="Diffuse")

class VIVY_OT_register_material(bpy.types.Operator):
    bl_idname = "vivy_node_tools.register_material"
    bl_label = "Register Material"

    def execute(self, context):
        vprop = context.scene.vivy_node_tools
        
        # Check if string has a name
        if context.active_object.active_material.name.strip() == "":
            self.report({'ERROR'}, "Name is required")
            return {'CANCELED'}
        
        json_path = vivy_materials.get_vivy_json()

        if not json_path.exists():
            json_path.touch()
        
        data = None

        # We do seperate open calls because
        # Python is absolutely annoying with doing
        # it all in one block. In theory, a race 
        # condition exists in this code as the file
        # referred to in `json_path` may have changed
        # between calls, but let's hope it doesn't 
        # manifest itself
        #
        # TODO: Figure out how to do this all in one block
        with open(json_path, 'r') as f:
            data = json.load(f) if json_path.stat().st_size != 0 else {}

        with open(json_path, 'w') as f:
            if "materials" not in data:
                data["materials"] = {}
            mats = data["materials"]
            mats[vprop.material_name] = {
                "base_material" : context.active_object.active_material.name,
                "desc" : vprop.desc,
                "passes" : {
                    "diffuse" : vprop.diffuse_name
                }
            }
            json.dump(data, f)
        
        anode = context.active_node
        anode.name = vprop.diffuse_name
        return {'FINISHED'}

class VIVY_PT_node_tools(bpy.types.Panel):
    bl_label = "Vivy Tools"
    bl_idname = "VIVY_PT_node_tools"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Vivy"
    bl_context = "scene"
    
    @classmethod
    def poll(cls, context):
        return context.area.ui_type == "ShaderNodeTree" and str(vivy_materials.get_vivy_blend().absolute()) == bpy.data.filepath

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        anode = context.active_node
        vprop = context.scene.vivy_node_tools
        if anode is not None and anode.type == "TEX_IMAGE":
            row.prop(vprop, "material_name")
            row = layout.row()
            row.prop(vprop, "desc")
            row = layout.row()
            row.prop(vprop, "diffuse_name")
            row = layout.row()

            # Grey out button if no name is inputed 
            # or if it's all spaces
            row.enabled = vprop.material_name.strip() != ""
            row.operator("vivy_node_tools.register_material")
        else:
            row.label(text="Select the image node that'll hold the diffuse pass")


classes = [
    VivyNodeToolProps,
    VIVY_PT_node_tools,
    VIVY_OT_register_material,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        bpy.types.Scene.vivy_node_tools = bpy.props.PointerProperty(type=VivyNodeToolProps)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.vivy_node_tools
