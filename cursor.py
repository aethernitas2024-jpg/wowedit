# -*- coding: utf-8 -*-
"""Reperage du curseur de souris dans une capture de jeu.

Le curseur est un petit objet net qui ne bouge pas alors que le decor defile :
meme signature que le HUD, mais localisee. On cherche donc le point ou la
texture est forte et la difference entre trames faible, a une echelle de
quelques dizaines de pixels -- la difference de deux moyennes glissantes
elimine les grandes zones stables (un rocher au centre de rotation, par
exemple) et ne laisse que les petits objets isoles.

Une fois le curseur localise et juge stable sur toute la duree d'un plan, le
filtre delogo de ffmpeg rebouche la zone en interpolant depuis ses bords.
"""
import subprocess
import numpy as np

from beat import FF

SIZE = 34                 # cote de la zone rebouchee, en pixels source


def _boxf(a, k):
    """Moyenne glissante carree, par image integrale."""
    c = np.cumsum(np.cumsum(a, axis=0, dtype=np.float64), axis=1)
    c = np.pad(c, ((1, 0), (1, 0)))
    h, (H, W) = k // 2, a.shape
    y0 = np.clip(np.arange(H) - h, 0, H)
    y1 = np.clip(np.arange(H) + h + 1, 0, H)
    x0 = np.clip(np.arange(W) - h, 0, W)
    x1 = np.clip(np.arange(W) + h + 1, 0, W)
    s = (c[np.ix_(y1, x1)] - c[np.ix_(y0, x1)]
         - c[np.ix_(y1, x0)] + c[np.ix_(y0, x0)])
    area = (y1 - y0)[:, None] * (x1 - x0)[None, :]
    return (s / area).astype(np.float32)


def _frames(path, t, crop, n, step=0.2):
    """n trames espacees de step secondes, en niveaux de gris, pleine taille."""
    vf = []
    if crop:
        vf.append("crop=%d:%d:%d:%d" % (crop[2], crop[3], crop[0], crop[1]))
    vf += ["fps=%.4f" % (1.0 / step), "format=gray"]
    cmd = [FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % (n * step + 0.3),
           "-i", path, "-an", "-vf", ",".join(vf), "-frames:v", str(n),
           "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, stdout=subprocess.PIPE).stdout
    w, h = (crop[2], crop[3]) if crop else (0, 0)
    if not w or len(raw) < w * h:
        return None
    k = min(n, len(raw) // (w * h))
    return np.frombuffer(raw[:k * w * h], np.uint8).reshape(k, h, w).astype(np.float32)


def _spot(g0, g1, margin=60):
    """(x, y, force) du meilleur candidat curseur entre deux trames.

    La marge n'est pas un detail : les bords de l'image concentrent les
    artefacts de compression et tout reste de chrome mal decoupe, qui sont
    eux aussi du detail immobile et rafleraient le maximum.
    """
    d = np.abs(g0 - g1)
    tex = np.zeros_like(g0)
    tex[:, :-1] += np.abs(np.diff(g0, axis=1))
    tex[:-1, :] += np.abs(np.diff(g0, axis=0))
    det = _boxf(tex, 9) / (1.0 + _boxf(d, 9))
    # petite echelle moins grande echelle : ne restent que les objets isoles
    small = _boxf(det, 17) - _boxf(det, 81)
    m = int(margin)
    if small.shape[0] > 2 * m and small.shape[1] > 2 * m:
        inner = small[m:-m, m:-m]
        i = int(np.argmax(inner))
        y, x = divmod(i, inner.shape[1])
        return x + m, y + m, float(inner.flat[i])
    i = int(np.argmax(small))
    y, x = divmod(i, small.shape[1])
    return x, y, float(small.flat[i])


def locate(path, t, dur, crop, samples=5, tol=9.0):
    """Position du curseur sur un plan, ou None s'il bouge ou reste introuvable.

    On exige que les releves successifs tombent au meme endroit : un faux
    positif se promene d'une trame a l'autre, un vrai curseur non.
    """
    step = max(0.12, dur / (samples + 1.0))
    g = _frames(path, t, crop, samples + 1, step)
    if g is None or len(g) < 3:
        return None
    if np.abs(g[0] - g[1]).mean() < 1.0:      # camera figee : rien a conclure
        return None

    pts = [_spot(g[i], g[i + 1]) for i in range(len(g) - 1)]
    xs = np.array([p[0] for p in pts], np.float32)
    ys = np.array([p[1] for p in pts], np.float32)
    mx, my = float(np.median(xs)), float(np.median(ys))
    keep = (np.abs(xs - mx) < tol) & (np.abs(ys - my) < tol)
    if keep.sum() < max(2, len(pts) - 1):
        return None
    return mx, my, float(np.mean([p[2] for p in pts]))


def delogo(x, y, w, h, size=SIZE):
    """Filtre delogo centre sur (x, y), borde a l'interieur de l'image.

    delogo interpole depuis les bords de la zone : il lui faut au moins un
    pixel de marge de chaque cote, sinon il refuse le rendu.
    """
    s = int(size)
    x0 = int(np.clip(x - s // 2, 1, max(1, w - s - 2)))
    y0 = int(np.clip(y - s // 2, 1, max(1, h - s - 2)))
    return "delogo=x=%d:y=%d:w=%d:h=%d" % (x0, y0, s, s)
