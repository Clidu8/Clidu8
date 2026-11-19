# -*- coding: utf-8 -*-
"""Uso: python3 build.py [tts|preview N|render N...|all|thumbs|canal]"""
import os, sys, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from guiones import VIDEOS
import render as R
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "videos")
CACHE = os.path.join(ROOT, "pipeline", ".tts_cache")
VOICE = "em_alex"; SPEED = 1.08; SR = 24000

def tts_all(only=None):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro("/opt/tts/kokoro-v1.0.onnx", "/opt/tts/voices-v1.0.bin")
    os.makedirs(CACHE, exist_ok=True)
    for vi, v in enumerate(VIDEOS):
        if only is not None and vi not in only: continue
        for si, (_, _, text) in enumerate(v["scenes"]):
            fn = os.path.join(CACHE, f"{v['slug']}_{si:02}.wav")
            meta = fn + ".txt"
            if os.path.exists(fn) and open(meta).read() == text + VOICE + str(SPEED): continue
            a, sr = k.create(text, voice=VOICE, speed=SPEED, lang="es")
            # recorta silencios de los extremos
            nz = np.where(np.abs(a) > 0.01)[0]
            if len(nz): a = a[max(0, nz[0] - 600):nz[-1] + 1200]
            sf.write(fn, a, sr); open(meta, "w").write(text + VOICE + str(SPEED))
            print("tts", v["slug"], si, round(len(a) / sr, 1), flush=True)

def load_voices(v):
    import soundfile as sf
    return [sf.read(os.path.join(CACHE, f"{v['slug']}_{si:02}.wav"), dtype="float32")[0] for si in range(len(v["scenes"]))]

