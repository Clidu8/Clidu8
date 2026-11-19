# -*- coding: utf-8 -*-
"""Motor de vídeo MODO LEONIDA: fondos animados, motion graphics, subtítulos, audio."""
import math, os, re, json, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1920, 1080, 30
BW, BH = 2112, 1188  # fondo un 10% mayor para el zoom de cámara
CANAL = "DON PALMERA"
FD = "/usr/share/fonts/opentype/inter/"
F_BLACK = FD + "InterDisplay-Black.otf"
F_XB = FD + "InterDisplay-ExtraBold.otf"
F_BOLD = FD + "InterDisplay-Bold.otf"
F_MED = FD + "InterDisplay-Medium.otf"
F_BI = FD + "InterDisplay-BlackItalic.otf"

PALETTES = {
    "sunset": dict(top=(20, 6, 48), mid=(120, 20, 110), hor=(255, 110, 80), sun1=(255, 230, 90), sun2=(255, 40, 140),
                   a1=(255, 60, 170), a2=(40, 230, 255), grid=(255, 60, 200), floor=(18, 4, 40)),
    "night": dict(top=(4, 6, 24), mid=(30, 14, 80), hor=(150, 40, 160), sun1=(255, 160, 220), sun2=(140, 40, 255),
                  a1=(170, 90, 255), a2=(40, 230, 255), grid=(130, 80, 255), floor=(6, 4, 22)),
    "cyber": dict(top=(2, 14, 30), mid=(10, 50, 90), hor=(40, 200, 220), sun1=(200, 255, 250), sun2=(255, 50, 120),
                  a1=(255, 40, 90), a2=(40, 240, 255), grid=(40, 220, 255), floor=(2, 10, 24)),
    "toxic": dict(top=(4, 18, 14), mid=(20, 70, 50), hor=(170, 255, 90), sun1=(240, 255, 140), sun2=(40, 200, 120),
                  a1=(120, 255, 90), a2=(255, 70, 190), grid=(90, 255, 140), floor=(3, 14, 10)),
    "gold": dict(top=(24, 10, 4), mid=(110, 50, 10), hor=(255, 170, 40), sun1=(255, 245, 160), sun2=(255, 120, 30),
                 a1=(255, 200, 40), a2=(255, 80, 120), grid=(255, 170, 60), floor=(22, 8, 2)),
    "ocean": dict(top=(2, 10, 36), mid=(10, 60, 120), hor=(60, 220, 230), sun1=(255, 240, 200), sun2=(255, 120, 120),
                  a1=(40, 230, 255), a2=(255, 110, 160), grid=(60, 200, 255), floor=(2, 10, 30)),
}
WHITE = (255, 255, 255)
GOOD = (70, 240, 120)
BAD = (255, 70, 80)
MID = (255, 210, 60)

# ------------------------------------------------------------------ utilidades
@functools.lru_cache(maxsize=256)
def font(path, size):
    return ImageFont.truetype(path, size)

def ease_out(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3

def ease_back(x):
    x = max(0.0, min(1.0, x)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def lerp(a, b, t):
    return a + (b - a) * t

def with_alpha(im, a):
    if a >= 0.999: return im
    im = im.copy()
    al = im.getchannel("A").point(lambda v: int(v * max(0.0, a)))
    im.putalpha(al)
    return im

def paste(canvas, im, x, y, a=1.0, scale=1.0, anchor="mm"):
    if a <= 0.01: return
    if abs(scale - 1.0) > 0.01:
        nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        im = im.resize((nw, nh), Image.BILINEAR)
    im = with_alpha(im, a)
    if anchor == "mm": x, y = x - im.width // 2, y - im.height // 2
    elif anchor == "lm": y = y - im.height // 2
    elif anchor == "rm": x, y = x - im.width, y - im.height // 2
    canvas.alpha_composite(im, (int(x), int(y)))

@functools.lru_cache(maxsize=512)
def text_img(text, path, size, fill=WHITE, glow=None, glow_r=18, stroke=0, stroke_fill=(0, 0, 0), shadow=True, spacing=0):
    f = font(path, size)
    lines = text.split("\n")
    asc, desc = f.getmetrics()
    lh = asc + desc + spacing
    widths = [f.getbbox(l)[2] if l else 0 for l in lines]
    pad = glow_r * 3 + stroke + 10
    w = max(widths) + pad * 2; h = lh * len(lines) + pad * 2
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    for i, l in enumerate(lines):
        x = pad + (max(widths) - widths[i]) // 2
        d.text((x, pad + i * lh), l, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        sh = mask.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.7))
        out.paste(Image.new("RGBA", (w, h), (0, 0, 0, 255)), (6, 10), sh)
    if glow:
        g = mask.filter(ImageFilter.GaussianBlur(glow_r))
        g = g.point(lambda v: min(255, int(v * 2.2)))
        out.alpha_composite(Image.composite(Image.new("RGBA", (w, h), glow + (255,)), Image.new("RGBA", (w, h), (0, 0, 0, 0)), g))
    if stroke:
        sm = Image.new("L", (w, h), 0); sd = ImageDraw.Draw(sm)
        for i, l in enumerate(lines):
            x = pad + (max(widths) - widths[i]) // 2
            sd.text((x, pad + i * lh), l, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
        out.paste(Image.new("RGBA", (w, h), stroke_fill + (255,)), (0, 0), sm)
        fm = Image.new("L", (w, h), 0); fdw = ImageDraw.Draw(fm)
        for i, l in enumerate(lines):
            x = pad + (max(widths) - widths[i]) // 2
            fdw.text((x, pad + i * lh), l, font=f, fill=255)
        out.paste(Image.new("RGBA", (w, h), fill + (255,)), (0, 0), fm)
    else:
        out.paste(Image.new("RGBA", (w, h), fill + (255,)), (0, 0), mask)
    return out

def rrect(size, r, fill, outline=None, width=0):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), r, fill=fill, outline=outline, width=width)
    return im

