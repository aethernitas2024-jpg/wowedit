# -*- coding: utf-8 -*-
"""Raccords entre plans : coupe franche ou enchainement fluide, sur le temps.

Une transition dure T : pour que la coupe reste calee sur le beat, elle doit
etre *centree* dessus. Chaque plan est donc rendu avec T/2 de rab a chaque
bout, et l'assemblage par xfade reprend ces marges. Tout est compte en trames
et non en secondes : sur soixante raccords, l'arrondi au flottant suffirait a
decaler la fin du montage de plusieurs trames.
"""
import random

# Enchainements xfade, ranges par caractere.
FAST = ["zoomin", "hblur", "slideup", "smoothright", "smoothleft", "squeezeh"]
SOFT = ["dissolve", "fade", "radial", "circleopen", "wiperight", "smoothup"]
HARSH = ["pixelize", "fadewhite", "hlslice", "vdslice"]


class Join:
    __slots__ = ("kind", "frames", "name")

    def __init__(self, kind, frames, name):
        self.kind = kind          # "cut" ou "fluid"
        self.frames = frames      # duree de la transition, en trames
        self.name = name          # nom du xfade ffmpeg

    @property
    def tail(self):
        """Marge fournie par le plan de gauche, en trames."""
        return self.frames // 2

    @property
    def head(self):
        """Marge fournie par le plan de droite. tail + head == frames, donc
        aucune trame ne se perd a l'arrondi quand la transition est impaire."""
        return self.frames - self.frames // 2


def plan_joins(shots, fps, rng, fluid=0.70, hot_q=0.72):
    """Un raccord par intervalle entre deux plans (donc len(shots)-1).

    Le seuil de "gros temps" est un quantile des energies *de cette fenetre*,
    jamais une valeur absolue : l'energie etant normalisee morceau par
    morceau, un seuil fixe classerait presque tous les temps du cote fort sur
    une piste compressee, et le montage n'aurait plus que des coupes seches.
    """
    if len(shots) < 2:
        return []
    import numpy as np
    hot = float(np.quantile([s["e"] for s in shots], hot_q))

    joins = []
    for i in range(len(shots) - 1):
        e = max(shots[i]["e"], shots[i + 1]["e"])
        room = min(shots[i]["dur"], shots[i + 1]["dur"])
        # Un fondu long noie la frappe : etale sur la moitie d'un temps, il n'y
        # a plus d'instant ou l'image bascule, et le montage cesse de coller au
        # rythme meme quand la coupe est parfaitement calee.
        budget = max(1, int(room * 0.40 * fps))
        if e >= hot:
            # Sur les plus gros temps, la coupe franche et elle seule fait
            # claquer le montage. Meme une transition courte y emousse
            # l'instant ou l'image bascule, et c'est precisement la que
            # l'oreille attend de le voir.
            if rng.random() < 0.88:
                joins.append(Join("cut", 1, "fade"))   # 1 trame : coupe franche
            else:
                n = min(budget, max(2, int(0.07 * fps)))
                joins.append(Join("fluid", n, rng.choice(HARSH)))
        elif rng.random() < fluid:
            if shots[i]["dur"] < 0.45:
                n = min(budget, max(2, int(rng.uniform(0.06, 0.11) * fps)))
                joins.append(Join("fluid", n, rng.choice(FAST)))
            else:
                n = min(budget, max(2, int(rng.uniform(0.11, 0.18) * fps)))
                joins.append(Join("fluid", n, rng.choice(SOFT)))
        else:
            joins.append(Join("cut", 1, "fade"))
    return joins


def pads(shots, joins):
    """(marge avant, marge apres) en trames, pour chaque plan."""
    n = len(shots)
    out = []
    for i in range(n):
        head = joins[i - 1].head if i > 0 else 0
        tail = joins[i].tail if i < n - 1 else 0
        out.append((head, tail))
    return out


def graph(nframes, joins, fps):
    """Chaine xfade complete + duree de sortie en trames.

    nframes[i] : longueur rendue du plan i, marges comprises.
    """
    if len(nframes) == 1:
        return "", nframes[0], "[0:v]"
    parts = []
    cur = "[0:v]"
    total = nframes[0]
    for i in range(1, len(nframes)):
        j = joins[i - 1]
        off = (total - j.frames) / float(fps)
        dur = j.frames / float(fps)
        lbl = "[x%d]" % i
        parts.append("%s[%d:v]xfade=transition=%s:duration=%.6f:offset=%.6f%s"
                     % (cur, i, j.name, dur, off, lbl))
        cur = lbl
        total += nframes[i] - j.frames
    return ";".join(parts), total, cur
