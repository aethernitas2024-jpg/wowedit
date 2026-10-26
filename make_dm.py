"""Derive build_dm.py (Deadmines comedy short) from build.py (Ruins of Lordaeron v2)."""
import re
s = open('build.py', encoding='utf-8').read()


def sub(a, b, count=1):
    global s
    assert a in s, a
    s = s.replace(a, b, count)


V = r'C:\Users\d2460n\Videos\World Of Warcraft\World Of Warcraft 2026.09.22 - '
sub("WORK = os.path.join(HERE, 'build')", "WORK = os.path.join(HERE, 'build_dm')")
sub("'lordaeron_short.mp4'", "'deadmines_short.mp4'")
sub("MUS = os.path.join(HERE, 'music')",
    "MUS = os.path.join(HERE, 'music')\n"
    "SONG = r'C:\\Users\\d2460n\\Downloads\\Welcome to the Deadmines (Rise to Power 2010 Winner).mp3'\n"
    "SONG_START = 38.0\n"
    f"FILES = [r'{V}08.54.06.12.mp4', r'{V}09.01.44.13.mp4', r'{V}09.12.55.14.mp4', r'{V}09.14.01.15.mp4']")

bosses = r'''BOSSES = [
    dict(num='I', name="RHAHK'ZOR", lvl=19, kind='The Foreman',
         joke='Management style: punching.', shots=[
        (30, 2.5), (34, 2.5), (41, 2.2), (51, 2.5), (59.2, 2.2, 'kill', 60.3)]),
    dict(escort=True, name='THE MINE TOUR', top='MEANWHILE', sub='Keep your hands inside the mine cart.', shots=[
        ('1@24', 2.5), ('1@96', 2.5), ('1@324', 2.5), ('2@40', 2.5), (170, 2.0)]),
    dict(num='II', name='SNEED', lvl=20, kind='Lumbermaster',
         joke="Brought a shredder to a sword fight.\nLost the shredder too.", shots=[
        (241, 2.5), (268, 2.2), (277, 2.2), (287.6, 2.2, 'kill', 288.7)]),
    dict(num='III', name='GILNID', lvl=20, kind='The Smelter', shots=[
        (655, 2.2), (670.8, 2.2, 'kill', 671.6)]),
    dict(escort=True, name='THE FRONT DOOR', top='OBSTACLE', sub='Locked. Reinforced. Very rude.', shots=[
        (790.2, 1.6), (792.2, 2.6, 'boom', 793.0)]),
    dict(num='IV', name='MR. SMITE', lvl=20, kind="The Ship's First Mate",
         joke='Swaps weapons mid-fight.\nStill no dental plan.', shots=[
        (941, 2.5), (947, 2.5), (952, 2.5), (956, 2.5), (961, 2.0), (967, 2.5), (983.3, 2.2, 'kill', 984.4)]),
    dict(num='V', name='COOKIE', lvl=20, kind="The Ship's Cook",
         joke='A murloc chef.\nHealth inspection: failed.', shots=[
        (1363, 2.5), (1367, 2.5), (1373, 2.2), (1384.9, 2.2, 'kill', 1386.0)]),
    dict(num='VI', name='CAPTAIN GREENSKIN', lvl=21, kind='Pirate Captain',
         joke="Captain of a ship...\nthat can't leave a cave.", shots=[
        (1262, 2.5), (1266, 2.5), (1272, 2.2), (1283.2, 2.2, 'kill', 1284.3)]),
    dict(num='VII', name='EDWIN VANCLEEF', lvl=21, kind='Leader of the Defias', card_shot=1,
         lead='And now... the man himself.', joke='Still waiting on that paycheck.', shots=[
        (1309, 2.5), (1313, 2.5), (1318, 2.2), (1321, 2.2), (1326, 2.2), (1334.1, 2.4, 'kill', 1335.3)]),
]
NB = sum(1 for b in BOSSES if not b.get('escort'))
INTRO = [(48.5, 2.2), ('0@375', 2.8, 'still'), ('0@24', 2.5), ('0@36', 2.5), ('0@108', 2.5), ('1@216', 2.5), ('2@37', 2.5), ('0@156', 2.5), ('1@168', 2.5), ('2@21', 2.3)]  # [0] = hook
OUTRO = [(1352.5, 3.0), (1356, 3.5)]
'''
s = re.sub(r"BOSSES = \[\n.*?\]\nINTRO = .*?\nOUTRO = .*?\n", lambda m: bosses, s, count=1, flags=re.S)

