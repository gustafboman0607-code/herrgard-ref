import os; os.environ["PYOPENGL_PLATFORM"] = "osmesa"
import numpy as np, trimesh, pyrender, pickle, sys
from PIL import Image
from build import COLORS
from program import ROOMS, LEVELS, BLOCKS

parts = pickle.load(open("out/parts.pkl", "rb"))

def look_at(eye, target, up=(0, 0, 1)):
    eye, target, up = map(lambda v: np.array(v, float), (eye, target, up))
    f = target - eye; f /= np.linalg.norm(f)
    s = np.cross(f, up); s /= np.linalg.norm(s)
    u = np.cross(s, f)
    m = np.eye(4); m[:3, 0] = s; m[:3, 1] = u; m[:3, 2] = -f; m[:3, 3] = eye
    return m

def make_scene(include, extra=None):
    scene = pyrender.Scene(bg_color=[0.78, 0.85, 0.95, 1.0], ambient_light=[0.35, 0.35, 0.35])
    for name in include:
        for m in parts.get(name, []):
            if m is None or not len(m.faces): continue
            c = np.array(COLORS[name][:3]) / 255
            mat = pyrender.MetallicRoughnessMaterial(baseColorFactor=[*c, 1.0], metallicFactor=0.0, roughnessFactor=0.4 if name == "glass" else 0.9)
            scene.add(pyrender.Mesh.from_trimesh(m, material=mat, smooth=False))
    for m, col in (extra or []):
        mat = pyrender.MetallicRoughnessMaterial(baseColorFactor=[*col, 1.0], metallicFactor=0.0, roughnessFactor=0.9)
        scene.add(pyrender.Mesh.from_trimesh(m, material=mat, smooth=False))
    sun = pyrender.DirectionalLight(color=[1.0, 0.95, 0.85], intensity=4.0)
    scene.add(sun, pose=look_at((40, -60, 60), (13, 5, 0)))
    fill = pyrender.DirectionalLight(color=[0.8, 0.85, 1.0], intensity=1.5)
    scene.add(fill, pose=look_at((-40, 40, 30), (13, 5, 0)))
    return scene

def render(scene, eye, target, out, w=1600, h=1000, yfov=0.75):
    cam = pyrender.PerspectiveCamera(yfov=yfov, aspectRatio=w / h)
    scene.add(cam, pose=look_at(eye, target))
    r = pyrender.OffscreenRenderer(w, h)
    color, _ = r.render(scene, flags=pyrender.RenderFlags.SHADOWS_DIRECTIONAL)
    r.delete()
    Image.fromarray(color).save(out)
    print("saved", out)

ALL = ["walls", "roof", "glass", "frames", "slab", "stone", "ground", "tech", "greenery", "water", "concrete", "brass"]

if __name__ == "__main__":
    s = make_scene(ALL)
    render(s, (-22, -48, 7), (13, 0, 4.5), "out/render_front.png", yfov=0.62)
    s = make_scene(ALL)
    render(s, (46, 48, 9), (15, 15, 4), "out/render_back.png", yfov=0.62)
    s = make_scene(ALL)
    render(s, (13, -95, 70), (13, -5, 2), "out/render_aerial.png")
    s = make_scene(ALL)
    render(s, (13, -26, 3.5), (13, 0, 4.0), "out/render_entry.png", yfov=0.7)
    # snittvyer per våning (dockhus): väggar + bjälklag för aktuell våning
    for i, (level, z0, hgt) in enumerate(LEVELS):
        lw = trimesh.load(f"out/vaggar_{level.replace(' ', '_').lower()}.stl")
        # kapa väggarna till 1.2 m höjd för överblick
        cut = trimesh.boolean.difference([lw, trimesh.creation.box(extents=(300, 300, 50)).apply_translation((13, 0, z0 + 1.2 + 25))], engine="manifold", check_volume=False)
        slab = parts["slab"][i]
        extra = [(cut, np.array(COLORS["walls"][:3]) / 255), (slab, np.array(COLORS["slab"][:3]) / 255)]
        if level == "Källare":
            cc = trimesh.boolean.difference([parts["concrete"][0], trimesh.creation.box(extents=(300, 300, 50)).apply_translation((13, 0, z0 + 1.2 + 25))], engine="manifold", check_volume=False)
            extra.append((cc, np.array(COLORS["concrete"][:3]) / 255))
        sc = make_scene([], extra)
        render(sc, (13, -28, 42 + z0), (13, 3, z0), f"out/snitt_{i}_{level.replace(' ', '_').lower()}.png", yfov=0.9)