def preview(vi):
    v = VIDEOS[vi]; P = R.PALETTES[v["palette"]]
    bg = R.Background(v["palette"], vi)
    os.makedirs("/tmp/prev", exist_ok=True)
    for si, (kind, data, text) in enumerate(v["scenes"]):
        s = R.Scene(kind, data, text, P, si, None); s.voice_dur = 8; s.dur = 9
        cv = bg.get(0, 1.02)
        s.draw(cv, 6.0, 0)
        cv.alpha_composite(R.subtitle_img(("ESTO", "ES", "UN", "SUBTÍTULO"), 1, R.MID), (W2 := 1920 // 2 - 400, 930))
        cv.convert("RGB").save(f"/tmp/prev/{vi:02}_{si:02}_{kind}.jpg", quality=80)
    print("ok")

def fmt(t):
    t = int(t); return f"{t // 60}:{t % 60:02}"

def chapter_name(kind, data):
    if kind == "title": return "Intro"
    if kind == "cta": return "Final"
    if kind == "list": return f"{data['n']} · {data['title'].title()}" if data["n"] not in "+−" else data["title"].capitalize()
    if kind == "map": return data["title"].title()
    if kind == "stat": return data["label"].capitalize()
    return data.get("title", kind).capitalize()

def render_one(vi):
    v = VIDEOS[vi]
    outdir = os.path.join(OUT, v["slug"])
    info = R.render_video(v, load_voices(v), SR, outdir, seed=vi)
    # capítulos (mínimo 10 s cada uno)
    ch = []
    for start, kind, data in info["scenes"]:
        if not ch or start - ch[-1][0] >= 10: ch.append((start, chapter_name(kind, data)))
    ch[0] = (0, "Intro")
    json.dump(dict(total=info["total"], chapters=ch), open(os.path.join(outdir, "_info.json"), "w"), ensure_ascii=False, indent=1)
    print("render ok", v["slug"], round(info["total"], 1), flush=True)

# ------------------------------------------------------------------ miniaturas
def thumb(vi):
    v = VIDEOS[vi]; th = v["thumb"]; P = R.PALETTES[v["palette"]]
    acc = dict(cyan=(40, 230, 255), pink=(255, 50, 170), red=(255, 40, 60), green=(110, 255, 90), gold=(255, 200, 30))[th["accent"]]
    bg = R.Background(v["palette"], vi)
    im = bg.get(7, 1.0, dim=False).resize((1280, 720), Image.LANCZOS)
    # oscurecer lado izquierdo para el texto
    sh = np.zeros((720, 1280, 4), np.uint8); sh[..., 3] = np.clip(np.linspace(210, 30, 1280), 0, 255)[None, :].astype(np.uint8)
    im.alpha_composite(Image.fromarray(sh, "RGBA"))
    # etiqueta
    tag = R.text_img(th["tag"], R.F_BLACK, 52, fill=(10, 10, 15), shadow=False)
    pill = R.rrect((tag.width - 30, 84), 18, acc + (255,))
    im.alpha_composite(pill, (40, 40)); im.alpha_composite(tag, (40 - 15 + 0, 40 - (tag.height - 84) // 2))
    # número/palabra gigante
    big = th["big"]; size = 300 if len(big) <= 3 else (220 if len(big) <= 6 else (170 if len(big) <= 8 else 140))
    bi = R.text_img(big, R.F_BLACK, size, fill=(255, 255, 255), glow=acc, glow_r=26, stroke=6, stroke_fill=(0, 0, 0))
    if bi.width > 1240: bi = bi.resize((1240, int(bi.height * 1240 / bi.width)), Image.LANCZOS)
    im.alpha_composite(bi, (max(-20, 20 - 60), 360 - bi.height // 2 + 10))
    # subtítulo
    sm = R.text_img(th["small"], R.F_BLACK, 66, fill=R.MID, stroke=5, stroke_fill=(0, 0, 0))
    if sm.width > 1240: sm = sm.resize((1240, int(sm.height * 1240 / sm.width)), Image.LANCZOS)
    im.alpha_composite(sm, (10, 720 - sm.height - 10))
    # flecha
    ar = Image.new("RGBA", (220, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(ar)
    d.polygon([(10, 80), (130, 80), (130, 20), (210, 110), (130, 200), (130, 140), (10, 140)], fill=(255, 40, 50, 255), outline=(255, 255, 255, 255), width=6)
    # marco
    d = ImageDraw.Draw(im); d.rectangle((0, 0, 1279, 719), outline=acc + (255,), width=10)
    out = os.path.join(OUT, v["slug"], "miniatura.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.convert("RGB").save(out, quality=92)
    print("thumb", out)

# ------------------------------------------------------------------ canal
def canal():
    d = os.path.join(ROOT, "canal"); os.makedirs(d, exist_ok=True)
    P = R.PALETTES["sunset"]
    bg = R.Background("sunset", 42)
    # banner 2560x1440 (zona segura central 1546x423)
    im = bg.get(3, 1.0, dim=False).resize((2560, 1440), Image.LANCZOS)
    t = R.text_img("MODO LEONIDA", R.F_BI, 190, fill=(255, 255, 255), glow=P["a1"], glow_r=30, stroke=5, stroke_fill=(0, 0, 0))
    if t.width > 1500: t = t.resize((1500, int(t.height * 1500 / t.width)), Image.LANCZOS)
    im.alpha_composite(t, (1280 - t.width // 2, 640 - t.height // 2 - 10))
    s = R.text_img("GUÍAS · TRUCOS · SECRETOS DE GTA 6 · CADA DÍA", R.F_BLACK, 52, fill=R.MID, stroke=4, stroke_fill=(0, 0, 0))
    im.alpha_composite(s, (1280 - s.width // 2, 790 - s.height // 2))
    im.convert("RGB").save(os.path.join(d, "banner_2560x1440.jpg"), quality=92)
    # avatar 800x800
    av = bg.get(5, 1.6, dim=False).crop((560, 140, 1360, 940)).convert("RGBA")
    dk = Image.new("RGBA", av.size, (0, 0, 0, 90)); av.alpha_composite(dk)
    t = R.text_img("ML", R.F_BI, 400, fill=(255, 255, 255), glow=P["a1"], glow_r=30, stroke=8, stroke_fill=(0, 0, 0))
    av.alpha_composite(t, (400 - t.width // 2, 400 - t.height // 2))
    av.convert("RGB").save(os.path.join(d, "avatar_800x800.jpg"), quality=92)
    # marca de agua 150x150
    wm = Image.new("RGBA", (150, 150), (0, 0, 0, 0)); wd = ImageDraw.Draw(wm)
    wd.ellipse((4, 4, 146, 146), fill=(230, 20, 30, 255), outline=(255, 255, 255, 255), width=5)
    t = R.text_img("ML", R.F_BI, 70, fill=(255, 255, 255), shadow=False)
    wm.alpha_composite(t, (75 - t.width // 2, 72 - t.height // 2))
    wm.save(os.path.join(d, "marca_agua_150x150.png"))
    print("canal ok")

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "tts": tts_all()
    elif cmd == "preview": preview(int(sys.argv[2]))
    elif cmd == "render":
        for x in sys.argv[2:]: render_one(int(x))
    elif cmd == "thumbs":
        for i in range(len(VIDEOS)): thumb(i)
    elif cmd == "canal": canal()
