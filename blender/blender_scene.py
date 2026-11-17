"""Bygger Blender-scenen: hus + möbler, PBR-material, ljus, kamerabana. Sparar herrgard.blend."""
import bpy, math, sys, json
sys.path.insert(0, "/home/claude/herrgard")
from program import ROOMS, LEVELS, BLOCKS
from mathutils import Vector

ROOT = "/home/claude/herrgard"
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'

# ---------- import ----------
bpy.ops.import_scene.gltf(filepath=f"{ROOT}/out/herrgard.glb")
bpy.ops.import_scene.gltf(filepath=f"{ROOT}/out/furniture.glb")
# trimesh-GLB kommer in med Y/Z bytta -> rotera meshdata -90 grader runt X
from mathutils import Matrix
for o in bpy.data.objects:
    if o.type == 'MESH': o.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'X'))
objs = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
print("objects:", sorted(objs))

# ---------- material-fabrik ----------
def new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return m, nt, bsdf

def tex_coord(nt, scale):
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); return mp

def noisy(nt, bsdf, base, var, scale=2.0, detail=6.0, bump=0.15, rough=0.7, rough_var=0.15):
    mp = tex_coord(nt, scale)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Detail"].default_value = detail; nz.inputs["Roughness"].default_value = 0.6
    nt.links.new(mp.outputs[0], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (*base, 1); ramp.color_ramp.elements[1].color = (*var, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    r = nt.nodes.new("ShaderNodeMapRange"); r.inputs["To Min"].default_value = rough - rough_var; r.inputs["To Max"].default_value = rough + rough_var
    nt.links.new(nz.outputs["Fac"], r.inputs["Value"]); nt.links.new(r.outputs[0], bsdf.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
    nz2 = nt.nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 40; nz2.inputs["Detail"].default_value = 8
    nt.links.new(mp.outputs[0], nz2.inputs["Vector"]); nt.links.new(nz2.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs[0], bsdf.inputs["Normal"])

def wood(nt, bsdf, light, dark, scale=1.0):
    mp = tex_coord(nt, scale)
    mp.inputs["Scale"].default_value = (scale * 0.4, scale * 12, scale * 0.4)
    w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = 'BANDS'; w.bands_direction = 'Y'; w.inputs["Scale"].default_value = 1.2; w.inputs["Distortion"].default_value = 6; w.inputs["Detail"].default_value = 3
    nt.links.new(mp.outputs[0], w.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (*dark, 1); ramp.color_ramp.elements[1].color = (*light, 1)
    nt.links.new(w.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.45
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08
    nt.links.new(w.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs[0], bsdf.inputs["Normal"])

def tiles(nt, bsdf, base, var, size=0.6, grout=0.012):
    mp = tex_coord(nt, 1.0)
    br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0 / size; br.inputs["Mortar Size"].default_value = grout; br.offset = 0.5
    br.inputs["Color1"].default_value = (*base, 1); br.inputs["Color2"].default_value = (*var, 1); br.inputs["Mortar"].default_value = (0.55, 0.52, 0.48, 1)
    nt.links.new(mp.outputs[0], br.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3; nz.inputs["Detail"].default_value = 6
    nt.links.new(mp.outputs[0], nz.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.inputs["Factor"].default_value = 0.35
    nt.links.new(br.outputs["Color"], mix.inputs[6]); nt.links.new(nz.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.35
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25
    nt.links.new(br.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs[0], bsdf.inputs["Normal"])

MATS = {}
def mat(name, kind, **kw):
    m, nt, b = new_mat(name)
    if kind == "plaster": noisy(nt, b, kw["base"], kw["var"], scale=1.5, bump=0.12, rough=0.75)
    elif kind == "stone": noisy(nt, b, kw["base"], kw["var"], scale=0.8, bump=0.3, rough=0.6)
    elif kind == "slate": noisy(nt, b, kw["base"], kw["var"], scale=3.0, bump=0.5, rough=0.55, rough_var=0.1)
    elif kind == "wood": wood(nt, b, kw["light"], kw["dark"], kw.get("scale", 1.0))
    elif kind == "tiles": tiles(nt, b, kw["base"], kw["var"], kw.get("size", 0.6))
    elif kind == "glass":
        b.inputs["Base Color"].default_value = (0.9, 0.95, 1.0, 1); b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.02; b.inputs["IOR"].default_value = 1.5
    elif kind == "metal":
        b.inputs["Base Color"].default_value = (*kw["base"], 1); b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = kw.get("rough", 0.3)
    elif kind == "fabric":
        noisy(nt, b, kw["base"], kw["var"], scale=30, detail=4, bump=0.35, rough=0.95, rough_var=0.04); b.inputs["Sheen Weight"].default_value = 0.6
    elif kind == "water":
        b.inputs["Base Color"].default_value = (0.75, 0.9, 0.95, 1); b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.05; b.inputs["IOR"].default_value = 1.33
        mp = tex_coord(nt, 2.0); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6; nt.links.new(mp.outputs[0], nz.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.06; nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])
    elif kind == "flat":
        b.inputs["Base Color"].default_value = (*kw["base"], 1); b.inputs["Roughness"].default_value = kw.get("rough", 0.8)
    elif kind == "grass":
        noisy(nt, b, kw["base"], kw["var"], scale=8, detail=8, bump=0.6, rough=0.9, rough_var=0.05)
    MATS[name] = m; return m

CREAM = (0.86, 0.80, 0.68); CREAM2 = (0.80, 0.73, 0.60)
mat("Kalkputs", "plaster", base=CREAM, var=CREAM2)
mat("Kalksten", "stone", base=(0.82, 0.77, 0.66), var=(0.70, 0.64, 0.54))
mat("Skiffer", "slate", base=(0.11, 0.12, 0.14), var=(0.20, 0.21, 0.24))
mat("Glas", "glass")
mat("Svart stål", "metal", base=(0.03, 0.03, 0.03), rough=0.45)
mat("Mässing", "metal", base=(0.85, 0.62, 0.30), rough=0.25)
mat("Kalkstensgolv", "tiles", base=(0.78, 0.72, 0.62), var=(0.68, 0.62, 0.52), size=0.8)
mat("Ek", "wood", light=(0.62, 0.45, 0.27), dark=(0.40, 0.27, 0.15))
mat("Ekgolv", "wood", light=(0.58, 0.42, 0.25), dark=(0.42, 0.29, 0.16), scale=0.5)
mat("Linne", "fabric", base=(0.80, 0.75, 0.66), var=(0.72, 0.67, 0.58))
mat("Grön sammet", "fabric", base=(0.12, 0.22, 0.15), var=(0.08, 0.15, 0.10))
mat("Läder", "flat", base=(0.30, 0.17, 0.09), rough=0.35)
mat("Matta", "fabric", base=(0.45, 0.32, 0.22), var=(0.30, 0.20, 0.14))
mat("Svart lack", "flat", base=(0.02, 0.02, 0.02), rough=0.3)
mat("Rostfritt", "metal", base=(0.6, 0.6, 0.6), rough=0.35)
mat("Terrakotta", "stone", base=(0.55, 0.30, 0.20), var=(0.45, 0.24, 0.16))
mat("Rotting", "wood", light=(0.70, 0.55, 0.35), dark=(0.55, 0.40, 0.24), scale=3)
mat("Grönska", "fabric", base=(0.10, 0.30, 0.08), var=(0.05, 0.18, 0.05))
mat("Vatten", "water")
mat("Gräs", "grass", base=(0.18, 0.32, 0.10), var=(0.28, 0.42, 0.14))
mat("Betong", "stone", base=(0.5, 0.5, 0.5), var=(0.4, 0.4, 0.4))
mat("Kullersten", "tiles", base=(0.55, 0.52, 0.48), var=(0.42, 0.40, 0.37), size=0.12)
mat("Teknikgrå", "flat", base=(0.3, 0.32, 0.34), rough=0.5)

ASSIGN = {
    "walls": "Kalkputs", "roof": "Skiffer", "glass": "Glas", "frames": "Svart stål", "slab": "Kalkstensgolv", "stone": "Kalksten",
    "ground": "Gräs", "tech": "Teknikgrå", "greenery": "Grönska", "water": "Vatten", "concrete": "Betong", "brass": "Mässing",
    "f_oak": "Ek", "f_stone": "Kalksten", "f_brass": "Mässing", "f_linen": "Linne", "f_green": "Grön sammet", "f_rug": "Matta",
    "f_black": "Svart lack", "f_steel": "Rostfritt", "f_glass": "Glas", "f_leather": "Läder", "f_terracotta": "Terrakotta",
    "f_rattan": "Rotting", "f_greenery": "Grönska", "f_water": "Vatten",
}
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    key = o.name.split(".")[0]
    if key in ASSIGN:
        o.data.materials.clear(); o.data.materials.append(MATS[ASSIGN[key]])
        for p in o.data.polygons: p.use_smooth = False
    o.data.validate()

# kullersten: egen plan ovanpå gårdsplanen (så att stone-gruppen kan vara kalksten)
bpy.ops.mesh.primitive_plane_add(size=1, location=(13, -13, -0.549)); cp = bpy.context.object; cp.scale = (50, 26.3, 1); cp.name = "Gardsplan"; cp.data.materials.append(MATS["Kullersten"])
bpy.ops.mesh.primitive_plane_add(size=1, location=(13, -53, -0.549)); dp = bpy.context.object; dp.scale = (5, 54, 1); dp.name = "Uppfart"; dp.data.materials.append(MATS["Kullersten"])
# ekgolv i salong, bibliotek, matsal, sovrum
for (x0, y0, x1, y1, z) in ((0, 0, 8, 8, 0), (0, 8, 8, 15, 0), (16, 0, 26, 8, 0), (16, 8, 26, 15, 0), (-10, -3, 0, 5, 3.9), (0, 0, 8, 7, 3.9), (16, 0, 26, 7, 3.9), (16, 7, 22, 15, 3.9), (10, 9, 16, 15, 3.9)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, z + 0.012)); f = bpy.context.object; f.scale = (x1 - x0 - 0.3, y1 - y0 - 0.3, 1); f.data.materials.append(MATS["Ekgolv"])

# ---------- värld & sol ----------
w = bpy.data.worlds.new("Himmel"); sc.world = w; w.use_nodes = True
nt = w.node_tree; nt.nodes.clear(); bg = nt.nodes.new("ShaderNodeBackground"); out = nt.nodes.new("ShaderNodeOutputWorld")
sky = nt.nodes.new("ShaderNodeTexSky"); sky.sky_type = 'MULTIPLE_SCATTERING'; sky.sun_elevation = math.radians(14); sky.sun_rotation = math.radians(215); sky.sun_intensity = 0.6; sky.altitude = 100
nt.links.new(sky.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.035; nt.links.new(bg.outputs[0], out.inputs[0])
bpy.ops.object.light_add(type='SUN', location=(0, 0, 50)); sun = bpy.context.object; sun.data.energy = 2.5; sun.data.color = (1.0, 0.86, 0.7); sun.data.angle = math.radians(1.5)
sun.rotation_euler = (math.radians(76), 0, math.radians(215 - 180))

# ---------- invändigt ljus: varma area-ljus per rum + "cove" ----------
Z = {l: (z, h) for l, z, h in LEVELS}
for level, rooms in ROOMS.items():
    z0, h = Z[level]
    for name, x0, y0, x1, y1 in rooms:
        area = (x1 - x0) * (y1 - y0)
        if name in ("Korridor", "Förråd", "Hiss & trappa") and area < 20: continue
        bpy.ops.object.light_add(type='AREA', location=((x0 + x1) / 2, (y0 + y1) / 2, z0 + h - 0.9))
        L = bpy.context.object; L.data.shape = 'RECTANGLE'; L.data.size = max(1.0, (x1 - x0) - 1.5); L.data.size_y = max(1.0, (y1 - y0) - 1.5)
        L.data.energy = 60 + area * 6; L.data.color = (1.0, 0.80, 0.60); L.name = f"L_{level}_{name}"
        if name == "Entréhall (dubbelhöjd)": L.location.z = z0 + 7.0; L.data.energy = 900
        if name == "Pool & spa": L.data.color = (1.0, 0.75, 0.5); L.data.energy *= 0.6

# ---------- kamerabana ----------
bpy.ops.object.camera_add(location=(13, -85, 2)); cam = bpy.context.object; cam.name = "Kamera"; sc.camera = cam
cam.data.lens = 22; cam.data.sensor_width = 36; cam.data.clip_start = 0.05; cam.data.clip_end = 500
bpy.ops.object.empty_add(location=(13, 0, 4)); tgt = bpy.context.object; tgt.name = "Blick"
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'

FPS = 24
# (tid s, kamerapos, blickpunkt)
PATH = [
    (0,   (13, -92, 2.2),  (13, 0, 5)),      # grinden
    (6,   (13, -40, 2.0),  (13, 0, 4.5)),    # allén
    (11,  (13, -14, 1.8),  (13, 0, 3.5)),    # gårdsplanen
    (15,  (13, -4.5, 1.7), (13, 2, 2.6)),    # entrétrappan
    (19,  (13, 1.0, 1.7),  (13, 8, 2.4)),    # in i hallen
    (23,  (13, 5.0, 1.7),  (12, 9.5, 3.0)),    # hallen, trappan
    (27,  (10.8, 2.0, 1.6),(4, 4, 1.3)),     # mot salongen
    (31,  (6.5, 2.5, 1.6), (2, 5, 1.2)),     # salong
    (35,  (6.5, 6.5, 1.6), (4, 0.5, 1.3)),   # salong mot spisen
    (40,  (12, 4.5, 1.6),  (18, 4, 1.4)),    # tillbaka genom hallen
    (44,  (16.6, 4.0, 1.6),(24, 4, 1.2)),    # matsalen
    (48,  (21, 5.5, 1.6),  (21, 12, 1.3)),   # mot vardagsrummet
    (52,  (21, 10.5, 1.6), (13, 12, 1.4)),   # vardagsrum
    (56,  (15.5, 11.5, 1.6),(11, 12, 1.6)),  # orangeri
    (60,  (13, 15.3, 1.6), (13, 19, 1.4)),   # ut på terrassen
    (64,  (18, 21, 1.7),   (13, 8, 4)),      # vänder mot huset
    (69,  (6, 4.5, 1.6),   (0, 6, 1.4)),     # tillbaka via salong (cut)
    (73,  (-1.5, 6.5, 1.6),(-6, 6, 1.2)),    # köket
    (77,  (-4, 9.5, 1.6),  (-5.5, 3.5, 1.1)),# köket mot spisen
    (81,  (-3, 2.0, 1.6),  (-5, -2.5, 1.2)), # AI-köket
    (85,  (-7, -1.5, 1.6), (-1, 0, 1.3)),    # AI-köket, stationen
    (90,  (13, 5, 2.0),    (13, 4, 6)),      # hallen, blick upp (cut)
    (94,  (13, 5, 5.6),    (9, 2.5, 5.3)),   # galleriet plan 2
    (98,  (4, 3, 5.5),     (-4, 1.5, 5.2)),  # sovrum 2 → master
    (102, (-1.5, 1.5, 5.5),(-8, 0, 5.0)),    # master
    (106, (-6, 3.5, 5.5),  (-4, -2.5, 5.2)), # master mot spisen
    (110, (-2.5, 6.0, 5.5),(-2.5, 10.5, 4.8)),# spa-badet
    (115, (9.5, 7.5, 1.7), (9.5, 7.5, -2.5)),# ner genom trapphuset (cut)
    (119, (9.5, 7.5, -1.6),(13, 3, -2.0)),   # källaren
    (123, (12.5, 1.5, -1.5),(17, 12, -2.6)), # poolen
    (128, (14, 11, -1.5),  (3, 13, -1.8)),   # pool mot bastun
    (132, (20.5, 4, -1.6), (25, 3, -2.3)),   # biografen
    (137, (-5.5, 6.5, -1.6),(-9.5, 3.5, -2.3)),# serverrum / KC
    (141, (-2, 1.5, -1.6), (-4.8, 0.5, -2.0)),# ståldörren
    (146, (13, 5, 13),     (13, 8, 12)),     # upp på taket (cut)
    (150, (20, -10, 16),   (13, 7, 12.5)),   # drönardockan
    (156, (40, -70, 30),   (13, 2, 5)),      # avslut, flyger ut
]
for t, p, look in PATH:
    f = int(t * FPS) + 1
    cam.location = p; cam.keyframe_insert("location", frame=f)
    tgt.location = look; tgt.keyframe_insert("location", frame=f)
def fcurves_of(ob):
    act = ob.animation_data.action
    if hasattr(act, "fcurves") and len(act.fcurves): return list(act.fcurves)
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out
for ob in (cam, tgt):
    for fc in fcurves_of(ob):
        for k in fc.keyframe_points: k.interpolation = 'BEZIER'; k.easing = 'AUTO'; k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
sc.frame_start = 1; sc.frame_end = int(156 * FPS); sc.render.fps = FPS
# "cuts": gör hoppen momentana genom att sätta CONSTANT på frame innan hoppet
CUTS = [64, 85, 110, 141]
for ob in (cam, tgt):
    for fc in fcurves_of(ob):
        for k in fc.keyframe_points:
            if any(abs(k.co[0] - (t * FPS + 1)) < 1 for t in CUTS): k.interpolation = 'CONSTANT'

# ---------- render-inställningar ----------
sc.render.engine = 'CYCLES'; sc.cycles.device = 'GPU'; sc.cycles.samples = 256; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 8; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.resolution_x = 1920; sc.render.resolution_y = 1080; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = "//render/frame_"
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.use_motion_blur = False
bpy.ops.wm.save_as_mainfile(filepath=f"{ROOT}/out/herrgard.blend")
print("saved blend")
