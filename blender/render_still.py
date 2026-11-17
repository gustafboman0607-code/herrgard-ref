"""Renderar enskilda bildrutor ur kamerabanan: python3 render_still.py <frame> [<frame>...] --res 1280x720 --samples 96"""
import bpy, sys, time, os
args = sys.argv[1:]
res = "1280x720"; samples = 96; frames = []
i = 0
while i < len(args):
    if args[i] == "--res": res = args[i + 1]; i += 2
    elif args[i] == "--samples": samples = int(args[i + 1]); i += 2
    else: frames.append(int(args[i])); i += 1
bpy.ops.wm.open_mainfile(filepath=os.environ.get("BLEND", "/home/claude/herrgard/out/herrgard.blend"))
sc = bpy.context.scene
sc.cycles.device = 'CPU'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
w, h = map(int, res.split("x")); sc.render.resolution_x = w; sc.render.resolution_y = h
os.makedirs("/home/claude/herrgard/out/stills", exist_ok=True)
for f in frames:
    sc.frame_set(f); sc.render.filepath = f"/home/claude/herrgard/out/stills/f{f:05d}.png"
    t = time.time(); bpy.ops.render.render(write_still=True); print(f"frame {f} done in {time.time()-t:.0f}s", flush=True)
