"""Gör texturerna sömlösa + räkna fram normal-, roughness- och höjdkartor. tex/<namn>.png → tex/<namn>_{col,nrm,rgh,hgt}.png"""
import numpy as np, glob, os
from PIL import Image, ImageFilter
R = {"travertin": (0.35, 0.3), "ek": (0.38, 0.3), "puts_inne": (0.75, 0.35), "puts_ute": (0.8, 0.3), "kalksten": (0.55, 0.3), "linne": (0.9, 0.2), "grus": (0.8, 0.4), "betong": (0.45, 0.3), "gras": (0.85, 0.3), "matta": (0.95, 0.15)}
def seamless(a):
    """offset halvvägs och blenda skarven med mjuk mask"""
    h, w = a.shape[:2]; b = np.roll(a, (h//2, w//2), (0, 1))
    yy, xx = np.mgrid[0:h, 0:w]; d = np.minimum(np.minimum(yy, h-1-yy), np.minimum(xx, w-1-xx)) / (0.12*min(h, w))
    m = np.clip(d, 0, 1)[..., None]
    return (b*(1-m) + a*m) if False else (a*m + np.roll(a, (h//2, w//2), (0,1))*(1-m))
for f in glob.glob("tex/*.png"):
    n = os.path.basename(f)[:-4]
    if n.endswith(("_col","_hgt","_nrm","_rgh")): continue
    im = Image.open(f).convert("RGB").resize((2048, 2048), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)/255
    a = seamless(a)
    Image.fromarray((a*255).astype(np.uint8)).save(f"tex/{n}_col.png")
    g = a.mean(2); low = np.asarray(Image.fromarray((g*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(24))).astype(np.float32)/255
    hp = g - low                                              # högpass = ytdetalj
    hgt = np.clip(0.5 + hp*2.5 + (g-0.5)*0.3, 0, 1)
    Image.fromarray((hgt*255).astype(np.uint8)).save(f"tex/{n}_hgt.png")
    s = 6.0 if n not in ("puts_inne", "puts_ute") else 3.0
    dx = np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1); dy = np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)
    nx, ny, nz = -dx*s, -dy*s, np.ones_like(dx); l = np.sqrt(nx*nx+ny*ny+nz*nz)
    nrm = np.stack([(nx/l+1)/2, (ny/l+1)/2, (nz/l+1)/2], -1)
    Image.fromarray((nrm*255).astype(np.uint8)).save(f"tex/{n}_nrm.png")
    base, var = R.get(n, (0.6, 0.3))
    rgh = np.clip(base + (0.5 - g)*var, 0.05, 1)
    Image.fromarray((rgh*255).astype(np.uint8)).save(f"tex/{n}_rgh.png")
    print(n, "ok")
