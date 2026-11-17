"""Inredning av nyckelrum i 3D-modellen (enkla volymer med materialfärger) – förhandsvisning innan rendering."""
import numpy as np, trimesh, pickle
from trimesh.creation import cylinder, icosphere
from build import box, union, COLORS
from program import ROOMS, LEVELS

def room(level, name):
    for n, x0, y0, x1, y1 in ROOMS[level]:
        if n == name: return x0, y0, x1, y1
    raise KeyError(name)

Z = {l: z for l, z, h in LEVELS}
F = {}  # material -> list of meshes
def add(mat, m): F.setdefault(mat, []).append(m)

def sofa(x, y, w, d, z, rot=0):
    parts = [box(-w/2, -d/2, 0.0, w/2, d/2, 0.42), box(-w/2, d/2-0.25, 0.42, w/2, d/2, 0.85), box(-w/2, -d/2, 0.42, -w/2+0.25, d/2, 0.65), box(w/2-0.25, -d/2, 0.42, w/2, d/2, 0.65)]
    m = union(parts); m.apply_transform(trimesh.transformations.rotation_matrix(rot, (0, 0, 1))); m.apply_translation((x, y, z)); return m

def table(x, y, w, d, z, h=0.75, top=0.05):
    m = union([box(-w/2, -d/2, h-top, w/2, d/2, h)] + [box(sx-0.05, sy-0.05, 0, sx+0.05, sy+0.05, h-top) for sx in (-w/2+0.15, w/2-0.15) for sy in (-d/2+0.15, d/2-0.15)])
    m.apply_translation((x, y, z)); return m

def chair(x, y, z, rot=0):
    m = union([box(-0.25, -0.25, 0.4, 0.25, 0.25, 0.46), box(-0.25, 0.18, 0.46, 0.25, 0.25, 0.95)] + [box(sx-0.02, sy-0.02, 0, sx+0.02, sy+0.02, 0.4) for sx in (-0.2, 0.2) for sy in (-0.2, 0.2)])
    m.apply_transform(trimesh.transformations.rotation_matrix(rot, (0, 0, 1))); m.apply_translation((x, y, z)); return m

def bed(x, y, z, w=2.0, d=2.2):
    return union([box(-w/2, -d/2, 0, w/2, d/2, 0.55), box(-w/2, d/2-0.1, 0, w/2, d/2, 1.3), box(-w/2+0.1, -d/2+0.1, 0.55, w/2-0.1, d/2-0.4, 0.75)]).apply_translation((x, y, z))

def fireplace(x, y, z, facing='y+', w=2.4):
    # spiskåpa i kalksten mot vägg, öppning svart
    body = box(-w/2, -0.5, 0, w/2, 0.0, 1.5); hole = box(-0.6, -0.5, 0.1, 0.6, 0.0, 1.0)
    m = trimesh.boolean.difference([body, hole], engine="manifold")
    r = {'y+': 0, 'y-': np.pi, 'x+': -np.pi/2, 'x-': np.pi/2}[facing]
    m.apply_transform(trimesh.transformations.rotation_matrix(r, (0, 0, 1))); m.apply_translation((x, y, z)); return m

def chandelier(x, y, z, r=0.9):
    ring = trimesh.creation.annulus(r_min=r-0.06, r_max=r, height=0.08); ring.apply_translation((x, y, z))
    rod = cylinder(radius=0.02, height=1.2).apply_translation((x, y, z+0.6)); return union([ring, rod])

def shelves(x0, y0, x1, y1, z, h=3.4):
    return box(x0, y0, z, x1, y1, z+h)

def column(x, y, z, h, r=0.3):
    return cylinder(radius=r, height=h, sections=24).apply_translation((x, y, z+h/2))

# ---------- Plan 1 ----------
z1 = Z["Plan 1"]
x0, y0, x1, y1 = room("Plan 1", "Entréhall (dubbelhöjd)")
# svängd trappa längs västra väggen upp till plan 2
steps = []
n = 22
for i in range(n):
    a = np.pi * 0.9 * i / n
    cx, cy = x0 + 0.3, y0 + 4.5
    rx, ry = 2.6 + 0.0, 2.6
    px, py = cx + rx * np.cos(np.pi/2 - a) * 0 + (i / n) * 0, 0
    # enkel: rak trappa längs väggen med svag kurva
    t = i / (n - 1)
    sx = x0 + 0.2 + 0.9 * np.sin(t * np.pi)  # buktar ut i rummet
    sy = y0 + 0.8 + t * 7.2
    steps.append(box(sx, sy - 0.15, z1 + i * 0.17, sx + 1.3, sy + 0.17, z1 + (i + 1) * 0.17))
