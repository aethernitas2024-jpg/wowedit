# -*- coding: utf-8 -*-
"""Montage TikTok cale au beat : coupe sur la grille rythmique du morceau.

  py -3.11 wowedit.py --audio piste.mp3 --clips DOSSIER --out edit.mp4

scout.py choisit les plus beaux passages (et ecarte ceux ou le HUD du jeu est
visible), border.py enleve le chrome de la capture d'ecran, shotfx.py anime
chaque plan, joins.py fait les raccords, et la passe finale ajoute les effets
globaux cales sur la grille.
"""
import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beat
import border
import cursor as cur
import joins as jn
import scout
import shotfx

FF = beat.FF
IMPACT = "C\\:/Windows/Fonts/impact.ttf"
ARIALBD = "C\\:/Windows/Fonts/arialbd.ttf"
IMPACT_FILE = "C:/Windows/Fonts/impact.ttf"


def has_alpha(path):
    """Vrai si l'image porte une transparence reellement utilisee."""
    try:
        from PIL import Image
        im = Image.open(path)
        if im.mode not in ("RGBA", "LA", "P"):
            return False
        im = im.convert("RGBA")
        return min(im.getchannel("A").getextrema()) < 250
    except Exception:
        return False


def fit_size(txt, max_w, want, fontfile=IMPACT_FILE):
    """Plus grand corps <= want dont le texte tient dans max_w.

    Indispensable : une taille fixee en proportion de la *hauteur* ne dit rien
    de la largeur du texte rendu, et un titre un peu long sort du cadre, coupe
    des deux cotes sans que rien ne le signale.
    """
    try:
        from PIL import ImageFont
    except ImportError:
        return int(want)
    lo, hi, best = 8, int(want), 8
    while lo <= hi:
        mid = (lo + hi) // 2
        b = ImageFont.truetype(fontfile, mid).getbbox(txt)
        if (b[2] - b[0]) <= max_w:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return best


def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode:
        sys.stderr.write(p.stdout.decode("utf-8", "replace")[-4000:] + "\n")
        raise SystemExit("ffmpeg a echoue (%d)" % p.returncode)
    return p.stdout.decode("utf-8", "replace")


def enc_args(enc, quality=19, maxrate=None):
    """maxrate n'est pose que sur la passe finale : les plans intermediaires
    restent en qualite libre pour ne pas cumuler deux compressions serrees."""
    if enc == "nvenc":
        a = ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr",
             "-cq", str(quality), "-b:v", "0", "-pix_fmt", "yuv420p"]
    else:
        a = ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(quality - 2),
             "-pix_fmt", "yuv420p"]
    if maxrate:
        a += ["-maxrate", "%dM" % maxrate, "-bufsize", "%dM" % (maxrate * 2)]
    return a


