import bpy
from bpy.types import Operator
import bmesh
import math
from mathutils import Matrix
import os
import time
import struct
import numpy as np
from bpy_extras.io_utils import (
	orientation_helper,
	axis_conversion,
)


def export_nfshs_ps1_models(file_path, is_traffic):
	os.system('cls')
	
	main_collection = bpy.context.scene.collection
	global_matrix = axis_conversion(from_forward='Z', from_up='Y', to_forward='-Y', to_up='Z').to_4x4()
	m = global_matrix
	
	for main_collection in bpy.context.scene.collection.children:
		is_hidden = bpy.context.view_layer.layer_collection.children.get(main_collection.name).hide_viewport
		is_excluded = bpy.context.view_layer.layer_collection.children.get(main_collection.name).exclude
		
		if is_hidden or is_excluded:
			print("WARNING: skipping main collection %s since it is hidden or excluded." % (main_collection.name))
			print("")
			continue
		
		objects = main_collection.objects
		object_index = -1
		
		with open(file_path, 'wb') as f:
			if is_traffic == False:
				if "header_unk0" in main_collection:
					header_unk0 = [id_to_int(i) for i in main_collection["header_unk0"]]
					f.write(struct.pack('<57I', *header_unk0))
				else:
					f.write(b'\x00' * 0xE4)
				if "header_unk1" in main_collection:
					header_unk1 = [id_to_int(i) for i in main_collection["header_unk1"]]
					f.write(struct.pack('<90I', *header_unk1))
				else:
					f.write(b'\x00' * 0x168)
			else:
				f.write(b'\x00' * 0x24C)
			
			object_by_index = {}
			for obj in objects:
				if obj.type == 'MESH' and "object_index" in obj:
					idx = obj["object_index"]
					if idx in object_by_index:
						print(f"WARNING: Duplicate object_index {idx}! Skipping duplicate.")
						continue
					object_by_index[idx] = obj
			
			for index in range(57):
				if index in object_by_index:
					object = object_by_index[index]
					# Inits
					mesh = object.data
					mesh.calc_normals_split()
					loops = mesh.loops
					bm = bmesh.new()
					bm.from_mesh(mesh)
				
					numVertex = len(mesh.vertices)
					numFacet = len(mesh.polygons)
					translation = Matrix(np.linalg.inv(m) @ object.matrix_world)
					translation = translation.to_translation()
					translation = [round(translation[0]*0x7FFF),
								   round(translation[1]*0x7FFF),
								   round(translation[2]*0x7FFF)]
					if index == 39:
						translation[0] += 0x7AE
					elif index == 40:
						translation[0] -= 0x7AE
					
					f.write(struct.pack('<H', numVertex))
					f.write(struct.pack('<H', numFacet))
					f.write(struct.pack('<3i', *translation))
					
					try:
						object_unk0 = [id_to_int(i) for i in object["object_unk0"]]
						f.write(struct.pack('<3I', *object_unk0))
					except:
						f.write(b'\x00' * 0xC)
					
					for vert in mesh.vertices:
						vertex = [round(vert.co[0]*0x7F),
								  round(vert.co[1]*0x7F),
								  round(vert.co[2]*0x7F)]
						f.write(struct.pack('<3h', *vertex))
					if len(mesh.vertices) % 2 == 1:	#Data offset after positions, happens when numVertex is odd.
						f.write(b'\x00\x00')
					
					if is_traffic == False:
						if get_R3DCar_ObjectInfo(index)[1] & 1 != 0:
							for vert in mesh.vertices:
								Nvertex = [round(vert.normal[0]*0x7F),
										   round(vert.normal[1]*0x7F),
										   round(vert.normal[2]*0x7F)]
								f.write(struct.pack('<3h', *Nvertex))
							if len(mesh.vertices) % 2 == 1:	#Data offset after positions, happens when numVertex is odd.
								f.write(b'\x00\x00')
					
					uv_layer = mesh.uv_layers.active.data
					flags = mesh.attributes.get("flag")
						
					for face in mesh.polygons:
						flag = flags.data[face.index].value
						textureIndex = int(mesh.materials[face.material_index].name)
						vertexId0, vertexId1, vertexId2 = face.vertices
						
						loop_start = face.loop_start
						uv0 = uv_layer[loop_start].uv
						uv1 = uv_layer[loop_start + 1].uv
						uv2 = uv_layer[loop_start + 2].uv
						
						uv0 = int(round(uv0[0]*255)) & 0xFF, int(round((1.0 - uv0[1])*255)) & 0xFF
						uv1 = int(round(uv1[0]*255)) & 0xFF, int(round((1.0 - uv1[1])*255)) & 0xFF
						uv2 = int(round(uv2[0]*255)) & 0xFF, int(round((1.0 - uv2[1])*255)) & 0xFF
						
						f.write(struct.pack('<h', flag))
						f.write(struct.pack('<B', textureIndex))
						f.write(struct.pack('<B', vertexId0))
						f.write(struct.pack('<B', vertexId1))
						f.write(struct.pack('<B', vertexId2))
						f.write(struct.pack('<2B', *uv0))
						f.write(struct.pack('<2B', *uv1))
						f.write(struct.pack('<2B', *uv2))
					
					mesh.free_normals_split()
					bm.clear()
					bm.free()
				else:
					f.write(b'\x00' * 0x1C)


