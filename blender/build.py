"""Bygger herrgården som 3D-modell från program.py och exporterar GLB/OBJ."""
import numpy as np, trimesh, json, sys
from trimesh.creation import box as _box, cylinder
from program import *

def box(x0, y0, z0, x1, y1, z1):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    b = _box(extents=(x1 - x0, y1 - y0, z1 - z0))
    b.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return b

def hull(pts):
    return trimesh.PointCloud(np.array(pts, float)).convex_hull

def rect_pts(x0, y0, x1, y1, z):
    return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]

def union(meshes):
    meshes = [m for m in meshes if m is not None and len(m.faces)]
    if not meshes: return None
    if len(meshes) == 1: return meshes[0]
    return trimesh.boolean.union(meshes, engine="manifold")

def diff(a, cutters):
    cutters = [c for c in cutters if c is not None]
    if not cutters: return a
    return trimesh.boolean.difference([a] + cutters, engine="manifold")

EXT_T, INT_T = 0.45, 0.15

def block_of(room):
    _, x0, y0, x1, y1 = room
    for name, (bx0, by0, bx1, by1) in BLOCKS.items():
        if x0 >= bx0 - 1e-6 and x1 <= bx1 + 1e-6 and y0 >= by0 - 1e-6 and y1 <= by1 + 1e-6:
            return name
    raise ValueError(room)

def footprint_union(z0, z1):
    return union([box(bx0, by0, z0, bx1, by1, z1) for (bx0, by0, bx1, by1) in BLOCKS.values()])

def exterior_walls(z0, z1):
    outer = union([box(bx0 - EXT_T, by0 - EXT_T, z0, bx1 + EXT_T, by1 + EXT_T, z1) for (bx0, by0, bx1, by1) in BLOCKS.values()])
    inner = union([box(bx0, by0, z0 - 1, bx1, by1, z1 + 1) for (bx0, by0, bx1, by1) in BLOCKS.values()])
    walls = diff(outer, [inner])
    # vägg mellan flygel och huvudkropp (de delar linjen x=0 resp x=26)
    for x in (0, 26):
        walls = union([walls, box(x - EXT_T / 2, 0, z0, x + EXT_T / 2, 11, z1)])
    return walls

def interior_walls(level, z0, z1):
    segs = set()
    for name, x0, y0, x1, y1 in ROOMS[level]:
        segs.add(('h', y0, x0, x1)); segs.add(('h', y1, x0, x1))
        segs.add(('v', x0, y0, y1)); segs.add(('v', x1, y0, y1))
    parts = []
    for kind, c, a, b in segs:
        if kind == 'h':
            parts.append(box(a, c - INT_T / 2, z0, b, c + INT_T / 2, z1))
        else:
            parts.append(box(c - INT_T / 2, a, z0, c + INT_T / 2, b, z1))
    return union(parts)

def exterior_edges(room):
    """Returnerar lista av (kind, const, a, b, outward) för rummets ytterväggar."""
    name, x0, y0, x1, y1 = room
    bname = block_of(room)
    bx0, by0, bx1, by1 = BLOCKS[bname]
    edges = []
    def covered_by_other_block(kind, c, a, b):
        for n, (ox0, oy0, ox1, oy1) in BLOCKS.items():
            if n == bname: continue
            if kind == 'h' and oy0 - 1e-6 <= c <= oy1 + 1e-6 and a >= ox0 - 1e-6 and b <= ox1 + 1e-6 and (c == oy0 or c == oy1 or True):
                # kanten ligger inne i/på annan kropp
                if ox0 - 1e-6 <= a and b <= ox1 + 1e-6 and oy0 - 1e-6 <= c <= oy1 + 1e-6: return True
            if kind == 'v' and ox0 - 1e-6 <= c <= ox1 + 1e-6 and oy0 - 1e-6 <= a and b <= oy1 + 1e-6: return True
        return False
    if abs(y0 - by0) < 1e-6 and not covered_by_other_block('h', y0, x0, x1): edges.append(('h', y0, x0, x1, -1))
    if abs(y1 - by1) < 1e-6 and not covered_by_other_block('h', y1, x0, x1): edges.append(('h', y1, x0, x1, +1))
    if abs(x0 - bx0) < 1e-6 and not covered_by_other_block('v', x0, y0, y1): edges.append(('v', x0, y0, y1, -1))
    if abs(x1 - bx1) < 1e-6 and not covered_by_other_block('v', x1, y0, y1): edges.append(('v', x1, y0, y1, +1))
    return edges

