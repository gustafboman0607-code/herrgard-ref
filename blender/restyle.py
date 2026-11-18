"""Restyle: mörk modern-organisk interiör (travertin, rökt ek, svart stål, varma spots), ljus kalkputs ute.
Kör: python3 restyle.py  → out/herrgard_v2.blend"""
import bpy, math, os, sys, mathutils
sys.path.insert(0, "/home/claude/herrgard")
from program import ROOMS, LEVELS, BLOCKS

bpy.ops.wm.open_mainfile(filepath="/home/claude/herrgard/out/herrgard_moblerad.blend")
sc = bpy.context.scene

# ---------- hjälpare ----------
def principled(nt):
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); return b

def mapping(nt, scale):
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale); nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); return mp

def noisy_into(nt, b, base, var, scale=2.0, detail=6.0, bump=0.15, rough=0.7, rough_var=0.15, distortion=0.0):
    mp = mapping(nt, scale)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Detail"].default_value = detail; nz.inputs["Roughness"].default_value = 0.6; nz.inputs["Distortion"].default_value = distortion
    nt.links.new(mp.outputs[0], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (*base, 1); ramp.color_ramp.elements[1].color = (*var, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    r = nt.nodes.new("ShaderNodeMapRange"); r.inputs["To Min"].default_value = rough - rough_var; r.inputs["To Max"].default_value = rough + rough_var
    nt.links.new(nz.outputs["Fac"], r.inputs["Value"]); nt.links.new(r.outputs[0], b.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
    nz2 = nt.nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 40; nz2.inputs["Detail"].default_value = 8
    nt.links.new(mp.outputs[0], nz2.inputs["Vector"]); nt.links.new(nz2.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])
    return nz

def travertine_into(nt, b, base, var, vein, size=0.8):
    """stora plattor, horisontell ådring, matt-satin"""
    mp = mapping(nt, 1.0)
    br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0 / size; br.inputs["Mortar Size"].default_value = 0.006; br.offset = 0.0
    br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (0.92, 0.92, 0.92, 1); br.inputs["Mortar"].default_value = (0.45, 0.45, 0.45, 1)
    nt.links.new(mp.outputs[0], br.inputs["Vector"])
    mp2 = nt.nodes.new("ShaderNodeMapping"); mp2.inputs["Scale"].default_value = (1.0, 14.0, 1.0)
    tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], mp2.inputs["Vector"])
    w = nt.nodes.new("ShaderNodeTexNoise"); w.inputs["Scale"].default_value = 2.5; w.inputs["Detail"].default_value = 7; w.inputs["Distortion"].default_value = 1.2
    nt.links.new(mp2.outputs[0], w.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); e = ramp.color_ramp.elements
    e[0].position = 0.35; e[0].color = (*vein, 1); e[1].position = 0.6; e[1].color = (*base, 1)
    e2 = ramp.color_ramp.elements.new(0.9); e2.color = (*var, 1)
    nt.links.new(w.outputs["Fac"], ramp.inputs["Fac"])
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs["Factor"].default_value = 1.0
    nt.links.new(ramp.outputs["Color"], mul.inputs[6]); nt.links.new(br.outputs["Color"], mul.inputs[7])
    nt.links.new(mul.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.32; b.inputs["Specular IOR Level"].default_value = 0.6
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12
    pit = nt.nodes.new("ShaderNodeTexNoise"); pit.inputs["Scale"].default_value = 60; pit.inputs["Detail"].default_value = 10
    nt.links.new(mp.outputs[0], pit.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = 'ADD'
    nt.links.new(pit.outputs["Fac"], add.inputs[0]); nt.links.new(br.outputs["Fac"], add.inputs[1])
    nt.links.new(add.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])

def wood_into(nt, b, light, dark, scale=1.0, rough=0.38):
    mp = mapping(nt, 1.0); mp.inputs["Scale"].default_value = (scale * 0.4, scale * 12, scale * 0.4)
    w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = 'BANDS'; w.bands_direction = 'Y'; w.inputs["Scale"].default_value = 1.2; w.inputs["Distortion"].default_value = 7; w.inputs["Detail"].default_value = 3
    nt.links.new(mp.outputs[0], w.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (*dark, 1); ramp.color_ramp.elements[1].color = (*light, 1)
    nt.links.new(w.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough; b.inputs["Coat Weight"].default_value = 0.15; b.inputs["Coat Roughness"].default_value = 0.25
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.06
    nt.links.new(w.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])

def inside_factor(nt):
    """1 om punkten ligger inom husets fotavtryck (= insida), annars 0"""
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    total = None
    for (x0, y0, x1, y1) in BLOCKS.values():
        terms = []
        for axis, lo, hi in (("X", x0, x1), ("Y", y0, y1)):
            g = nt.nodes.new("ShaderNodeMath"); g.operation = 'GREATER_THAN'; g.inputs[1].default_value = lo - 0.02
            l = nt.nodes.new("ShaderNodeMath"); l.operation = 'LESS_THAN'; l.inputs[1].default_value = hi + 0.02
            nt.links.new(sep.outputs[axis], g.inputs[0]); nt.links.new(sep.outputs[axis], l.inputs[0])
            m = nt.nodes.new("ShaderNodeMath"); m.operation = 'MULTIPLY'; nt.links.new(g.outputs[0], m.inputs[0]); nt.links.new(l.outputs[0], m.inputs[1])
            terms.append(m)
        m = nt.nodes.new("ShaderNodeMath"); m.operation = 'MULTIPLY'; nt.links.new(terms[0].outputs[0], m.inputs[0]); nt.links.new(terms[1].outputs[0], m.inputs[1])
        # under taket (z < 7.3) – takvåningens insida räknas också
        zl = nt.nodes.new("ShaderNodeMath"); zl.operation = 'LESS_THAN'; zl.inputs[1].default_value = 7.35; nt.links.new(sep.outputs["Z"], zl.inputs[0])
        m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; nt.links.new(m.outputs[0], m2.inputs[0]); nt.links.new(zl.outputs[0], m2.inputs[1])
        if total is None: total = m2
        else:
            a = nt.nodes.new("ShaderNodeMath"); a.operation = 'ADD'; nt.links.new(total.outputs[0], a.inputs[0]); nt.links.new(m2.outputs[0], a.inputs[1]); total = a
    cl = nt.nodes.new("ShaderNodeClamp"); nt.links.new(total.outputs[0], cl.inputs[0]); return cl

def down_factor(nt):
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    l = nt.nodes.new("ShaderNodeMath"); l.operation = 'LESS_THAN'; l.inputs[1].default_value = -0.5; nt.links.new(sep.outputs["Z"], l.inputs[0]); return l

M = bpy.data.materials
CREAM, CREAM2 = (0.86, 0.80, 0.68), (0.80, 0.73, 0.60)
DARK_PL, DARK_PL2 = (0.33, 0.29, 0.25), (0.26, 0.23, 0.20)          # mörk mineralputs (väggar inne)
CEIL, CEIL2 = (0.40, 0.36, 0.32), (0.34, 0.31, 0.27)                 # tak inne
TRAV, TRAV2, VEIN = (0.36, 0.31, 0.26), (0.30, 0.26, 0.22), (0.20, 0.17, 0.14)  # mörk travertin
OAK_L, OAK_D = (0.30, 0.20, 0.12), (0.17, 0.11, 0.06)                # rökt ek

# ---------- väggar: ljus kalkputs ute, mörk mineralputs inne ----------
wm = M["Kalkputs"]; nt = wm.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial"); mix = nt.nodes.new("ShaderNodeMixShader")
b_out = principled(nt); noisy_into(nt, b_out, CREAM, CREAM2, scale=1.5, bump=0.12, rough=0.78)
b_in = principled(nt); noisy_into(nt, b_in, DARK_PL, DARK_PL2, scale=1.2, bump=0.18, rough=0.72, rough_var=0.12, distortion=0.4)
nt.links.new(inside_factor(nt).outputs[0], mix.inputs[0]); nt.links.new(b_out.outputs[0], mix.inputs[1]); nt.links.new(b_in.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0])

# ---------- bjälklag: travertin uppåt, mörkt tak nedåt ----------
sm = M["Kalkstensgolv"]; nt = sm.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial"); mix = nt.nodes.new("ShaderNodeMixShader")
b_f = principled(nt); travertine_into(nt, b_f, TRAV, TRAV2, VEIN, size=1.2)
b_c = principled(nt); noisy_into(nt, b_c, CEIL, CEIL2, scale=1.5, bump=0.10, rough=0.85)
nt.links.new(down_factor(nt).outputs[0], mix.inputs[0]); nt.links.new(b_f.outputs[0], mix.inputs[1]); nt.links.new(b_c.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0])

