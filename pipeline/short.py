# -*- coding: utf-8 -*-
"""Short vertical de ejemplo (1080x1920) con el estilo de la skill clips-virales:
hook apilado, ráfaga flash, remate centrado, interludio sobre color, troceo, cortes secos."""
import os, sys, math, subprocess
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import render as R
from musica import generar, whoosh, pop, impacto

W, H, FPS = 1080, 1920, 30
SR = 24000
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "shorts", "01-bigfoot")
os.makedirs(OUT, exist_ok=True)
P = R.PALETTES["toxic"]
RED = (255, 45, 60); WHITE = (255, 255, 255); BLACK = (10, 10, 14); PINK = (255, 150, 200)

voices = [sf.read(os.path.join(os.path.dirname(__file__), f".tts_cache/short/{i}.wav"), dtype="float32")[0] for i in range(7)]
# escenas: (tipo, pausa_antes, extra_después)
KINDS = ["hook", "bigfoot", "mapa", "interludio", "cangrejo", "antena", "cta"]
GAP = 0.12
starts, durs = [], []
t = 0.0
for i, v in enumerate(voices):
    d = len(v) / SR + (0.55 if KINDS[i] == "bigfoot" else 0.18)
    if KINDS[i] == "cta": d += 1.2
    starts.append(t); durs.append(d); t += d
TOTAL = t
N = int(TOTAL * FPS)

# ---------- fondo vertical (recorte del fondo horizontal)
bg = R.Background("toxic", 6)
def background(fi, zoom):
    f = bg.frames[fi % len(bg.frames)]
    cw = int(R.BH * W / H / zoom); ch = int(R.BH / zoom)
    x0 = (R.BW - cw) // 2; y0 = (R.BH - ch) // 2
    im = f.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR).convert("RGBA")
    im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 110)))
    return im

def T(text, size, fill=WHITE, glow=None, stroke=0):
    return R.text_img(text, R.F_BLACK, size, fill=fill, glow=glow, glow_r=16, stroke=stroke, stroke_fill=(0, 0, 0))

def ease(x): return R.ease_out(x)