# multi-file sources: '<file>@<t>' strings, plain numbers = main capture (file 3)
sub("    kill = 'kill' in flags\n",
    "    kill = 'kill' in flags or 'boom' in flags\n"
    "    fi = 3\n"
    "    if isinstance(src, str):\n"
    "        fi, src = src.split('@'); fi, src = int(fi), float(src)\n"
    "    IN = FILES[fi]\n")
sub("'colorbalance=rs=-0.02:gs=0.03:bs=0.02:rh=0.02:bh=-0.02'", "'colorbalance=rs=0.02:gs=0.0:bs=-0.02:rh=0.04:bh=-0.03'")

# Defias palette: red / gold instead of plague green
s = s.replace('(120, 200, 90, 255)', '(230, 110, 40, 255)')
s = s.replace('(150, 214, 120, 255)', '(242, 196, 96, 255)')
sub("SICK = (150, 214, 120, 255)", "SICK = (242, 196, 96, 255)") if 'SICK = (150' in s else None

sub("ROMAN[len(BOSSES)]", "ROMAN[NB]")
sub("DONE_TXT = f'{len(BOSSES)} / {len(BOSSES)}  BOSSES DEFEATED'", "DONE_TXT = f'{NB} / {NB}  BOSSES DEFEATED'")
sub("    n, gap, y = len(BOSSES), 70, 118", "    n, gap, y = NB, 70, 118")
sub("    lab = 'RUINS OF LORDAERON'", "    lab = 'THE DEADMINES'")
sub("""    top = f'BOSS  {b["num"]}  /  ' + ROMAN[NB]""",
    """    top = b['top'] if b.get('escort') else f'BOSS  {b["num"]}  /  ' + ROMAN[NB]""")
sub("""    sub = f'Level {b["lvl"]}  ·  {b["kind"]}'""",
    """    sub = b['sub'] if b.get('escort') else f'Level {b["lvl"]}  ·  {b["kind"]}'""")
s = s.replace("'LORDAERON'", "'DEADMINES'").replace("'THE RUINS OF'", "'THE'")
sub("f'Tirisfal Glades  ·  {len(BOSSES)} bosses'", "f'Westfall  ·  {NB} bosses  ·  1 cannon'")
s = s.replace("'6 BOSSES.'", "'7 BOSSES.'").replace("'ONE CURSED CITY.'", "'0 PAYCHECKS.'")
sub("'At the gates of the Undercity,\\nthe dead city never sleeps.'",
    "'The Defias: the masons who rebuilt\\nStormwind... and never got paid.'")
sub("'Six guardians. One way through.'", "'So they built a pirate ship.\\nInside a mine. As you do.'")

# progress: count only real bosses
sub("""        pp = os.path.join(WORK, f'prog_{k}.png'); progress_png(k, k).save(pp)""",
    """        bi = sum(1 for bb in BOSSES[:k] if not bb.get('escort'))
        pp = os.path.join(WORK, f'prog_{k}.png'); progress_png(bi, None if b.get('escort') else bi).save(pp)""")
sub("progress_png(len(BOSSES), None)", "progress_png(NB, None)")

