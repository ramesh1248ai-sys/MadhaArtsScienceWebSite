"""Prepare the college's event photos (September 2026 batch) for the website.

Most of the supplied photos are social-media collages, so each job cuts one frame
out of a collage, trims any white gutter left at its edges, caps the width and
saves a web JPEG. EXIF/GPS metadata is not copied. No AI enhancement is applied:
these are recent phone photos, and the collage frames are too small to upscale well.

Skipped from the batch: the three admissions flyers (graphics, not photos), the
event posters inside the collages, and a group photo with a burned-in timestamp.

Usage (from the project root):
    pip install pillow numpy
    python tools/prepare_photos.py "C:/Users/you/Downloads/MadhaPhotos"
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "assets" / "img"
MAX_W = 1800

# (source file, crop box in source pixels or None for the whole photo, output)
JOBS = [
    # Recent events
    ("TNPSC CoachingProgram.jpeg", (558, 355, 1075, 740), "event-tnpsc-coaching.jpg"),
    ("CyberSafetyAwareness 2.jpeg", (202, 1145, 880, 1462), "event-cyber-safety.jpg"),
    ("WhatsApp Image 2026-09-14 at 20.52.45 (1).jpeg", (148, 1058, 928, 1437), "event-biotech-study-tour.jpg"),
    ("CompusToCorporateTraining 2026.jpeg", (118, 848, 742, 1150), "event-campus-to-corporate.jpg"),
    ("StreetPlay.jpeg", (532, 0, 1065, 530), "event-street-play.jpg"),
    ("VettiverNaduVizha.jpeg", (0, 1065, 800, 1599), "event-vettiver-planting.jpg"),
    ("CoastalCleanUp.jpeg", (835, 1065, 1565, 1599), "event-coastal-cleanup.jpg"),
    ("TamilDeptOnedayTour.jpeg", (0, 0, 1065, 530), "event-tamil-chennai-tour.jpg"),
    ("Field Visit 1.jpeg", (800, 1062, 1599, 1599), "event-biotech-kanchipuram.jpg"),
    # Gallery and outreach
    ("IdependanceDay.jpeg", None, "event-independence-day.jpg"),
    ("CollegeDay.jpeg", (800, 1125, 1599, 1540), "event-college-day-prizes.jpg"),
    ("Event.jpeg", None, "campus-assembly.jpg"),
    ("TraficAwarness.jpeg", None, "outreach-road-safety.jpg"),
    ("SayNoToDrugs.jpeg", None, "outreach-say-no-to-drugs.jpg"),
    ("Field Visit 2.jpeg", None, "visit-research-complex.jpg"),
    ("Field Visit 3.jpeg", None, "visit-industrial.jpg"),
    ("WhatsApp Image 2026-09-14 at 20.52.45 (1).jpeg", (152, 180, 928, 563), "biotech-mushrooms.jpg"),
    ("Field Visit 1.jpeg", (842, 22, 1558, 558), "biotech-silkworms.jpg"),
    ("WhatsApp Image 2026-09-14 at 20.52.54.jpeg", (0, 950, 4032, 2630), "students-faculty.jpg"),
]

def trim_gutters(im, limit=24):
    """Drop near-white, flat rows/columns left at the edges by the collage layout."""
    a = np.asarray(im.convert("L"), np.float32)
    flat = lambda line: line.mean() > 232 and line.std() < 14
    t = 0
    while t < limit and flat(a[t]): t += 1
    b = a.shape[0]
    while a.shape[0] - b < limit and flat(a[b - 1]): b -= 1
    l = 0
    while l < limit and flat(a[:, l]): l += 1
    r = a.shape[1]
    while a.shape[1] - r < limit and flat(a[:, r - 1]): r -= 1
    return im.crop((l, t, r, b))

def main(src_dir):
    for src, box, dst in JOBS:
        im = Image.open(src_dir / src).convert("RGB")
        if box:
            im = trim_gutters(im.crop(box))
        if im.width > MAX_W:
            im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
            im = im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=35, threshold=2))
        im.save(OUT / dst, "JPEG", quality=82, optimize=True, progressive=True)
        print(f"{dst:34s} {im.width}x{im.height}  {(OUT / dst).stat().st_size // 1024} KB")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
