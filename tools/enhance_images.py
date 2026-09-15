"""AI photo enhancement pipeline for the Madha Arts redesign.

Stage 1  Real-ESRGAN super-resolution (removes JPEG blocking/noise, restores detail).
Stage 2  Photographic grade: white balance, local contrast (CLAHE), vibrance,
         gentle S-curve, optional graduated sky filter, output sharpening.
No generative face restoration is used, so people's likeness is not altered.

Usage (from the project root):
    pip install torch spandrel opencv-python-headless pillow numpy
    # put the two Real-ESRGAN weight files in tools/models/ (see README.md)
    python tools/enhance_images.py                 # every image
    python tools/enhance_images.py classroom.jpg   # a single output
"""
import os, sys, time
from pathlib import Path
import numpy as np
import cv2
import torch
import spandrel
from PIL import Image

ROOT = Path(__file__).resolve().parent            # tools/
ORIG = ROOT.parent / "assets" / "img" / "originals"
OUT = ROOT.parent / "assets" / "img"
torch.set_num_threads(os.cpu_count() or 4)

_models = {}
def model(name):
    if name not in _models:
        _models[name] = spandrel.ModelLoader().load_from_file(str(ROOT / "models" / name)).eval()
    return _models[name]

def upscale(rgb, name, tile=256, pad=16):
    """Tiled x4 inference. rgb: HxWx3 uint8 -> 4Hx4Wx3 uint8."""
    m = model(name)
    s = m.scale
    h, w, _ = rgb.shape
    x = torch.from_numpy(rgb).permute(2, 0, 1).float().div(255).unsqueeze(0)
    out = torch.zeros(1, 3, h * s, w * s)
    with torch.inference_mode():
        for y0 in range(0, h, tile):
            for x0 in range(0, w, tile):
                y1, x1 = min(y0 + tile, h), min(x0 + tile, w)
                py0, px0 = max(y0 - pad, 0), max(x0 - pad, 0)
                py1, px1 = min(y1 + pad, h), min(x1 + pad, w)
                y = m.model(x[:, :, py0:py1, px0:px1])
                oy, ox = (y0 - py0) * s, (x0 - px0) * s
                out[:, :, y0 * s:y1 * s, x0 * s:x1 * s] = y[:, :, oy:oy + (y1 - y0) * s, ox:ox + (x1 - x0) * s]
    return (out.squeeze(0).clamp(0, 1).permute(1, 2, 0).numpy() * 255).round().astype(np.uint8)

def resize_w(rgb, width):
    h, w = rgb.shape[:2]
    if w == width:
        return rgb
    interp = cv2.INTER_AREA if width < w else cv2.INTER_LANCZOS4
    return cv2.resize(rgb, (width, round(h * width / w)), interpolation=interp)

def restore(src, mdl, final, strength, protect=()):
    """Super-resolve, then blend with a plain resample of the source.

    Full-strength ESRGAN output looks painterly and invents glyphs on small text;
    blending keeps the real texture while inheriting the de-blocking and edge detail.
    `protect` boxes (relative x0, y0, x1, y1) cover small signage, which keeps the
    plain resample so lettering is never replaced by invented glyphs.
    """
    sr = resize_w(upscale(src, mdl), final).astype(np.float32)
    plain = resize_w(src, final).astype(np.float32)
    h, w = plain.shape[:2]
    k = np.full((h, w), strength, np.float32)
    for x0, y0, x1, y1 in protect:
        k[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = 0
    if protect:
        k = cv2.GaussianBlur(k, (0, 0), w / 250)
    return np.clip(plain + k[..., None] * (sr - plain), 0, 255).round().astype(np.uint8)

def grade(rgb, wb=0.5, clahe=0.5, vib=0.22, curve=0.12, sky=0.0, sharpen=0.18, warmth=0.0):
    img = rgb.astype(np.float32) / 255

    # White balance / levels: per-channel percentile stretch, blended.
    if wb:
        lo = np.percentile(img, 0.4, axis=(0, 1))
        hi = np.percentile(img, 99.6, axis=(0, 1))
        stretched = np.clip((img - lo) / np.maximum(hi - lo, 1e-3), 0, 1)
        img = (img * (1 - wb) + stretched * wb).astype(np.float32)

    # Local contrast on luminance only.
    if clahe:
        lab = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_RGB2LAB)
        l = lab[:, :, 0]
        c = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8)).apply(l)
        lab[:, :, 0] = cv2.addWeighted(l, 1 - clahe, c, clahe, 0)
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB).astype(np.float32) / 255

    # Graduated sky filter: deepen bright, low-saturation pixels near the top.
    if sky:
        h, w = img.shape[:2]
        hsv = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32) / 255
        mask = np.clip((hsv[:, :, 2] - 0.62) / 0.25, 0, 1) * np.clip((0.35 - hsv[:, :, 1]) / 0.25, 0, 1)
        ramp = np.clip(1 - np.linspace(0, 1, h) / 0.55, 0, 1)[:, None]
        mask = cv2.GaussianBlur(mask * ramp, (0, 0), w / 200)
        tint = np.array([0.80, 0.88, 1.0], np.float32)  # soft blue, multiplicative
        img = (img * (1 - sky * mask[..., None]) + img * tint * (sky * mask[..., None])).astype(np.float32)

    # Vibrance: boost chroma more where it is low (protects skin & saturated saris).
    if vib:
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        a, b = lab[:, :, 1], lab[:, :, 2]
        chroma = np.sqrt(a * a + b * b)
        k = 1 + vib * np.clip(1 - chroma / 60, 0, 1)
        lab[:, :, 1], lab[:, :, 2] = a * k, b * k
        img = np.clip(cv2.cvtColor(lab, cv2.COLOR_LAB2RGB), 0, 1)

    if warmth:
        img = np.clip(img * np.array([1 + warmth, 1, 1 - warmth], np.float32), 0, 1)

    # Gentle filmic S-curve.
    if curve:
        s = img * img * (3 - 2 * img)
        img = img * (1 - curve) + s * curve

    out = (np.clip(img, 0, 1) * 255).round().astype(np.uint8)

    if sharpen:
        blur = cv2.GaussianBlur(out, (0, 0), 1.0)
        out = cv2.addWeighted(out, 1 + sharpen, blur, -sharpen, 0)
    return out

