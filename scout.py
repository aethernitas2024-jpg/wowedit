# -*- coding: utf-8 -*-
"""Reperage automatique des plus beaux passages d'un clip.

On parcourt le clip en vignettes 256x144 a 8 im/s, en flux (un enregistrement
de 45 min passe sans saturer la RAM), et on mesure pour chaque instant :

  - mouvement, saturation, texture, exposition ;
  - la presence du HUD du jeu (barres d'action, minimap, chat, cadres de
    personnage et de cible) ;
  - quatre signatures : rais de lumiere, eau courante, paysage degage,
    et combat (celle-la pour ecarter, pas pour choisir).

Le HUD est repere comme du *detail qui ne bouge pas*. Les deux conditions sont
indispensables ensemble : mesurer la seule immobilite d'une zone fait prendre
un ciel uni ou du sable lisse pour une barre d'action, puisqu'une surface sans
detail ne peut de toute facon produire aucune difference d'une trame a
l'autre. On compare donc la proportion de pixels structures-et-geles de chaque
zone d'interface a celle du decor : quand le joueur est a l'arret, tout gele,
les deux montent ensemble et l'ecart s'annule de lui-meme.
"""
import hashlib
import json
import os
import subprocess
import numpy as np

from beat import FF, probe_duration

RATE = 8.0                      # im/s d'analyse
TW, TH = 256, 144               # taille des vignettes
VER = 11                         # invalide le cache quand la notation change
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".scout_cache")
EXT = (".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v", ".ts")

# Zones, en fractions de la vignette : (y0, y1, x0, x1)
Z_WORLD = (0.25, 0.70, 0.25, 0.75)      # reference : le decor
Z_BAR = (0.86, 1.00, 0.28, 0.72)        # barres d'action
Z_MINI = (0.01, 0.20, 0.84, 1.00)       # minimap
Z_CHAT = (0.68, 0.96, 0.00, 0.27)       # fenetre de chat
Z_UNIT = (0.01, 0.20, 0.00, 0.40)       # cadres de personnage et de cible


def list_clips(folder):
    out = []
    for root, _, files in os.walk(folder):
        for f in sorted(files):
            if f.lower().endswith(EXT):
                out.append(os.path.join(root, f))
    return out


def _key(path, crop):
    st = os.stat(path)
    sig = f"{path}|{st.st_size}|{int(st.st_mtime)}|{RATE}|{TW}x{TH}|{crop}|{VER}"
    return os.path.join(CACHE, hashlib.md5(sig.encode()).hexdigest() + ".json")


def _box(z):
    return (slice(int(z[0] * TH), max(int(z[0] * TH) + 1, int(z[1] * TH))),
            slice(int(z[2] * TW), max(int(z[2] * TW) + 1, int(z[3] * TW))))


def _sample(gray, tex, z, step):
    """Pixels et texture d'une zone, sous-echantillonnes et aplatis."""
    ys, xs = _box(z)
    g = gray[:, ys, xs][:, ::step, ::step]
    t = tex[:, ys, xs][:, ::step, ::step]
    n = g.shape[0]
    return (g.reshape(n, -1).astype(np.uint8),
            np.clip(t, 0, 255).reshape(n, -1).astype(np.uint8))


def _frozen(pix, tex, win, blk=1500, still=2.0, detail=6.0):
    """Part des pixels a la fois structures et immobiles sur la fenetre.

    C'est la signature d'un element d'interface : un decor structure defile,
    un ciel immobile n'est pas structure ; seul un HUD est les deux.
    """
    from numpy.lib.stride_tricks import sliding_window_view
    n = len(pix)
    if n < win + 1:
        return np.zeros(n, np.float32)
    h = win // 2
    pad = np.pad(pix, ((h, win - 1 - h), (0, 0)), mode="edge")
    out = np.zeros(n, np.float32)
    for a in range(0, n, blk):
        b = min(n, a + blk)
        w = sliding_window_view(pad[a:b + win - 1].astype(np.float32), win, axis=0)
        sd = w.std(axis=2)
        out[a:b] = ((sd < still) & (tex[a:b] > detail)).mean(axis=1)
    return out


