"""Hämta riktiga skannade PBR-set (CC0) från ambientCG till tex/ – kör på mongo:
    python3 hamta_texturer.py
Skapar tex/<namn>_col.png, _nrm.png, _rgh.png (samma namn som apply_tex.py använder)."""
import json, os, sys, io, zipfile, urllib.request, urllib.parse
from PIL import Image

# namn i scenen → sökord på ambientCG (första träff med nedladdning väljs)
WANT = {
    "travertin": "Travertine", "ek": "WoodFloor", "puts_inne": "Plaster", "puts_ute": "Plaster",
    "kalksten": "PavingStones", "linne": "Fabric", "grus": "Gravel", "betong": "Concrete", "gras": "Grass", "matta": "Carpet",
}
PREFER = {"travertin": ["Travertine009", "Travertine013"], "ek": ["WoodFloor051", "WoodFloor043"], "puts_inne": ["Plaster001", "Plaster003"],
          "puts_ute": ["Plaster004", "Plaster002"], "kalksten": ["PavingStones131", "PavingStones135"], "linne": ["Fabric030", "Fabric046"],
          "grus": ["Gravel022", "Gravel023"], "betong": ["Concrete034", "Concrete031"], "gras": ["Grass004", "Grass001"], "matta": ["Carpet013", "Carpet008"]}
RES = "2K"
os.makedirs("tex", exist_ok=True)
UA = {"User-Agent": "herrgard-render/1.0"}

def api(q):
    u = "https://ambientcg.com/api/v2/full_json?" + urllib.parse.urlencode({"q": q, "type": "Material", "include": "downloadData", "limit": 20})
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA)))["foundAssets"]

def pick_zip(asset):
    for d in asset["downloadFolders"]["default"]["downloadFiletypeCategories"]["zip"]["downloads"]:
        if d["attribute"] == f"{RES}-JPG": return d["downloadLink"]

for name, q in WANT.items():
    assets = api(q); byid = {a["assetId"]: a for a in assets}
    chosen = next((byid[i] for i in PREFER[name] if i in byid), assets[0] if assets else None)
    if not chosen: print(name, "ingen träff"); continue
    link = pick_zip(chosen); print(name, "←", chosen["assetId"])
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(urllib.request.Request(link, headers=UA)).read()))
    for n in z.namelist():
        low = n.lower()
        for key, out in (("_color.", "_col"), ("_normalgl.", "_nrm"), ("_roughness.", "_rgh"), ("_displacement.", "_hgt")):
            if key in low and low.endswith((".jpg", ".png")):
                im = Image.open(io.BytesIO(z.read(n))); im = im.convert("RGB") if out != "_rgh" else im.convert("L")
                im.save(f"tex/{name}{out}.png"); break
print("klart – kör sedan: blender -b herrgard_v3.blend --python apply_tex.py")
