"""Make smaller copies of the gallery and event photos for phones.

On screens up to 520px wide the Campus Life mosaic is a single column of 220px-tall
tiles and each event card is 16:10, both about 485px wide. The photos fill these boxes
with object-fit: cover, so a wide photo is cropped and needs more pixels than the box
width. Each copy is sized for a 2x phone screen: twice the larger of the box width and
the width the crop needs. Photos that would shrink by less than 10% get no copy.

The pages pick the copy with <picture><source media="(max-width: 520px)">, so phones
always get it, whatever their pixel density. Run this again after changing a photo.

Usage (from the project root):
    pip install pillow
    python tools/make_phone_copies.py
"""
import math, re
from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"
OUT = IMG / "phone"
PAGES = ["index.html", "campus-life.html"]
SLOT_W = 485          # single-column box width at a 520px viewport
TILE_H = 220          # mosaic row height on phones
EVENT_AR = 16 / 10    # .event__media aspect ratio

def zoom_photos():
    """{photo file: {"tile", "event"}} for every photo in a lightbox button."""
    found = {}
    pattern = r'<(div class="event__media"|figure class="tile[^"]*"[^>]*)><button type="button" data-zoom="[^"]*">(?:<picture>.*?)?<img src="assets/img/([^"]+)"'
    for page in PAGES:
        for m in re.finditer(pattern, (ROOT / page).read_text(encoding="utf-8")):
            found.setdefault(m.group(2), set()).add("event" if "event__media" in m.group(1) else "tile")
    return found

def main():
    OUT.mkdir(exist_ok=True)
    for name, kinds in zoom_photos().items():
        im = Image.open(IMG / name).convert("RGB")
        ar = im.width / im.height
        need = max(SLOT_W, *(TILE_H * ar if k == "tile" else SLOT_W / EVENT_AR * ar for k in kinds))
        width = math.ceil(2 * need / 10) * 10
        if width >= im.width * 0.9:
            print(f"{name:34s} {im.width}px, no copy needed")
            continue
        small = im.resize((width, round(width / ar)), Image.LANCZOS)
        small = small.filter(ImageFilter.UnsharpMask(radius=1.0, percent=35, threshold=2))
        small.save(OUT / name, "JPEG", quality=82, optimize=True, progressive=True)
        print(f"{name:34s} {im.width} -> {width}px  {(IMG / name).stat().st_size // 1024} -> {(OUT / name).stat().st_size // 1024} KB")

if __name__ == "__main__":
    main()
