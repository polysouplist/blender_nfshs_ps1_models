bl_info = {
    "name": "Facet Flag Properties Panel",
    "author": "PolySoupList",
    "version": (1, 0, 0),
    "blender": (3, 6, 23),
    "location": "Properties Panel > Object Data Properties",
    "description": "Quick access to facet flag properties",
    "category": "UI",
}


import bpy
import bmesh


class FacetFlagPanel(bpy.types.Panel):
	"""Creates a Panel in the Mesh properties window"""
	bl_label = "Facet Flag"
	bl_idname = "OBJECT_PT_FacetFlag"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "data"
	ebm = dict()
	
	@classmethod
	def poll(cls, context):
		if context.mode == 'EDIT_MESH':
			me = context.edit_object.data
			fl = me.polygon_layers_int.get("flag") or me.polygon_layers_int.new(name="flag")
			
			ret = False
			if fl:
				cls.ebm.setdefault(me.name, bmesh.from_edit_mesh(me))
				ret = True
				#return True
			
			if ret == True:
				return True
		
		cls.ebm.clear()
		return False
	
	def draw(self, context):
		layout = self.layout
		me = context.edit_object.data
		layout.prop(me, "flag")


def set_int_facet_flag(self, value):
	bm = FacetFlagPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

	# get the facet flag layer
	flag = (bm.faces.layers.int.get("flag") or bm.faces.layers.int.new("flag"))

	af = None
	for elem in reversed(bm.select_history):
		if isinstance(elem, bmesh.types.BMFace):
			af = elem
			break
	if af:
		af[flag] = value
		bmesh.update_edit_mesh(self)

def get_int_facet_flag(self):
	bm = FacetFlagPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))
	flag = bm.faces.layers.int.get("flag") or bm.faces.layers.int.new("flag")

	for elem in reversed(bm.select_history):
		if isinstance(elem, bmesh.types.BMFace):
			return(elem[flag])
	
	return 0


def register():
	for klass in CLASSES:
		bpy.utils.register_class(klass)
	
	bpy.types.Mesh.flag = bpy.props.IntProperty(name="Facet flag", description="Facet flag", min=-32768, max=32767, get=get_int_facet_flag, set=set_int_facet_flag)


def unregister():
	for klass in CLASSES:
		bpy.utils.unregister_class(klass)
	
	delattr(bpy.types.Mesh, "flag")


CLASSES = [FacetFlagPanel]


if __name__ == "__main__":
	register()
