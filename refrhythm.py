# -*- coding: utf-8 -*-
"""Mesure le rythme de montage d'une video de reference.

On ne "regarde" pas la video : on detecte ses coupes par difference entre
trames, on repere le tempo de sa bande son, et on exprime la duree de chaque
plan en temps musicaux. Ce sont exactement les reglages que prend le moteur.

Une coupe franche fait un pic isole d'une ou deux trames ; un enchainement
fondu etale la difference sur plusieurs trames. La largeur du pic separe donc
les deux, et donne la proportion de fondus du montage de reference.

  py -3.11 refrhythm.py "reference.mp4"
"""
import subprocess
import sys
import numpy as np

import beat
from beat import FF, probe_duration

TW, TH = 128, 72
RATE = 30.0


def diffs(path):
    """Difference moyenne entre trames consecutives, a RATE im/s."""
    vf = "fps=%g,scale=%d:%d,format=gray" % (RATE, TW, TH)
    cmd = [FF, "-v", "error", "-i", path, "-an", "-vf", vf,
           "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, stdout=subprocess.PIPE).stdout
    n = len(raw) // (TW * TH)
    if n < 3:
        return np.zeros(1, np.float32)
    f = np.frombuffer(raw[:n * TW * TH], np.uint8).reshape(n, TH, TW)
    return np.abs(np.diff(f.astype(np.float32), axis=0)).mean(axis=(1, 2))


def events(d, floor=6.0, k=3.5):
    """(instant, largeur, concentration) de chaque changement de plan.

    La concentration est la part du saut portee par la trame la plus forte.
    C'est elle qui distingue une coupe d'un fondu, et non la largeur du pic :
    dans un montage rapide, une coupe franche entre deux plans tres animes
    etale la difference sur plusieurs trames sans etre un fondu pour autant.
    Se fier a la largeur fait compter la moitie des coupes comme des fondus.
    """
    thr = max(floor, k * float(np.median(d)))
    out, i = [], 0
    while i < len(d):
        if d[i] > thr:
            j = i
            while j < len(d) and d[j] > thr * 0.6:
                j += 1
            run = d[i:j]
            peak = float(run.max() / max(run.sum(), 1e-9))
            out.append(((i + j) / 2.0 / RATE, j - i, peak))
            i = j
        else:
            i += 1
    return out, thr


GRID = np.array([0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0])


def profile(path):
    """Renvoie le rythme mesure : proportion de fondus et longueurs de plan.

    Les longueurs sont exprimees en temps musicaux, jamais en secondes : c'est
    ce qui permet de transposer le rythme sur un morceau d'un autre tempo.
    """
    dur = probe_duration(path)
    ev, thr = events(diffs(path))
    if len(ev) < 4:
        raise SystemExit("trop peu de coupes dans la reference pour conclure")

    peaks = np.array([p for _, _, p in ev], np.float64)
    soft = int((peaks < 0.40).sum())
    hard = len(ev) - soft
    ts = np.array([t for t, _, _ in ev], np.float64)
    lens = np.diff(ts)
    an = beat.analyze(path)
    per = 60.0 / an["bpm"]
    snap = GRID[np.argmin(np.abs((lens / per)[:, None] - GRID[None, :]), axis=1)]
    weights = {float(g): float((snap == g).mean()) for g in GRID
               if (snap == g).mean() > 0.02}
    tot = sum(weights.values())
    return {"dur": dur, "cuts": len(ev), "thr": thr,
            "fluid": (len(ev) - hard) / float(len(ev)),
            "bpm": an["bpm"], "density": len(ev) / dur,
            "median_ms": 1000 * float(np.median(lens)),
            # Duree moyenne en temps : c'est elle qui fixe la densite reelle.
            # La seule forme de la distribution ne suffit pas, parce qu'un
            # temps fort engendre d'office quatre plans d'un quart et gonfle
            # leur compte.
            "mean_beats": float(np.mean(lens) / per),
            "onbeat": float((np.abs(lens / per - snap) / snap < 0.20).mean()),
            "weights": {k: v / tot for k, v in weights.items()}}


def describe(p):
    out = ["reference : %.1f s, %d changements de plan (seuil %.1f)"
           % (p["dur"], p["cuts"], p["thr"]),
           "  fondus %.0f %% -> --fluid %.2f" % (100 * p["fluid"], p["fluid"]),
           "  densite %.2f coupe/s, plan median %.0f ms"
           % (p["density"], p["median_ms"]),
           "  tempo %.1f BPM, plans cales sur la grille : %.0f %%"
           % (p["bpm"], 100 * p["onbeat"]),
           "  repartition des longueurs, en temps :"]
    for g in sorted(p["weights"]):
        s = p["weights"][g]
        out.append("      %4.2f temps : %s %.0f %%"
                   % (g, "#" * int(round(s * 40)), 100 * s))
    return "\n".join(out)


if __name__ == "__main__":
    print(describe(profile(sys.argv[1])), flush=True)