# joke caption after the card, KABOOM on the cannon shot
sub("""        ovs.append((wp, c0, c0 + 0.45, 0.06, 0.38))
""", """        ovs.append((wp, c0, c0 + 0.45, 0.06, 0.38))
        ks = [x for x in segs if len(x['shot']) > 2 and x['shot'][2] in ('kill', 'boom')]
        je = (ks[0]['start'] if ks else c1) - 0.15
        if b.get('joke') and je - (cs + 3.8) > 1.2:
            ovs.append((caption_png(b['joke'], f'joke_{k}'), cs + 3.8, je, 0.3, 0.3))
""")
sub("""            if 'kill' in x['shot']:""", """            if 'boom' in x['shot']:
                kt = x['start'] + (x['shot'][3] - x['shot'][0]) / SLOW
                ovs.append((wp, kt - 0.03, kt + 0.7, 0.03, 0.6))
                ovs.append((boom_png(), kt, x['start'] + x['dur'] + 0.6, 0.04, 0.35))
            if 'kill' in x['shot']:""")
sub("    ovs.append((outro_png(), o0 + 0.6, total, 0.7, 1.0))\n",
    "    ovs.append((outro_png(), o0 + 0.6, total, 0.7, 1.0))\n"
    "    ovs.append((caption_png(\"Stormwind still hasn't paid them.\", 'final'), o0 + 2.2, total - 0.2, 0.4, 0.6))\n")

boom = '''def boom_png():
    """Comic-book KABOOM burst."""
    import math
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    cx, cy = W / 2, 820
    pts = []
    for i in range(28):
        a = i / 28 * 2 * math.pi
        r = 470 if i % 2 == 0 else 290
        r *= 1 + 0.08 * math.sin(i * 2.7)
        pts.append((cx + r * math.cos(a), cy + r * 0.78 * math.sin(a)))
    d = ImageDraw.Draw(im)
    d.polygon([(x + 12, y + 16) for x, y in pts], fill=(0, 0, 0, 200))
    d.polygon(pts, fill=(255, 214, 40, 255), outline=(20, 10, 0, 255), width=10)
    inner = [(cx + (x - cx) * 0.72, cy + (y - cy) * 0.72) for x, y in pts]
    d.polygon(inner, fill=(255, 120, 20, 255))
    f = fit(IMPACT, 'KABOOM!', 900, 230)
    txt = Image.new('RGBA', (W, 400), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt)
    td.text((W / 2, 200), 'KABOOM!', font=f, anchor='mm', fill=(255, 250, 225, 255), stroke_width=16, stroke_fill=(150, 0, 0, 255))
    txt = txt.rotate(8, resample=Image.BICUBIC, center=(W / 2, 200))
    im.alpha_composite(txt, (0, int(cy - 200)))
    p = os.path.join(WORK, 'boom.png'); im.save(p); return p


'''
sub("def white_png():", boom + "def white_png():")
sub("GEORGIA_I = r\"C:\\Windows\\Fonts\\georgiai.ttf\"", "GEORGIA_I = r\"C:\\Windows\\Fonts\\georgiai.ttf\"\nIMPACT = r\"C:\\Windows\\Fonts\\impact.ttf\"")

# music: the song from 0:38
s = re.sub(r"    run\(\[FF, '-v', 'error', '-y', '-i', os\.path\.join\(MUS, 'UndercityIntro\.mp3'\).*?music\]\)\n",
           lambda m: "    run([FF, '-v', 'error', '-y', '-ss', str(SONG_START), '-i', SONG, '-af',\n"
                     "         f'atrim=0:{total},asetpts=PTS-STARTPTS,afade=t=in:d=0.2,afade=t=out:st={total - 3}:d=3,aresample=48000',\n"
                     "         '-ac', '2', music])\n", s, count=1, flags=re.S)
assert 'SONG_START), ' in s
open('build_dm.py', 'w', encoding='utf-8').write(s)
print('ok')

# shorter cap2 + a third intro line (re-applied on the generated file)
g = open('build_dm.py', encoding='utf-8').read()
a = "'cap2'), hook_end + 5.8, intro_end - 0.2, 0.35, 0.4))\n"
assert a in g
g = g.replace(a, "'cap2'), hook_end + 5.8, hook_end + 9.8, 0.35, 0.4))\n"
              "    ovs.append((caption_png('Business was booming.\\nThen the adventurers showed up.', 'cap3'), hook_end + 11.0, hook_end + 15.8, 0.35, 0.4))\n")
open('build_dm.py', 'w', encoding='utf-8').write(g)
print('captions ok')
