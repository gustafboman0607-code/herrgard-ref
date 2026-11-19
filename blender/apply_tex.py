"""Byt procedurella material mot PBR-texturer (tex/<namn>_{col,nrm,rgh}.png). Kör efter restyle.py.
out/herrgard_v2.blend → out/herrgard_v3.blend"""
import bpy, os, sys
sys.path.insert(0, "/home/claude/herrgard")
from program import BLOCKS
TEX = "/home/claude/herrgard/tex"
bpy.ops.wm.open_mainfile(filepath="/home/claude/herrgard/out/herrgard_v2.blend")
sc = bpy.context.scene
M = bpy.data.materials

def img(name):
    p = f"{TEX}/{name}.png"
    if name in bpy.data.images: return bpy.data.images[name]
    i = bpy.data.images.load(p); i.name = name
    if not name.endswith("_col"): i.colorspace_settings.name = 'Non-Color'
    return i

def pbr_bsdf(nt, name, scale, strength=0.6, rough_mul=1.0, tint=None, proj='BOX'):
    """principled med col/nrm/rgh via box-mapping i objektkoordinater. scale = meter per upprepning"""
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    s = 1.0 / scale; mp.inputs["Scale"].default_value = (s, s, s); nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    def tex(suffix):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img(f"{name}{suffix}"); t.projection = proj; t.projection_blend = 0.3
        nt.links.new(mp.outputs[0], t.inputs["Vector"]); return t
    c = tex("_col")
    if tint:
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
        mx.inputs[7].default_value = (*tint, 1); nt.links.new(c.outputs["Color"], mx.inputs[6]); nt.links.new(mx.outputs[2], b.inputs["Base Color"])
    else:
        nt.links.new(c.outputs["Color"], b.inputs["Base Color"])
    r = tex("_rgh")
    if rough_mul != 1.0:
        m = nt.nodes.new("ShaderNodeMath"); m.operation = 'MULTIPLY'; m.inputs[1].default_value = rough_mul
        nt.links.new(r.outputs["Color"], m.inputs[0]); nt.links.new(m.outputs[0], b.inputs["Roughness"])
    else:
        nt.links.new(r.outputs["Color"], b.inputs["Roughness"])
    n = tex("_nrm"); nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = strength
    nt.links.new(n.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs[0], b.inputs["Normal"])
    return b

def inside_factor(nt):
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
    total = None
    for (x0, y0, x1, y1) in BLOCKS.values():
        acc = None
        for axis, lo, hi in (("X", x0, x1), ("Y", y0, y1), ("Z", -9, 7.35)):
            g = nt.nodes.new("ShaderNodeMath"); g.operation = 'GREATER_THAN'; g.inputs[1].default_value = lo - 0.02
            l = nt.nodes.new("ShaderNodeMath"); l.operation = 'LESS_THAN'; l.inputs[1].default_value = hi + 0.02
            nt.links.new(sep.outputs[axis], g.inputs[0]); nt.links.new(sep.outputs[axis], l.inputs[0])
            m = nt.nodes.new("ShaderNodeMath"); m.operation = 'MULTIPLY'; nt.links.new(g.outputs[0], m.inputs[0]); nt.links.new(l.outputs[0], m.inputs[1])
            if acc is None: acc = m
            else:
                m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; nt.links.new(acc.outputs[0], m2.inputs[0]); nt.links.new(m.outputs[0], m2.inputs[1]); acc = m2
        if total is None: total = acc
        else:
            a = nt.nodes.new("ShaderNodeMath"); a.operation = 'ADD'; nt.links.new(total.outputs[0], a.inputs[0]); nt.links.new(acc.outputs[0], a.inputs[1]); total = a
    cl = nt.nodes.new("ShaderNodeClamp"); nt.links.new(total.outputs[0], cl.inputs[0]); return cl

def down_factor(nt):
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    l = nt.nodes.new("ShaderNodeMath"); l.operation = 'LESS_THAN'; l.inputs[1].default_value = -0.5; nt.links.new(sep.outputs["Z"], l.inputs[0]); return l

def two_way(matname, factor_fn, a_args, b_args):
    m = M[matname]; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new("ShaderNodeOutputMaterial"); mix = nt.nodes.new("ShaderNodeMixShader")
    A = pbr_bsdf(nt, **a_args); B = pbr_bsdf(nt, **b_args)
    nt.links.new(factor_fn(nt).outputs[0], mix.inputs[0]); nt.links.new(A.outputs[0], mix.inputs[1]); nt.links.new(B.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0])

def one_way(matname, **args):
    m = M[matname]; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new("ShaderNodeOutputMaterial"); b = pbr_bsdf(nt, **args); nt.links.new(b.outputs[0], out.inputs[0])

# väggar: ute ljus kalkputs / inne mörk mineralputs
two_way("Kalkputs", inside_factor, dict(name="puts_ute", scale=3.0, strength=0.4), dict(name="puts_inne", scale=2.5, strength=0.5, tint=(0.80, 0.78, 0.76)))
# bjälklag: golv travertin / tak mörk puts
two_way("Kalkstensgolv", down_factor, dict(name="travertin", scale=2.4, strength=0.5), dict(name="puts_inne", scale=2.5, strength=0.3, tint=(0.75, 0.73, 0.71)))
# kalksten (lister, trappa, spisar, pelare): ute ljus kalksten / inne travertin
two_way("Kalksten", inside_factor, dict(name="kalksten", scale=1.6, strength=0.5), dict(name="travertin", scale=1.6, strength=0.5))
one_way("Ekgolv", name="ek", scale=2.0, strength=0.5)
one_way("Ek", name="ek", scale=1.2, strength=0.4)
if "Linne" in M: one_way("Linne", name="linne", scale=0.6, strength=0.6)
if "Matta2" in M: one_way("Matta2", name="matta", scale=0.8, strength=0.7)
if "Matta" in M: one_way("Matta", name="matta", scale=0.8, strength=0.7)
one_way("Gräs", name="gras", scale=2.5, strength=0.6)
one_way("Kullersten", name="grus", scale=1.2, strength=0.7)
one_way("Betong", name="betong", scale=3.0, strength=0.4)
one_way("Teknikgrå", name="betong", scale=2.0, strength=0.3, tint=(0.7, 0.72, 0.75))

# packa texturerna i filen så den är självständig på mongo
for i in bpy.data.images:
    if i.name.split("_")[0] in ("travertin", "ek", "puts", "kalksten", "linne", "matta", "gras", "grus", "betong"):
        i.pack()
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/herrgard/out/herrgard_v3.blend", compress=True)
print("saved v3")