# ---------- ekgolv → rökt ek-plank ----------
for name, (l, d, s) in {"Ekgolv": (OAK_L, OAK_D, 0.5), "Ek": ((0.34, 0.23, 0.14), (0.20, 0.13, 0.07), 1.0)}.items():
    m = M[name]; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new("ShaderNodeOutputMaterial"); b = principled(nt); wood_into(nt, b, l, d, s); nt.links.new(b.outputs[0], out.inputs[0])

# ---------- kalksten (trappa, lister, entré) → varm ljus kalksten ute, travertin inne ----------
km = M["Kalksten"]; nt = km.node_tree; nt.nodes.clear(); out = nt.nodes.new("ShaderNodeOutputMaterial"); mix = nt.nodes.new("ShaderNodeMixShader")
b_o = principled(nt); noisy_into(nt, b_o, (0.80, 0.75, 0.64), (0.68, 0.62, 0.52), scale=0.8, bump=0.3, rough=0.6)
b_i = principled(nt); travertine_into(nt, b_i, TRAV, TRAV2, VEIN, size=0.6)
nt.links.new(inside_factor(nt).outputs[0], mix.inputs[0]); nt.links.new(b_o.outputs[0], mix.inputs[1]); nt.links.new(b_i.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0])

# ---------- mässing bort → svart stål; svart stål lite mattare ----------
for name in ("Mässing", "Svart stål"):
    m = M[name]; b = [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    b.inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1); b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.4
