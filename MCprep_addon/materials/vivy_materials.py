# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.types import Context, Material

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Union, Optional
import json

from .. import tracking
from .. import util
from ..conf import env
from . import generate
from . import sync
from .generate import checklist, get_mc_canonical_name

@dataclass
class ViviPasses:
	diffuse: str 
	specular: Optional[str]
	normal: Optional[str]

@dataclass
class ViviExtensions:
	emissive: Optional[str]

@dataclass
class VivyMaterial:
	base_material: str 
	desc: str 
	passes: ViviPasses
	extensions: Optional[ViviExtensions]

@dataclass
class VivyOptions:
	source_mat: str
	material: VivyMaterial
	passes: Dict[str, str]

def reload_material_vivy_library(context: Context) -> None:
	"""Reloads the library and cache"""
	sync_file = get_vivy_blend(context)
	if not sync_file.exists():
		env.log("Vivy file not found", vv_only=True)
		env.vivy_cache = []
		return

	with bpy.data.libraries.load(str(sync_file)) as (data_from, _):
		env.vivy_cache = list(data_from.materials)
	env.log("Updated Vivy cache", vv_only=True)

def material_in_vivy_library(material: str, context: Context) -> bool:
	"""Returns true if the material is in the sync mat library blend file."""
	if env.vivy_cache is None:
		reload_material_vivy_library(context)
	if util.nameGeneralize(material) in env.vivy_cache:
		return True
	elif material in env.vivy_cache:
		return True
	return False

def set_material(context: Context, material: Material, options: VivyOptions) -> Optional[Union[Material, str]]:
	if isinstance(options.material.extensions, ViviExtensions):
		ext = options.material.extensions
		if ext.emissive is not None:
			matGen = util.nameGeneralize(options.source_mat)
			canon, _ = get_mc_canonical_name(matGen)
			if checklist(canon, "emit"):
				options.material.base_material = ext.emissive

	import_name: Optional[str] = None
	if options.material.base_material in env.vivy_cache:
		import_name = options.material.base_material
	elif util.nameGeneralize(options.material.base_material) in env.vivy_cache:
		import_name = util.nameGeneralize(options.material.base_material)

	# If link is true, check library material not already linked.
	sync_file = get_vivy_blend(context)

	init_mats = list(bpy.data.materials)
	path = os.path.join(str(sync_file), "Material")

	if isinstance(import_name, str):
		util.bAppendLink(path, import_name, False)  # No linking.

	imported = set(list(bpy.data.materials)) - set(init_mats)
	if not imported:
		return f"Could not import {material.name}"
	selected_material = list(imported)[0]
	
	# Set the diffuse pass
	new_material_nodes = selected_material.node_tree.nodes
	if not new_material_nodes.get(options.material.passes.diffuse):
		return "Material has no diffuse node"

	if not material.node_tree.nodes:
		return "Material has no nodes"

	nnodes = selected_material.node_tree.nodes
	material_nodes = material.node_tree.nodes

	if not material_nodes.get("Image Texture"):
		return "Material has no Image Texture node"

	nnode_diffuse = nnodes.get(options.material.passes.diffuse)
	nnode_diffuse.image = options.passes["diffuse"]

	material.user_remap(selected_material)

	m_name = material.name
	bpy.data.materials.remove(material)
	selected_material.name = m_name
	return None

def get_vivy_blend(context: Context) -> Path:
	"""Return the sync blend file path that might exist, based on active pack"""
	resource_pack = bpy.path.abspath(context.scene.mcprep_texturepack_path)
	return Path(os.path.join(resource_pack, "vivy_materials.blend"))

def get_vivy_json(context: Context) -> Path:
	"""Return the sync blend file path that might exist, based on active pack"""
	resource_pack = bpy.path.abspath(context.scene.mcprep_texturepack_path)
	return Path(os.path.join(resource_pack, "vivy_materials.json"))

def generate_vivy_materials(self, context, options: VivyOptions):
	# Sync file stuff.
	sync_file = get_vivy_blend(context)
	if not os.path.isfile(sync_file):
		self.report({'ERROR'}, f"Sync file not found: {sync_file}")
		return {'CANCELLED'}

	if sync_file == bpy.data.filepath:
		return {'CANCELLED'}

	# Find the material
	if not material_in_vivy_library(options.material.base_material, context):
		self.report({'ERROR'}, f"Material not found: {options.material.base_material}")
		return {'CANCELLED'}

	mat_list = list(bpy.data.materials)
	mat = [m for m in mat_list if m.name == options.source_mat]
	if len(mat) != 1:
		self.report({'ERROR'}, f"Could not get {options.source_mat}")
	try:
		err = set_material(context, mat[0], options) # no linking
		if err:
			env.log(err)
	except Exception as e:
		print(e)

"""
Panel related parts below
"""
class VivyMaterialProps():
	def get_materials(self, context):
		if env.vivy_material_json is None:
			with open(get_vivy_json(context), 'r') as f:
				env.vivy_material_json = json.load(f)
		itms = []
		for m, d in env.vivy_material_json["materials"].items():
			itms.append((m, m, d["desc"]))
		return itms

	materialName: bpy.props.EnumProperty(
		name="Material",
		description="Material to use for prepping",
		items=get_materials
	)