def window_specs(level):
    if level == "Plan 1": return dict(w=1.6, h=3.0, sill=0.35, arch=True, pitch=2.7)
    if level == "Plan 2": return dict(w=1.4, h=2.0, sill=0.9, arch=False, pitch=2.7)
    return None

WINDOW_POS = {"Plan 1": [], "Plan 2": []}
def windows_for(level, z0):
    spec = window_specs(level)
    if not spec: return [], []
    cutters, glass, frames = [], [], []
    surrounds = []
    for room in ROOMS[level]:
        if room[0] in NO_WINDOWS: continue
        for kind, c, a, b, out in exterior_edges(room):
            L = b - a
            n = max(1, int((L - 0.8) // spec['pitch']))
            if L < 2.2: continue
            step = L / n
            for i in range(n):
                m = a + step * (i + 0.5)
                w, h = spec['w'], spec['h']
                zb, zt = z0 + spec['sill'], z0 + spec['sill'] + h
                if kind == 'h':
                    cut = box(m - w / 2, c - 1, zb, m + w / 2, c + 1, zt)
                    gl = box(m - w / 2, c + out * 0.12 - 0.03, zb, m + w / 2, c + out * 0.12 + 0.03, zt)
                    fr = diff(box(m - w / 2 - 0.08, c + out * 0.10 - 0.05, zb - 0.08, m + w / 2 + 0.08, c + out * 0.10 + 0.05, zt + 0.08), [box(m - w / 2, c - 1, zb, m + w / 2, c + 1, zt)])
                    if spec['arch']:
                        cy = cylinder(radius=w / 2, height=2, sections=32); cy.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0))); cy.apply_translation((m, c, zt))
                        cut = union([cut, cy])
                        g2 = cylinder(radius=w / 2, height=0.06, sections=32); g2.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0))); g2.apply_translation((m, c + out * 0.12, zt)); gl = union([gl, g2])
                        f2 = cylinder(radius=w / 2 + 0.08, height=0.1, sections=32); f2.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0))); f2.apply_translation((m, c + out * 0.10, zt)); fr = union([fr, diff(f2, [cy])])
                else:
                    cut = box(c - 1, m - w / 2, zb, c + 1, m + w / 2, zt)
                    gl = box(c + out * 0.12 - 0.03, m - w / 2, zb, c + out * 0.12 + 0.03, m + w / 2, zt)
                    fr = diff(box(c + out * 0.10 - 0.05, m - w / 2 - 0.08, zb - 0.08, c + out * 0.10 + 0.05, m + w / 2 + 0.08, zt + 0.08), [box(c - 1, m - w / 2, zb, c + 1, m + w / 2, zt)])
                    if spec['arch']:
                        cy = cylinder(radius=w / 2, height=2, sections=32); cy.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0))); cy.apply_translation((c, m, zt))
                        cut = union([cut, cy])
                        g2 = cylinder(radius=w / 2, height=0.06, sections=32); g2.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0))); g2.apply_translation((c + out * 0.12, m, zt)); gl = union([gl, g2])
                        f2 = cylinder(radius=w / 2 + 0.08, height=0.1, sections=32); f2.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0))); f2.apply_translation((c + out * 0.10, m, zt)); fr = union([fr, diff(f2, [cy])])
                cutters.append(cut); glass.append(gl); frames.append(fr)
                WINDOW_POS[level].append((m if kind == 'h' else c, c if kind == 'h' else m, kind))
                # stenomfattning + fönsterbänk + fransk balkong på plan 2
                sw, pr = 0.14, 0.07
                if kind == 'h':
                    yo0, yo1 = (c + out * EXT_T - pr, c + out * EXT_T + pr) if out > 0 else (c + out * EXT_T - pr, c + out * EXT_T + pr)
                    ring = diff(box(m - w/2 - sw, yo0, zb - 0.12, m + w/2 + sw, yo1, zt + (w/2 if spec['arch'] else 0) + sw), [cut])
                    sill = box(m - w/2 - 0.22, c + out * EXT_T - 0.12, zb - 0.12, m + w/2 + 0.22, c + out * EXT_T + 0.12, zb - 0.02)
                    surrounds += [ring, sill]
                    if spec['arch']:
                        surrounds.append(box(m - 0.14, yo0 - 0.03, zt + w/2 - 0.1, m + 0.14, yo1 + 0.03, zt + w/2 + sw + 0.1))  # slutsten
                    if level == "Plan 2":
                        surrounds.append(box(m - w/2 - 0.1, c + out * (EXT_T + 0.02), zb + 0.55, m + w/2 + 0.1, c + out * (EXT_T + 0.3), zb + 0.62))
                        frames.append(diff(box(m - w/2 - 0.1, c + out * (EXT_T + 0.02), zb + 0.62, m + w/2 + 0.1, c + out * (EXT_T + 0.3), zb + 1.05), [box(m - w/2 - 0.05, c - 2, zb + 0.66, m + w/2 + 0.05, c + 2, zb + 1.0)]))
                else:
                    xo0, xo1 = (c + out * EXT_T - pr, c + out * EXT_T + pr)
                    ring = diff(box(xo0, m - w/2 - sw, zb - 0.12, xo1, m + w/2 + sw, zt + (w/2 if spec['arch'] else 0) + sw), [cut])
                    sill = box(c + out * EXT_T - 0.12, m - w/2 - 0.22, zb - 0.12, c + out * EXT_T + 0.12, m + w/2 + 0.22, zb - 0.02)
                    surrounds += [ring, sill]
    return cutters, glass + frames + [("stone", s) for s in surrounds]

