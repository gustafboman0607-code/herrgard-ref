import os; os.environ["PYOPENGL_PLATFORM"] = "osmesa"
import numpy as np, trimesh, pyrender, pickle
from PIL import Image
from build import COLORS
from furnish import MAT
from program import ROOMS, LEVELS
from render import look_at

parts = pickle.load(open("out/parts.pkl", "rb"))
furn = pickle.load(open("out/furniture.pkl", "rb"))
Z = {l: z for l, z, h in LEVELS}

def scene_with_lights(level_rooms):
    sc = pyrender.Scene(bg_color=[0.80, 0.86, 0.95, 1.0], ambient_light=[0.22, 0.20, 0.18])
    def addm(m, col, rough=0.9, alpha=1.0):
        c = np.array(col[:3]) / 255
        mat = pyrender.MetallicRoughnessMaterial(baseColorFactor=[*c, alpha], metallicFactor=0.0, roughnessFactor=rough, alphaMode="BLEND" if alpha < 1 else "OPAQUE")
        sc.add(pyrender.Mesh.from_trimesh(m, material=mat, smooth=False))
    for name in ["walls", "slab", "stone", "frames", "brass", "concrete", "tech"]:
        for m in parts[name]: addm(m, COLORS[name])
    for m in parts["glass"]: addm(m, (140, 175, 205), 0.2, 0.35)
    for name, ms in furn.items():
        col = MAT[name]; alpha = col[3] / 255
        for m in ms: addm(m, col, 0.3 if name in ("glass", "water", "brass") else 0.85, alpha)
    sun = pyrender.DirectionalLight(color=[1.0, 0.93, 0.80], intensity=2.5)
    sc.add(sun, pose=look_at((30, -50, 40), (13, 5, 0)))
    for level, z0, h in LEVELS:
        for name, x0, y0, x1, y1 in ROOMS[level]:
            if (level, name) not in level_rooms: continue
            area = (x1 - x0) * (y1 - y0)
            n = 1 if area < 40 else (2 if area < 90 else 3)
            for i in range(n):
                px = x0 + (x1 - x0) * (i + 1) / (n + 1); py = (y0 + y1) / 2
                L = pyrender.PointLight(color=[1.0, 0.85, 0.65], intensity=55.0 + area * 0.6)
                p = np.eye(4); p[:3, 3] = (px, py, z0 + h - 0.45); sc.add(L, pose=p)
    return sc

def render(sc, eye, target, out, w=1600, h=1000, yfov=1.05):
    cam = pyrender.PerspectiveCamera(yfov=yfov, aspectRatio=w / h, znear=0.05)
    sc.add(cam, pose=look_at(eye, target))
    r = pyrender.OffscreenRenderer(w, h); color, _ = r.render(sc); r.delete()
    Image.fromarray(color).save(out); print("saved", out)

VIEWS = [
    ("Plan 1", "Entréhall (dubbelhöjd)", (13, 0.6, 1.7), (12.5, 8, 2.5)),
    ("Plan 1", "Salong", (7.6, 1.2, 1.6), (2, 6, 1.3)),
    ("Plan 1", "Matsal", (16.4, 1.0, 1.6), (24, 6, 1.2)),
    ("Plan 1", "Eget kök", (-1.0, 10.4, 1.6), (-5.5, 5, 1.0)),
    ("Plan 1", "AI-kök (robotkök)", (-1.0, 2.4, 1.6), (-8, -2, 1.2)),
    ("Plan 1", "Bibliotek", (7.0, 9.0, 1.6), (1, 13.5, 1.3)),
    ("Plan 2", "Master sovrum", (-1.0, 4.4, 1.6 + 3.9), (-7, -2, 1.0 + 3.9)),
    ("Källare", "Pool & spa", (12.2, 0.8, 1.7 - 3.2), (17, 13, -0.6 - 3.2)),
    ("Källare", "Biograf", (20.3, 7.6, 1.5 - 3.2), (25, 1.5, 0.2 - 3.2)),
    ("Källare", "Serverrum", (-5.2, 6.8, 1.6 - 3.2), (-9.5, 3.5, 0.9 - 3.2)),
]
if __name__ == "__main__":
    rooms = {(l, r) for l, r, _, _ in VIEWS} | {("Plan 1", "Orangeri"), ("Plan 1", "Vardagsrum"), ("Plan 1", "Hiss & trappa"), ("Plan 2", "Galleri (öppet ner)"), ("Källare", "Bastu & relax"), ("Källare", "Teknik / UPS / el")}
    for i, (level, room, eye, tgt) in enumerate(VIEWS):
        sc = scene_with_lights(rooms)
        render(sc, eye, tgt, f"out/int_{i:02d}_{room.split(' ')[0].lower()}.png")