def get_geoPartNames(index):
	geoPartNames = {0: "Body Medium",
					1: "Body Low",
					2: "Body Undertray",
					3: "Wheel Wells",
					4: "Wheel Squares (unknown LOD)",
					5: "Wheel Squares (A little bigger)",
					6: "Unknown Invisible??",
					7: "Unknown Invisible??",
					8: "Spoiler Original",
					9: "Spoiler Uprights",
					10: "Spoiler Upgraded",
					11: "Spoiler Upgraded Uprights ",
					12: "Fog Lights and Rear bumper Top",
					13: "Fog Lights and Rear bumper TopR",
					14: "Wing Mirror Attachment Points",
					15: "Wheel Attachment Points",
					16: "Brake Light Quads",
					17: "Unknown Invisible",
					18: "Unknown Rear Light tris",
					19: "Rear Inner Light Quads",
					20: "Rear Inner Light Quads rotated",
					21: "Rear Inner Light Tris",
					22: "Front Light quads",
					23: "Bigger Front Light quads",
					24: "Front Light triangles",
					25: "Rear Main Light Quads",
					26: "Rear Main Light Quads dup",
					27: "Rear Main Light Tris",
					28: "Unknown Invisible",
					29: "Unknown Invisible",
					30: "Front Headlight light Pos",
					31: "Logo and Rear Numberplate",
					32: "Exhaust Tips",
					33: "Low LOD Exhaust Tips",
					34: "Mid Body F/R Triangles",
					35: "Interior Cutoff + Driver Pos",
					36: "Unknown Invisible",
					37: "Unknown Invisible",
					38: "Unknown Invisible",
					39: "Unknown Invisible",
					40: "Unknown Invisible",
					41: "Right Body High",
					42: "Left Body High",
					43: "Right Wing Mirror",
					44: "Left Wing Mirror",
					45: "Front Right Light Bucket",
					46: "Front Left Light bBucket",
					47: "Front Right Wheel",
					48: "Front Left Wheel",
					49: "Unknown Invisible",
					50: "Unknown Invisible",
					51: "Front Right Tire",
					52: "Front Left Tire",
					53: "Unknown Invisible",
					54: "Unknown Invisible",
					55: "Rear Right Wheel",
					56: "Rear Left Wheel"}
	
	return geoPartNames[index]


