# -*- coding: utf-8 -*-
"""Controle visuel des detecteurs : extrait les images ou chacun culmine."""
import glob, os, subprocess, sys, time
import numpy as np
import border, scout
from beat import FF

REC = glob.glob("C:/Users/d2460n/Videos/World Of Warcraft/clips_edit/*.mp4")[0]
OUT = sys.argv[1]

w, h = border.video_size(REC)
crop = border.detect(REC, w, h)
print("source %dx%d -> zone de jeu %s" % (w, h, crop), flush=True)

t0 = time.time()
sc = scout.Scout(REC, crop=crop)
print("analyse en %.0f s, %d trames" % (time.time() - t0, len(sc.score)), flush=True)
p = sc.parts
for k in ("hud", "sun", "water", "vista", "combat"):
    v = p[k]
    print("%-6s med %.5f  q90 %.5f  q99 %.5f  max %.5f"
          % (k, np.median(v), np.quantile(v, .9), np.quantile(v, .99), v.max()), flush=True)
print("trames avec HUD (>0.5) : %.1f %% du total"
      % (100.0 * (p["hud"] > 0.5).mean()), flush=True)


def sheet(key, name, n=8, gap=40):
    """n instants les mieux notes, espaces d'au moins gap secondes."""
    v = p[key]
    picked = []
    for i in np.argsort(-v):
        t = i / scout.RATE
        if all(abs(t - u) > gap for u in picked):
            picked.append(t)
        if len(picked) == n:
            break
    os.makedirs(f"{OUT}/{name}", exist_ok=True)
    for j, t in enumerate(picked):
        subprocess.run([FF, "-v", "error", "-y", "-ss", "%.2f" % t, "-i", REC,
                        "-frames:v", "1", "-vf",
                        "crop=%d:%d:%d:%d,scale=440:-2" % (crop[2], crop[3], crop[0], crop[1]),
                        "-q:v", "4", f"{OUT}/{name}/{j:02d}.jpg"])
    subprocess.run([FF, "-v", "error", "-y", "-i", f"{OUT}/{name}/%02d.jpg",
                    "-vf", "tile=4x2", "-frames:v", "1", f"{OUT}/{name}.jpg"])
    print("%s : %s" % (name, ", ".join("%.0fs" % t for t in picked)), flush=True)


sheet("sun", "sun")
sheet("water", "water")
sheet("hud", "hud")
sheet("vista", "vista")
sheet("combat", "combat")