# rostfritt → mörkare borstat stål
b = [n for n in M["Rostfritt"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]; b.inputs["Base Color"].default_value = (0.35, 0.35, 0.36, 1); b.inputs["Roughness"].default_value = 0.4
# linne/matta mörkare
for name, base, var in (("Linne", (0.42, 0.38, 0.33), (0.34, 0.30, 0.26)), ("Matta2", (0.30, 0.25, 0.20), (0.22, 0.18, 0.14)), ("Matta", (0.30, 0.25, 0.20), (0.22, 0.18, 0.14))):
    if name in M:
        ramps = [n for n in M[name].node_tree.nodes if n.type == 'VALTORGB']
        for rp in ramps: rp.color_ramp.elements[0].color = (*base, 1); rp.color_ramp.elements[1].color = (*var, 1)

# ---------- mark: gräs med mer variation + grus-uppfart ----------
g = M["Gräs"]; ramps = [n for n in g.node_tree.nodes if n.type == 'VALTORGB']
for rp in ramps: rp.color_ramp.elements[0].color = (0.10, 0.17, 0.05, 1); rp.color_ramp.elements[1].color = (0.24, 0.30, 0.10, 1)
k = M["Kullersten"]; brs = [n for n in k.node_tree.nodes if n.type == 'TEX_BRICK']
for br in brs: br.inputs["Color1"].default_value = (0.40, 0.37, 0.33, 1); br.inputs["Color2"].default_value = (0.30, 0.28, 0.25, 1); br.inputs["Mortar"].default_value = (0.25, 0.23, 0.21, 1)

# ---------- möbler från Tripo: dämpa ljusa toner ----------
for m in M:
    if m.name.startswith("tripo_material") and m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs["Roughness"].default_value = max(n.inputs["Roughness"].default_value, 0.55)
                n.inputs["Specular IOR Level"].default_value = 0.35
        # mörka ner basfärgen via en Mix efter texturen
        for n in list(m.node_tree.nodes):
            if n.type == 'BSDF_PRINCIPLED' and n.inputs["Base Color"].is_linked:
                src = n.inputs["Base Color"].links[0].from_socket
                mx = m.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
                mx.inputs[7].default_value = (0.62, 0.58, 0.54, 1)
                m.node_tree.links.new(src, mx.inputs[6]); m.node_tree.links.new(mx.outputs[2], n.inputs["Base Color"])

# ---------- ljus ----------
for o in list(bpy.data.objects):
    if o.type == 'LIGHT' and o.data.type == 'AREA':
        o.data.energy *= 0.30; o.data.color = (1.0, 0.74, 0.52)   # svagt, varmt grundljus (2700K)
sun = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data.type == 'SUN'][0]
sun.data.energy = 3.2; sun.data.color = (1.0, 0.82, 0.62); sun.rotation_euler = (math.radians(70), 0, math.radians(215 - 180))
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.05 if "Background" in sc.world.node_tree.nodes else None