def get_R3DCar_ObjectInfo(index):
	R3DCar_ObjectInfo = {0: [0x00, 0x49, 0x00, 0x01, 0x00, 0x00],
						 1: [0x00, 0x00, 0x00, 0x00, 0x01, 0x00],
						 2: [0x20, 0x02, 0x01, 0x01, 0x00, 0x00],
						 3: [0x30, 0x00, 0x01, 0x01, 0x00, 0x00],
						 4: [0xF8, 0x00, 0x00, 0x00, 0x01, 0x00],
						 5: [0xF0, 0x08, 0x0A, 0x0A, 0x00, 0x00],
						 6: [0xE0, 0x00, 0x0C, 0x00, 0x00, 0x00],
						 7: [0xE0, 0x00, 0x00, 0x0C, 0x00, 0x00],
						 8: [0xEC, 0x89, 0x0B, 0x0B, 0x00, 0x0B],
						 9: [0xF0, 0x88, 0x0B, 0x0B, 0x00, 0x0B],
						 10: [0xEC, 0x89, 0x0C, 0x0C, 0x00, 0x0C],
						 11: [0xF0, 0x88, 0x0C, 0x0C, 0x00, 0x0C],
						 12: [0xE8, 0x00, 0x01, 0x00, 0x00, 0x00],
						 13: [0xE8, 0x00, 0x00, 0x01, 0x00, 0x00],
						 14: [0xD4, 0x00, 0x11, 0x00, 0x00, 0x00],
						 15: [0xD4, 0x00, 0x11, 0x00, 0x00, 0x00],
						 16: [0xE1, 0x08, 0x01, 0x00, 0x00, 0x00],
						 17: [0xE1, 0x08, 0x00, 0x01, 0x00, 0x00],
						 18: [0xD4, 0x00, 0x12, 0x12, 0x12, 0x00],
						 19: [0xE2, 0x00, 0x01, 0x00, 0x00, 0x00],
						 20: [0xE2, 0x00, 0x00, 0x01, 0x00, 0x00],
						 21: [0xD4, 0x00, 0x13, 0x13, 0x13, 0x00],
						 22: [0xE2, 0x18, 0x0F, 0x10, 0x00, 0x00],
						 23: [0xE2, 0x08, 0x00, 0x01, 0x00, 0x00],
						 24: [0xD4, 0x10, 0x14, 0x14, 0x14, 0x00],
						 25: [0xE2, 0x18, 0x0F, 0x10, 0x00, 0x00],
						 26: [0xE2, 0x08, 0x00, 0x01, 0x00, 0x00],
						 27: [0xD4, 0x10, 0x15, 0x15, 0x15, 0x00],
						 28: [0xE8, 0x08, 0x01, 0x00, 0x00, 0x00],
						 29: [0xE8, 0x08, 0x00, 0x01, 0x00, 0x00],
						 30: [0xD4, 0x00, 0x16, 0x16, 0x16, 0x00],
						 31: [0xD8, 0x00, 0x01, 0x01, 0x00, 0x00],
						 32: [0xF4, 0x00, 0x0D, 0x00, 0x00, 0x00],
						 33: [0xF4, 0x00, 0x0E, 0x00, 0x00, 0x00],
						 34: [0xD4, 0x00, 0x11, 0x00, 0x00, 0x00],
						 35: [0x30, 0x00, 0x02, 0x01, 0x00, 0x00],
						 36: [0x28, 0x02, 0x03, 0x00, 0x00, 0x03],
						 37: [0x28, 0x02, 0x03, 0x00, 0x00, 0x03],
						 38: [0x26, 0x02, 0x04, 0x00, 0x00, 0x00],
						 39: [0x24, 0x02, 0x04, 0x00, 0x00, 0x04],
						 40: [0x24, 0x02, 0x04, 0x00, 0x00, 0x04],
						 41: [0x00, 0x49, 0x01, 0x00, 0x00, 0x01],
						 42: [0x00, 0x49, 0x01, 0x00, 0x00, 0x01],
						 43: [0xF0, 0x80, 0x05, 0x00, 0x00, 0x05],
						 44: [0xF0, 0x80, 0x06, 0x00, 0x00, 0x06],
						 45: [0xE8, 0x89, 0x07, 0x07, 0x00, 0x07],
						 46: [0xE8, 0x89, 0x08, 0x08, 0x00, 0x08],
						 47: [0x1F, 0x00, 0x01, 0x01, 0x00, 0x00],
						 48: [0x1F, 0x00, 0x01, 0x01, 0x00, 0x00],
						 49: [0x20, 0x00, 0x01, 0x00, 0x00, 0x00],
						 50: [0x20, 0x00, 0x01, 0x00, 0x00, 0x00],
						 51: [0x20, 0x00, 0x09, 0x01, 0x00, 0x00],
						 52: [0x20, 0x00, 0x09, 0x01, 0x00, 0x00],
						 53: [0x20, 0x00, 0x01, 0x00, 0x00, 0x00],
						 54: [0x20, 0x00, 0x01, 0x00, 0x00, 0x00],
						 55: [0x20, 0x00, 0x09, 0x01, 0x00, 0x00],
						 56: [0x20, 0x00, 0x09, 0x01, 0x00, 0x00]}
	
	return R3DCar_ObjectInfo[index]


def id_to_int(id):
	id_old = id
	id = id.replace('_', '')
	id = id.replace(' ', '')
	id = id.replace('-', '')
	id = ''.join(id[::-1][x:x+2][::-1] for x in range(0, len(id), 2))
	return int(id, 16)


export_nfshs_ps1_models(
	file_path = r"C:\Users\user\Desktop\your_geo.geo",
	is_traffic = False
)