def door_cutters(level, z0):
    cs = []
    for x, y, kind in DOORS[level]:
        if kind == 'h': cs.append(box(x - 0.55, y - 1, z0 + 0.01, x + 0.55, y + 1, z0 + 2.3))
        else: cs.append(box(x - 1, y - 0.55, z0 + 0.01, x + 1, y + 0.55, z0 + 2.3))
    return cs

def mansard(bx0, by0, bx1, by1, z0, lower=3.3, upper=1.2, inset1=1.25, inset2=2.6, over=0.55):
    low = hull(rect_pts(bx0 - over, by0 - over, bx1 + over, by1 + over, z0) +
               rect_pts(bx0 + inset1, by0 + inset1, bx1 - inset1, by1 - inset1, z0 + lower))
    top = hull(rect_pts(bx0 + inset1, by0 + inset1, bx1 - inset1, by1 - inset1, z0 + lower) +
               rect_pts(bx0 + inset1 + inset2, by0 + inset1 + inset2, bx1 - inset1 - inset2, by1 - inset1 - inset2, z0 + lower + upper))
    return union([low, top])

def dormer(x, yface, out, z0):
    """Takkupa: smal stenfront med rundbåge, kinder i skiffer, liten valmad huv."""
    w, d, h = 1.25, 2.2, 1.95
    y_out = yface + out * 0.35          # fronten står nästan i fasadliv
    y_in = yface - out * d
    ya, yb = sorted((y_out, y_in))
    zb = z0 + 0.35
    body = box(x - w / 2, ya, zb, x + w / 2, yb, zb + h)
    arch = cylinder(radius=w / 2, height=yb - ya, sections=32); arch.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0))); arch.apply_translation((x, (ya + yb) / 2, zb + h))
    body = union([body, arch])
    roof = hull([(x - w / 2 - 0.12, ya - 0.05, zb + h + 0.05), (x + w / 2 + 0.12, ya - 0.05, zb + h + 0.05),
                 (x - w / 2 - 0.12, yb + 0.05, zb + h + 0.05), (x + w / 2 + 0.12, yb + 0.05, zb + h + 0.05),
                 (x, ya + 0.2, zb + h + 0.95), (x, yb - 0.2, zb + h + 0.95)])
    # fönster med båge i fronten
    gy0, gy1 = (y_out - 0.08, y_out) if out < 0 else (y_out, y_out + 0.08)
    glass = box(x - 0.42, gy0, zb + 0.35, x + 0.42, gy1, zb + 1.35)
    g2 = cylinder(radius=0.42, height=0.08, sections=24); g2.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0))); g2.apply_translation((x, (gy0 + gy1) / 2, zb + 1.35))
    glass = union([glass, g2])
    return body, roof, glass

