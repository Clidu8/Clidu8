# -*- coding: utf-8 -*-
"""Clip vertical 9:16 de stream: facecam arriba, gameplay abajo, overlay de la campaña,
subtítulos palabra a palabra, gancho y golpes de zoom. Config en un JSON."""
import os, sys, json, subprocess, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import render as R

W, H, FPS = 1080, 1920, 30
cfg = json.load(open(sys.argv[1]))
D = cfg["dir"]
SRC = os.path.join(D, cfg["src"])
OUT = cfg["out"]

# 1) recortar y unir los tramos (cortes secos)
segs = cfg["segments"]
parts = []
for i, (a, b) in enumerate(segs):
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps={FPS}[v{i}];[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}]")
fc = ";".join(parts) + ";" + "".join(f"[v{i}][a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[v][a]"
cut = os.path.join(D, "_cut.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "aac", "-b:a", "192k", cut], check=True)

def src_to_out(t):
    acc = 0.0
    for a, b in segs:
        if a <= t <= b: return acc + (t - a)
        acc += b - a
    return None
TOTAL = sum(b - a for a, b in segs)
N = int(TOTAL * FPS)

# 2) subtítulos con tiempos de salida
subs = []
for s in cfg["subs"]:
    a, b = src_to_out(s[0]), src_to_out(s[1])
    if a is None or b is None: continue
    chunks = R.split_chunks(s[2], 3)
    wt = R.word_times(chunks, a, b - a); k = 0
    for c in chunks:
        ts = wt[k:k + len(c)]; subs.append((ts[0][0], ts[-1][1], c, ts)); k += len(c)
with open(os.path.join(os.path.dirname(OUT), "subtitles.srt"), "w") as fh:
    for n, (a, b, c, _) in enumerate(subs, 1):
        fh.write(f"{n}\n{R.srt_time(a)} --> {R.srt_time(b)}\n{' '.join(c)}\n\n")

punches = [src_to_out(t) for t in cfg.get("punches", [])]
texts = [(src_to_out(t0) if t0 > 0 else 0.0, src_to_out(t1), lines) for t0, t1, lines in cfg.get("texts", [])]

cam = cfg["cam"]; game = cfg["game"]; CAM_H = cfg.get("cam_h", 705)
overlay = Image.open(os.path.join(D, cfg["overlay"])).convert("RGBA")
bb = overlay.getbbox(); ov = overlay.crop(bb)
ow = 600; ov = ov.resize((ow, int(ov.height * ow / ov.width)), Image.LANCZOS)
# quitar fondo blanco del PNG si lo tiene
# fondo blanco exterior -> transparente (relleno desde las esquinas, sin tocar el texto blanco)
_m = Image.new("L", ov.size, 0); _rgb = ov.convert("RGB")
for corner in [(0, 0), (ov.width - 1, 0), (0, ov.height - 1), (ov.width - 1, ov.height - 1)]:
    ImageDraw.floodfill(_rgb, corner, (255, 0, 255), thresh=40)
_a = np.array(_rgb); _bg = (_a[..., 0] == 255) & (_a[..., 1] == 0) & (_a[..., 2] == 255)
arr = np.array(ov); arr[_bg, 3] = 0; ov = Image.fromarray(arr)

def T(text, size, fill=(255, 255, 255), stroke=7):
    return R.text_img(text, R.F_BLACK, size, fill=fill, stroke=stroke, stroke_fill=(0, 0, 0), shadow=True)

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", cut, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", cut, "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-14:TP=-1.5", "-c:v", "libx264", "-preset", "medium",
                        "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT],
                       stdin=subprocess.PIPE)
fsz = 1920 * 1080 * 3
sub_i = 0
for fi in range(N):
    raw = dec.stdout.read(fsz)
    if len(raw) < fsz: break
    t = fi / FPS
    src = Image.frombytes("RGB", (1920, 1080), raw)
    # golpe de zoom
    z = 1.0
    for p in punches:
        if p is not None and 0 <= t - p < 0.35: z = 1.0 + 0.14 * (1 - (t - p) / 0.35)
    cx0, cy0, cx1, cy1 = cam
    cw, ch = (cx1 - cx0) / z, (cy1 - cy0) / z; mx, my = (cx0 + cx1) / 2, (cy0 + cy1) / 2
    camim = src.crop((int(mx - cw / 2), int(my - ch / 2), int(mx + cw / 2), int(my + ch / 2))).resize((W, CAM_H), Image.LANCZOS)
    gx0, gy0, gx1, gy1 = game
    gameim = src.crop((gx0, gy0, gx1, gy1)).resize((W, H - CAM_H), Image.LANCZOS)
    cv = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    cv.paste(camim, (0, 0)); cv.paste(gameim, (0, CAM_H))
    d = ImageDraw.Draw(cv); d.rectangle((0, CAM_H - 3, W, CAM_H + 3), fill=(0, 0, 0, 255))
    # overlay de la campaña, siempre visible, en la unión
    cv.alpha_composite(ov, ((W - ov.width) // 2, CAM_H - ov.height // 2))
    # textos (gancho y remates)
    for t0, t1, lines in texts:
        if t0 is not None and t1 is not None and t0 <= t < t1:
            lt = t - t0; y = lines[0][2]
            for (txt, size, yy, color) in lines:
                im = T(txt, size, tuple(color))
                if im.width > W - 40: im = im.resize((W - 40, int(im.height * (W - 40) / im.width)), Image.LANCZOS)
                sc = 1.25 - 0.25 * R.ease_out(lt / 0.15)
                R.paste(cv, im, W // 2, yy, 1.0, sc)
    # subtítulos
    while sub_i < len(subs) and t > subs[sub_i][1] + 0.12: sub_i += 1
    if sub_i < len(subs) and subs[sub_i][0] - 0.05 <= t:
        a, b, c, ts = subs[sub_i]
        hi = max([j for j, (wa, wb) in enumerate(ts) if t >= wa] or [0])
        R.paste(cv, R.subtitle_img(tuple(c), hi, (255, 214, 60)), W // 2, cfg.get("sub_y", 1180), 1.0, 1.35 + 0.08 * max(0, 1 - (t - a) / 0.1))
    enc.stdin.write(cv.convert("RGB").tobytes())
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()
os.remove(cut)
print("ok", OUT, round(TOTAL, 1), "s")
