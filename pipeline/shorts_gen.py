# -*- coding: utf-8 -*-
"""Generador de Shorts verticales (1080x1920) con el estilo clips-virales.
Uso: python3 shorts_gen.py [slug ...]"""
import os, sys, math, subprocess
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import render as R
from musica import generar, whoosh, pop, impacto

W, H, FPS, SR = 1080, 1920, 30, 24000
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RED = (255, 45, 60); WHITE = (255, 255, 255); BLACK = (10, 10, 14); PINK = (255, 150, 200); YEL = (255, 214, 60)

# Cada escena: (tipo, datos, voz, subtítulo)
SHORTS = {
"02-huevos-torre": dict(pal="sunset", seed=11, scenes=[
  ("hook", dict(words=[("subí", 0), ("7 minutos", 0), ("para", 0), ("ESTO", 1)]),
   "Subí siete minutos a la torre más alta de ge te a seis... para esto.", "Subí 7 minutos a la torre más alta de GTA 6... para esto."),
  ("flash", dict(burst="HUEVOS", setup="un nido con", impact="HUEVOS", prop="eggs"),
   "Un nido con huevos de Pascua. De verdad.", "Un nido con huevos de Pascua. De verdad."),
  ("card", dict(setup="en la torre de radio", impact="MÁS ALTA", sub="de Leonida", prop="tower", punch=True),
   "Están arriba del todo de la torre de radio más alta de Leonida. Unos siete minutos de subida.", "Arriba del todo de la torre de radio más alta de Leonida. Unos 7 minutos de subida."),
  ("inter", dict(q1="¿y si tiras", q2="UNO?", a="SORPRESA"),
   "¿Y si tiras uno?", "¿Y si tiras uno?"),
  ("card", dict(setup="cae encima de un", impact="CONDUCTOR", sub="y salta una escena secreta", prop="egg_fall"),
   "Sale volando, cae encima de un conductor... y salta una escena secreta.", "Sale volando, cae encima de un conductor... y salta una escena secreta."),
  ("cta", dict(q="¿ya subiste?"),
   "¿Tú ya subiste? Sígueme para más secretos.", "¿Tú ya subiste? Sígueme para más secretos."),
]),
"03-cangrejo-gigante": dict(pal="ocean", seed=12, scenes=[
  ("hook", dict(words=[("hay", 0), ("un", 0), ("MONSTRUO", 1), ("en GTA 6", 0)]),
   "Hay un monstruo en ge te a seis.", "Hay un monstruo en GTA 6."),
  ("flash", dict(burst="CANGREJO", setup="un cangrejo", impact="GIGANTE", prop="crab"),
   "Un cangrejo gigante.", "Un cangrejo gigante."),
  ("card", dict(setup="lo han encontrado", impact="JUGADORES", sub="en los primeros días", prop="crab"),
   "Varios jugadores lo han encontrado en los primeros días de juego.", "Varios jugadores lo han encontrado en los primeros días de juego."),
  ("inter", dict(q1="¿dónde", q2="ESTÁ?", a="A BUSCARLO"),
   "¿Dónde está exactamente? Eso es lo que todos están buscando.", "¿Dónde está exactamente? Eso es lo que todos están buscando."),
  ("card", dict(setup="y no está solo:", impact="BIGFOOT", sub="también vive en Leonida", prop="foot"),
   "Y no está solo. En Leonida también se ha visto a Bigfut.", "Y no está solo. En Leonida también se ha visto a Bigfoot."),
  ("cta", dict(q="¿lo has visto?"),
   "¿Tú lo has visto? Cuéntamelo en comentarios.", "¿Tú lo has visto? Cuéntamelo en comentarios."),
]),
"04-rescate-conductor": dict(pal="cyber", seed=13, scenes=[
  ("hook", dict(words=[("GTA 6", 0), ("premia", 0), ("ser", 0), ("BUENA PERSONA", 1)]),
   "Ge te a seis premia ser buena persona.", "GTA 6 premia ser buena persona."),
  ("flash", dict(burst="CRASH", setup="un choque", impact="BRUTAL", prop="crash"),
   "Un coche choca contra un camión al lado de Yeison.", "Un coche choca contra un camión al lado de Jason."),
  ("card", dict(setup="el conductor queda", impact="ATRAPADO", sub=None, prop="crash", punch=True),
   "El otro conductor se queda atrapado.", "El otro conductor se queda atrapado."),
  ("inter", dict(q1="¿lo", q2="AYUDAS?", a="SÍ"),
   "¿Y si lo ayudas?", "¿Y si lo ayudas?"),
  ("card", dict(setup="te da las", impact="GRACIAS", sub="como en la vida real", prop="heart"),
   "Lo sacas del coche... y te da las gracias.", "Lo sacas del coche... y te da las gracias."),
  ("card", dict(setup="el camión es de", impact="SAHARA", sub="la parodia de Amazon", prop="truck"),
   "Y fíjate en el camión: es de Sahara, la parodia de Amazon de Rockstar.", "Y fíjate en el camión: es de Sahara, la parodia de Amazon de Rockstar."),
  ("cta", dict(q="¿ayudas o huyes?"),
   "¿Tú ayudas o sales corriendo? Sígueme.", "¿Tú ayudas o sales corriendo? Sígueme."),
]),
}

