"""Renderar fria kameravyer (inte ur kamerabanan). python3 render_views.py namn1 namn2 ..."""
import bpy, sys, time, os
VIEWS = {
    "salong":        ((6.8, 2.2, 1.6), (1.5, 5.5, 1.2)),
    "bibliotek":     ((7.2, 8.8, 1.6), (1.0, 13.8, 1.3)),
    "orangeri":      ((13.8, 9.3, 1.6), (11.5, 14.6, 1.3)),
    "gastsvit":      ((35.6, -2.6, 1.6), (30.5, 2.6, 1.1)),
    "kontor":        ((30.4, 3.4, 1.6), (35.6, 10.6, 1.2)),
    "privat":        ((5.6, 7.4, 5.5), (0.8, 14.2, 5.0)),
    "barnrum":       ((26.4, 3.6, 5.5), (30.6, -2.6, 4.9)),
    "lekrum":        ((26.4, 4.4, 5.5), (35.4, 10.6, 5.0)),
    "allrum":        ((10.4, 9.4, 5.5), (15.6, 14.6, 5.0)),
    "walkin":        ((-9.6, 5.4, 5.5), (-5.4, 10.6, 5.0)),
    "gym":           ((7.6, 0.4, -1.6), (0.4, 6.6, -2.3)),
    "vinkallare":    ((20.4, 8.4, -1.6), (25.6, 14.6, -2.3)),
    "garage":        ((26.4, 7.6, -1.6), (35.6, -2.6, -2.3)),
    "tvattstuga":    ((-0.4, 7.4, -1.6), (-9.6, 10.6, -2.3)),
    "skyddsrum":     ((-9.2, 2.4, -1.6), (-2.0, -1.8, -2.3)),
}
names = [a for a in sys.argv[1:] if a in VIEWS]
bpy.ops.wm.open_mainfile(filepath="/home/claude/herrgard/out/herrgard.blend")
sc = bpy.context.scene
sc.cycles.device = 'CPU'; sc.cycles.samples = 32; sc.cycles.use_denoising = True
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
sc.render.resolution_x = 1280; sc.render.resolution_y = 720
cam = bpy.data.objects["Kamera"]; tgt = bpy.data.objects["Blick"]
cam.animation_data_clear(); tgt.animation_data_clear()
os.makedirs("/home/claude/herrgard/out/views", exist_ok=True)
for n in names:
    eye, look = VIEWS[n]
    cam.location = eye; tgt.location = look
    sc.render.filepath = f"/home/claude/herrgard/out/views/{n}.png"
    t = time.time(); bpy.ops.render.render(write_still=True); print(f"view {n} done in {time.time()-t:.0f}s", flush=True)
