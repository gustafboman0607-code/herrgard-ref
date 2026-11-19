"""Lägg till nya möbler + himmel i v3. out/herrgard_v3.blend → out/herrgard_v4.blend"""
import bpy, os, sys, math, json
from mathutils import Vector, Matrix
sys.path.insert(0, "/home/claude/herrgard")
ROOT = "/home/claude/herrgard"
bpy.ops.wm.open_mainfile(filepath=f"{ROOT}/out/herrgard_v3.blend")
sc = bpy.context.scene
lib = bpy.data.collections["Assets_lib"]; placed = bpy.data.collections["Mobler"]
P1, P2, K = 0.0, 3.9, -3.2

def load(name):
    if f"lib_{name}" in bpy.data.objects: return bpy.data.objects[f"lib_{name}"]
    path = f"{ROOT}/out/assets/{name}.glb"
    if not os.path.exists(path): print("saknas", name); return None
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]; meshes = [o for o in new if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    for o in new:
        if o != obj and o.name in bpy.data.objects:
            try: bpy.data.objects.remove(o, do_unlink=True)
            except: pass
    obj.parent = None; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    nf = len(obj.data.polygons)
    if nf > 130000:
        md = obj.modifiers.new("dec", 'DECIMATE'); md.ratio = 120000 / nf; bpy.ops.object.modifier_apply(modifier="dec")
    for p in obj.data.polygons: p.use_smooth = True
    for c in list(obj.users_collection): c.objects.unlink(obj)
    lib.objects.link(obj); obj.name = f"lib_{name}"
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb))); mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    obj.data.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    obj["dims"] = [mx.x - mn.x, mx.y - mn.y, mx.z - mn.z]
    obj.hide_render = True; obj.hide_viewport = True
    return obj

H = {"floor_lamp": 1.7, "curtain": 3.2, "plant": 2.0, "sideboard": 0.8, "sconce": 0.3, "books": 0.35, "armchair": 0.8, "bunk_bed": 1.7}
def place(name, x, y, z, rot, L, tag):
    src = load(name)
    if src is None: return
    o = src.copy(); o.data = src.data; o.name = f"{name}_{tag}"; placed.objects.link(o)
    dx, dy, dz = src["dims"]; s = L / max(dx, dy) if L else 1.0
    o.scale = (s, s, H[name] / dz if name in H else s); o.rotation_euler = (0, 0, math.radians(rot)); o.location = (x, y, z)
    o.hide_render = False; o.hide_viewport = False; o.visible_camera = True

# ---- gardiner vid alla fönster i bostadsrum ----
CURTAIN_ROOMS = {"Salong", "Bibliotek", "Matsal", "Vardagsrum", "Orangeri", "Eget kök", "Frukostrum", "Kontor / KC", "Gästsvit", "Entréhall (dubbelhöjd)",
                 "Master sovrum", "Sovrum 2", "Sovrum 3", "Sovrum 4", "Sovrum 5", "Barnrum", "Lekrum", "Allrum", "Master spa-bad", "Privat rum"}
wins = json.load(open(f"{ROOT}/out/windows.json"))
n = 0
for level, room, kind, c, m, o, w in wins:
    if room not in CURTAIN_ROOMS: continue
    z = P1 if level == "Plan 1" else P2
    d = -o * 0.28                      # in i rummet
    for side in (-1, 1):
        off = side * (w / 2 + 0.45)
        if kind == 'h': place("curtain", m + off, c + d, z, 0, 0.9, f"{n}")
        else:           place("curtain", c + d, m + off, z, 90, 0.9, f"{n}")
        n += 1
print("gardiner", n)

