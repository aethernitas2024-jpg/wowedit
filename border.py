# -*- coding: utf-8 -*-
"""Detection des bordures d'une capture d'ecran (barre de titre, barre des taches).

Le chrome de Windows est immobile alors que l'image de jeu change en
permanence. On echantillonne donc des trames reparties sur toute la duree et
on regarde, ligne par ligne et colonne par colonne, ce qui varie dans le
temps : ce qui ne varie pas n'est pas du jeu.

Le critere est la *proportion* d'instants ou la ligne bouge, jamais sa
variation moyenne. La difference compte des qu'une fenetre est redimensionnee
en cours de capture : une ligne couverte par la barre de titre pendant la
moitie du film presente alors une forte variation moyenne — elle change quand
la barre s'en va — et une moyenne la classerait comme du jeu, laissant la
barre dans le montage sur toute l'autre moitie. En exigeant qu'elle bouge a
presque tous les instants, on retient la decoupe du cas le plus defavorable.

Plus fiable que cropdetect, qui ne sait reperer que des bords noirs -- or une
barre des taches est pleine d'icones colorees.
"""
import subprocess
import numpy as np

from beat import FF, probe_duration


def _strip(path, t, w, h):
    """Decode une trame en niveaux de gris a la taille demandee."""
    cmd = [FF, "-v", "error", "-ss", "%.2f" % t, "-i", path, "-frames:v", "1",
           "-vf", "scale=%d:%d,format=gray" % (w, h), "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, stdout=subprocess.PIPE).stdout
    if len(raw) < w * h:
        return None
    return np.frombuffer(raw[:w * h], np.uint8).reshape(h, w).astype(np.float32)


def _run(active):
    """Plus longue plage contigue de True ; (0, len) si tout est actif."""
    best = (0, 0)
    i = 0
    while i < len(active):
        if active[i]:
            j = i
            while j < len(active) and active[j]:
                j += 1
            if j - i > best[1] - best[0]:
                best = (i, j)
            i = j
        else:
            i += 1
    return best


ALWAYS = 0.88             # part des instants ou une bande de jeu doit bouger


def _activity(stack, axis, move=2.5):
    """Part des instants ou chaque ligne (ou colonne) change vraiment.

    On compare des trames consecutives deux a deux : une bande de chrome ne
    bouge jamais, une bande de jeu bouge presque toujours.
    """
    d = np.abs(np.diff(stack, axis=0)).mean(axis=axis)   # (paires, bandes)
    return (d > move).mean(axis=0)


def detect(path, w, h, samples=28):
    """Renvoie (x, y, cw, ch) : la zone de jeu, hors chrome immobile."""
    dur = probe_duration(path)
    ts = np.linspace(dur * 0.04, dur * 0.96, samples)

    rows, cols = [], []
    for t in ts:
        r = _strip(path, t, 64, h)
        c = _strip(path, t, w, 64)
        if r is not None:
            rows.append(r)
        if c is not None:
            cols.append(c)
    if len(rows) < 4 or len(cols) < 4:
        return 0, 0, w, h

    ract = _activity(np.stack(rows), 2)               # (paires, lignes, x)
    cact = _activity(np.stack(cols), 1)               # (paires, y, colonnes)
    y0, y1 = _run(ract >= ALWAYS)
    x0, x1 = _run(cact >= ALWAYS)

    # Largeur et hauteur paires : exigees par yuv420p.
    x0, y0 = x0 + (x0 & 1), y0 + (y0 & 1)
    cw, ch = (x1 - x0) & ~1, (y1 - y0) & ~1
    if cw < w * 0.4 or ch < h * 0.4:                  # detection douteuse
        return 0, 0, w & ~1, h & ~1
    return x0, y0, cw, ch


def video_size(path):
    """(largeur, hauteur) sans ffprobe."""
    p = subprocess.run([FF, "-i", path], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    txt = p.stdout.decode("utf-8", "replace")
    import re
    for m in re.finditer(r",\s(\d{2,5})x(\d{2,5})[\s,]", txt):
        return int(m.group(1)), int(m.group(2))
    return 0, 0