@functools.lru_cache(maxsize=64)
def panel(w, h, accent):
    """Panel translúcido con borde neón."""
    pad = 40
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle((pad, pad, pad + w, pad + h), 36, outline=accent + (255,), width=6)
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    im.alpha_composite(glow)
    ImageDraw.Draw(im).rounded_rectangle((pad, pad, pad + w, pad + h), 36, fill=(8, 6, 20, 190), outline=accent + (255,), width=3)
    return im

def wrap(text, f, maxw):
    words = text.split(); lines = []; cur = ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if f.getbbox(t)[2] <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w_
    if cur: lines.append(cur)
    return "\n".join(lines)

# ------------------------------------------------------------------ fondo
def _palm(d, x, y, h, color, flip=1, rng=None):
    # tronco curvo
    pts = []
    for i in range(30):
        t = i / 29
        pts.append((x + flip * 60 * math.sin(t * 1.4) * t, y - h * t))
    for i in range(len(pts) - 1):
        wdt = int(lerp(26, 12, i / 29))
        d.line([pts[i], pts[i + 1]], fill=color, width=wdt)
    tx, ty = pts[-1]
    for k in range(9):
        ang = math.radians(-170 + k * 22 + (rng.uniform(-6, 6) if rng else 0))
        L = h * 0.42
        poly = []
        for j in range(16):
            t = j / 15
            px = tx + math.cos(ang) * L * t
            py = ty + math.sin(ang) * L * t + (L * 0.45) * t * t
            poly.append((px, py))
        for j in range(len(poly) - 1):
            wdt = int(lerp(22, 3, j / 15))
            d.line([poly[j], poly[j + 1]], fill=color, width=wdt)
    d.ellipse((tx - 16, ty - 16, tx + 16, ty + 16), fill=color)