# varma spots längs väggarna (wall-wash) + ljusnischer i stora rum
Z = {l: (z, h) for l, z, h in LEVELS}
def spot(loc, energy=45, size=70, blend=0.7, name="S"):
    bpy.ops.object.light_add(type='SPOT', location=loc); L = bpy.context.object
    L.data.energy = energy; L.data.spot_size = math.radians(size); L.data.spot_blend = blend; L.data.color = (1.0, 0.70, 0.45); L.data.shadow_soft_size = 0.08
    L.rotation_euler = (0, 0, 0); L.name = name; return L
SKIP = ("Korridor", "Förråd", "Hiss & trappa", "Garderob", "Gäst-WC", "Skafferi / varulager", "Städ- & robotcentral", "Groventré")
for level, rooms in ROOMS.items():
    z0, h = Z[level]
    for name, x0, y0, x1, y1 in rooms:
        if name in SKIP: continue
        zc = z0 + h - 0.45
        n_x = max(1, int((x1 - x0) / 2.2)); n_y = max(1, int((y1 - y0) / 2.2))
        for i in range(n_x):          # längs y0 och y1-väggarna
            x = x0 + (x1 - x0) * (i + 0.5) / n_x
            spot((x, y0 + 0.35, zc), name=f"W_{name[:6]}_{i}a"); spot((x, y1 - 0.35, zc), name=f"W_{name[:6]}_{i}b")
        for j in range(n_y):          # längs x0 och x1-väggarna
            y = y0 + (y1 - y0) * (j + 0.5) / n_y
            spot((x0 + 0.35, y, zc), name=f"W_{name[:6]}_{j}c"); spot((x1 - 0.35, y, zc), name=f"W_{name[:6]}_{j}d")
        if name == "Entréhall (dubbelhöjd)":
            for L in [o for o in bpy.data.objects if o.name.startswith("W_Entréh")]: L.location.z = z0 + 7.5; L.data.energy = 90

# ---------- kamera ----------
cam = sc.camera; cam.data.lens = 24; cam.data.dof.use_dof = True; cam.data.dof.focus_object = bpy.data.objects["Blick"]; cam.data.dof.aperture_fstop = 4.0
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = 0.5
sc.cycles.samples = 128; sc.cycles.use_denoising = True; sc.cycles.adaptive_threshold = 0.03
sc.render.film_transparent = False

bpy.ops.wm.save_as_mainfile(filepath="/home/claude/herrgard/out/herrgard_v2.blend", compress=True)
print("saved v2, lights:", len([o for o in bpy.data.objects if o.type == 'LIGHT']))

# ---------- fix: matsalens spis stod mitt för dörren (21,8) → flytta till x=17.5 ----------
import bmesh
fs = bpy.data.objects["f_stone"]
bm = bmesh.new(); bm.from_mesh(fs.data); mw = fs.matrix_world; inv = mw.inverted()
moved = 0
for v in bm.verts:
    p = mw @ v.co
    if 19.5 <= p.x <= 22.5 and 7.0 <= p.y <= 8.2 and -0.1 <= p.z <= 3.0:
        v.co = inv @ (p + mathutils.Vector((-3.5, 0, 0))); moved += 1
bm.to_mesh(fs.data); bm.free(); fs.data.update(); print("fireplace verts moved:", moved)
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/herrgard/out/herrgard_v2.blend", compress=True)
