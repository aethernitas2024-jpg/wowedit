# -*- coding: utf-8 -*-
"""Analyse audio : grille de temps reguliere, energie par temps, reperage des drops.

Pas de librosa ni scipy ici (absents de l'install) : STFT et autocorrelation
sont faites a la main avec numpy.
"""
import re
import subprocess
import numpy as np

FF = ("C:/Users/d2460n/AppData/Local/Programs/Python/Python311/Lib/"
      "site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe")

SR, N_FFT, HOP = 22050, 1024, 256
FPS = SR / HOP                      # ~86.13 trames d'analyse par seconde


def load_mono(path):
    """Decode l'audio en mono 22050 Hz float32 dans [-1, 1]."""
    cmd = [FF, "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
           "-f", "s16le", "-"]
    raw = subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def _stft_mag(x):
    win = np.hanning(N_FFT).astype(np.float32)
    n = 1 + max(0, (len(x) - N_FFT) // HOP)
    idx = np.arange(N_FFT)[None, :] + HOP * np.arange(n)[:, None]
    return np.abs(np.fft.rfft(x[idx] * win, axis=1)).astype(np.float32)


def _norm(v, win=34):
    """Retire la moyenne glissante puis redresse : met tous les passages a egalite."""
    k = np.ones(win, dtype=np.float32) / win
    base = np.convolve(v, k, mode="same")
    v = np.maximum(v - base, 0.0)
    s = v.std()
    return v / s if s > 1e-9 else v


def onset_envelope(x):
    """Flux spectral global + flux des basses (la grosse caisse)."""
    mag = _stft_mag(x)
    spec = np.log1p(10.0 * mag)
    d = np.diff(spec, axis=0)
    d = np.maximum(d, 0.0)
    lo_bin = max(2, int(160.0 / (SR / N_FFT)))       # ~160 Hz
    full = _norm(d.sum(axis=1))
    low = _norm(d[:, :lo_bin].sum(axis=1))
    return full, low


def estimate_tempo(env, bpm_lo=70.0, bpm_hi=200.0, prior_bpm=140.0):
    """Autocorrelation ponderee par un prior log-normal (evite les octaves)."""
    o = env - env.mean()
    n = 1 << int(np.ceil(np.log2(len(o) * 2)))
    spec = np.fft.rfft(o, n)
    ac = np.fft.irfft(spec * np.conj(spec), n)[:len(o)]
    lags = np.arange(len(ac))
    lo, hi = int(60 * FPS / bpm_hi), int(60 * FPS / bpm_lo)
    hi = min(hi, len(ac) - 1)
    bpm = 60 * FPS / np.maximum(lags[lo:hi + 1], 1)
    prior = np.exp(-0.5 * (np.log2(bpm / prior_bpm) / 0.7) ** 2)
    score = ac[lo:hi + 1] * prior
    return float(60 * FPS / (lo + int(np.argmax(score))))


def fit_grid(env, bpm, t0=0.0, t1=None):
    """Affine la periode et cale la phase : renvoie (bpm_affine, temps des beats)."""
    dur = len(env) / FPS
    t1 = dur if t1 is None else min(t1, dur)
    p0 = 60.0 * FPS / bpm
    xs = np.arange(len(env), dtype=np.float32)
    best = (-1e18, p0, 0.0)
    for p in np.linspace(p0 * 0.975, p0 * 1.025, 41):
        nb = int((len(env) - 1) / p)
        if nb < 4:
            continue
        phis = np.arange(0.0, p, 0.2, dtype=np.float32)
        pos = (np.arange(nb, dtype=np.float32)[:, None] * p) + phis[None, :]
        val = np.interp(pos.ravel(), xs, env).reshape(pos.shape).sum(axis=0)
        i = int(np.argmax(val))
        if val[i] > best[0]:
            best = (float(val[i]), float(p), float(phis[i]))
    _, p, phi = best
    beats = np.arange(phi, len(env) - 1, p) / FPS
    return 60.0 * FPS / p, beats[(beats >= t0) & (beats <= t1)]


def beat_energy(x, beats, half=0.09):
    """Energie RMS autour de chaque temps, normalisee 0..1."""
    e = np.zeros(len(beats), dtype=np.float32)
    for i, t in enumerate(beats):
        a, b = int((t - half) * SR), int((t + half) * SR)
        seg = x[max(0, a):max(1, b)]
        e[i] = float(np.sqrt(np.mean(seg * seg))) if len(seg) else 0.0
    if e.max() > 1e-9:
        e /= e.max()
    return e


def find_drops(energy, bars=2):
    """Index des temps ou l'energie bondit apres une accalmie (entree de drop)."""
    w = bars * 4
    if len(energy) < 2 * w:
        return []
    k = np.ones(w, dtype=np.float32) / w
    sm = np.convolve(energy, k, mode="same")
    drops, last = [], -999
    for i in range(w, len(sm) - w):
        if i % 4:                                  # un drop tombe sur un temps fort
            continue
        before, after = sm[i - w:i].mean(), sm[i:i + w].mean()
        if after > before * 1.22 and after > 0.55 and i - last > 12:
            drops.append(i)
            last = i
    return drops


def analyze(path, prior_bpm=140.0, force_bpm=None):
    x = load_mono(path)
    full, low = onset_envelope(x)
    env = 0.65 * full + 0.35 * low
    bpm0 = force_bpm or estimate_tempo(env, prior_bpm=prior_bpm)
    bpm, beats = fit_grid(env, bpm0)
    energy = beat_energy(x, beats)
    return {"dur": len(x) / SR, "bpm": bpm, "beats": beats,
            "energy": energy, "drops": find_drops(energy)}


def probe_duration(path):
    """Duree d'un media sans ffprobe (absent) : on lit la sortie de ffmpeg -i."""
    p = subprocess.run([FF, "-i", path], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stdout.decode("utf-8", "replace"))
    if not m:
        return 0.0
    h, mn, s = m.groups()
    return int(h) * 3600 + int(mn) * 60 + float(s)