def draw_mats_common(self, context: Context) -> None:
	row = self.layout.row()
	row.prop(self, "materialName")

	md = env.vivy_material_json["materials"][self.materialName]
	row = self.layout.row()
	row.label(text=md["desc"])
	
	box = self.layout.box()
	box.label(text="Expects the following passes:")
	row = box.row()
	row.label(text="Diffuse", icon="MATERIAL")
	if "specular" in md["passes"]:
		row = box.row()
		row.label(text="Specular", icon="NODE_MATERIAL")
	if "normal" in md["passes"]:
		row = box.row()
		row.label(text="Normal", icon="ORIENTATION_NORMAL")
	
	if "extensions" in md:
		box = self.layout.box()
		box.label(text="Has extensions for the following:")
		if "emissive" in md["extensions"]:
			row = box.row()
			row.label(text="Emission", icon="OUTLINER_OB_LIGHT")

class VIVY_OT_materials(bpy.types.Operator, VivyMaterialProps):
	"""
	Vivy's custom material generator that 
	derives much of its code from MCprep's 
	Prep materials operator
	"""
	bl_idname = "vivy.prep_materials"
	bl_label = "MCprep Materials"
	bl_options = {'REGISTER', 'UNDO'}


	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(
			self, width=300 * util.ui_scale())

	def draw(self, context):
		draw_mats_common(self, context)

	track_function = "vivy_materials"
	track_param = None
	track_exporter = None
	@tracking.report_error
	def execute(self, context):
		# get list of selected objects
		obj_list = context.selected_objects
		if not obj_list:
			if not self.skipUsage:
				self.report({'ERROR'}, "No objects selected")
			return {'CANCELLED'}

		# gets the list of materials (without repetition) from selected
		mat_list = util.materialsFromObj(obj_list)
		if not mat_list:
			if not self.skipUsage:
				self.report({'ERROR'}, "No materials found on selected objects")
			return {'CANCELLED'}

		# check if linked material exists
		engine = context.scene.render.engine
		count = 0
		count_lib_skipped = 0

		for mat in mat_list:
			if not mat:
				env.log(
					"During prep, found null material:" + str(mat), vv_only=True)
				continue

			elif mat.library:
				count_lib_skipped += 1
				continue

			passes = generate.get_textures(mat)
			if passes.get("diffuse"):
				# Otherwise, attempt to get or load extra passes. Needed if
				# swap texturepack hasn't been used yet, otherwise would need
				# to prep twice (even if the base diff texture was already
				# loaded from that pack).
				diff_filepath = passes["diffuse"].filepath
				# bpy. makes rel to file, os. resolves any os.pardir refs.
				abspath = os.path.abspath(bpy.path.abspath(diff_filepath))
				other_passes = generate.find_additional_passes(abspath)
				for pass_name in other_passes:
					if pass_name not in passes or not passes.get(pass_name):
						# Need to update the according tagged node with tex.
						passes[pass_name] = bpy.data.images.load(
							other_passes[pass_name],
							check_existing=True)

			if engine == 'CYCLES' or engine == 'BLENDER_EEVEE':
				# Make sure Vivy has loaded the JSON
				if not isinstance(env.vivy_material_json, Dict):
					if env.vivy_material_json is None:
						with open(get_vivy_json(context), 'r') as f:
							env.vivy_material_json = json.load(f)

				# Set all options and go!
				md = env.vivy_material_json["materials"][self.materialName]
				options = VivyOptions(
					source_mat=mat.name,
					material=VivyMaterial(
						base_material=md["base_material"],
						desc=md["desc"],
						passes=ViviPasses(
							diffuse=md["passes"]["diffuse"],
							specular=md["passes"]["specular"] if "specular" in md["passes"] else None,
							normal=md["passes"]["normal"] if "normal" in md["passes"] else None
						),
						extensions=None if "extensions" not in md else ViviExtensions(
							emissive=md["extensions"]["emissive"] if "emissive" in md["extensions"] else None
						)
					),
					passes=passes
				)
				generate_vivy_materials(self, context, options)
				count += 1
			else:
				self.report(
					{'ERROR'},
					"Only Cycles and Eevee are supported")
				return {'CANCELLED'}

		if count_lib_skipped > 0:
			self.report(
				{"INFO"},
				f"Modified {count} materials, skipped {count_lib_skipped} linked ones.")
		elif count > 0:
			self.report({"INFO"}, f"Modified  {count} materials")
		else:
			self.report(
				{"ERROR"},
				"Nothing modified, be sure you selected objects with existing materials!"
			)

		addon_prefs = util.get_user_preferences(context)
		self.track_param = context.scene.render.engine
		self.track_exporter = addon_prefs.MCprep_exporter_type
		return {'FINISHED'}

classes = (
	VIVY_OT_materials,
)


def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.app.handlers.load_post.append(sync.clear_sync_cache)


def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	try:
		bpy.app.handlers.load_post.remove(sync.clear_sync_cache)
	except:
		pass
