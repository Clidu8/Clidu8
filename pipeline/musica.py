# -*- coding: utf-8 -*-
"""Música synthwave original generada por código (sin derechos de terceros)."""
import numpy as np
from scipy.signal import lfilter, butter

SR = 24000

def _lp(x, fc, order=2):
    b, a = butter(order, min(fc / (SR / 2), 0.99), "low")
    return lfilter(b, a, x)

def _hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), "high")
    return lfilter(b, a, x)

def _saw(f, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f + phase) % 1.0) - 1

def _sq(f, n):
    t = np.arange(n) / SR
    return np.sign(np.sin(2 * np.pi * f * t))

def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)

PROGS = [
    [(57, "m"), (53, "M"), (48, "M"), (55, "M")],   # Am F C G
    [(50, "m"), (58, "M"), (53, "M"), (48, "M")],   # Dm Bb F C
    [(52, "m"), (48, "M"), (55, "M"), (50, "M")],   # Em C G D
    [(57, "m"), (55, "M"), (53, "M"), (52, "m")],   # Am G F Em
    [(49, "m"), (57, "M"), (52, "M"), (56, "M")],   # C#m A E G#
]

def chord(root, q):
    return [root, root + (3 if q == "m" else 4), root + 7]

def generar(dur_s, seed=0):
    rng = np.random.default_rng(seed)
    bpm = [96, 100, 104, 108, 92][seed % 5]
    prog = PROGS[seed % len(PROGS)]
    beat = 60.0 / bpm
    bar = 4 * beat
    nb = int(bar * SR)
    loop_bars = 8
    L = nb * loop_bars
    pad = np.zeros(L); bass = np.zeros(L); arp = np.zeros(L); drums = np.zeros(L)
    s16 = nb // 16
    for b in range(loop_bars):
        root, q = prog[b % 4]
        notes = chord(root, q)
        o = b * nb
        # pad: saws desafinadas
        p = np.zeros(nb)
        for m in notes:
            for det in (-0.08, 0.0, 0.08):
                p += _saw(midi(m) * 2 ** (det / 12), nb, rng.random())
        env = np.minimum(1, np.arange(nb) / (0.25 * SR)) * np.minimum(1, (nb - np.arange(nb)) / (0.05 * SR))
        pad[o:o + nb] += p * env / 9
        # bajo en corcheas
        for k in range(8):
            n8 = nb // 8
            f = midi(root - 24 + (12 if k % 4 == 3 else 0))
            seg = _saw(f, n8) * np.exp(-np.arange(n8) / (0.12 * SR))
            bass[o + k * n8:o + (k + 1) * n8] += seg
        # arpegio en semicorcheas (solo desde el compás 3 del loop)
        if b >= 2:
            pat = [0, 1, 2, 1, 0, 2, 1, 2]
            for k in range(16):
                m = notes[pat[k % 8]] + 12 + (12 if k % 8 == 6 else 0)
                seg = _sq(midi(m), s16) * np.exp(-np.arange(s16) / (0.05 * SR))
                arp[o + k * s16:o + (k + 1) * s16] += seg * 0.5
        # batería
        for k in range(4):
            i = o + int(k * beat * SR)
            n = int(0.35 * SR); t = np.arange(n) / SR
            kick = np.sin(2 * np.pi * (50 + 120 * np.exp(-t * 30)) * t) * np.exp(-t * 9)
            drums[i:i + n] += kick[:L - i] * 1.0
            if k in (1, 3):
                n2 = int(0.25 * SR); t2 = np.arange(n2) / SR
                sn = (rng.standard_normal(n2) * 0.6 + np.sin(2 * np.pi * 190 * t2) * 0.4) * np.exp(-t2 * 18)
                drums[i:i + n2] += sn[:L - i] * 0.55
        for k in range(8):
            i = o + int(k * beat / 2 * SR)
            n3 = int(0.05 * SR)
            hh = rng.standard_normal(n3) * np.exp(-np.arange(n3) / (0.012 * SR))
            drums[i:i + n3] += hh * (0.22 if k % 2 else 0.12)
    pad = _lp(pad, 1800)
    bass = _lp(bass, 500)
    arp = _lp(arp, 3000)
    # eco en el arpegio
    d = int(beat * 0.75 * SR)
    arp_d = arp.copy(); arp_d[d:] += arp[:-d] * 0.35
    drums = drums.copy(); drums[:] = drums  # sin filtro
    hats_hp = _hp(drums, 30)
    # bombeo tipo sidechain
    pump = np.ones(L)
    for b in range(loop_bars * 4):
        i = int(b * beat * SR); n = int(beat * SR * 0.9)
        seg = 0.35 + 0.65 * (1 - np.exp(-np.arange(n) / (0.09 * SR)))
        pump[i:i + n] = seg[:max(0, min(n, L - i))]
    loop = pad * 0.55 * pump + bass * 0.45 * pump + arp_d * 0.18 + hats_hp * 0.42
    total = int(dur_s * SR)
    out = np.tile(loop, total // L + 1)[:total]
    # intro: primeros 2 compases sin batería fuerte -> fade in suave
    fi = int(1.0 * SR); out[:fi] *= np.linspace(0, 1, fi)
    fo = int(3.0 * SR); out[-fo:] *= np.linspace(1, 0, fo)
    out /= (np.max(np.abs(out)) + 1e-9)
    return out.astype(np.float32)

def whoosh(dur=0.45, seed=1):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    # barrido de filtro por bloques
    blocks = 12
    for k in range(blocks):
        a, b_ = k * n // blocks, (k + 1) * n // blocks
        fc = 300 + 5000 * np.sin(np.pi * (k + 0.5) / blocks)
        out[a:b_] = _lp(x, fc)[a:b_]
    env = np.sin(np.pi * np.arange(n) / n) ** 2
    return (out * env / (np.max(np.abs(out * env)) + 1e-9)).astype(np.float32)

def pop(seed=0):
    n = int(0.12 * SR); t = np.arange(n) / SR
    f = 880 + 440 * (seed % 3)
    return (np.sin(2 * np.pi * f * t * (1 + 0.5 * np.exp(-t * 40))) * np.exp(-t * 35)).astype(np.float32)

def impacto():
    n = int(0.9 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * (40 + 80 * np.exp(-t * 12)) * t) * np.exp(-t * 4)
    x += np.random.default_rng(3).standard_normal(n) * np.exp(-t * 20) * 0.3
    return (x / np.max(np.abs(x))).astype(np.float32)