def build():
    parts = {"walls": [], "roof": [], "glass": [], "frames": [], "slab": [], "stone": [], "ground": [], "tech": [], "greenery": [], "water": [], "concrete": [], "brass": []}
    level_walls = {}
    for i, (level, z0, hgt) in enumerate(LEVELS):
        z1 = z0 + hgt
        ext = exterior_walls(z0, z1)
        inn = interior_walls(level, z0 + 0.0, z1)
        wcut, wgeo = windows_for(level, z0)
        dcut = door_cutters(level, z0)
        ext = diff(ext, wcut + dcut)
        inn = diff(inn, dcut)
        lw = union([ext, inn])
        level_walls[level] = lw
        parts["walls"].append(lw)
        for g in wgeo:
            if g is None: continue
            if isinstance(g, tuple): parts[g[0]].append(g[1])
            else: parts["glass"].append(g)
        # bjälklag
        slab = footprint_union(z0 - 0.3, z0)
        holes = [box(8, 5, z0 - 1, 11, 10, z0 + 1)]  # trapphus/hiss
        if level == "Plan 2": holes.append(box(11, 0.5, z0 - 1, 15, 7.5, z0 + 1))  # dubbelhöjd entréhall
        if level == "Källare": holes.append(box(12.5, 2, z0 - 1, 18.5, 13, z0 + 1))  # pool
        parts["slab"].append(diff(slab, holes))
    # skyddsrum i betong (tjocka väggar + lock)
    parts["concrete"].append(diff(box(-10.6, -3.6, -3.5, 0.6, 3.6, 0.3), [box(-10, -3, -3.2, 0, 3, 0)]))
    # tak
    rz = ROOF_BASE
    roofs = [mansard(*BLOCKS["main"], rz), mansard(*BLOCKS["west"], rz - 0.4), mansard(*BLOCKS["east"], rz - 0.4)]
    parts["roof"].append(union(roofs))
    # takkupor – fram och bak på varje kropp
    for bname, (bx0, by0, bx1, by1) in BLOCKS.items():
        z = rz if bname == "main" else rz - 0.4
        for yface, out in ((by0, -1), (by1, +1)):
            xs = [wx for (wx, wy, kind) in WINDOW_POS["Plan 2"] if kind == 'h' and abs(wy - yface) < 1e-6 and bx0 < wx < bx1]
            xs = sorted(xs)[::2] if len(xs) > 4 else sorted(xs)
            if bname == "main" and out < 0: xs = [wx for wx in xs if abs(wx - 13) > 2.0] + [13.0]
            for x in xs:
                b, r, g = dormer(x, yface, out, z)
                parts["stone"].append(b); parts["roof"].append(r); parts["glass"].append(g)
    # listverk: kornisch under taket, våningsband, sockel
    for (bx0, by0, bx1, by1) in BLOCKS.values():
        e = EXT_T
        for (zz0, zz1, pr) in ((rz - 0.55, rz - 0.05, 0.28), (rz - 0.05, rz + 0.05, 0.42), (3.9 - 0.08, 3.9 + 0.14, 0.09), (-0.3, 0.65, 0.07)):
            parts["stone"].append(diff(box(bx0 - e - pr, by0 - e - pr, zz0, bx1 + e + pr, by1 + e + pr, zz1), [box(bx0 - e + 0.01, by0 - e + 0.01, zz0 - 1, bx1 + e - 0.01, by1 + e - 0.01, zz1 + 1)]))
        # hörnkedjor (kvadrar)
        for cx, cy in ((bx0 - e, by0 - e), (bx1 + e, by0 - e), (bx0 - e, by1 + e), (bx1 + e, by1 + e)):
            for k in range(11):
                zz = 0.65 + k * 0.6
                big = (k % 2 == 0)
                lx = 0.55 if big else 0.38
                parts["stone"].append(box(cx - lx, cy - lx, zz, cx + lx, cy + lx, zz + 0.5).apply_translation((0, 0, 0)) if True else None)
        parts["stone"] = [p for p in parts["stone"] if p is not None]
    # skorstenar
    for x, y in ((4, 5), (22, 5), (-5, 2), (31, 2), (13, 13)):
        parts["stone"].append(box(x - 0.6, y - 0.5, rz, x + 0.6, y + 0.5, rz + 6.0))
    # ENTRÉ: framskjutet mittparti med rundbågad port, kolonner, balkong med balustrad
    cx = 13.0
    # portöppning i fasaden (2.4 x 3.6 med båge) – skär i väggdelen
    door_cut = union([box(cx - 1.2, -1.5, 0.0, cx + 1.2, 1.5, 3.0), cylinder(radius=1.2, height=3, sections=32).apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, (1, 0, 0))).apply_translation((cx, 0, 3.0))])
    parts["walls"] = [diff(w, [door_cut]) if abs(w.bounds[0][2] - 0.0) < 0.5 and w.bounds[1][2] > 3 else w for w in parts["walls"]]
    # stenomfattning runt porten
    ring = diff(union([box(cx - 1.55, -0.6, -0.3, cx + 1.55, 0.0, 3.0), cylinder(radius=1.55, height=0.6, sections=32).apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, (1, 0, 0))).apply_translation((cx, -0.3, 3.0))]), [door_cut])
    parts["stone"].append(ring)
    parts["stone"].append(box(cx - 0.2, -0.66, 4.1, cx + 0.2, 0.0, 4.75))  # slutsten
    # dubbeldörr + överljus
    parts["frames"].append(box(cx - 1.15, -0.25, 0.0, cx + 1.15, -0.1, 2.6))
    parts["brass"].append(box(cx - 0.12, -0.3, 1.0, cx - 0.04, -0.1, 1.4)); parts["brass"].append(box(cx + 0.04, -0.3, 1.0, cx + 0.12, -0.1, 1.4))
    parts["glass"].append(union([box(cx - 1.15, -0.2, 2.6, cx + 1.15, -0.15, 3.0), cylinder(radius=1.15, height=0.05, sections=32).apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, (1, 0, 0))).apply_translation((cx, -0.175, 3.0))]))
    # portik: fyra slanka kolonner med bas och kapitäl, bjälklag, balkong med balustrad
    for x in (cx - 3.0, cx - 1.0, cx + 1.0, cx + 3.0):
        parts["stone"].append(cylinder(radius=0.26, height=3.7, sections=28).apply_translation((x, -2.6, 2.05)))
        parts["stone"].append(box(x - 0.42, -3.02, 0.0, x + 0.42, -2.18, 0.35))
        parts["stone"].append(box(x - 0.42, -3.02, 3.75, x + 0.42, -2.18, 4.1))
    parts["stone"].append(box(cx - 3.7, -3.3, 4.1, cx + 3.7, 0.0, 4.55))          # entablement/balkongplatta
    parts["stone"].append(box(cx - 3.8, -3.4, 4.55, cx + 3.8, 0.0, 4.62))
    def balustrade(x0_, y0_, x1_, y1_, z_):
        out_ = []
        out_.append(box(x0_, y0_, z_ + 0.95, x1_, y1_, z_ + 1.05))                           # handledare
        out_.append(box(x0_, y0_, z_, x1_, y1_, z_ + 0.1))                                     # fotlist
        L = max(x1_ - x0_, y1_ - y0_); n_ = int(L / 0.28)
        for i in range(n_ + 1):
            t_ = i / max(n_, 1)
            px, py = (x0_ + t_ * (x1_ - x0_), y0_ + t_ * (y1_ - y0_)) if (x1_ - x0_) > (y1_ - y0_) else (x0_ + t_ * (x1_ - x0_), y0_ + t_ * (y1_ - y0_))
            out_.append(cylinder(radius=0.055, height=0.85, sections=10).apply_translation((px, py, z_ + 0.525)))
        return union(out_)
    parts["stone"].append(balustrade(cx - 3.7, -3.3, cx + 3.7, -3.18, 4.62))
    parts["stone"].append(balustrade(cx - 3.7, -3.3, cx - 3.58, -0.1, 4.62)); parts["stone"].append(balustrade(cx + 3.58, -3.3, cx + 3.7, -0.1, 4.62))
    # balkongdörr (plan 2) ovanför entrén: öppning + glasdörr
    bd = box(cx - 0.9, -1.5, 3.9 + 0.1, cx + 0.9, 1.5, 3.9 + 2.5)
    parts["walls"] = [diff(w, [bd]) if w.bounds[0][2] > 3.5 and w.bounds[0][2] < 4.5 else w for w in parts["walls"]]
    parts["glass"].append(box(cx - 0.85, -0.2, 4.0, cx + 0.85, -0.14, 6.35)); parts["frames"].append(diff(box(cx - 0.95, -0.22, 3.95, cx + 0.95, -0.12, 6.45), [box(cx - 0.85, -1, 4.0, cx + 0.85, 1, 6.35)]))
    # trappa med vangstycken
    for i, (y0_, z_) in enumerate(((-4.9, -0.4), (-4.5, -0.2), (-4.1, 0.0))):
        parts["stone"].append(box(cx - 4.3, y0_, -0.6, cx + 4.3, -2.2, z_))
    parts["stone"].append(box(cx - 4.6, -5.0, -0.6, cx - 4.3, -2.2, 0.3)); parts["stone"].append(box(cx + 4.3, -5.0, -0.6, cx + 4.6, -2.2, 0.3))
    # lyktor vid entrén
    for x in (cx - 1.9, cx + 1.9):
        parts["frames"].append(box(x - 0.14, -0.72, 2.0, x + 0.14, -0.44, 2.5)); parts["glass"].append(box(x - 0.1, -0.7, 2.05, x + 0.1, -0.46, 2.45))
    # BALKONGER på flyglarnas framsidor (plan 2) – över mittfönstret
    for bx in (-5.0, 31.0):
        parts["stone"].append(box(bx - 1.9, -3.0 - EXT_T - 1.3, 3.9 - 0.05, bx + 1.9, -3.0 - EXT_T, 3.9 + 0.12))
        parts["stone"].append(balustrade(bx - 1.9, -3.0 - EXT_T - 1.3, bx + 1.9, -3.0 - EXT_T - 1.18, 4.02))
        parts["stone"].append(balustrade(bx - 1.9, -3.0 - EXT_T - 1.3, bx - 1.78, -3.0 - EXT_T, 4.02)); parts["stone"].append(balustrade(bx + 1.78, -3.0 - EXT_T - 1.3, bx + 1.9, -3.0 - EXT_T, 4.02))
        for k in (-1.3, 1.3):
            parts["stone"].append(hull([(bx + k - 0.15, -3.45, 3.85), (bx + k + 0.15, -3.45, 3.85), (bx + k - 0.15, -3.45, 2.9), (bx + k + 0.15, -3.45, 2.9), (bx + k - 0.15, -4.7, 3.85), (bx + k + 0.15, -4.7, 3.85)]))  # konsol
        bd = box(bx - 0.8, -3.0 - 1.5, 4.0, bx + 0.8, -3.0 + 1.5, 6.4)
        parts["walls"] = [diff(w, [bd]) if 3.5 < w.bounds[0][2] < 4.5 else w for w in parts["walls"]]
        parts["glass"].append(box(bx - 0.75, -3.0 - EXT_T - 0.1, 4.0, bx + 0.75, -3.0 - EXT_T - 0.04, 6.35))
    # TERRASS mot trädgården (plan 1) med balustrad och trappa ner, balkong över (plan 2)
    parts["stone"].append(box(9.0, 15.0 + EXT_T, -0.6, 27.0, 15.0 + EXT_T + 5.0, 0.0))
    parts["stone"].append(balustrade(9.0, 20.0 + EXT_T, 27.0, 20.12 + EXT_T, 0.0))
    parts["stone"].append(balustrade(9.0, 15.0 + EXT_T, 9.12, 20.0 + EXT_T, 0.0)); parts["stone"].append(balustrade(26.88, 15.0 + EXT_T, 27.0, 20.0 + EXT_T, 0.0))
    for i, (y0_, z_) in enumerate(((20.45, -0.2), (20.85, -0.4), (21.25, -0.55))):
        parts["stone"].append(box(15.0, y0_ + 0.0, -0.6, 21.0, y0_ + 0.45, z_))
    parts["stone"].append(box(10.0, 15.0 + EXT_T, 3.85, 26.0, 15.0 + EXT_T + 1.6, 4.02))
    parts["stone"].append(balustrade(10.0, 16.48 + EXT_T, 26.0, 16.6 + EXT_T, 4.02))
    for x in (10.0, 26.0): parts["stone"].append(balustrade(x - 0.06, 15.0 + EXT_T, x + 0.06, 16.6 + EXT_T, 4.02))
    for x in np.arange(11.5, 25, 2.5):
        parts["stone"].append(cylinder(radius=0.18, height=3.85, sections=20).apply_translation((x, 16.4 + EXT_T, 1.925)))
    # franska dörrar mot terrassen i stället för fönster (orangeri/vardagsrum)
    for x in (11.5, 14.5, 18.0, 21.0, 24.0):
        fd = box(x - 0.8, 14.0, 0.02, x + 0.8, 16.0, 3.0)
        parts["walls"] = [diff(w, [fd]) if -0.5 < w.bounds[0][2] < 0.5 else w for w in parts["walls"]]
        parts["glass"].append(box(x - 0.75, 15.0 + EXT_T - 0.14, 0.05, x + 0.75, 15.0 + EXT_T - 0.08, 2.95))
    # drönardocka på huvudkroppens platta takdel
    top = rz + 3.4 + 1.3
    parts["tech"].append(box(11, 5.5, top, 15, 9.5, top + 0.15))               # landningsplatta
    parts["tech"].append(diff(box(11.2, 10.0, top, 14.8, 12.5, top + 1.4), [box(11.4, 10.2, top + 0.1, 14.6, 12.3, top + 1.3)]))  # hangar
    parts["tech"].append(box(12.9, 12.6, top, 13.1, 12.8, top + 2.5))          # radarmast
    # mark, gårdsplan, damm, allé, grind
    parts["ground"].append(diff(box(-1500, -1500, -0.9, 1500, 1500, -0.6), [box(bx0 - 1, by0 - 1, -2, bx1 + 1, by1 + 1, 1) for (bx0, by0, bx1, by1) in BLOCKS.values()]))
    parts["stone"].append(box(-12, -26, -0.6, 38, 0.3, -0.55))                  # kullerstensgård
    parts["ground"].append(cylinder(radius=4.0, height=0.3, sections=48).apply_translation((13, -14, -0.55)))  # rondell med gräs
    parts["stone"].append(box(10.5, -80, -0.6, 15.5, -26, -0.55))               # allé/uppfart
    parts["water"].append(box(40, -30, -0.8, 62, -10, -0.62))                  # damm
    for y in np.arange(-78, -28, 6.5):
        for x in (7.5, 18.5):
            t = cylinder(radius=0.25, height=5, sections=8).apply_translation((x, y, 2.2)); parts["frames"].append(t)
            k = trimesh.creation.icosphere(subdivisions=1, radius=2.6).apply_translation((x, y, 6.5)); parts["greenery"].append(k)
    for x in (8.0, 18.0):
        parts["stone"].append(box(x - 0.7, -82, -0.6, x + 0.7, -80.6, 3.4))
    # häckar runt gårdsplanen
    for (x0, y0, x1, y1) in ((-12, -27, 9.5, -26), (16.5, -27, 38, -26), (-12, -26, -11, -3.4), (37, -26, 38, -3.4)):
        parts["greenery"].append(box(x0, y0, -0.55, x1, y1, 0.6))
    return parts, level_walls