add("oak", union(steps))
add("stone", table(13, 4.5, 1.3, 1.3, z1, h=0.8))  # rundat mittbord (fyrkantigt här)
add("brass", chandelier(13, 4.5, z1 + 5.5))
add("stone", column(x0 + 0.5, y0 + 0.5, z1, 7.0, 0.25)); add("stone", column(x1 - 0.5, y0 + 0.5, z1, 7.0, 0.25))

x0, y0, x1, y1 = room("Plan 1", "Salong")
add("stone", fireplace(4, 0.45, z1, 'y+'))
add("linen", sofa(4, 3.2, 3.2, 1.0, z1, 0)); add("linen", sofa(4, 5.8, 3.2, 1.0, z1, np.pi))
add("oak", table(4, 4.5, 1.6, 0.9, z1, h=0.42))
add("green", sofa(1.4, 4.5, 1.0, 1.0, z1, np.pi/2)); add("green", sofa(6.6, 4.5, 1.0, 1.0, z1, -np.pi/2))
add("rug", box(1.5, 2.3, z1, 6.5, 6.7, z1 + 0.02))

x0, y0, x1, y1 = room("Plan 1", "Matsal")
add("oak", table(21, 4, 5.6, 1.3, z1))
for i in range(7):
    add("green", chair(18.7 + i * 0.77, 3.1, z1, 0)); add("green", chair(18.7 + i * 0.77, 4.9, z1, np.pi))
add("brass", chandelier(19.5, 4, z1 + 2.6, 0.5)); add("brass", chandelier(22.5, 4, z1 + 2.6, 0.5))
add("stone", fireplace(21, 7.55, z1, 'y-'))

x0, y0, x1, y1 = room("Plan 1", "Eget kök")
add("stone", box(-5.5, 5.5, z1, -2.5, 6.6, z1 + 0.95))            # ö
add("oak", box(-0.6, 3.2, z1, 0.0, 10.8, z1 + 0.92))               # bänkrad östra väggen
add("oak", box(-5.9, 3.2, z1, -5.3, 10.8, z1 + 0.92))              # bänkrad västra väggen
add("black", box(-5.9, 6.4, z1, -5.3, 7.6, z1 + 0.95))             # spis
add("stone", box(-6.0, 6.0, z1 + 1.5, -5.2, 8.0, z1 + 3.0))        # kåpa i kalksten
for i in range(4): add("linen", chair(-4.9 + i * 0.8, 7.2, z1, np.pi))

x0, y0, x1, y1 = room("Plan 1", "AI-kök (robotkök)")
add("black", box(-8.5, -1.0, z1, -1.5, 0.2, z1 + 0.9))            # central station
add("steel", box(-9.9, -2.9, z1, -0.1, -2.2, z1 + 0.9))            # bakre rad
add("steel", box(-9.9, -2.9, z1 + 1.4, -0.1, -2.5, z1 + 2.2))      # överskåp/fläkt
add("black", box(-9.9, -0.4, z1 + 3.3, -0.1, -0.2, z1 + 3.45))     # takskena
for xx in (-7, -3): add("steel", union([cylinder(radius=0.08, height=1.4).apply_translation((xx, -0.3, z1 + 2.6)), box(xx - 0.4, -0.8, z1 + 1.6, xx + 0.4, -0.3, z1 + 1.9)]))
add("glass", box(-9.9, 2.4, z1, -0.1, 2.9, z1 + 3.3))              # glasvägg mot lager (skafferi)

x0, y0, x1, y1 = room("Plan 1", "Bibliotek")
add("oak", shelves(0.1, 8.1, 0.5, 14.9, z1)); add("oak", shelves(7.5, 8.1, 7.9, 14.9, z1)); add("oak", shelves(0.5, 14.5, 7.5, 14.9, z1))
add("oak", table(4, 10.5, 2.0, 1.0, z1)); add("leather", sofa(4, 13, 2.4, 1.0, z1, np.pi)); add("stone", fireplace(4, 8.55, z1, 'y+'))

x0, y0, x1, y1 = room("Plan 1", "Orangeri")
for px, py in ((11, 10), (15, 10), (11, 14), (15, 14)):
    add("terracotta", cylinder(radius=0.5, height=0.7).apply_translation((px, py, z1 + 0.35))); add("greenery", icosphere(2, 0.9).apply_translation((px, py, z1 + 1.8)))
add("rattan", sofa(13, 12, 2.4, 1.0, z1, 0)); add("stone", table(13, 13.6, 1.0, 1.0, z1, h=0.4))

