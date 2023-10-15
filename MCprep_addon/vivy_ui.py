import json
import bpy
from .materials import vivy_materials
from .conf import env

class VivyNodeToolProps(bpy.types.PropertyGroup):
    # Query materials in JSON
    #
    # TODO: Cache the JSON at some
    # point to reduce IO
    def query_materials(self, context):
        itms = []
        if env.vivy_material_json is not None:
            if "materials" in env.vivy_material_json:
                for mat in env.vivy_material_json["materials"]:
                    itms.append((mat, mat, ""))

        return itms

    # Material name and description
    material_name: bpy.props.StringProperty(name="Material Name", 
                                            maxlen=50,
                                            default="")
    desc: bpy.props.StringProperty(name="Description", 
                                        maxlen=75,
                                        default="")

    # Names for pass nodes
    diffuse_name: bpy.props.StringProperty(name="Diffuse Node Name", 
                                            maxlen=25,
                                            default="Diffuse")
    specular_name: bpy.props.StringProperty(name="Specular Node Name", 
                                            maxlen=25,
                                            default="Specular")
    normal_name: bpy.props.StringProperty(name="Normal Node Name", 
                                            maxlen=25,
                                            default="Normal")

    # Extensions
    extension_type: bpy.props.EnumProperty(name="Extension Type",
                                           items=[("emit",     "Emissive",     "Emissive Material"),
                                                ("reflective", "Glossy",       "Glossy Material"),
                                                ("metallic",   "Metal",        "Metallic Material"),
                                                ("glass",      "Transmissive", "Glass Material")]
                                           )
    extension_of: bpy.props.EnumProperty(name="Extension Of",
                                         items=query_materials)


class VIVY_OT_register_material(bpy.types.Operator):
    bl_idname = "vivy_node_tools.register_material"
    bl_label = "Register Material"

    def execute(self, context):
        vprop = context.scene.vivy_node_tools
        
        # Check if string has a name
        if context.active_object.active_material.name.strip() == "":
            self.report({'ERROR'}, "Name is required")
            return {'CANCELED'}
        
        # We do seperate open calls because
        # Python is absolutely annoying with doing
        # it all in one block. In theory, a race 
        # condition exists in this code as the file
        # referred to in `json_path` may have changed
        # between calls, but let's hope it doesn't 
        # manifest itself
        #
        # TODO: Figure out how to do this all in one block
        json_path = vivy_materials.get_vivy_json()
        env.reload_vivy_json() # To make sure we get the latest data
        data = env.vivy_material_json
        
        if data is None:
            self.report({'ERROR'}, "No data, report a bug on Vivy's GitHub repo!")
            return {'CANCELED'}

        with open(json_path, 'w') as f:
            active_material = context.active_object.active_material.name

            # Blender does allow pinning of a material's nodetree,
            # which in theory would make this None
            if active_material is None:
                self.report({'ERROR'}, "No active material selected! Maybe there's no active object?")
                return {'CANCELED'}
            
            # Set the material data
            if "materials" not in data:
                data["materials"] = {}
            mats = data["materials"]
            mats[vprop.material_name] = {
                "base_material" : active_material,
                "desc" : vprop.desc,
                "passes" : {
                    "diffuse" : vprop.diffuse_name
                }
            }
            
            # Set the mapping to use for the UI
            if "mapping" not in data:
                data["mapping"] = {}
            mapping = data["mapping"]
            
            if active_material not in mapping:
                mapping[active_material] = [vprop.material_name]
            else:
                # Check if it's actually a list. If it is, append
                # to the list. Otherwise, return an error and exit 
                # gracefully
                if isinstance(mapping[active_material], list):
                    mapping[active_material].append(vprop.material_name)
                else:
                    self.report({'ERROR'}, "Mapping in Vivy JSON is of the incorrect format!")
                    return {'CANCELED'}
            json.dump(data, f)
        
        anode = context.active_node
        anode.name = vprop.diffuse_name
        env.reload_vivy_json() # Reload once afterwards too
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
        active_material = context.active_object.active_material.name

        # We are assuming the data is up to date 
        # based on how the addon works and is supposed
        # to be used
        data = env.vivy_material_json
        if data is None:
            row = layout.row()
            row.label(text="No data, report a bug on Vivy's GitHub repo!")
            return

        # If no mappings exist or the material is 
        # not registered, then give the registration
        # menu
        if "mapping" not in data or active_material not in data["mapping"]:
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

        # If the material is known, then give access
        # to more advanced features, like extensions 
        # and whatnot
        elif "mapping" in data and active_material in data["mapping"]:
            if anode is not None and anode.type == "TEX_IMAGE":
                row.prop(vprop, "specular_name")
                row = layout.row()
                row.prop(vprop, "normal_name")
                row = layout.row()
            row.prop(vprop, "extension_type")
            row = layout.row()
            row.prop(vprop, "extension_of")



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