def pick_encoder(want):
    if want != "auto":
        return want
    t = os.path.join(os.environ.get("TEMP", "."), "_wowedit_enc.mp4")
    p = subprocess.run([FF, "-v", "error", "-y", "-f", "lavfi", "-i",
                        "testsrc=size=256x256:duration=0.2",
                        "-c:v", "h264_nvenc", t],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ok = p.returncode == 0
    if os.path.exists(t):
        os.remove(t)
    return "nvenc" if ok else "x264"


# ---------------------------------------------------------------- plan de coupe

def plan_shots(bpm, beats, energy, t_start, t_end, fps, rng, weights=None,
               target_beats=None):
    """Decoupe la fenetre en plans : plus ca tape, plus ca coupe court.

    Les frontieres sont arretees en trames des maintenant : sur soixante
    raccords, l'arrondi au flottant suffirait a decaler la fin du montage.
    """
    per = 60.0 / bpm
    # Le montage part exactement de t_start, pas du temps le plus proche :
    # demander le debut du morceau et se retrouver cale sur le premier temps
    # ampute l'attaque. On garde donc le depart exact et on decale la grille
    # de la phase qui separe t_start du premier temps, pour que les coupes
    # tombent quand meme juste.
    t0 = float(t_start)
    later = np.nonzero(beats >= t0 - 1e-6)[0]
    i0 = int(later[0]) if len(later) else max(0, len(beats) - 1)
    phase = float(beats[i0] - t0)
    if not 0.0 <= phase < per * 0.99:
        phase = 0.0
    hot = float(np.quantile(energy, 0.72))
    mid = float(np.quantile(energy, 0.42))

    # Rang d'energie de chaque temps de la fenetre, 0 = calme, 1 = le plus fort.
    nb = max(2, int((t_end - t0) / per) + 1)
    win = energy[i0:i0 + nb]
    rank = (win.argsort().argsort() / max(1.0, len(win) - 1.0)
            if len(win) > 1 else np.zeros(1))

    # Parite metrique : sur ce genre de morceau la frappe forte tombe un temps
    # sur deux. Couper sur l'autre parite donne une coupe qui ne se sent pas,
    # meme parfaitement calee sur la grille. On repere donc laquelle porte
    # l'energie.
    ab = np.arange(i0, min(len(energy), i0 + nb))
    if len(ab) > 3:
        e0 = energy[ab[ab % 2 == 0]].mean() if (ab % 2 == 0).any() else 0.0
        e1 = energy[ab[ab % 2 == 1]].mean() if (ab % 2 == 1).any() else 0.0
        strong = 0 if e0 >= e1 else 1
    else:
        strong = i0 % 2

    if weights:
        # On respecte la repartition mesuree sur la reference tout en la
        # rendant musicale : le quantile est pris a l'envers du rang
        # d'energie, donc les plans les plus courts tombent sur les temps qui
        # tapent le plus fort.
        lens = sorted(weights)
        cum = np.cumsum([weights[k] for k in lens])
        cum = cum / cum[-1]

        def pick(q):
            i = int(np.searchsorted(cum, min(q, 0.999999)))
            return lens[min(i, len(lens) - 1)]

        def walk(bias, seed):
            rr = random.Random(seed)
            out, b = [], 0.0
            while t0 + phase + b * per < t_end - 0.05:
                bi = int(round(b))
                r = float(rank[min(bi, len(rank) - 1)])
                q = min(1.0, max(0.0, 1.0 - r + bias + rr.uniform(-0.12, 0.12)))
                ln = pick(q)
                e = float(energy[min(len(energy) - 1, i0 + bi)])
                if ln < 1.0:
                    if (i0 + bi) % 2 != strong:
                        ln = 1.0          # temps faible : pas de subdivision
                    else:
                        # Une subdivision n'est emise qu'en groupe complet, de
                        # facon a retomber sur le temps suivant. Sinon les
                        # frontieres derivent sur des positions faibles et la
                        # coupe cesse de se faire sentir.
                        for _ in range(max(1, int(round(1.0 / ln)))):
                            out.append((b, ln, e))
                            b += ln
                        continue
                out.append((b, ln, e))
                b += ln
            return out

        # La forme de la distribution ne suffit pas a fixer la densite : un
        # temps fort engendre quatre plans d'un quart d'un coup, ce qui les
        # surrepresente. On decale donc le quantile jusqu'a retrouver la duree
        # moyenne de plan mesuree sur la reference.
        if target_beats:
            lo, hi = -0.60, 0.95
            for _ in range(18):
                b = (lo + hi) / 2.0
                w = walk(b, 20260920)
                m = float(np.mean([x[1] for x in w])) if w else target_beats
                if m < target_beats:
                    lo = b
                else:
                    hi = b
            bias = (lo + hi) / 2.0
        else:
            bias = 0.0
        raw = walk(bias, rng.randrange(1 << 30))
    else:
        raw = []

    bp = 0.0
    while not weights and t0 + phase + bp * per < t_end - 0.05:
        idx = min(len(energy) - 1, i0 + int(bp))
        e = float(energy[idx])
        if e >= hot:
            if rng.random() < 0.16:                  # rafale de doubles-croches
                for _ in range(4):
                    raw.append((bp, 0.25, e))
                    bp += 0.25
                continue
            ln = rng.choice([1.0, 1.0, 1.0, 0.5, 0.5])
        elif e >= mid:
            ln = rng.choice([1.0, 1.0, 2.0, 0.5])
        else:
            ln = rng.choice([2.0, 2.0, 4.0])
        raw.append((bp, ln, e))
        bp += ln

    out = []
    lead = int(round(phase * fps))
    if lead >= max(3, int(0.07 * fps)):
        # Amorce : de l'attaque du morceau jusqu'au premier temps. Sans elle,
        # demander un depart a zero couperait le debut de la musique.
        out.append({"t": 0.0, "frames": lead, "dur": lead / float(fps),
                    "e": float(energy[min(i0, len(energy) - 1)]),
                    "beats": phase / per})
    for bpos, ln, e in raw:
        a = t0 + phase + bpos * per
        b = min(t_end, a + ln * per)
        fa, fb = int(round((a - t0) * fps)), int(round((b - t0) * fps))
        if fb - fa >= max(3, int(0.07 * fps)):
            out.append({"t": a - t0, "frames": fb - fa,
                        "dur": (fb - fa) / float(fps), "e": e, "beats": ln})
    return t0, out


def pin_must(shots, must, window=3):
    """Reserve des plans pour des instants imposes a la main.

    On les repartit sur toute la duree, et dans chaque voisinage on prend le
    plan le plus long : un passage qu'on a expressement demande merite mieux
    qu'une rafale de 100 ms ou on ne verrait rien.
    """
    pinned = {}
    n = len(shots)
    if not must or not n:
        return pinned
    for k, (ci, t) in enumerate(must):
        mid = int((k + 0.5) / len(must) * n)
        cands = [i for i in range(max(0, mid - window), min(n, mid + window + 1))
                 if i not in pinned]
        if not cands:
            cands = [i for i in range(n) if i not in pinned]
        if not cands:
            break
        pinned[max(cands, key=lambda i: shots[i]["frames"])] = (ci, t)
    return pinned


def assign_clips(shots, scouts, pads, fps, rng, floor=0.20, must=None):
    """Attribue a chaque plan un clip et son meilleur extrait encore libre.

    On exige d'abord un score minimum : mieux vaut repiocher ailleurs dans un
    bon clip que de caser un plan mediocre pour faire tourner les sources.
    """
    q = np.array([s.quality for s in scouts], dtype=np.float64)
    lo, hi = q.min(), q.max()
    w = np.full(len(q), 0.6) if hi - lo < 1e-6 else 0.2 + 0.8 * (q - lo) / (hi - lo)
    order = []
    for i, wi in enumerate(w):
        order += [i] * max(1, int(round(wi * 4)))
    rng.shuffle(order)

    many = len(set(order)) > 1
    pinned = pin_must(shots, must)
    k, last = 0, -1
    for idx, (s, (head, tail)) in enumerate(zip(shots, pads)):
        s["speed"] = 1.0
        if s["e"] < 0.35 and s["beats"] >= 2 and rng.random() < 0.55:
            s["speed"] = 0.62                        # ralenti sur les plans calmes
        elif s["e"] > 0.70 and rng.random() < 0.18:
            s["speed"] = 1.45
        s["out_frames"] = s["frames"] + head + tail
        need = s["out_frames"] / float(fps) * s["speed"]

        if idx in pinned:                            # instant impose a la main
            ci, t = pinned[idx]
            ci = min(ci, len(scouts) - 1)
            t = max(0.0, min(t, max(0.0, scouts[ci].dur - need)))
            scouts[ci].used.append((t, t + need))
            s["clip"], s["src"] = ci, t
            last = ci
            continue

        got = None
        for lim in (floor, None):                    # exigeant, puis on se rabat
            for _ in range(len(order)):
                ci = order[k % len(order)]
                k += 1
                if ci == last and many:
                    continue
                r = scouts[ci].take(need, floor=lim)
                if r:
                    got = (ci, r[0])
                    break
            if got:
                break
        if got is None:                              # matiere epuisee : on recycle
            for sc in scouts:
                sc.rewind()
            ci = order[k % len(order)]
            k += 1
            r = scouts[ci].take(need)
            got = (ci, r[0] if r else 0.0)
        s["clip"], s["src"] = got
        last = got[0]
    return shots


# -------------------------------------------------------------------- rendu

def esc(txt):
    """Echappe un texte pour drawtext."""
    return txt.replace("\\", "\\\\").replace(":", "\\:").replace("'", "")


def render_shots(shots, scouts, credits, W, H, fps, enc, work, rng, quality,
                 decursor=True, cur_floor=18.0):
    os.makedirs(work, exist_ok=True)
    paths, wiped = [], 0
    for i, s in enumerate(shots):
        sc = scouts[s["clip"]]
        slow = s["speed"] < 1.0
        odur = s["out_frames"] / float(fps)
        style = shotfx.pick_style(s["e"], rng, slow=slow)
        chain = shotfx.build(W, H, fps, odur, s["e"], style, rng,
                             speed=s["speed"], cut_fx=True,
                             smear=(s["e"] > 0.70 and odur < 0.30),
                             whip=(rng.random() < 0.12))
        pre = []
        if sc.crop:
            pre.append("crop=%d:%d:%d:%d" % (sc.crop[2], sc.crop[3],
                                             sc.crop[0], sc.crop[1]))
            # Le curseur est cherche apres la decoupe, donc dans les memes
            # coordonnees que delogo. On n'efface que s'il reste au meme
            # endroit pendant tout le plan : sinon le rebouchage suivrait mal
            # et laisserait une trainee plus visible que le curseur.
            if decursor:
                r = cur.locate(sc.path, s["src"], odur * s["speed"], sc.crop)
                if r and r[2] >= cur_floor:
                    pre.append(cur.delogo(r[0], r[1], sc.crop[2], sc.crop[3]))
                    wiped += 1
        chain = ",".join(pre + [chain])

        name = os.path.basename(sc.path)
        who = credits.get(name) or credits.get(os.path.splitext(name)[0])
        if who:
            fs = max(14, int(H * 0.019))
            chain += (",drawtext=fontfile='%s':text='%s':fontcolor=white@0.72"
                      ":fontsize=%d:borderw=2:bordercolor=black@0.6:x=%d:y=h-%d"
                      % (ARIALBD, esc(who), fs, int(W * 0.045), int(H * 0.085)))
        out = os.path.join(work, "s%04d.mp4" % i)
        cmd = [FF, "-v", "error", "-y",
               "-ss", "%.3f" % s["src"],
               "-t", "%.3f" % (odur * s["speed"] + 0.30),
               "-i", sc.path, "-an", "-vf", chain,
               "-frames:v", str(s["out_frames"]),
               "-fps_mode", "cfr", "-r", str(fps)]
        cmd += enc_args(enc, quality) + [out]
        run(cmd)
        paths.append(out)
        if (i + 1) % 10 == 0 or i + 1 == len(shots):
            print("  plans %d/%d" % (i + 1, len(shots)), flush=True)
    if decursor:
        print("      curseur efface sur %d plans / %d" % (wiped, len(shots)),
              flush=True)
    return paths


def assemble(paths, shots, joins, fps, enc, work, quality):
    """Chaine les plans par xfade ; une transition d'une trame vaut coupe franche."""
    mid = os.path.join(work, "cut.mp4")
    nf = [s["out_frames"] for s in shots]
    graph, total, last = jn.graph(nf, joins, fps)
    cmd = [FF, "-v", "error", "-y"]
    for p in paths:
        cmd += ["-i", p]
    if graph:
        cmd += ["-filter_complex", graph, "-map", last]
    else:
        cmd += ["-map", "0:v"]
    cmd += ["-frames:v", str(total), "-fps_mode", "cfr", "-r", str(fps)]
    cmd += enc_args(enc, quality) + [mid]
    run(cmd)
    return mid, total


def beat_fx(W, H, fps, bpm, strength=1.0, phase=0.0):
    """Effets globaux cales sur la grille : respiration, secousse, flash, chroma.

    Le zoom de repos est a 1.03 : sans cette marge, la secousse n'aurait nulle
    part ou aller et serait rabotee au bord de l'image.
    """
    p = 60.0 / bpm
    t = "(on/%.5f)" % fps
    # La phase compte : le montage peut demarrer avant le premier temps, et
    # sans elle le pouls global bat a cote de la musique.
    ph = "mod(%s-%.6f+%.6f,%.6f)" % (t, phase % p, p, p)
    z = "1.03+%.3f*exp(-%s*13)" % (0.045 * strength, ph)
    dx = "%.2f*sin(%s*44)*exp(-%s*10)" % (4.5 * strength, t, ph)
    dy = "%.2f*cos(%s*37)*exp(-%s*10)" % (3.2 * strength, t, ph)
    return [
        "zoompan=z='%s':x='iw/2-(iw/zoom/2)+%s':y='ih/2-(ih/zoom/2)+%s'"
        ":d=1:s=%dx%d:fps=%d" % (z, dx, dy, W, H, fps),
        "eq=brightness='%.3f*exp(-mod(t-%.6f+%.6f,%.6f)*18)':eval=frame"
        % (0.065 * strength, phase % p, p, p),
        "rgbashift=rh=-%d:bh=%d:enable='lt(mod(t-%.6f+%.6f,%.6f),0.05)'"
        % (int(4 * strength) or 1, int(4 * strength) or 1,
           phase % (p * 4), p * 4, p * 4),
    ]


def title_filters(title, W, H, hits, dur):
    """Cartons titre : apparition nette, respiration, sortie rapide."""
    if not title:
        return []
    out, fs = [], fit_size(title, W * 0.86, H * 0.085)
    for t0 in hits:
        if t0 > dur - 0.5:
            continue
        a = ("if(lt(t,%.3f),0,if(lt(t,%.3f),(t-%.3f)/0.05,"
             "if(lt(t,%.3f),1,max(0,1-(t-%.3f)/0.18))))"
             % (t0, t0 + 0.05, t0, t0 + 0.75, t0 + 0.75))
        y = ("h*0.44-%d*exp(-(t-%.3f)*9)*sin((t-%.3f)*26)"
             % (int(H * 0.012), t0, t0))
        out.append("drawtext=fontfile='%s':text='%s':fontcolor=white:fontsize=%d"
                   ":borderw=%d:bordercolor=black@0.85:x=(w-tw)/2:y='%s'"
                   ":alpha='%s':enable='between(t,%.3f,%.3f)'"
                   % (IMPACT, esc(title), fs, max(3, fs // 14), y, a,
                      t0, t0 + 1.0))
    return out


def outro_text(txt, W, H, t0, dur):
    """Carton de fin typographique : monte, s'installe, reste jusqu'au bout."""
    if not txt:
        return []
    fs = fit_size(txt, W * 0.82, H * 0.105)
    a = ("if(lt(t,%.3f),0,min(1,(t-%.3f)/0.28))" % (t0, t0))
    y = ("h*0.46-%d*(1-min(1,(t-%.3f)/0.45))" % (int(H * 0.035), t0))
    return ["drawtext=fontfile='%s':text='%s':fontcolor=white:fontsize=%d"
            ":borderw=%d:bordercolor=black@0.9:x=(w-tw)/2:y='%s'"
            ":alpha='%s':enable='gte(t,%.3f)'"
            % (IMPACT, esc(txt), fs, max(4, fs // 13), y, a, t0)]


def finish(mid, audio, t0, dur, out, W, H, fps, bpm, enc, title, hits, grain,
           quality, fx, maxrate=16, logo="", outro="", t_outro=None, phase=0.0):
    vf = beat_fx(W, H, fps, bpm, fx, phase=phase) if fx > 0 else []
    vf += [shotfx.grade(W, H, grain)] + title_filters(title, W, H, hits, dur)
    if t_outro is None:
        t_outro = max(0.0, dur - 3.0)
    if not logo:
        vf += outro_text(outro, W, H, t_outro, dur)
    af = ("afade=t=in:st=0:d=0.04,afade=t=out:st=%.3f:d=0.35"
          % max(0.0, dur - 0.35))
    cmd = [FF, "-v", "error", "-y", "-i", mid,
           "-ss", "%.3f" % t0, "-t", "%.3f" % dur, "-i", audio]
    if logo:
        # Le logo est pose apres l'etalonnage : ni grain ni vignetage dessus,
        # il doit rester net alors que l'image, elle, est travaillee.
        cmd += ["-loop", "1", "-i", logo]
        lw = int(W * 0.80) & ~1
        vgfmt = ""
        if has_alpha(logo):
            lg = ("[2:v]fps=%d,scale=%d:-1:flags=lanczos,format=rgba,"
                  "fade=t=in:st=%.3f:d=0.45:alpha=1[lg]" % (fps, lw, t_outro))
            mix = ("[vg][lg]overlay=(W-w)/2:(H-h)/2"
                   ":enable='gte(t,%.3f)'[v]" % t_outro)
        else:
            # Sans alpha, le logo arrive sur fond noir : une incrustation
            # simple collerait un rectangle noir sur l'image. En fusion
            # "screen" le noir n'ajoute rien et seul le logo ressort -- et
            # comme le flux reste noir avant son apparition, le fondu d'entree
            # suffit a gerer le minutage, sans filtre de plus.
            # La fusion se fait en RVB, jamais en YUV : "screen" appliquee aux
            # canaux de chrominance est un non-sens (un gris neutre a 128
            # ressort a 192) et teinte toute l'image en magenta.
            vgfmt = ",format=gbrp"
            lg = ("[2:v]fps=%d,scale=%d:-1:flags=lanczos,"
                  "pad=%d:%d:(ow-iw)/2:(oh-ih)/2:black,"
                  "fade=t=in:st=%.3f:d=0.45,format=gbrp[lg]"
                  % (fps, lw, W, H, t_outro))
            mix = ("[vg][lg]blend=all_mode=screen:shortest=1,"
                   "format=yuv420p[v]")
        # On assombrit un peu le fond pendant le carton, sinon le logo se perd
        # dans un plan clair.
        dim = ("eq=brightness='-0.15*min(1,max(0,(t-%.3f)/0.6))':eval=frame"
               % t_outro)
        graph = "[0:v]%s,%s%s[vg];%s;%s;[1:a]%s[a]" % (
            ",".join(vf), dim, vgfmt, lg, mix, af)
    else:
        graph = "[0:v]%s[v];[1:a]%s[a]" % (",".join(vf), af)
    cmd += ["-filter_complex", graph,
            "-map", "[v]", "-map", "[a]", "-t", "%.3f" % dur]
    cmd += enc_args(enc, quality, maxrate=maxrate) + [
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    run(cmd)


# --------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--clips", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dur", type=float, default=30.0)
    ap.add_argument("--start", default="auto",
                    help="auto (1er gros drop), secondes, ou drop:N")
    ap.add_argument("--res", default="1080x1920")
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--bpm", type=float, default=0.0, help="force le tempo")
    ap.add_argument("--prior-bpm", type=float, default=140.0)
    ap.add_argument("--title", default="")
    ap.add_argument("--logo", default="",
                    help="image incrustee en fin de montage (png transparent)")
    ap.add_argument("--outro", default="",
                    help="carton de fin typographique, si aucun --logo")
    ap.add_argument("--outro-at", type=float, default=3.0,
                    help="secondes avant la fin ou le carton apparait")
    ap.add_argument("--credits", default="", help="json {fichier: '@pseudo'}")
    ap.add_argument("--grain", type=float, default=6.0)
    ap.add_argument("--fx", type=float, default=1.0,
                    help="intensite des effets globaux (0 = aucun)")
    ap.add_argument("--ref", default="",
                    help="video dont on recopie le rythme de montage "
                         "(longueurs de plan en temps, part de fondus)")
    ap.add_argument("--fluid", type=float, default=0.70,
                    help="part d'enchainements fondus plutot que de coupes")
    ap.add_argument("--sun", type=float, default=0.9,
                    help="poids donne aux plans a contre-jour")
    ap.add_argument("--water", type=float, default=0.0,
                    help="poids donne aux plans d'eau (detecteur peu fiable)")
    ap.add_argument("--vista", type=float, default=1.4,
                    help="poids donne aux plans de paysage degage")
    ap.add_argument("--combat", type=float, default=0.0,
                    help="penalite combat (detecteur peu fiable : torches, "
                         "cascades et textes de zone le declenchent)")
    ap.add_argument("--no-decursor", action="store_true",
                    help="ne pas effacer le curseur de souris")
    ap.add_argument("--must", default="",
                    help="instants a inclure d'office : '826,1150' ou "
                         "'clip.mp4@826' si plusieurs sources")
    ap.add_argument("--min-gap", type=float, default=-1.0,
                    help="ecart minimal entre deux extraits d'un meme fichier")
    ap.add_argument("--no-autocrop", action="store_true")
    ap.add_argument("--maxrate", type=int, default=16)
    ap.add_argument("--min-quality", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--enc", default="auto", choices=["auto", "nvenc", "x264"])
    ap.add_argument("--preview", action="store_true", help="540x960, rendu rapide")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()

    W, H = (540, 960) if a.preview else [int(v) for v in a.res.split("x")]
    fps = 30 if a.preview else a.fps
    quality = 25 if a.preview else 19
    rng = random.Random(a.seed or None)
    enc = pick_encoder(a.enc)

    print("[1/6] analyse du morceau...", flush=True)
    an = beat.analyze(a.audio, prior_bpm=a.prior_bpm, force_bpm=a.bpm or None)
    beats, energy = an["beats"], an["energy"]
    print("      %.2f BPM, %d temps, %d drops, piste %.1fs"
          % (an["bpm"], len(beats), len(an["drops"]), an["dur"]), flush=True)

    if a.start == "auto":
        t_start = float(beats[an["drops"][0]]) if an["drops"] else float(beats[0])
    elif a.start.startswith("drop:"):
        n = min(int(a.start.split(":")[1]), len(an["drops"]) - 1)
        t_start = float(beats[an["drops"][n]])
    else:
        t_start = float(a.start)
    dur = min(a.dur, an["dur"] - t_start - 0.05)
    print("      depart %.2fs, duree %.2fs" % (t_start, dur), flush=True)

    print("[2/6] reperage des plans...", flush=True)
    files = scout.list_clips(a.clips)
    if not files:
        raise SystemExit("aucun clip video dans %s" % a.clips)
    scouts = []
    for f in files:
        crop = None
        if not a.no_autocrop:
            w, h = border.video_size(f)
            if w and h:
                c = border.detect(f, w, h)
                if c != (0, 0, w & ~1, h & ~1):
                    crop = c
                    print("      %s : bordures %d/%d/%d/%d coupees"
                          % (os.path.basename(f), c[1], h - c[1] - c[3],
                             c[0], w - c[0] - c[2]), flush=True)
        s = scout.Scout(f, crop=crop, w_sun=a.sun, w_water=a.water,
                        w_vista=a.vista, w_combat=a.combat)
        if s.dur > 0.6:
            scouts.append(s)
    if not scouts:
        raise SystemExit("aucun clip exploitable")
    good = [s for s in scouts if s.quality >= a.min_quality]
    weak = [s for s in scouts if s.quality < a.min_quality]
    if weak and len(good) >= 3:
        for s in weak:
            print("      ecarte : %s [%.2f]"
                  % (os.path.basename(s.path), s.quality), flush=True)
        scouts = good
    hud = float(np.mean([(s.parts["hud"] > 0.5).mean() for s in scouts]))
    print("      %d clips, %.1f min de matiere, %.0f %% avec HUD (ecarte)"
          % (len(scouts), sum(s.dur for s in scouts) / 60.0, 100 * hud),
          flush=True)

    weights, fluid, target = None, a.fluid, None
    if a.ref:
        import refrhythm
        rp = refrhythm.profile(a.ref)
        print(refrhythm.describe(rp), flush=True)
        weights, fluid, target = rp["weights"], rp["fluid"], rp["mean_beats"]

    t0, shots = plan_shots(an["bpm"], beats, energy, t_start, t_start + dur,
                           fps, rng, weights=weights, target_beats=target)
    joins = jn.plan_joins(shots, fps, rng, fluid=fluid)
    pads = jn.pads(shots, joins)
    gap = a.min_gap
    if gap < 0:                       # une seule longue source : on etale
        total = sum(s.dur for s in scouts)
        gap = float(np.clip(total / max(1, len(shots) * 2), 1.5, 25.0))
    for s in scouts:
        s.min_gap = gap
    must = []
    for item in [x.strip() for x in a.must.split(",") if x.strip()]:
        name, _, ts = item.rpartition("@")
        ci = 0
        if name:
            hits = [i for i, s in enumerate(scouts)
                    if os.path.basename(s.path).lower() == name.lower()]
            if not hits:
                raise SystemExit("--must : fichier introuvable : %s" % name)
            ci = hits[0]
        must.append((ci, float(ts)))
    if must:
        print("      %d instants imposes" % len(must), flush=True)
    shots = assign_clips(shots, scouts, pads, fps, rng, must=must)
    nfluid = sum(1 for j in joins if j.kind == "fluid")
    print("[3/6] %d plans, %.0f ms de moyenne, %d enchainements fondus / "
          "%d coupes, ecart mini %.1fs"
          % (len(shots), dur / max(1, len(shots)) * 1000, nfluid,
             len(joins) - nfluid, gap), flush=True)

    creds = json.load(open(a.credits, encoding="utf-8")) if a.credits else {}
    work = os.path.splitext(a.out)[0] + "_work"
    print("[4/6] rendu des plans...", flush=True)
    paths = render_shots(shots, scouts, creds, W, H, fps, enc, work, rng,
                         quality, decursor=not a.no_decursor)

    print("[5/6] raccords...", flush=True)
    mid, total = assemble(paths, shots, joins, fps, enc, work, quality)

    print("[6/6] effets globaux + etalonnage + son...", flush=True)
    hits = []
    if a.title:
        hits = [0.08] + [float(beats[d]) - t0 for d in an["drops"]
                         if 0.5 < float(beats[d]) - t0 < dur]
    if a.logo and not os.path.exists(a.logo):
        raise SystemExit("--logo : fichier introuvable : %s" % a.logo)
    fdur = min(dur, total / float(fps))
    # Phase du premier temps par rapport au debut du montage : les effets
    # globaux doivent battre avec la musique, pas avec le zero du fichier.
    later = np.nonzero(beats >= t0 - 1e-6)[0]
    fx_phase = float(beats[later[0]] - t0) if len(later) else 0.0
    # Le carton de fin est cale sur un temps : sinon il apparait entre deux
    # frappes et se decolle visiblement du reste du montage.
    want = max(0.0, fdur - a.outro_at)
    per = 60.0 / an["bpm"]
    t_outro = round(want / per) * per if per > 0 else want
    finish(mid, a.audio, t0, fdur, a.out, W, H, fps,
           an["bpm"], enc, a.title, hits, a.grain, quality, a.fx,
           maxrate=6 if a.preview else a.maxrate,
           logo=a.logo, outro=a.outro, t_outro=min(t_outro, fdur - 0.4),
           phase=fx_phase)
    if not a.keep:
        shutil.rmtree(work, ignore_errors=True)
    print("OK -> %s" % a.out, flush=True)


if __name__ == "__main__":
    main()
