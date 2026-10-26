# -*- coding: utf-8 -*-
"""Chaines de filtres ffmpeg pour un plan : cadrage 9:16, zoom, secousse, glitch.

Le plan source est d'abord agrandi a OVER fois la cible : cette marge donne de
la matiere au zoom et aux secousses sans laisser apparaitre de bord noir.
"""
import math
import random

# Marge au-dela du cadre cible, pour que zoom et secousses aient ou aller.
# Elle se paie en nettete : tout ce qui depasse est agrandi puis jete. A 1.40
# une source 16:9 recadree en 9:16 finissait agrandie deux fois ; 1.06 laisse
# assez de jeu pour quelques pixels de tremblement et garde la definition.
OVER = 1.06


def _even(v):
    return int(round(v / 2.0)) * 2


def cover(W, H):
    ow, oh = _even(W * OVER), _even(H * OVER)
    return (f"scale={ow}:{oh}:force_original_aspect_ratio=increase:flags=bicubic,"
            f"crop={ow}:{oh}"), ow, oh


STYLES = ["punch_in", "punch_out", "slam", "drift", "shake", "hold"]


def pick_style(energy, rng, slow=False):
    if slow:
        return rng.choice(["drift", "punch_in", "hold"])
    if energy > 0.72:
        return rng.choice(["slam", "shake", "punch_in", "punch_out", "shake"])
    if energy > 0.45:
        return rng.choice(["punch_in", "punch_out", "drift", "slam"])
    return rng.choice(["drift", "punch_in", "hold"])


def _zoom_expr(style, dur, fps, energy, rng):
    """Expressions (z, dx, dy) pour zoompan. z=1 cadre la marge entiere,
    z=OVER cadre pile la cible : on part donc toujours autour de OVER."""
    nf = max(1, int(round(dur * fps)))
    t = f"(on/{fps:.4f})"
    amp = 0.10 + 0.14 * energy
    if style == "punch_in":
        z = f"{OVER:.3f}*(1+{amp:.3f}*min(1,{t}/{dur:.3f}))"
    elif style == "punch_out":
        z = f"{OVER:.3f}*(1+{amp:.3f}*(1-min(1,{t}/{dur:.3f})))"
    elif style == "slam":
        z = f"{OVER:.3f}*(1+{amp + 0.06:.3f}*(1-exp(-{t}*14)))"
    elif style == "shake":
        z = f"{OVER:.3f}*{1 + amp * 0.6:.3f}"
    elif style == "drift":
        z = f"{OVER:.3f}*{1 + amp * 0.35:.3f}"
    else:
        z = f"{OVER:.3f}*1.02"

    sh = (2.0 + 16.0 * energy) if style == "shake" else (1.0 + 4.0 * energy)
    f1, f2 = rng.uniform(7, 13), rng.uniform(5, 11)
    p1, p2 = rng.uniform(0, 6.28), rng.uniform(0, 6.28)
    dx = f"{sh:.2f}*sin({t}*{f1:.2f}+{p1:.2f})"
    dy = f"{sh * 0.8:.2f}*cos({t}*{f2:.2f}+{p2:.2f})"
    if style == "drift":
        d = rng.choice([-1, 1]) * (24 + 60 * energy)
        dx = f"{d:.1f}*({t}/{dur:.3f})"
        dy = f"{d * 0.35:.1f}*({t}/{dur:.3f})"
    return z, dx, dy, nf


def build(W, H, fps, dur, energy, style, rng, speed=1.0,
          cut_fx=True, smear=False, whip=False):
    """Renvoie la chaine de filtres complete d'un plan (sans le son)."""
    chain = []
    if abs(speed - 1.0) > 1e-3:
        chain.append(f"setpts={1.0 / speed:.5f}*PTS")
    chain.append(f"fps={fps}")
    cov, ow, oh = cover(W, H)
    chain.append(cov)

    z, dx, dy, nf = _zoom_expr(style, dur, fps, energy, rng)
    cx = f"(iw-iw/zoom)/2+{dx}"
    cy = f"(ih-ih/zoom)/2+{dy}"
    chain.append(f"zoompan=z='{z}':x='{cx}':y='{cy}':d=1:s={W}x{H}:fps={fps}")

    if smear:
        chain.append("tmix=frames=2:weights='1 1'")

    if cut_fx:
        # Eclat a l'attaque. Volontairement bref : au-dela d'une poignee de
        # trames le plan vire au barbouillage arc-en-ciel et on ne lit plus
        # l'image, ce qui gache justement les beaux plans.
        sp = int(3 + 10 * energy)
        chain.append(f"rgbashift=rh=-{sp}:bh={sp}:rv={sp // 3}:bv=-{sp // 3}"
                     f":enable='lt(t,{0.028 + 0.018 * energy:.3f})'")
        b = 0.12 + 0.16 * energy
        chain.append(f"eq=brightness='{b:.3f}*exp(-t*42)':"
                     f"contrast='1+{0.14 * energy:.3f}*exp(-t*34)':eval=frame")

    if whip and dur > 0.18:
        chain.append(f"gblur=sigma=18:steps=1:enable='gt(t,{dur - 0.055:.3f})'")

    chain.append("setsar=1")
    return ",".join(chain)


def grade(W, H, grain=6.0):
    """Etalonnage final : contraste, matiere, vignette, grain."""
    return ",".join([
        # gamma > 1 : les captures de jeu sont souvent sombres, on deboucle
        # les ombres avant de pousser le contraste.
        "eq=contrast=1.10:saturation=1.26:gamma=1.05",
        "unsharp=5:5:0.55:3:3:0.0",
        "vignette=PI/4.6",
        f"noise=alls={int(grain)}:allf=t+u",
        "format=yuv420p",
    ])