def load(src):
    """`src` is a file in originals/, or (file, crop box) to cut one frame out of a collage."""
    name, box = src if isinstance(src, tuple) else (src, None)
    im = Image.open(ORIG / name).convert("RGB")
    return np.array(im.crop(box) if box else im)

def save(rgb, name, q=84):
    Image.fromarray(rgb).save(OUT / name, "JPEG", quality=q, optimize=True, progressive=True)

GEN, PLUS = "realesr-general-x4v3.pth", "RealESRGAN_x4plus.pth"

# (source, output, pre-downscale width or None, model, final width, SR strength, grade kwargs)
FACE = dict(wb=0.3, clahe=0.2, vib=0.05, curve=0.08, sharpen=0.1)
JOBS = [
    ("group.jpg", "madha-group-campus.jpg", None, PLUS, 1400, (0.85, [(0.335, 0.325, 0.48, 0.375)]), dict(sky=0.35, wb=0.4)),
    ("madha-group.jpg", "classroom.jpg", None, GEN, 1600, 0.5, dict(wb=0.45, vib=0.12)),
    ("banner-3.jpg", "event-college-day.jpg", None, GEN, 1800, 0.5, dict(wb=0.3, clahe=0.35, vib=0.1)),
    ("TeachersDay Sep 2026.jpeg", "event-teachers-day.jpg", None, GEN, 2000, 0.5, dict(wb=0.3, clahe=0.35, vib=0.1)),
    # A 624px collage frame; the slide text and the trainer's head keep the plain resample
    (("CompusToCorporateTraining 2026.jpeg", (118, 848, 742, 1150)), "event-campus-to-corporate.jpg", None, GEN, 1600, (0.6, [(0.41, 0.23, 0.69, 0.46)]), dict(wb=0.3, clahe=0.35, vib=0.1)),
    ("banner-2.jpg", "event-christmas.jpg", None, GEN, 1800, 0.5, dict(wb=0.25, clahe=0.4, vib=0.05)),
    ("banner-4.jpg", "sports-cricket.jpg", None, GEN, 1800, 0.55, dict(wb=0.5, clahe=0.5, sky=0.3)),
    ("banner-5.jpg", "outreach-traffic-awareness.jpg", None, GEN, 1800, 0.5, dict(wb=0.45, clahe=0.45)),
    ("banner-6.jpg", "outreach-relief.jpg", None, GEN, 1800, 0.5, dict(wb=0.45, clahe=0.45)),
    ("chairman.jpg", "leader-chairman.jpg", None, GEN, 900, 0.45, FACE),
    ("mercy.jpg", "leader-vice-chair.jpg", None, GEN, 900, 0.45, dict(FACE, vib=0.0)),
    ("ajay.jpg", "leader-md.jpg", None, GEN, 900, 0.45, FACE),
    ("principal.jpg", "principal.jpg", 900, GEN, 900, 0.4, dict(FACE, vib=0.0)),
]

def emblem():
    im = Image.open(ORIG / "favico.png").convert("RGBA")
    arr = np.array(im)
    alpha = arr[:, :, 3]
    # Composite on white before SR so edge pixels don't pick up black fringes.
    rgb = (arr[:, :, :3].astype(np.float32) * (alpha[..., None] / 255) + 255 * (1 - alpha[..., None] / 255)).astype(np.uint8)
    up = upscale(rgb, PLUS)
    a_up = cv2.resize(alpha, (up.shape[1], up.shape[0]), interpolation=cv2.INTER_CUBIC)
    rgba = np.dstack([up, a_up])
    small = Image.fromarray(rgba, "RGBA").resize((256, round(256 * up.shape[0] / up.shape[1])), Image.LANCZOS)
    small.quantize(colors=128, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(OUT / "emblem.png", optimize=True)
    Image.fromarray(rgba, "RGBA").resize((64, 56), Image.LANCZOS).save(OUT / "favicon.png", optimize=True)

if __name__ == "__main__":
    only = set(sys.argv[1:])
    for src, dst, pre, mdl, final, strength, g in JOBS:
        if only and dst not in only:
            continue
        t = time.time()
        rgb = load(src)
        if pre:
            rgb = resize_w(rgb, pre)
        strength, protect = strength if isinstance(strength, tuple) else (strength, ())
        save(grade(restore(rgb, mdl, final, strength, protect), **g), dst)
        name = src[0] if isinstance(src, tuple) else src
        print(f"{dst:34s} {name:30s} -> {final}px  {time.time() - t:6.1f}s", flush=True)
    if not only or "emblem.png" in only:
        t = time.time(); emblem(); print(f"emblem.png  {time.time() - t:.1f}s", flush=True)