def _measure(path, crop=None, chunk=32):
    """Parcourt les vignettes en flux et renvoie les mesures par trame."""
    vf = []
    if crop:
        vf.append("crop=%d:%d:%d:%d" % (crop[2], crop[3], crop[0], crop[1]))
    vf += [f"fps={RATE}", f"scale={TW}:{TH}", "format=rgb24"]
    cmd = [FF, "-v", "error", "-i", path, "-an", "-vf", ",".join(vf),
           "-f", "rawvideo", "-"]
    fsz = TW * TH * 3
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=fsz * chunk)

    cols = {k: [] for k in ("mot", "sat", "bri", "tex", "flat", "sun",
                            "water", "vista", "combat")}
    zones = {"world": (Z_WORLD, 4), "bar": (Z_BAR, 2),
             "mini": (Z_MINI, 2), "chat": (Z_CHAT, 2),
             "unit": (Z_UNIT, 2)}
    zpix = {k: [] for k in zones}
    ztex = {k: [] for k in zones}
    # L'eau est presque toujours dans la moitie basse ; le ciel, jamais.
    vweight = np.linspace(0.35, 1.0, TH, dtype=np.float32)[None, :, None]
    # Les signatures lumiere et eau ignorent les emplacements d'interface :
    # les icones bleues et les barres de vie du HUD se faisaient compter
    # comme de l'eau, ce qui remontait des plans pleins d'UI.
    core = np.ones((TH, TW), dtype=bool)
    for z in (Z_BAR, Z_MINI, Z_CHAT, Z_UNIT):
        ys, xs = _box(z)
        core[ys, xs] = False
    corew = core[None].astype(np.float32)
    prev = None
    try:
        while True:
            buf = proc.stdout.read(fsz * chunk)
            n = len(buf) // fsz
            if n == 0:
                break
            f = np.frombuffer(buf[:n * fsz], np.uint8).reshape(n, TH, TW, 3)
            f = f.astype(np.float32)
            r, g, b = f[..., 0], f[..., 1], f[..., 2]
            gray = r * .299 + g * .587 + b * .114

            ref = gray if prev is None else np.concatenate([prev[None], gray])
            dif = np.abs(np.diff(ref, axis=0))
            if prev is None:
                dif = np.concatenate([dif[:1], dif]) if n > 1 else \
                    np.zeros((1, TH, TW), np.float32)
            prev = gray[-1]

            gx = np.abs(np.diff(gray, axis=2))
            gy = np.abs(np.diff(gray, axis=1))
            tex = np.zeros_like(gray)
            tex[:, :, :-1] += gx
            tex[:, :-1, :] += gy

            # Rais de lumiere : des hautes lumieres chaudes et etendues.
            hot = gray > 225.0
            warm = (r - b) > 6.0
            sun = ((hot & warm).astype(np.float32) * corew).mean(axis=(1, 2))

            # Eau : plus claire que le reste de l'image, non chaude, et tres
            # contrastee de pres. Surtout pas de critere de couleur absolu :
            # chaque zone du jeu a sa dominante, et sous le brouillard vert de
            # Zangarmarsh une cascade est verte, pas bleue. C'est la clarte
            # relative au reste de la trame qui tient d'une zone a l'autre.
            sat = f.max(axis=3) - f.min(axis=3)
            med = np.median(gray, axis=(1, 2))[:, None, None]
            wet = (gray > med + 22.0) & ((r - b) < 10.0) & (tex > 14.0)
            water = (wet.astype(np.float32) * vweight * corew).mean(axis=(1, 2))

            # Paysage : du ciel ou un lointain degage en haut de l'image,
            # c'est-a-dire une grande plage lisse et plus claire que le reste.
            up = slice(0, int(TH * 0.45))
            vista = (((tex[:, up, :] < 6.0)
                      & (gray[:, up, :] > med + 10.0))
                     .astype(np.float32) * corew[:, up, :]).mean(axis=(1, 2))

            # Combat : chiffres de degats, barres de vie ennemies, impacts de
            # sorts. Tous petits, tres satures, clairs et a bords francs --
            # un decor est soit lisse, soit moins sature, rarement les trois.
            fight = ((sat > 80.0) & (gray > 150.0) & (tex > 25.0))
            combat = (fight.astype(np.float32) * corew).mean(axis=(1, 2))

            for k, (z, step) in zones.items():
                p, x = _sample(gray, tex, z, step)
                zpix[k].append(p)
                ztex[k].append(x)

            cols["mot"].append(dif.mean(axis=(1, 2)))
            cols["sat"].append(sat.mean(axis=(1, 2)) / 255.0)
            cols["bri"].append(gray.mean(axis=(1, 2)) / 255.0)
            cols["tex"].append(tex.mean(axis=(1, 2)) / 2.0)
            cols["flat"].append((tex < 8.0).mean(axis=(1, 2)))
            cols["sun"].append(sun)
            cols["water"].append(water)
            cols["vista"].append(vista)
            cols["combat"].append(combat)
            if n < chunk:
                break
    finally:
        proc.stdout.close()
        proc.wait()
    if not cols["mot"]:
        return None
    out = {k: np.concatenate(v).astype(np.float32) for k, v in cols.items()}
    win = max(4, int(RATE * 1.5))
    for k in zones:
        out["frz_" + k] = _frozen(np.concatenate(zpix[k]),
                                  np.concatenate(ztex[k]), win)
    return out