def build_background(pal, seed=0):
    P = PALETTES[pal]
    rng = np.random.default_rng(seed)
    hor = int(BH * 0.64)
    # cielo
    y = np.linspace(0, 1, hor)[:, None]
    top, mid, ho = [np.array(c, float) for c in (P["top"], P["mid"], P["hor"])]
    sky = np.where(y < 0.6, top + (mid - top) * (y / 0.6), mid + (ho - mid) * ((y - 0.6) / 0.4)) if False else None
    col = np.zeros((hor, 3))
    for i in range(hor):
        t = i / hor
        col[i] = top + (mid - top) * (t / 0.6) if t < 0.6 else mid + (ho - mid) * ((t - 0.6) / 0.4)
    img = np.zeros((BH, BW, 3), np.uint8)
    img[:hor] = col[:, None, :].astype(np.uint8)
    im = Image.fromarray(img).convert("RGBA")
    d = ImageDraw.Draw(im)
    # estrellas
    for _ in range(260):
        sx, sy = rng.integers(0, BW), rng.integers(0, int(hor * 0.6))
        b = int(rng.integers(90, 255)); r = rng.choice([1, 1, 1, 2])
        d.ellipse((sx, sy, sx + r, sy + r), fill=(b, b, b, 255))
    # sol con franjas
    sr = 300; cx, cy = BW // 2, hor - 90
    sun = Image.new("RGBA", (sr * 2, sr * 2), (0, 0, 0, 0))
    sa = np.zeros((sr * 2, sr * 2, 4), np.uint8)
    yy, xx = np.mgrid[0:sr * 2, 0:sr * 2]
    inside = (xx - sr) ** 2 + (yy - sr) ** 2 <= sr ** 2
    t = yy / (sr * 2)
    c1, c2 = np.array(P["sun1"]), np.array(P["sun2"])
    for k in range(3): sa[..., k] = (c1[k] + (c2[k] - c1[k]) * t).astype(np.uint8)
    stripes = np.ones_like(inside)
    for k in range(7):
        y0 = int(sr * 1.0 + k * 42); hh = 4 + k * 3
        stripes[y0:y0 + hh] = 0
    sa[..., 3] = (inside & stripes.astype(bool)) * 255
    sun = Image.fromarray(sa, "RGBA")
    sglow = Image.new("RGBA", (sr * 4, sr * 4), (0, 0, 0, 0))
    ImageDraw.Draw(sglow).ellipse((sr * 0.7, sr * 0.7, sr * 3.3, sr * 3.3), fill=P["sun2"] + (150,))
    sglow = sglow.filter(ImageFilter.GaussianBlur(90))
    im.alpha_composite(sglow, (cx - sr * 2, cy - sr * 2))
    im.alpha_composite(sun, (cx - sr, cy - sr))
    # skyline
    sky_l = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); sd = ImageDraw.Draw(sky_l)
    dark = tuple(int(c * 0.25) for c in P["top"]) + (255,)
    x = 0
    while x < BW:
        bw_ = int(rng.integers(40, 130)); bh_ = int(rng.integers(60, 330))
        if abs(x - BW / 2) < 360: bh_ = int(bh_ * 0.45)
        sd.rectangle((x, hor - bh_, x + bw_, hor), fill=dark)
        for wy in range(hor - bh_ + 12, hor - 8, 22):
            for wx in range(x + 8, x + bw_ - 8, 18):
                if rng.random() < 0.18:
                    sd.rectangle((wx, wy, wx + 6, wy + 9), fill=P["a2"] + (200,))
        if rng.random() < 0.15:
            sd.rectangle((x + bw_ // 2 - 2, hor - bh_ - 50, x + bw_ // 2 + 2, hor - bh_), fill=dark)
        x += bw_ + int(rng.integers(0, 14))
    im.alpha_composite(sky_l)
    # suelo
    floor = np.zeros((BH - hor, BW, 3), np.uint8)
    fc = np.array(P["floor"], float)
    for i in range(BH - hor):
        floor[i] = (fc * (0.6 + 0.4 * i / (BH - hor))).astype(np.uint8)
    im.paste(Image.fromarray(floor), (0, hor))
    # palmeras
    palms = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); pd = ImageDraw.Draw(palms)
    pc = (4, 2, 10, 255)
    _palm(pd, 150, BH + 10, 760, pc, 1, rng)
    _palm(pd, 330, BH + 40, 560, pc, -1, rng)
    _palm(pd, BW - 170, BH + 10, 800, pc, -1, rng)
    _palm(pd, BW - 380, BH + 40, 520, pc, 1, rng)
    return im, palms, hor

def grid_frames(pal, hor, n=30):
    P = PALETTES[pal]
    frames = []
    vx = BW // 2
    gh = BH - hor
    for k in range(n):
        g = Image.new("RGBA", (BW, gh), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
        ph = k / n
        for i in range(-24, 25):
            x_bot = vx + i * 170
            d.line([(vx + i * 6, 0), (x_bot, gh)], fill=P["grid"] + (150,), width=2)
        for j in range(14):
            z = (j + ph)
            yy = gh * (z / 14) ** 2.2
            a = int(60 + 160 * (z / 14))
            d.line([(0, yy), (BW, yy)], fill=P["grid"] + (min(255, a),), width=2 + int(z / 6))
        glow = g.filter(ImageFilter.GaussianBlur(6))
        out = Image.new("RGBA", (BW, gh), (0, 0, 0, 0)); out.alpha_composite(glow); out.alpha_composite(g)
        # niebla del horizonte
        fog = Image.new("RGBA", (BW, 160), (0, 0, 0, 0))
        fa = np.zeros((160, BW, 4), np.uint8); fa[..., :3] = P["hor"]
        fa[..., 3] = (np.linspace(150, 0, 160)[:, None]).astype(np.uint8)
        out.alpha_composite(Image.fromarray(fa, "RGBA"))
        frames.append(out)
    return frames

def vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a = np.clip((r - 0.55) / 0.8, 0, 1) * 200
    v = np.zeros((H, W, 4), np.uint8); v[..., 3] = a.astype(np.uint8)
    return Image.fromarray(v, "RGBA")

class Background:
    def __init__(self, pal, seed):
        static, palms, hor = build_background(pal, seed)
        grids = grid_frames(pal, hor)
        self.frames = []
        for g in grids:
            f = static.copy(); f.alpha_composite(g, (0, hor)); f.alpha_composite(palms)
            self.frames.append(f.convert("RGB"))
        self.dim = Image.new("RGBA", (W, H), (0, 0, 0, 95))
        self.vig = vignette()

    def get(self, fi, zoom, dim=True, shake=(0, 0)):
        f = self.frames[fi % len(self.frames)]
        cw, ch = int(BW / zoom), int(BH / zoom)
        cw = max(cw, W); ch = max(ch, H)
        x0 = (BW - cw) // 2 + shake[0]; y0 = (BH - ch) // 2 + shake[1]
        x0 = max(0, min(BW - cw, x0)); y0 = max(0, min(BH - ch, y0))
        im = f.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR).convert("RGBA")
        if dim: im.alpha_composite(self.dim)
        im.alpha_composite(self.vig)
        return im

# ------------------------------------------------------------------ mapa ilustrativo
LAND = [(80, 120), (520, 120), (600, 150), (690, 170), (760, 200), (800, 260), (830, 360), (860, 470), (880, 580),
        (870, 690), (840, 780), (800, 860), (740, 900), (690, 880), (650, 820), (610, 760), (570, 680), (540, 600),
        (520, 520), (500, 440), (470, 360), (430, 300), (360, 270), (280, 260), (200, 270), (120, 250), (80, 200)]
KEYS = [(700, 930), (650, 955), (600, 975), (545, 990), (490, 1000), (440, 1005)]
REGIONS = {
    "VICE CITY": (835, 790), "LEONIDA KEYS": (560, 985), "GRASSRIVERS": (660, 730),
    "PORT GELLHORN": (220, 215), "AMBROSIA": (650, 420), "MOUNT KALAGA": (600, 205),
}

LABEL_OFF = {"VICE CITY": (150, 0), "GRASSRIVERS": (-170, -10), "LEONIDA KEYS": (-120, 55), "PORT GELLHORN": (60, 60),
             "AMBROSIA": (0, -55), "MOUNT KALAGA": (60, 60)}

@functools.lru_cache(maxsize=8)
def map_base(accent, accent2):
    s = 0.95
    im = Image.new("RGBA", (1250, 1100), (0, 0, 0, 0))
    pts = [(x * s, y * s) for x, y in LAND]
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.polygon(pts, outline=accent + (255,), width=10)
    for kx, ky in KEYS: gd.ellipse((kx * s - 16, ky * s - 9, kx * s + 16, ky * s + 9), outline=accent + (255,), width=6)
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    im.alpha_composite(glow)
    d = ImageDraw.Draw(im)
    d.polygon(pts, fill=(14, 22, 40, 235), outline=accent + (255,), width=4)
    for kx, ky in KEYS: d.ellipse((kx * s - 16, ky * s - 9, kx * s + 16, ky * s + 9), fill=(14, 22, 40, 235), outline=accent + (255,), width=3)
    # pantano / ríos
    for k in range(6):
        y0 = 640 + k * 22
        d.line([(560 * s, y0 * s), (640 * s, (y0 + 10) * s), (720 * s, (y0 - 6) * s), (790 * s, (y0 + 8) * s)], fill=accent2 + (90,), width=2)
    # lago
    d.ellipse((600 * s, 520 * s, 690 * s, 580 * s), outline=accent2 + (160,), width=3)
    f = font(F_MED, 22)
    d.text((40, 1040), "Mapa ilustrativo · no oficial", font=f, fill=(200, 200, 220, 200))
    return im

# ------------------------------------------------------------------ escenas
class Scene:
    def __init__(self, kind, data, text, P, idx, total_list):
        self.kind, self.data, self.text, self.P = kind, data, text, P
        self.idx = idx
        self.dur = 0; self.start = 0; self.voice_dur = 0

    def events(self):
        """Momentos (s, relativos a la escena) donde suena un 'pop'."""
        if self.kind == "text":
            n = len(self.data["lines"]); return [self._line_t(i) for i in range(n)]
        if self.kind in ("versus",):
            return [0.5 + i * 0.35 for i in range(len(self.data["items"]))]
        if self.kind == "map" and self.data["show"]:
            return [0.6]
        if self.kind == "cta":
            return [self.dur * 0.55]
        return []

    def _line_t(self, i):
        n = len(self.data["lines"])
        span = max(1.0, self.voice_dur * 0.75)
        return 0.5 + span * i / max(1, n)

    def draw(self, cv, t, fi):
        P = self.P; a1, a2 = P["a1"], P["a2"]
        D = self.dur
        out_a = 1.0 - ease_out((t - (D - 0.25)) / 0.25) if t > D - 0.25 else 1.0
        k = self.kind; d = self.data
        if k == "title":
            e = ease_out(t / 0.6)
            paste(cv, text_img(" " + d["kicker"] + " ", F_XB, 46, fill=(10, 10, 20), shadow=False), W // 2, 300, out_a * e)
            pill = rrect((text_img(" " + d["kicker"] + " ", F_XB, 46, shadow=False).width - 40, 74), 37, a2 + (255,))
            paste(cv, pill, W // 2, 300 - int((1 - e) * 40), out_a * e)
            paste(cv, text_img(d["kicker"], F_XB, 46, fill=(10, 10, 20), shadow=False), W // 2, 298 - int((1 - e) * 40), out_a * e)
            sc = lerp(1.35, 1.0, ease_back(t / 0.55))
            ti = text_img(d["title"], F_BLACK, 170, glow=a1, glow_r=22, spacing=-20)
            if t < 0.35:  # glitch RGB
                off = int(18 * (1 - t / 0.35))
                r = text_img(d["title"], F_BLACK, 170, fill=(255, 40, 80), shadow=False, spacing=-20)
                b = text_img(d["title"], F_BLACK, 170, fill=(40, 200, 255), shadow=False, spacing=-20)
                paste(cv, r, W // 2 - off, 580, 0.6, sc); paste(cv, b, W // 2 + off, 580, 0.6, sc)
            paste(cv, ti, W // 2, 580, out_a * min(1, t / 0.15), sc)
        elif k == "stat":
            e = ease_back(t / 0.6)
            paste(cv, panel(1400, 560, a1), W // 2, 470, out_a * ease_out(t / 0.3), lerp(0.9, 1, e))
            if "count" in d:
                c = d["count"]; v = c * ease_out(t / 1.4)
                s = f"{int(round(v)):,}".replace(",", ".")
                val = d.get("prefix", "") + s + d.get("suffix", "")
                if t >= 1.4: val = d["value"]
            else:
                val = d["value"]
            size = 200 if len(d["value"]) <= 7 else (160 if len(d["value"]) <= 10 else 130)
            paste(cv, text_img(val, F_BLACK, size, glow=a2, glow_r=20), W // 2, 400, out_a, lerp(0.6, 1, e))
            paste(cv, text_img(d["label"], F_XB, 54, fill=a1), W // 2, 575 + int((1 - ease_out((t - 0.3) / 0.5)) * 30), out_a * ease_out((t - 0.3) / 0.5))
            if d.get("sub"):
                paste(cv, text_img(d["sub"], F_MED, 40, fill=(225, 225, 235)), W // 2, 655, out_a * ease_out((t - 0.6) / 0.5))
        elif k == "text":
            e = ease_out(t / 0.5)
            paste(cv, panel(1500, 640, a1 if not d.get("bad") else BAD), W // 2, 470, out_a * e)
            ti = text_img(d["title"], F_BLACK, 76, glow=a1 if not d.get("bad") else BAD, glow_r=14)
            paste(cv, ti, 260 - 40 + int((1 - e) * -60), 240, out_a * e, anchor="lm")
            uw = int(500 * ease_out((t - 0.2) / 0.6))
            if uw > 2: cv.alpha_composite(rrect((uw, 8), 4, a2 + (255,)), (260, 300))
            for i, line in enumerate(d["lines"]):
                lt = t - self._line_t(i)
                if lt <= 0: continue
                le = ease_out(lt / 0.4)
                y = 400 + i * 110
                col = BAD if d.get("bad") else a2
                if not line.startswith("× "):
                    paste(cv, rrect((26, 26), 6, col + (255,)), 280 + int((1 - le) * 80), y, out_a * le)
                    txt = line
                else:
                    txt = line
                paste(cv, text_img(txt, F_BOLD, 54, fill=WHITE), 330 + int((1 - le) * 80), y, out_a * le, anchor="lm")
        elif k == "list":
            e = ease_back(t / 0.55)
            good = d.get("good")
            col = GOOD if good is True else (BAD if good is False else a1)
            paste(cv, panel(1560, 460, col), W // 2, 470, out_a * ease_out(t / 0.3))
            badge = rrect((300, 300), 60, col + (255,))
            paste(cv, badge, 400, 470, out_a, lerp(0.2, 1, e))
            paste(cv, text_img(d["n"], F_BLACK, 190 if len(d["n"]) < 2 else 150, fill=(10, 10, 20), shadow=False), 400, 455, out_a, lerp(0.2, 1, e))
            te = ease_out((t - 0.15) / 0.5)
            f = font(F_BLACK, 92)
            title = wrap(d["title"], f, 1050)
            paste(cv, text_img(title, F_BLACK, 92, glow=col, glow_r=12, spacing=-6), 600 - 30 + int((1 - te) * 100), 420 - (40 if "\n" in title else 0), out_a * te, anchor="lm")
            se = ease_out((t - 0.4) / 0.5)
            sub = wrap(d["sub"], font(F_MED, 46), 1050)
            paste(cv, text_img(sub, F_MED, 46, fill=(230, 230, 240)), 600 - 30 + int((1 - se) * 100), 560 + (20 if "\n" in title else 0), out_a * se, anchor="lm")
        elif k == "bars":
            e = ease_out(t / 0.4)
            paste(cv, panel(1560, 660, a1), W // 2, 470, out_a * e)
            paste(cv, text_img(d["title"], F_BLACK, 70, glow=a1, glow_r=12), W // 2, 210, out_a * e)
            items = d["items"]; mx = max(v for _, v, _ in items); mn = d.get("minv", 0)
            n = len(items); gap = min(130, 480 // n)
            y0 = 470 - (n - 1) * gap // 2
            for i, (lab, v, vt) in enumerate(items):
                be = ease_out((t - 0.4 - i * 0.3) / 0.9)
                y = y0 + i * gap
                paste(cv, text_img(lab, F_XB, 44, fill=WHITE), 640, y, out_a * min(1, be * 3), anchor="rm")
                frac = (v - mn) / (mx - mn) if mx > mn else 1
                frac = max(0.08, frac)
                bw_ = int(820 * frac * be)
                col = a2 if i else a1
                if bw_ > 4:
                    bar = rrect((bw_, 64), 14, col + (255,))
                    cv.alpha_composite(with_alpha(bar, out_a), (670, y - 32))
                paste(cv, text_img(vt, F_BLACK, 48, fill=WHITE), 670 + bw_ + 24, y, out_a * min(1, be * 2), anchor="lm")
            if d.get("note"):
                paste(cv, text_img(d["note"], F_MED, 32, fill=(200, 200, 215)), W // 2, 770, out_a * ease_out((t - 1.2) / 0.5))
        elif k == "versus":
            e = ease_out(t / 0.4)
            paste(cv, text_img(d["title"], F_BLACK, 72, glow=a1, glow_r=12), W // 2, 210, out_a * e)
            items = d["items"]; n = len(items)
            cw = 500 if n == 3 else 620
            gap = 40
            x0 = W // 2 - ((n * cw + (n - 1) * gap) // 2) + cw // 2
            for i, (lab, st, kind) in enumerate(items):
                ce = ease_back((t - 0.5 - i * 0.35) / 0.5)
                if t - 0.5 - i * 0.35 <= 0: continue
                col = GOOD if kind == "good" else (BAD if kind == "bad" else MID)
                x = x0 + i * (cw + gap)
                card = panel(cw - 80, 380, col)
                paste(cv, card, x, 500, out_a, lerp(0.5, 1, ce))
                f = font(F_BLACK, 60)
                paste(cv, text_img(wrap(lab, f, cw - 140), F_BLACK, 60, fill=WHITE), x, 450, out_a, lerp(0.5, 1, ce))
                st_im = text_img(st, F_BLACK, 44, fill=(10, 10, 20), shadow=False)
                if st_im.width > cw - 60: st_im = st_im.resize((cw - 60, int(st_im.height * (cw - 60) / st_im.width)), Image.LANCZOS)
                pill = rrect((min(cw - 120, st_im.width - 20), 84), 42, col + (255,))
                paste(cv, pill, x, 590, out_a, lerp(0.5, 1, ce))
                paste(cv, st_im, x, 588, out_a, lerp(0.5, 1, ce))
        elif k == "warn":
            e = ease_back(t / 0.5)
            # cinta de precaución
            tape = Image.new("RGBA", (W + 200, 70), (255, 210, 0, 255)); td = ImageDraw.Draw(tape)
            off = int(t * 120) % 100
            for x in range(-100, W + 300, 100):
                td.polygon([(x + off, 0), (x + off + 50, 0), (x + off, 70), (x + off - 50, 70)], fill=(15, 15, 15, 255))
            paste(cv, tape.rotate(-3, expand=True, resample=Image.BILINEAR), W // 2, 170, out_a)
            paste(cv, tape.rotate(3, expand=True, resample=Image.BILINEAR), W // 2, 790, out_a)
            paste(cv, panel(1500, 420, MID), W // 2, 480, out_a * ease_out(t / 0.3))
            tri = Image.new("RGBA", (200, 180), (0, 0, 0, 0)); trd = ImageDraw.Draw(tri)
            trd.polygon([(100, 5), (195, 175), (5, 175)], fill=MID + (255,))
            trd.rectangle((92, 55, 108, 125), fill=(15, 15, 15, 255)); trd.ellipse((90, 138, 110, 158), fill=(15, 15, 15, 255))
            pulse = 1 + 0.05 * math.sin(t * 8)
            paste(cv, tri, 360, 480, out_a, lerp(0.3, 1, e) * pulse)
            f = font(F_BLACK, 74)
            paste(cv, text_img(wrap(d["title"], f, 1050), F_BLACK, 74, fill=MID, stroke=3, stroke_fill=(20, 16, 0)), 520, 420, out_a * ease_out((t - 0.2) / 0.4), anchor="lm")
            paste(cv, text_img(wrap(d["sub"], font(F_MED, 44), 1050), F_MED, 44, fill=WHITE), 520, 560, out_a * ease_out((t - 0.45) / 0.4), anchor="lm")
        elif k == "map":
            mb = map_base(a2, a1)
            e = ease_out(t / 0.6)
            mapim = mb.copy(); md = ImageDraw.Draw(mapim)
            shown = d["show"]
            for j, rn in enumerate(shown):
                rx, ry = REGIONS[rn]; rx *= 0.95; ry *= 0.95
                new = (j == len(shown) - 1)
                pe = ease_back((t - 0.5) / 0.5) if new else 1
                if pe <= 0: continue
                col = a1 if new else (230, 230, 240)
                if new:
                    pr = 20 + (t * 60) % 60
                    md.ellipse((rx - pr, ry - pr, rx + pr, ry + pr), outline=col + (int(255 * (1 - ((t * 60) % 60) / 60)),), width=4)
                rr = 14 * pe
                md.ellipse((rx - rr, ry - rr, rx + rr, ry + rr), fill=col + (255,), outline=(10, 10, 20, 255), width=3)
                lab = text_img(rn, F_BLACK, 34 if not new else 40, fill=col, stroke=4, stroke_fill=(5, 5, 15), shadow=False)
                dx, dy = LABEL_OFF.get(rn, (0, -60))
                lx = rx + dx - lab.width // 2; ly = ry + dy - lab.height // 2
                lx = max(0, min(mapim.width - lab.width, lx))
                mapim.alpha_composite(with_alpha(lab, min(1, pe)), (int(lx), int(ly)))
            paste(cv, mapim, 1360, 470, out_a * e, lerp(0.70, 0.74, ease_out(t / D)))
            # columna de título
            paste(cv, text_img("ZONA" if shown else "EL MAPA", F_XB, 40, fill=a2), 140, 330, out_a * e, anchor="lm")
            f = font(F_BLACK, 96)
            paste(cv, text_img(wrap(d["title"], f, 700), F_BLACK, 96, glow=a1, glow_r=14, spacing=-8), 140, 470, out_a * ease_out((t - 0.2) / 0.5), anchor="lm")
            if shown:
                paste(cv, text_img(f"{len(shown)} / 6", F_BLACK, 60, fill=WHITE), 140, 640, out_a * e, anchor="lm")
        elif k == "cta":
            e = ease_back(t / 0.5)
            paste(cv, text_img(d["title"], F_BLACK, 110, glow=a1, glow_r=18), W // 2, 300, out_a, lerp(0.6, 1, e))
            clicked = t > D * 0.55
            bcol = (60, 60, 70) if clicked else (230, 20, 30)
            label = "SUSCRITO ✓" if clicked else "SUSCRIBIRSE"
            btn = rrect((560, 130), 65, bcol + (255,))
            press = 0.92 if abs(t - D * 0.55) < 0.12 else 1.0
            paste(cv, btn, W // 2 - 60, 520, out_a * ease_out((t - 0.3) / 0.4), press)
            paste(cv, text_img(label, F_BLACK, 50, fill=WHITE, shadow=False), W // 2 - 60, 516, out_a * ease_out((t - 0.3) / 0.4), press)
            # campana
            bell = Image.new("RGBA", (120, 120), (0, 0, 0, 0)); bd = ImageDraw.Draw(bell)
            bd.pieslice((20, 10, 100, 100), 180, 360, fill=WHITE + (255,)); bd.rectangle((20, 55, 100, 85), fill=WHITE + (255,))
            bd.rectangle((10, 85, 110, 95), fill=WHITE + (255,)); bd.ellipse((48, 95, 72, 115), fill=WHITE + (255,))
            ang = 18 * math.sin(t * 20) * max(0, 1 - abs(t - D * 0.65) / 0.4) if clicked else 0
            paste(cv, bell.rotate(ang, resample=Image.BILINEAR), W // 2 + 300, 520, out_a * ease_out((t - 0.3) / 0.4))
            # cursor
            if t < D * 0.55 + 0.6:
                cp = ease_out((t - 0.5) / (D * 0.55 - 0.5))
                cx_ = lerp(W // 2 + 500, W // 2 - 20, cp); cy_ = lerp(800, 540, cp)
                cur = Image.new("RGBA", (60, 80), (0, 0, 0, 0)); cd = ImageDraw.Draw(cur)
                cd.polygon([(5, 5), (5, 65), (20, 50), (32, 76), (42, 71), (30, 46), (52, 46)], fill=WHITE + (255,), outline=(0, 0, 0, 255))
                paste(cv, cur, cx_, cy_, out_a, anchor="lt") if False else cv.alpha_composite(cur, (int(cx_), int(cy_)))
            paste(cv, text_img(d["sub"], F_BOLD, 48, fill=(235, 235, 245)), W // 2, 700, out_a * ease_out((t - 0.6) / 0.5))
        elif k == "end":
            e = ease_out(t / 0.6)
            paste(cv, text_img("SIGUE VIENDO", F_BLACK, 80, glow=a1, glow_r=14), W // 2, 160, e)
            box = Image.new("RGBA", (760, 428), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
            bd.rounded_rectangle((0, 0, 759, 427), 24, fill=(0, 0, 0, 120), outline=a2 + (255,), width=5)
            paste(cv, box, 560, 560, e)
            paste(cv, text_img("PRÓXIMO VÍDEO", F_XB, 44, fill=WHITE), 560, 560, e)
            ring = Image.new("RGBA", (440, 440), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
            rd.ellipse((10, 10, 430, 430), fill=(0, 0, 0, 120), outline=a1 + (255,), width=6)
            paste(cv, ring, 1380, 560, e)
            paste(cv, text_img("SUSCRÍBETE", F_XB, 44, fill=WHITE), 1380, 560, e)

# ------------------------------------------------------------------ subtítulos
def split_chunks(text, maxw=5):
    words = text.split()
    chunks, cur = [], []
    for w_ in words:
        cur.append(w_)
        if len(cur) >= maxw or re.search(r"[.,;:?!]$", w_) and len(cur) >= 2:
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    return chunks

def word_times(chunks, t0, dur):
    """Tiempo aproximado por palabra, proporcional a sus letras (+pausas en puntuación)."""
    flat = [w for c in chunks for w in c]
    weights = [len(re.sub(r"\W", "", w)) + 2 + (4 if re.search(r"[.?!]$", w) else (2 if re.search(r"[,;:]$", w) else 0)) for w in flat]
    tot = sum(weights); acc = 0; times = []
    for wgt in weights:
        times.append((t0 + dur * acc / tot, t0 + dur * (acc + wgt) / tot)); acc += wgt
    return times

def subtitle_img(words, hi, accent):
    key = (tuple(words), hi, accent)
    return _sub_cached(key)

@functools.lru_cache(maxsize=2048)
def _sub_cached(key):
    words, hi, accent = key
    f = font(F_BLACK, 58)
    sp = 18
    ws = [w.upper() for w in words]
    widths = [f.getbbox(w)[2] for w in ws]
    tw = sum(widths) + sp * (len(ws) - 1)
    im = Image.new("RGBA", (tw + 60, 110), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = 30
    for i, w in enumerate(ws):
        col = accent if i == hi else WHITE
        d.text((x, 20), w, font=f, fill=col + (255,), stroke_width=7, stroke_fill=(0, 0, 0, 255))
        x += widths[i] + sp
    return im

def spoken_to_display(text):
    """Para los subtítulos: deshacer la escritura fonética."""
    rep = {"ge te a": "GTA", "Ge te a": "GTA", "PS cinco": "PS5", "Vais Siti": "Vice City", "Yeison Shráier": "Jason Schreier",
           "Yeison": "Jason", "Ocarina of Taim": "Ocarina of Time", "Red Ded Redemshon": "Red Dead Redemption", "Bigfut": "Bigfoot",
           "Leonida Kis": "Leonida Keys", "Grasrívers": "Grassrivers", "Port Guélhorn": "Port Gellhorn", "Maunt Kalaga": "Mount Kalaga",
           "Díyital Faundri": "Digital Foundry", "Bak Mi": "Buck Me", "Blúmberg": "Bloomberg", "Series equis": "Series X",
           "Series ese": "Series S", "equis": "X", "ele uno": "L1", "ele be": "LB", "erre uno": "R1", "erre be": "RB",
           "cuatro ka": "4K", "mil cuatrocientos cuarenta pe": "1440p"}
    for k in sorted(rep, key=len, reverse=True):
        text = text.replace(k, rep[k])
    return text

def srt_time(s):
    ms = int(round(s * 1000)); h = ms // 3600000; ms %= 3600000; m = ms // 60000; ms %= 60000
    return f"{h:02}:{m:02}:{ms // 1000:02},{ms % 1000:03}"

# ------------------------------------------------------------------ render principal
def render_video(video, voices, sr, outdir, seed=0):
    from musica import generar, whoosh, pop, impacto
    P = PALETTES[video["palette"]]
    scenes = []
    t = 0.0
    LEAD, TAIL = 0.35, 0.55
    for i, (kind, data, text) in enumerate(video["scenes"]):
        s = Scene(kind, data, text, P, i, None)
        s.voice_dur = len(voices[i]) / sr
        s.dur = LEAD + s.voice_dur + TAIL
        if kind == "cta": s.dur += 0.8
        s.start = t; t += s.dur
        scenes.append(s)
    end = Scene("end", {}, "", P, len(scenes), None); end.dur = 12.0; end.start = t; t += end.dur
    scenes.append(end)
    total = t
    N = int(math.ceil(total * FPS))

    # ---------- audio
    L = int(total * sr) + sr
    voice = np.zeros(L, np.float32); sfx = np.zeros(L, np.float32)
    wh = whoosh(); im_ = impacto()
    for i, s in enumerate(scenes[:-1]):
        a = int((s.start + LEAD) * sr); v = voices[i]
        voice[a:a + len(v)] += v
        b = int(max(0, s.start - 0.15) * sr)
        snd = im_ if i == 0 else wh
        sfx[b:b + len(snd)] += snd[:L - b] * (0.5 if i == 0 else 0.22)
        for k_, et in enumerate(s.events()):
            c = int((s.start + et) * sr); p = pop(k_)
            sfx[c:c + len(p)] += p[:L - c] * 0.18
    pk = np.max(np.abs(voice)) + 1e-9; voice = voice / pk * 0.89
    mus = generar(total + 1, seed)[:L]
    if len(mus) < L: mus = np.pad(mus, (0, L - len(mus)))
    # ducking
    env = np.abs(voice)
    win = int(0.25 * sr)
    env = np.convolve(env, np.ones(win) / win, mode="same")
    active = (env > 0.01).astype(np.float32)
    sm = int(0.3 * sr)
    active = np.convolve(active, np.ones(sm) / sm, mode="same")
    gain = 0.30 - 0.20 * active
    mix = voice + mus * gain + sfx
    mix /= max(1.0, np.max(np.abs(mix)) / 0.97)
    import soundfile as sf
    os.makedirs(outdir, exist_ok=True)
    wav = os.path.join(outdir, "_audio.wav")
    sf.write(wav, mix[:int(total * sr)], sr)

    # ---------- subtítulos (tiempos)
    subs = []  # (start, end, words, word_times)
    for i, s in enumerate(scenes[:-1]):
        disp = spoken_to_display(s.text)
        chunks = split_chunks(disp)
        wt = word_times(chunks, s.start + LEAD, s.voice_dur)
        k = 0
        for c in chunks:
            ts = wt[k:k + len(c)]
            subs.append((ts[0][0], ts[-1][1], c, ts)); k += len(c)
    with open(os.path.join(outdir, "subtitulos.srt"), "w") as fh:
        for j, (a, b, c, _) in enumerate(subs, 1):
            fh.write(f"{j}\n{srt_time(a)} --> {srt_time(b)}\n{' '.join(c)}\n\n")

    # ---------- vídeo
    bg = Background(video["palette"], seed)
    out_mp4 = os.path.join(outdir, "video.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out_mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    rng = np.random.default_rng(seed)
    particles = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 4), rng.uniform(10, 40), rng.uniform(0, 6.28)) for _ in range(40)]
    si = 0; sub_i = 0
    brand = text_img(CANAL, F_BI, 30, fill=WHITE, glow=P["a1"], glow_r=8)
    for fi in range(N):
        tt = fi / FPS
        while si < len(scenes) - 1 and tt >= scenes[si].start + scenes[si].dur: si += 1
        s = scenes[si]; lt = tt - s.start
        zoom = 1.0 + 0.06 * (lt / s.dur)
        shake = (0, 0)
        if lt < 0.12 and si > 0:
            shake = (int(rng.integers(-8, 9)), int(rng.integers(-6, 7)))
        cv = bg.get(fi, zoom, dim=True, shake=shake)
        # partículas
        pdraw = ImageDraw.Draw(cv)
        for (px, py, pr, sp, ph) in particles:
            y = (py - tt * sp) % H; x = px + 20 * math.sin(tt * 0.5 + ph)
            al = int(120 + 100 * math.sin(tt * 2 + ph))
            pdraw.ellipse((x - pr, y - pr, x + pr, y + pr), fill=P["a2"] + (max(0, al),))
        s.draw(cv, lt, fi)
        # flash de transición
        if lt < 0.08 and si > 0:
            cv.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(120 * (1 - lt / 0.08)))))
        # marca y barra de progreso
        cv.alpha_composite(brand, (20, 14))
        pw = int(W * tt / total)
        if pw > 0: cv.alpha_composite(Image.new("RGBA", (pw, 6), P["a1"] + (255,)), (0, 0))
        # subtítulos
        while sub_i < len(subs) and tt > subs[sub_i][1] + 0.15: sub_i += 1
        if sub_i < len(subs) and subs[sub_i][0] - 0.05 <= tt and s.kind != "end":
            a, b, c, ts = subs[sub_i]
            hi = 0
            for j, (wa, wb) in enumerate(ts):
                if tt >= wa: hi = j
            simg = subtitle_img(tuple(c), hi, MID)
            pop_s = 1.0 + 0.08 * max(0, 1 - (tt - a) / 0.12)
            paste(cv, simg, W // 2, 975, 1.0, pop_s)
        proc.stdin.write(cv.convert("RGB").tobytes())
    proc.stdin.close(); proc.wait()
    os.remove(wav)
    chapters = [(s.start, s) for s in scenes[:-1]]
    return dict(total=total, scenes=[(s.start, s.kind, s.data) for s in scenes[:-1]])