COLORS = {
    "walls": (232, 222, 200, 255), "roof": (52, 54, 60, 255), "glass": (60, 75, 90, 255), "frames": (25, 25, 25, 255),
    "slab": (205, 195, 175, 255), "stone": (200, 190, 170, 255), "ground": (110, 140, 70, 255), "tech": (120, 125, 130, 255),
    "greenery": (60, 100, 45, 255), "water": (70, 110, 140, 255), "concrete": (150, 150, 150, 255), "brass": (190, 150, 80, 255),
}

def to_scene(parts):
    scene = trimesh.Scene()
    for name, meshes in parts.items():
        meshes = [m for m in meshes if m is not None and len(m.faces)]
        if not meshes: continue
        m = trimesh.util.concatenate(meshes)
        c = COLORS[name]
        m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            name=name, baseColorFactor=c, metallicFactor=0.0, roughnessFactor=0.3 if name == "glass" else 0.85))
        scene.add_geometry(m, node_name=name, geom_name=name)
    return scene

if __name__ == "__main__":
    parts, level_walls = build()
    scene = to_scene(parts)
    scene.export("out/herrgard.glb")
    # OBJ – med färger via mtl
    scene.export("out/herrgard.obj")
    # per-våning väggar för snittvyer
    for level, lw in level_walls.items():
        lw.export(f"out/vaggar_{level.replace(' ', '_').lower()}.stl")
    import pickle; pickle.dump({k: [m for m in v if m is not None] for k, v in parts.items()}, open("out/parts.pkl", "wb"))
    tot = sum(len(m.faces) for v in parts.values() for m in v if m is not None)
    print("faces", tot, "bounds", scene.bounds.round(1).tolist())