def _dilate(v, win):
    """Etale un masque dans le temps (maximum glissant)."""
    from numpy.lib.stride_tricks import sliding_window_view
    n, w = len(v), int(win)
    if w < 2 or n < w + 1:
        return v
    h = w // 2
    pad = np.pad(v, (h, w - 1 - h), mode="edge")
    return sliding_window_view(pad, w).max(axis=1)


def _smooth(v, win):
    if win < 2:
        return v
    k = np.ones(int(win), dtype=np.float32) / float(int(win))
    return np.convolve(v, k, mode="same")


def detect_hud(m, margin=0.12):
    """Probabilite de HUD par trame.

    On compare la part de pixels structures-et-geles de chaque zone d'interface
    a celle du decor. Un ciel uni ne compte pas (aucun detail), un decor qui
    defile non plus (rien de gele), et si le joueur s'arrete les deux montent
    ensemble et la difference s'annule.
    """
    ref = _smooth(m["frz_world"], RATE * 0.5)
    hud = np.zeros(len(ref), dtype=np.float32)
    for zone in ("bar", "mini", "chat", "unit"):
        z = _smooth(m["frz_" + zone], RATE * 0.5)
        hud = np.maximum(hud, np.clip((z - ref - margin) / 0.22, 0, 1))
    return _smooth(hud, RATE * 1.2)


class Scout:
    """Sert les meilleurs segments d'un clip, sans jamais resservir le meme."""

    def __init__(self, path, crop=None, w_sun=0.0, w_water=0.0,
                 w_vista=0.0, w_combat=0.0, min_gap=0.0):
        self.path = path
        self.crop = crop
        self.min_gap = min_gap
        self.score, self.cut, self.dur, self.parts = _profile(
            path, crop, w_sun, w_water, w_vista, w_combat)
        self.used = []                                    # (debut, fin) en secondes
        self.quality = float(np.percentile(self.score, 90)) if len(self.score) else -9.0

    def _free(self, t, d):
        pad = max(0.35, self.min_gap)
        return all(t + d + pad <= a or t >= b + pad for a, b in self.used)

    def best(self, d, margin=0.25, floor=None):
        """Meilleure fenetre libre de duree d ; None si rien n'atteint floor."""
        w = max(1, int(round(d * RATE)))
        if len(self.score) < w + 1 or self.dur < d + 2 * margin:
            return None
        c = np.concatenate([[0.0], np.cumsum(self.score, dtype=np.float64)])
        means = (c[w:] - c[:-w]) / w
        starts = np.arange(len(means)) / RATE
        ok = (starts >= margin) & (starts + d <= self.dur - margin)
        if not ok.any():
            return None
        for i in np.argsort(-means):
            if not ok[i]:
                continue
            if floor is not None and means[i] < floor:
                return None                               # le reste est pire
            t = float(starts[i])
            if self._free(t, d):
                return t, float(means[i])
        return None

    def take(self, d, floor=None):
        r = self.best(d, floor=floor)
        if r is None:
            return None
        t, s = r
        self.used.append((t, t + d))
        return t, s

    def rewind(self):
        self.used = []