def draw_scene(cv, k, lt, d, fi):
    if k == "hook":  # Tipo 1: apilado a la izquierda, acumula
        words = [("lo", 86, WHITE), ("encontraron", 86, WHITE), ("en", 86, WHITE), ("GTA 6", 150, RED)]
        y = 620
        for j, (w_, s, c) in enumerate(words):
            tt = lt - j * 0.28
            if tt < 0: break
            im = T(w_, s, c, stroke=(6 if c == RED else 0))
            sc = 1.25 - 0.25 * ease(tt / 0.15)
            R.paste(cv, im, 90 - 40, y, 1.0, sc, anchor="lm")
            y += int(s * 1.3)
    elif k == "bigfoot":  # ráfaga flash (12 x 0.05s) + Tipo 2 remate
        if lt < 0.6:
            j = int(lt / 0.05)
            col = [RED, WHITE, P["a1"], BLACK][j % 4]
            cv.alpha_composite(Image.new("RGBA", (W, H), col + (255,)))
            R.paste(cv, T("BIGFOOT", 185, BLACK if col == WHITE else WHITE), W // 2, H // 2 + (j % 3 - 1) * 40, 1.0, 1.0 + 0.1 * (j % 2))
        else:
            tt = lt - 0.6
            R.paste(cv, T("nada menos que", 78), W // 2, 760, 1.0)
            R.paste(cv, T("BIGFOOT", 185, WHITE, glow=RED, stroke=6), W // 2, 960, 1.0, 1.35 - 0.35 * ease(tt / 0.18))
            # huella
            fp = Image.new("RGBA", (260, 340), (0, 0, 0, 0)); fd = ImageDraw.Draw(fp)
            fd.ellipse((40, 110, 220, 330), fill=(255, 255, 255, 235))
            for n, (x, y_) in enumerate([(30, 70), (85, 30), (145, 22), (200, 45), (235, 95)]):
                fd.ellipse((x - 26, y_ - 26, x + 26, y_ + 26), fill=(255, 255, 255, 235))
            R.paste(cv, fp.rotate(-15, expand=True), W // 2, 1320, ease(tt / 0.3))
    elif k == "mapa":
        mb = R.map_base(P["a2"], P["a1"])
        im = mb.copy(); md = ImageDraw.Draw(im)
        rx, ry = 660 * 0.95, 730 * 0.95
        pr = 20 + (lt * 70) % 70
        md.ellipse((rx - pr, ry - pr, rx + pr, ry + pr), outline=RED + (int(255 * (1 - ((lt * 70) % 70) / 70)),), width=6)
        md.ellipse((rx - 18, ry - 18, rx + 18, ry + 18), fill=RED + (255,), outline=(0, 0, 0, 255), width=4)
        R.paste(cv, im, W // 2 + 60, 1040, 1.0, 0.95 + 0.05 * ease(lt / d))
        R.paste(cv, T("visto en los", 76), W // 2, 360, 1.0)
        R.paste(cv, T("PANTANOS", 170, WHITE, glow=P["a1"], stroke=5), W // 2, 500, 1.0, 1.25 - 0.25 * ease(lt / 0.18))
        R.paste(cv, T("de Leonida", 76, P["a1"]), W // 2, 640, ease(lt / 0.3))
    elif k == "interludio":  # Tipo 3: fondo de color, texto invertido
        sat = lt > d * 0.55
        cv.alpha_composite(Image.new("RGBA", (W, H), (RED if sat else PINK) + (255,)))
        if not sat:
            R.paste(cv, T("¿es el único", 90, BLACK), W // 2, 820, 1.0)
            R.paste(cv, T("SECRETO?", 190, BLACK), W // 2, 990, 1.0, 1.2 - 0.2 * ease(lt / 0.15))
        else:
            R.paste(cv, T("PARA NADA", 190, WHITE), W // 2, 940, 1.0, 1.2 - 0.2 * ease((lt - d * 0.55) / 0.15))
    elif k == "cangrejo":
        R.paste(cv, T("también hay un", 80), W // 2, 700, 1.0)
        R.paste(cv, T("CANGREJO", 190, WHITE, glow=RED, stroke=5), W // 2, 880, 1.0, 1.3 - 0.3 * ease(lt / 0.18))
        R.paste(cv, T("GIGANTE", 190, RED, stroke=5), W // 2, 1080, ease((lt - 0.25) / 0.2), 1.3 - 0.3 * ease((lt - 0.25) / 0.18))
        # pinzas
        cr = Image.new("RGBA", (420, 220), (0, 0, 0, 0)); cd = ImageDraw.Draw(cr)
        for sx in (0, 1):
            x = 60 + sx * 300
            cd.pieslice((x - 60, 20, x + 60, 140), 200 if sx == 0 else -20, 340 if sx == 0 else 160, fill=RED + (255,))
        cd.ellipse((110, 110, 310, 210), fill=RED + (255,))
        ang = 8 * math.sin(lt * 14)
        R.paste(cv, cr.rotate(ang, expand=True), W // 2, 1380, ease((lt - 0.4) / 0.3))
    elif k == "antena":  # troceo: golpes de zoom cada vez más rápidos
        beats = [0, 0.9, 1.7, 2.38, 2.78, 3.1, 3.35, 3.55]
        last = max(b for b in beats if b <= lt)
        punch = 1.18 - 0.18 * ease((lt - last) / 0.12)
        # torre
        tw = Image.new("RGBA", (360, 900), (0, 0, 0, 0)); td = ImageDraw.Draw(tw)
        td.polygon([(180, 40), (60, 880), (300, 880)], outline=P["a2"] + (255,), width=8)
        for yy in range(120, 880, 90):
            hw = 120 * (yy - 40) / 840
            td.line((180 - hw, yy, 180 + hw, yy), fill=P["a2"] + (255,), width=5)
            td.line((180 - hw, yy, 180 + hw * 0.9, yy + 90), fill=P["a2"] + (150,), width=3)
        td.ellipse((140, 0, 220, 60), fill=RED + (255,))
        for n in range(3):
            td.ellipse((150 + n * 22, 14, 172 + n * 22, 46), fill=[(255, 220, 80, 255), (120, 220, 255, 255), (255, 140, 200, 255)][n])
        R.paste(cv, tw, W // 2 + 230, 1180, 1.0, punch * 0.9)
        R.paste(cv, T("un nido con", 80), 70, 520, 1.0, 1.0, anchor="lm")
        R.paste(cv, T("HUEVOS", 180, WHITE, glow=RED, stroke=5), 50, 690, 1.0, punch, anchor="lm")
        R.paste(cv, T("en la torre", 80), 70, 860, 1.0, 1.0, anchor="lm")
        R.paste(cv, T("más alta", 80, P["a1"]), 70, 950, 1.0, 1.0, anchor="lm")
        if lt > 3.0:
            R.paste(cv, T("7 MIN", 150, RED, stroke=5), 60, 1180, 1.0, punch, anchor="lm")
            R.paste(cv, T("de escalada", 70), 70, 1300, 1.0, 1.0, anchor="lm")
    elif k == "cta":
        av = Image.open(os.path.join(ROOT, "canal", "avatar_800x800.jpg")).convert("RGBA").resize((360, 360))
        mk = Image.new("L", (360, 360), 0); ImageDraw.Draw(mk).ellipse((0, 0, 359, 359), fill=255)
        ring = Image.new("RGBA", (384, 384), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse((0, 0, 383, 383), fill=P["a1"] + (255,))
        e = ease(lt / 0.3)
        cv.alpha_composite(R.with_alpha(ring, e), (W // 2 - 192, 560 - 192))
        avc = Image.new("RGBA", (360, 360), (0, 0, 0, 0)); avc.paste(av, (0, 0), mk)
        cv.alpha_composite(R.with_alpha(avc, e), (W // 2 - 180, 560 - 180))
        R.paste(cv, T("vídeo completo", 84), W // 2, 880, 1.0)
        R.paste(cv, T("EN EL CANAL", 150, WHITE, glow=RED, stroke=5), W // 2, 1030, 1.0, 1.2 - 0.2 * ease(lt / 0.15))
        R.paste(cv, T("@DonPalmeraGTA", 70, P["a1"]), W // 2, 1180, ease((lt - 0.4) / 0.3))
        btn = R.rrect((520, 130), 65, (230, 20, 30, 255))
        sc = 0.92 if abs(lt - 2.2) < 0.12 else 1.0
        R.paste(cv, btn, W // 2, 1400, ease((lt - 0.8) / 0.3), sc)
        R.paste(cv, T("SÍGUEME", 60), W // 2, 1396, ease((lt - 0.8) / 0.3), sc)

# ---------- audio
L = int(TOTAL * SR) + SR
voice = np.zeros(L, np.float32); sfx = np.zeros(L, np.float32)
for i, v in enumerate(voices):
    off = 0.55 if KINDS[i] == "bigfoot" else 0.05
    a = int((starts[i] + off) * SR); voice[a:a + len(v)] += v
    b = int(starts[i] * SR)
    s = impacto() if KINDS[i] in ("bigfoot", "interludio") else whoosh(0.3)
    sfx[b:b + len(s)] += s[:L - b] * (0.45 if KINDS[i] in ("bigfoot", "interludio") else 0.2)
for j in range(4):  # pops del hook
    c = int((starts[0] + j * 0.28) * SR); p = pop(j); sfx[c:c + len(p)] += p * 0.2
for j in range(12):  # ráfaga
    c = int((starts[1] + j * 0.05) * SR); p = pop(j % 3)[:1200]; sfx[c:c + len(p)] += p * 0.15
for bt in [0, 0.9, 1.7, 2.38, 2.78, 3.1, 3.35, 3.55]:
    c = int((starts[5] + bt) * SR); p = impacto()[:2400]; sfx[c:c + len(p)] += p * 0.25
voice = voice / (np.max(np.abs(voice)) + 1e-9) * 0.9
mus = generar(TOTAL + 1, 3)[:L]; mus = np.pad(mus, (0, max(0, L - len(mus))))
env = np.convolve(np.abs(voice), np.ones(4000) / 4000, mode="same")
gain = 0.34 - 0.2 * np.clip(env * 30, 0, 1)
mix = voice + mus * gain + sfx
mix /= max(1.0, np.max(np.abs(mix)) / 0.97)
wav = os.path.join(OUT, "_a.wav"); sf.write(wav, mix[:int(TOTAL * SR)], SR)

# ---------- subtítulos inferiores (palabra a palabra)
TEXTS = ["Lo encontraron en GTA 6.", "Nada menos que... Bigfoot.", "Varios jugadores lo han visto en los pantanos de Leonida.",
         "¿Y es el único secreto? Para nada.", "También hay un cangrejo gigante...",
         "y un nido con huevos pintados en lo alto de la torre de radio más alta. Siete minutos de escalada.",
         "Te lo cuento todo en el vídeo completo. Sígueme para más secretos."]
subs = []
for i, txt in enumerate(TEXTS):
    off = 0.55 if KINDS[i] == "bigfoot" else 0.05
    chunks = R.split_chunks(txt, 3)
    wt = R.word_times(chunks, starts[i] + off, len(voices[i]) / SR)
    k = 0
    for c in chunks:
        ts = wt[k:k + len(c)]; subs.append((ts[0][0], ts[-1][1], c, ts)); k += len(c)

cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", os.path.join(OUT, "short.mp4")]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
brand = R.text_img("DON PALMERA", R.F_BI, 40, fill=WHITE, glow=P["a1"], glow_r=8)
si = 0; sub_i = 0
for fi in range(N):
    tt = fi / FPS
    while si < len(starts) - 1 and tt >= starts[si + 1]: si += 1
    lt = tt - starts[si]
    cv = background(fi, 1.0 + 0.05 * lt / durs[si])
    draw_scene(cv, KINDS[si], lt, durs[si], fi)
    cv.alpha_composite(brand, (W - brand.width - 20, 90))
    pw = int(W * tt / TOTAL); cv.alpha_composite(Image.new("RGBA", (max(1, pw), 8), RED + (255,)), (0, 0))
    while sub_i < len(subs) and tt > subs[sub_i][1] + 0.1: sub_i += 1
    if sub_i < len(subs) and subs[sub_i][0] - 0.05 <= tt and KINDS[si] not in ("interludio",):
        a, b, c, ts = subs[sub_i]
        hi = max([j for j, (wa, wb) in enumerate(ts) if tt >= wa] or [0])
        R.paste(cv, R.subtitle_img(tuple(c), hi, R.MID), W // 2, 1620, 1.0, 1.15)
    proc.stdin.write(cv.convert("RGB").tobytes())
proc.stdin.close(); proc.wait(); os.remove(wav)
print("ok", round(TOTAL, 1), "s")