x0, y0, x1, y1 = room("Plan 1", "Vardagsrum")
add("linen", sofa(21, 10.5, 4.0, 1.1, z1, 0)); add("oak", table(21, 12.3, 1.6, 0.8, z1, h=0.4)); add("black", box(16.1, 10.0, z1 + 0.9, 16.2, 13.0, z1 + 2.5)); add("rug", box(18, 9, z1, 24, 14, z1 + 0.02))

# ---------- Plan 2 ----------
z2 = Z["Plan 2"]
add("linen", bed(-5, 0.6, z2)); add("stone", fireplace(-5, -2.55, z2, 'y+')); add("linen", sofa(-5, 3.8, 3.0, 1.0, z2, np.pi)); add("rug", box(-8, -1.5, z2, -2, 4.6, z2 + 0.02))
x0, y0, x1, y1 = room("Plan 2", "Master spa-bad")
add("stone", union([box(-3.4, 9.4, z2, -1.6, 10.3, z2 + 0.6)]))   # kar
add("stone", box(-4.9, 5.2, z2, -0.1, 5.8, z2 + 0.9))               # tvättställsbänk
add("glass", box(-0.9, 7.0, z2, -0.1, 9.0, z2 + 2.4))               # dusch
for n_, xx in ((0, 1.5), (1, 5.5), (2, 19), (3, 21.5)): pass
add("linen", bed(4, 3.0, z2)); add("linen", bed(21, 2.5, z2)); add("linen", bed(19, 11, z2)); add("linen", bed(28.5, 0.0, z2, 1.4, 2.1)); add("linen", bed(33.5, 0.0, z2, 1.4, 2.1))
add("linen", sofa(13, 11.5, 3.6, 1.1, z2, 0)); add("black", box(10.1, 10.5, z2 + 0.9, 10.2, 13.5, z2 + 2.4))

# ---------- Källare ----------
z0 = Z["Källare"]
# pool: urgröpning i golvet + vatten
add("water", box(12.5, 2, z0 - 1.6, 18.5, 13, z0 - 0.05))
add("stone", trimesh.boolean.difference([box(11.5, 1, z0 - 1.9, 19.5, 14, z0 + 0.0), box(12.5, 2, z0 - 1.6, 18.5, 13, z0 + 1)], engine="manifold"))
for yy in (3, 5.5, 8, 10.5): add("linen", box(11.3, yy, z0, 12.1, yy + 1.9, z0 + 0.4))
add("oak", box(0.2, 11.0, z0, 4.0, 14.8, z0 + 2.4))                  # bastu
add("glass", box(4.0, 11.0, z0, 4.1, 14.8, z0 + 2.4))
x0, y0, x1, y1 = room("Källare", "Biograf")
add("black", box(20.1, 0.3, z0 + 0.6, 20.2, 7.7, z0 + 3.0))          # duk
for r_, (xx, zz) in enumerate(((22.5, 0.0), (24.0, 0.35), (25.3, 0.7))):
    add("stone", box(xx - 0.7, 0.5, z0, xx + 0.7, 7.5, z0 + zz)) if zz > 0 else None
    for yy in (1.5, 3.2, 4.9, 6.6): add("leather", sofa(xx, yy, 1.1, 1.1, z0 + zz, -np.pi/2))
x0, y0, x1, y1 = room("Källare", "Serverrum")
for i in range(6): add("black", box(-9.6 + i * 0.75, 3.3, z0, -9.0 + i * 0.75, 4.3, z0 + 2.2))
add("oak", table(-7.5, 6.0, 3.2, 1.0, z0)); add("black", box(-9.0, 6.6, z0 + 0.8, -6.0, 6.7, z0 + 1.9))
add("steel", box(-5.2, -0.2, z0, -4.4, 1.1, z0 + 2.3))               # ståldörr skyddsrum
# garage: bilar som volymer
for i in range(5): add("black", box(27 + i * 1.8, -2, z0, 28.6 + i * 1.8, 2.8, z0 + 1.5))

MAT = {
    "oak": (160, 120, 80, 255), "stone": (214, 203, 182, 255), "brass": (190, 150, 80, 255), "linen": (222, 212, 194, 255),
    "green": (54, 78, 58, 255), "rug": (150, 110, 85, 255), "black": (35, 35, 38, 255), "steel": (140, 145, 150, 255),
    "glass": (120, 160, 190, 120), "leather": (110, 70, 45, 255), "terracotta": (170, 100, 70, 255), "rattan": (190, 160, 110, 255),
    "greenery": (60, 100, 45, 255), "water": (70, 120, 150, 200),
}

if __name__ == "__main__":
    pickle.dump({k: [m for m in v if m is not None] for k, v in F.items()}, open("out/furniture.pkl", "wb"))
    print({k: len(v) for k, v in F.items()})
