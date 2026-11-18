# Herrgården – Blender-pipeline

## Filer
- `herrgard_moblerad.blend` (skickad separat, ~225 MB): hela huset med material, ljus, kamerabana (156 s) och 25 genererade möbler (91 placerade objekt). Texturer packade i filen.
- `program.py` – rumsprogram (alla rum med mått), dörrar, fönsterregler
- `build.py` – bygger huset (väggar, fönster, tak, fasad, entré, balkonger, terrass) → GLB/OBJ
- `furnish.py` – inbyggda volymer (trappa, köksbänkar, pool, bastu, biografsteg…)
- `placements.py` – var varje möbel står (asset, x, y, z, rotation, mått)
- `place_assets.py` – sätter in möblerna i Blender och gör materialjusteringar
- `blender_scene.py` – material, himmel/sol, rumsljus, kamerabana
- `render_still.py` – rendera bildrutor ur kamerabanan: `BLEND=herrgard_moblerad.blend python3 render_still.py 745 2449 --res 1920x1080 --samples 128`

## Rendera på servern (R9700, Cycles HIP)
1. Öppna `herrgard_moblerad.blend` i Blender 4.2+.
2. Edit → Preferences → System → Cycles Render Devices → HIP → bocka i R9700.
3. Render → Render Animation. Output: `//render/frame_####.png`, 1920×1080, 24 fps, 3744 bildrutor.
4. `ffmpeg -framerate 24 -i render/frame_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 herrgarden.mp4`

Kommandorad: `blender -b herrgard_moblerad.blend -E CYCLES -- --cycles-device HIP -a`

## Nästa steg för fotorealism (iteration på servern)
- Ljus: IES-spots i nischer, ljusare fönsterljus (sun strength / exposure), ljuskällor i rummen (golvlampor, ljus)
- Material: byt procedurella texturer mot PBR-set (travertin, rökt ek, kalkputs)
- Detaljer: taklister, fönstersmygar, gardiner, växter, böcker, textil
- Kameran: lens 24 mm, lägg till lätt depth of field

## Hämta scenen på servern
```bash
git clone https://github.com/gustafboman0607-code/herrgard-ref.git
cd herrgard-ref
cat blend/herrgard_v2.blend.part* > herrgard_v2.blend
sha256sum -c <(echo "$(cat blend/SHA256)  herrgard_moblerad.blend")
```