def _profile(path, crop=None, w_sun=0.0, w_water=0.0,
             w_vista=0.0, w_combat=0.0):
    """(score par trame, coupes, duree, detail). Mis en cache sur disque."""
    ck = _key(path, crop)
    if os.path.exists(ck):
        with open(ck) as fh:
            d = json.load(fh)
        parts = {k: np.array(v, np.float32) for k, v in d["parts"].items()}
    else:
        dur = probe_duration(path)
        m = _measure(path, crop)
        if m is None:
            parts = {k: np.zeros(1, np.float32)
                     for k in ("base", "hud", "cut", "sun", "water",
                               "vista", "combat")}
            dur = dur or 0.0
        else:
            mot, sat, bri = m["mot"], m["sat"], m["bri"]
            ui = np.clip((m["flat"] - 0.45) / 0.35, 0, 1)
            tex = np.clip(m["tex"] / 12.0, 0, 1)
            mv = np.clip(mot / 6.0, 0, 1.4)
            col = np.clip(sat * 2.4, 0, 1.2)
            expo = 1.0 - np.clip(np.abs(bri - 0.45) / 0.45, 0, 1)
            base = 0.55 * mv + 0.55 * col + 0.45 * tex + 0.35 * expo - 1.60 * ui
            base -= 3.0 * np.clip((0.10 - bri) / 0.06, 0, 1)      # noir / fondu
            base -= 1.5 * np.clip((bri - 0.88) / 0.07, 0, 1)      # blanc crame
            parts = {"base": base, "hud": detect_hud(m),
                     "cut": (mot > 12.0).astype(np.float32),
                     "sun": m["sun"], "water": m["water"],
                     "vista": m["vista"], "combat": m["combat"]}
            dur = dur or len(mot) / RATE
        os.makedirs(CACHE, exist_ok=True)
        with open(ck, "w") as fh:
            json.dump({"parts": {k: v.tolist() for k, v in parts.items()},
                       "dur": dur}, fh)
    with open(ck) as fh:
        dur = json.load(fh)["dur"]

    sc = parts["base"].copy()
    sc -= 2.5 * parts["cut"]
    # Le HUD arrive par blocs : aux deux bouts d'un bloc, le lissage fait
    # passer des trames sous le seuil alors que l'interface est encore a
    # l'ecran. On elargit donc le rejet de part et d'autre.
    hud = parts["hud"]
    hard = _dilate((hud > 0.35).astype(np.float32), int(RATE * 3.0))
    sc -= 4.0 * hud + 4.0 * hard
    if w_sun:
        sc += w_sun * _bonus(parts["sun"])
    if w_water:
        sc += w_water * _bonus(parts["water"])
    if w_vista:
        sc += w_vista * _bonus(parts["vista"])
    if w_combat:
        # On dilate : l'approche et la fin de l'echauffouree sont aussi
        # a ecarter, pas seulement l'instant ou les chiffres s'affichent.
        c = _bonus(parts["combat"])
        sc -= w_combat * np.maximum(c, _dilate(c, int(RATE * 2.0)))
    return sc, parts["cut"] > 0.5, dur, parts


def _bonus(v, lo=0.55, hi=0.95):
    """Normalise une signature en 0..1 sur ses propres quantiles.

    Un seuil absolu ne marcherait pas : la quantite de ciel brillant depend
    entierement de la zone et de l'heure du jeu.
    """
    a, b = float(np.quantile(v, lo)), float(np.quantile(v, hi))
    if b - a < 1e-6:
        return np.zeros_like(v)
    return np.clip((v - a) / (b - a), 0, 1.3)
