"""Importerar genererade möbler (GLB) i herrgard.blend, skalar och placerar dem enligt placements.py.
Kör: python3 place_assets.py  (förväntar assets i out/assets/<namn>.glb)"""
import bpy, math, json, os, sys
sys.path.insert(0, "/home/claude/herrgard")
from placements import PLACEMENTS
from mathutils import Vector, Matrix
ROOT = "/home/claude/herrgard"; A = f"{ROOT}/out/assets"

bpy.ops.wm.open_mainfile(filepath=f"{ROOT}/out/herrgard.blend")
# ta bort gamla volymmöbler, importera "keep"-volymerna
for o in list(bpy.data.objects):
    if o.name.startswith("f_"): bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.import_scene.gltf(filepath=f"{ROOT}/out/furniture_keep.glb")
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith("f_") and "keep_done" not in o:
        o.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'X')); o["keep_done"] = True
ASSIGN = {"f_oak": "Ek", "f_stone": "Kalksten", "f_steel": "Rostfritt", "f_glass": "Glas", "f_water": "Vatten", "f_black": "Svart lack"}
for o in bpy.data.objects:
    key = o.name.split(".")[0]
    if o.type == 'MESH' and key in ASSIGN:
        o.data.materials.clear(); o.data.materials.append(bpy.data.materials[ASSIGN[key]])

# importera varje asset en gång till en gömd samling, instansiera sedan
lib = bpy.data.collections.new("Assets_lib"); bpy.context.scene.collection.children.link(lib); lib.hide_render = True; lib.hide_viewport = True
placed = bpy.data.collections.new("Mobler"); bpy.context.scene.collection.children.link(placed)
cache = {}
def load(name):
    if name in cache: return cache[name]
    path = f"{A}/{name}.glb"
    if not os.path.exists(path): print("saknas", name); cache[name] = None; return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    # slå ihop till ett objekt
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    for o in new:
        if o != obj and o.name in bpy.data.objects:
            try: bpy.data.objects.remove(o, do_unlink=True)
            except: pass
    obj.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # decimera till ca 120k trianglar
    nf = len(obj.data.polygons)
    if nf > 130000:
        md = obj.modifiers.new("dec", 'DECIMATE'); md.ratio = 120000 / nf
        bpy.context.view_layer.objects.active = obj; bpy.ops.object.modifier_apply(modifier="dec")
    for p in obj.data.polygons: p.use_smooth = True
    for c in list(obj.users_collection): c.objects.unlink(obj)
    lib.objects.link(obj); obj.name = f"lib_{name}"
    # normalisera: origo i botten-mitt
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb))); mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    ctr = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    obj.data.transform(Matrix.Translation(-ctr))
    obj["dims"] = [mx.x - mn.x, mx.y - mn.y, mx.z - mn.z]
    cache[name] = obj; return obj

for i, (name, x, y, z, rot, L) in enumerate(PLACEMENTS):
    src = load(name)
    if src is None: continue
    o = src.copy(); o.data = src.data; o.name = f"{name}_{i:02d}"
    placed.objects.link(o)
    dx, dy, dz = src["dims"]
    s = 1.0
    if L: s = L / max(dx, dy)
    o.scale = (s, s, s); o.rotation_euler = (0, 0, math.radians(rot)); o.location = (x, y, z)
    o.hide_render = False; o.hide_viewport = False
    o.visible_camera = True

# ---- efterjusteringar ----
H = {"sofa":0.82,"coffee_table":0.38,"dining_table":0.76,"dining_chair":0.88,"kitchen_island":0.95,"range":0.92,"bed_master":1.15,"bathtub":0.6,"vanity":0.9,
     "bookshelf":3.3,"desk":1.1,"lounger":0.7,"recliner":1.05,"server_rack":2.2,"olive_tree":3.0,"pendant":0.7,"robot_arm":1.4,"ring_chandelier":0.5,
     "suv":1.9,"bed_single":0.9,"oak_cabinet":2.4,"side_table":0.5,"hall_table":1.3,"tv":1.25}
for o in list(placed.objects):
    key = o.name.rsplit("_",1)[0]
    if key == "rug":
        x, y, z = o.location; bpy.data.objects.remove(o, do_unlink=True)
        m = bpy.data.materials.get("Matta2")
        if m is None:
            m = bpy.data.materials.new("Matta2"); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.22, 0.17, 0.13, 1); b.inputs["Roughness"].default_value = 0.95; b.inputs["Sheen Weight"].default_value = 0.8
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, z + 0.015)); p = bpy.context.object; p.scale = (5.0, 4.0, 1); p.name = "matta"; p.data.materials.append(m)
        continue
    lib = cache.get(key)
    if lib is not None and key in H:
        dx, dy, dz = lib["dims"]; sx = o.scale.x; o.scale = (sx, sx, H[key] / dz)
w = bpy.data.materials["Kalkputs"].node_tree
for nd in w.nodes:
    if nd.type == 'VALTORGB': nd.color_ramp.elements[0].color = (0.62, 0.56, 0.48, 1); nd.color_ramp.elements[1].color = (0.50, 0.45, 0.38, 1)
slab = bpy.data.materials["Kalkstensgolv"]; nt = slab.node_tree
out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]; bsdf_floor = out.inputs[0].links[0].from_node
plaster = nt.nodes.new("ShaderNodeBsdfPrincipled"); plaster.inputs["Base Color"].default_value = (0.50, 0.45, 0.39, 1); plaster.inputs["Roughness"].default_value = 0.8
geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Normal"], sep.inputs[0])
lt = nt.nodes.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.0; nt.links.new(sep.outputs["Z"], lt.inputs[0])
mix = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(lt.outputs[0], mix.inputs[0]); nt.links.new(bsdf_floor.outputs[0], mix.inputs[1]); nt.links.new(plaster.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0])
for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.data.type == 'AREA': o.data.energy *= 0.55; o.data.color = (1.0, 0.78, 0.58)
for im in bpy.data.images:
    if im.size[0] > 1024 or im.size[1] > 1024:
        f = 1024 / max(im.size); im.scale(int(im.size[0]*f), int(im.size[1]*f)); im.pack()
print("placerade", len([o for o in placed.objects]))
bpy.ops.wm.save_as_mainfile(filepath=f"{ROOT}/out/herrgard_moblerad.blend", compress=True)
print("saved")