def T(text, size, fill=WHITE, glow=None, stroke=0):
    return R.text_img(text, R.F_BLACK, size, fill=fill, glow=glow, glow_r=16, stroke=stroke, stroke_fill=(0, 0, 0))

def fit(im, maxw=1000):
    if im.width > maxw: im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    return im

def e(x): return R.ease_out(x)

def prop_img(name, t, P):
    im = Image.new("RGBA", (520, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if name == "eggs":
        d.chord((60, 300, 460, 500), 0, 180, fill=(110, 70, 30, 255))
        for n, c in enumerate([(255, 220, 80), (120, 220, 255), (255, 140, 200), (140, 255, 140)]):
            x = 120 + n * 85; y = 250 + (n % 2) * 20 - int(6 * math.sin(t * 6 + n))
            d.ellipse((x, y, x + 80, y + 105), fill=c + (255,), outline=(0, 0, 0, 255), width=4)
            d.line((x + 10, y + 50, x + 70, y + 50), fill=(255, 255, 255, 200), width=6)
    elif name == "tower":
        d.polygon([(260, 20), (150, 510), (370, 510)], outline=P["a2"] + (255,), width=8)
        for yy in range(80, 510, 60):
            hw = 110 * (yy - 20) / 490
            d.line((260 - hw, yy, 260 + hw, yy), fill=P["a2"] + (255,), width=5)
        d.ellipse((235, 0, 285, 40), fill=RED + (255,))
    elif name == "egg_fall":
        y = 60 + (t * 500) % 260
        d.ellipse((220, y, 300, y + 100), fill=(255, 140, 200, 255), outline=(0, 0, 0, 255), width=4)
        d.rounded_rectangle((90, 380, 430, 480), 30, fill=P["a2"] + (255,))
        d.rounded_rectangle((160, 320, 360, 400), 25, fill=P["a2"] + (255,))
        for x in (150, 370): d.ellipse((x - 40, 450, x + 40, 520), fill=(10, 10, 10, 255))
    elif name == "crab":
        ang = 10 * math.sin(t * 12)
        for sx in (-1, 1):
            cx = 260 + sx * 170
            d.pieslice((cx - 90, 80, cx + 90, 260), 200 if sx < 0 else -20, 340 if sx < 0 else 160, fill=RED + (255,))
            d.line((260 + sx * 90, 330, cx, 240), fill=RED + (255,), width=26)
        d.ellipse((110, 280, 410, 460), fill=RED + (255,), outline=(0, 0, 0, 255), width=5)
        for sx in (-1, 1):
            d.ellipse((260 + sx * 55 - 22, 300, 260 + sx * 55 + 22, 344), fill=WHITE + (255,))
            d.ellipse((260 + sx * 55 - 9, 314, 260 + sx * 55 + 9, 332), fill=BLACK + (255,))
        for k in range(3):
            for sx in (-1, 1):
                d.line((260 + sx * 120, 400 + k * 20, 260 + sx * 220, 470 + k * 15), fill=RED + (255,), width=12)
        im = im.rotate(ang, resample=Image.BILINEAR)
    elif name == "foot":
        d.ellipse((150, 200, 370, 480), fill=WHITE + (235,))
        for x, y in [(140, 160), (205, 115), (275, 105), (340, 130), (385, 185)]:
            d.ellipse((x - 32, y - 32, x + 32, y + 32), fill=WHITE + (235,))
    elif name == "crash":
        sh = int(8 * math.sin(t * 40)) if t < 0.5 else 0
        d.rounded_rectangle((20 + sh, 300, 260 + sh, 420), 30, fill=P["a2"] + (255,))
        d.rectangle((280, 200, 500, 420), fill=(230, 230, 235, 255))
        for x in (80, 210, 330, 450): d.ellipse((x - 35 + (sh if x < 260 else 0), 400, x + 35 + (sh if x < 260 else 0), 470), fill=BLACK + (255,))
        for k in range(8):
            a = k * math.pi / 4; d.line((270, 330, 270 + 70 * math.cos(a), 330 + 70 * math.sin(a)), fill=YEL + (255,), width=10)
    elif name == "heart":
        s = 1 + 0.08 * math.sin(t * 8)
        r = int(110 * s)
        d.ellipse((260 - 2 * r + 20, 200 - r, 260 + 20, 200 + r), fill=RED + (255,))
        d.ellipse((260 - 20, 200 - r, 260 + 2 * r - 20, 200 + r), fill=RED + (255,))
        d.polygon([(260 - 2 * r + 25, 230), (260 + 2 * r - 25, 230), (260, 230 + int(2.1 * r))], fill=RED + (255,))
    elif name == "truck":
        d.rectangle((30, 160, 360, 420), fill=(245, 245, 245, 255), outline=(0, 0, 0, 255), width=5)
        d.rectangle((360, 260, 490, 420), fill=P["a2"] + (255,), outline=(0, 0, 0, 255), width=5)
        tx = R.text_img("sahara", R.F_BI, 70, fill=(240, 140, 30), shadow=False)
        im.alpha_composite(tx, (195 - tx.width // 2, 270 - tx.height // 2))
        d.arc((110, 320, 280, 380), 20, 160, fill=(240, 140, 30, 255), width=10)
        for x in (100, 300, 430): d.ellipse((x - 40, 390, x + 40, 470), fill=BLACK + (255,))
    return im

class Short:
    def __init__(self, slug, spec):
        self.slug, self.spec = slug, spec
        self.P = R.PALETTES[spec["pal"]]
        self.out = os.path.join(ROOT, "shorts", slug); os.makedirs(self.out, exist_ok=True)
        self.bg = R.Background(spec["pal"], spec["seed"])

    def tts(self):
        from kokoro_onnx import Kokoro
        k = Kokoro("/opt/tts/kokoro-v1.0.onnx", "/opt/tts/voices-v1.0.bin")
        self.voices = []
        for _, _, v, _ in self.spec["scenes"]:
            a, _ = k.create(v, voice="em_alex", speed=1.15, lang="es")
            nz = np.where(np.abs(a) > 0.01)[0]; self.voices.append(a[max(0, nz[0] - 400):nz[-1] + 800].astype(np.float32))

    def background(self, fi, zoom):
        f = self.bg.frames[fi % len(self.bg.frames)]
        cw = int(R.BH * W / H / zoom); ch = int(R.BH / zoom)
        x0 = (R.BW - cw) // 2; y0 = (R.BH - ch) // 2
        im = f.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR).convert("RGBA")
        im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 115)))
        return im

    def draw(self, cv, k, d, lt, D):
        P = self.P
        if k == "hook":
            y = 600
            for j, (w_, imp) in enumerate(d["words"]):
                tt = lt - j * 0.28
                if tt < 0: break
                im = fit(T(w_.upper() if imp else w_, 150 if imp else 88, RED if imp else WHITE, stroke=6 if imp else 0), 960)
                R.paste(cv, im, 50, y, 1.0, 1.25 - 0.25 * e(tt / 0.15), anchor="lm")
                y += int((150 if imp else 88) * 1.3)
        elif k == "flash":
            if lt < 0.6:
                j = int(lt / 0.05); col = [RED, WHITE, P["a1"], BLACK][j % 4]
                cv.alpha_composite(Image.new("RGBA", (W, H), col + (255,)))
                R.paste(cv, fit(T(d["burst"], 180, BLACK if col == WHITE else WHITE)), W // 2, H // 2 + (j % 3 - 1) * 40, 1.0, 1.0 + 0.1 * (j % 2))
            else:
                tt = lt - 0.6
                R.paste(cv, T(d["setup"], 80), W // 2, 680, 1.0)
                R.paste(cv, fit(T(d["impact"], 185, WHITE, glow=RED, stroke=6)), W // 2, 870, 1.0, 1.35 - 0.35 * e(tt / 0.18))
                R.paste(cv, prop_img(d["prop"], lt, P), W // 2, 1250, e(tt / 0.3), 0.9)
        elif k == "card":
            sc = 1.0
            if d.get("punch"):
                beats = [b for b in [0, 0.9, 1.7, 2.38, 2.78, 3.1, 3.35, 3.55] if b < D]
                last = max(b for b in beats if b <= lt); sc = 1.18 - 0.18 * e((lt - last) / 0.12)
            R.paste(cv, T(d["setup"], 80), W // 2, 600, 1.0)
            R.paste(cv, fit(T(d["impact"], 175, WHITE, glow=RED, stroke=6)), W // 2, 780, 1.0, (1.3 - 0.3 * e(lt / 0.18)) * sc)
            if d.get("sub"): R.paste(cv, fit(T(d["sub"], 70, YEL, stroke=4)), W // 2, 920, e((lt - 0.3) / 0.3))
            R.paste(cv, prop_img(d["prop"], lt, P), W // 2, 1260, e((lt - 0.2) / 0.3), 0.85 * sc)
        elif k == "inter":
            sat = lt > D * 0.6
            cv.alpha_composite(Image.new("RGBA", (W, H), (RED if sat else PINK) + (255,)))
            if not sat:
                R.paste(cv, T(d["q1"], 95, BLACK), W // 2, 820, 1.0)
                R.paste(cv, fit(T(d["q2"], 190, BLACK)), W // 2, 990, 1.0, 1.2 - 0.2 * e(lt / 0.15))
            else:
                R.paste(cv, fit(T(d["a"], 190, WHITE)), W // 2, 940, 1.0, 1.2 - 0.2 * e((lt - D * 0.6) / 0.15))
        elif k == "cta":
            av = Image.open(os.path.join(ROOT, "canal", "avatar_800x800.jpg")).convert("RGBA").resize((340, 340))
            mk = Image.new("L", (340, 340), 0); ImageDraw.Draw(mk).ellipse((0, 0, 339, 339), fill=255)
            a = e(lt / 0.3)
            ring = Image.new("RGBA", (364, 364), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse((0, 0, 363, 363), fill=P["a1"] + (255,))
            cv.alpha_composite(R.with_alpha(ring, a), (W // 2 - 182, 540 - 182))
            avc = Image.new("RGBA", (340, 340), (0, 0, 0, 0)); avc.paste(av, (0, 0), mk)
            cv.alpha_composite(R.with_alpha(avc, a), (W // 2 - 170, 540 - 170))
            R.paste(cv, fit(T(d["q"].upper(), 140, WHITE, glow=RED, stroke=5)), W // 2, 880, 1.0, 1.2 - 0.2 * e(lt / 0.15))
            R.paste(cv, T("comenta 👇".replace(" 👇", ""), 80, YEL), W // 2, 1030, e((lt - 0.3) / 0.3))
            R.paste(cv, T("@DonPalmeraGTA", 66, P["a1"]), W // 2, 1150, e((lt - 0.5) / 0.3))
            R.paste(cv, R.rrect((520, 130), 65, (230, 20, 30, 255)), W // 2, 1380, e((lt - 0.8) / 0.3))
            R.paste(cv, T("SÍGUEME", 60), W // 2, 1376, e((lt - 0.8) / 0.3))

    def render(self):
        self.tts()
        sc = self.spec["scenes"]
        starts, durs = [], []; t = 0.0
        offs = []
        for (k, d, _, _), v in zip(sc, self.voices):
            off = 0.6 if k == "flash" else 0.05
            dur = off + len(v) / SR + 0.18 + (1.2 if k == "cta" else 0)
            starts.append(t); durs.append(dur); offs.append(off); t += dur
        TOTAL = t; N = int(TOTAL * FPS); L = int(TOTAL * SR) + SR
        voice = np.zeros(L, np.float32); sfx = np.zeros(L, np.float32)
        for i, ((k, d, _, _), v) in enumerate(zip(sc, self.voices)):
            a = int((starts[i] + offs[i]) * SR); voice[a:a + len(v)] += v
            b = int(starts[i] * SR); s = impacto() if k in ("flash", "inter") else whoosh(0.3)
            sfx[b:b + len(s)] += s[:L - b] * (0.45 if k in ("flash", "inter") else 0.2)
            if k == "hook":
                for j in range(len(d["words"])):
                    c = int((starts[i] + j * 0.28) * SR); p = pop(j); sfx[c:c + len(p)] += p * 0.2
            if k == "flash":
                for j in range(12):
                    c = int((starts[i] + j * 0.05) * SR); p = pop(j % 3)[:1200]; sfx[c:c + len(p)] += p * 0.15
            if k == "card" and d.get("punch"):
                for bt in [0, 0.9, 1.7, 2.38, 2.78, 3.1, 3.35, 3.55]:
                    if bt < durs[i]:
                        c = int((starts[i] + bt) * SR); p = impacto()[:2400]; sfx[c:c + len(p)] += p * 0.25
        voice = voice / (np.max(np.abs(voice)) + 1e-9) * 0.9
        mus = generar(TOTAL + 1, self.spec["seed"])[:L]; mus = np.pad(mus, (0, max(0, L - len(mus))))
        env = np.convolve(np.abs(voice), np.ones(4000) / 4000, mode="same")
        mix = voice + mus * (0.34 - 0.2 * np.clip(env * 30, 0, 1)) + sfx
        mix /= max(1.0, np.max(np.abs(mix)) / 0.97)
        wav = os.path.join(self.out, "_a.wav"); sf.write(wav, mix[:int(TOTAL * SR)], SR)
        subs = []
        for i, (k, d, _, st) in enumerate(sc):
            chunks = R.split_chunks(st, 3)
            wt = R.word_times(chunks, starts[i] + offs[i], len(self.voices[i]) / SR); j = 0
            for c in chunks:
                ts = wt[j:j + len(c)]; subs.append((ts[0][0], ts[-1][1], c, ts)); j += len(c)
        with open(os.path.join(self.out, "subtitulos.srt"), "w") as fh:
            for n, (a, b, c, _) in enumerate(subs, 1):
                fh.write(f"{n}\n{R.srt_time(a)} --> {R.srt_time(b)}\n{' '.join(c)}\n\n")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", os.path.join(self.out, "short.mp4")]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        brand = R.text_img("DON PALMERA", R.F_BI, 40, fill=WHITE, glow=self.P["a1"], glow_r=8)
        si = 0; sub_i = 0
        for fi in range(N):
            tt = fi / FPS
            while si < len(starts) - 1 and tt >= starts[si + 1]: si += 1
            lt = tt - starts[si]; k, d, _, _ = sc[si]
            cv = self.background(fi, 1.0 + 0.05 * lt / durs[si])
            self.draw(cv, k, d, lt, durs[si])
            cv.alpha_composite(brand, (W - brand.width - 20, 90))
            cv.alpha_composite(Image.new("RGBA", (max(1, int(W * tt / TOTAL)), 8), RED + (255,)), (0, 0))
            while sub_i < len(subs) and tt > subs[sub_i][1] + 0.1: sub_i += 1
            if sub_i < len(subs) and subs[sub_i][0] - 0.05 <= tt and k != "inter":
                a, b, c, ts = subs[sub_i]
                hi = max([j for j, (wa, wb) in enumerate(ts) if tt >= wa] or [0])
                R.paste(cv, R.subtitle_img(tuple(c), hi, R.MID), W // 2, 1640, 1.0, 1.15)
            proc.stdin.write(cv.convert("RGB").tobytes())
        proc.stdin.close(); proc.wait(); os.remove(wav)
        print("ok", self.slug, round(TOTAL, 1), "s", flush=True)

if __name__ == "__main__":
    for slug in (sys.argv[1:] or list(SHORTS)):
        Short(slug, SHORTS[slug]).render()
