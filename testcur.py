# -*- coding: utf-8 -*-
"""Controle visuel du detecteur de curseur."""
import glob, os, subprocess, sys
import border, cursor
from beat import FF

REC = glob.glob("C:/Users/d2460n/Videos/World Of Warcraft/clips_edit/*.mp4")[0]
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
w, h = border.video_size(REC)
crop = border.detect(REC, w, h)
print("zone de jeu", crop, flush=True)

TIMES = [240, 420, 674, 830, 1100, 1359, 1700, 2100, 2342, 2554, 2700, 480]
n = 0
for t in TIMES:
    r = cursor.locate(REC, t, 0.8, crop)
    if not r:
        print("%5ds : aucun candidat stable" % t, flush=True)
        continue
    x, y, s = r
    print("%5ds : x=%4d y=%4d force=%.1f" % (t, x, y, s), flush=True)
    # vignette 160x160 autour du point, agrandie x3
    x0 = max(0, min(int(x) - 80, crop[2] - 160))
    y0 = max(0, min(int(y) - 80, crop[3] - 160))
    subprocess.run([FF, "-v", "error", "-y", "-ss", "%.2f" % t, "-i", REC,
                    "-frames:v", "1", "-vf",
                    "crop=%d:%d:%d:%d,crop=160:160:%d:%d,scale=480:480:flags=neighbor"
                    % (crop[2], crop[3], crop[0], crop[1], x0, y0),
                    "-q:v", "2", "%s/c%02d.jpg" % (OUT, n)])
    n += 1
if n:
    subprocess.run([FF, "-v", "error", "-y", "-i", "%s/c%%02d.jpg" % OUT,
                    "-vf", "tile=4x3", "-frames:v", "1", "%s/grid.jpg" % OUT])
print("vignettes :", n, flush=True)