# ---- golvlampor, växter, skänkar, böcker ----
EXTRA = [
    ("floor_lamp", 7.2, 1.0, P1, 0, 0.6), ("floor_lamp", 0.8, 7.2, P1, 0, 0.6),              # salong
    ("floor_lamp", 7.2, 9.0, P1, 0, 0.6), ("plant", 0.9, 8.8, P1, 0, 1.1),                   # bibliotek
    ("floor_lamp", 25.2, 14.2, P1, 0, 0.6), ("plant", 16.9, 14.2, P1, 0, 1.1), ("sideboard", 16.6, 9.6, P1, 90, 2.2),  # vardagsrum
    ("sideboard", 23.0, 7.55, P1, 0, 2.4), ("plant", 25.2, 0.9, P1, 0, 1.1),                 # matsal
    ("plant", 10.9, 2.4, P1, 0, 1.2), ("plant", 15.1, 2.4, P1, 30, 1.2), ("sideboard", 10.6, 6.5, P1, 90, 2.0),  # entréhall
    ("books", 4, 4.5, P1 + 0.38, 20, 0.5), ("books", 21, 12.3, P1 + 0.38, -15, 0.5),         # soffbord
    ("plant", 12.5, 14.2, P1, 0, 1.4), ("floor_lamp", 15.2, 12.0, P1, 0, 0.6),               # orangeri
    ("floor_lamp", -9.2, 4.2, P2, 0, 0.6), ("plant", -0.8, -2.2, P2, 0, 1.2), ("sideboard", -5, -2.55, P2, 0, 2.2),  # master
    ("plant", 5.5, 14.2, P2, 0, 1.1), ("floor_lamp", 0.8, 13.5, P2, 0, 0.6),                 # privat rum
    ("floor_lamp", 10.8, 14.2, P2, 0, 0.6), ("plant", 15.2, 14.2, P2, 0, 1.1),               # allrum plan 2
]
for i, (name, x, y, z, rot, L) in enumerate(EXTRA): place(name, x, y, z, rot, L, f"e{i:02d}")
for name in ("armchair", "bunk_bed"):   # tidigare saknade – nu nedladdade
    if os.path.exists(f"{ROOT}/out/assets/{name}.glb"):
        from placements import PLACEMENTS
        for i, (nm, x, y, z, rot, L) in enumerate(PLACEMENTS):
            if nm == name: place(name, x, y, z, rot, L, f"p{i:02d}")

# ---- små ljuskällor i golvlamporna (riktigt ljus) ----
for o in list(placed.objects):
    if o.name.startswith("floor_lamp"):
        bpy.ops.object.light_add(type='POINT', location=(o.location.x, o.location.y, o.location.z + 1.45)); L = bpy.context.object
        L.data.energy = 35; L.data.color = (1.0, 0.68, 0.40); L.data.shadow_soft_size = 0.18; L.name = f"lampljus_{o.name}"

# ---- himmel: genererad panorama som world ----
w = sc.world; nt = w.node_tree
for nd in list(nt.nodes): nt.nodes.remove(nd)
out = nt.nodes.new("ShaderNodeOutputWorld"); bg = nt.nodes.new("ShaderNodeBackground")
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(f"{ROOT}/tex/himmel_eq.jpg"); env.image.pack()
tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, 0, math.radians(0))
nt.links.new(tc.outputs["Generated"], mp.inputs[0]); nt.links.new(mp.outputs[0], env.inputs[0])
nt.links.new(env.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 1.4; nt.links.new(bg.outputs[0], out.inputs[0])
# solen i panoramat ligger vid u≈0.15 → riktning (0.59,-0.81), låg. Rikta sol-lampan därifrån.
sun = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data.type == 'SUN'][0]
sun.location = (0.59 * 60, -0.81 * 60, 12); sun.data.energy = 4.0; sun.data.color = (1.0, 0.78, 0.55); sun.data.angle = math.radians(1.5)
tgt = bpy.data.objects.new("sol_mal", None); sc.collection.objects.link(tgt); tgt.location = (13, 6, 2)
c = sun.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'

# texturer från nya assets: 1K + packa
for im in bpy.data.images:
    if im.size[0] > 1024 and not im.name.startswith(("himmel", "travertin", "ek", "puts", "kalksten", "linne", "matta", "gras", "grus", "betong")):
        f = 1024 / max(im.size); im.scale(int(im.size[0] * f), int(im.size[1] * f))
    if not im.packed_file: im.pack()
bpy.ops.wm.save_as_mainfile(filepath=f"{ROOT}/out/herrgard_v4.blend", compress=True)
print("saved v4, objekt i Mobler:", len(placed.objects))
