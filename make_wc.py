"""Derive build_wc.py (Wailing Caverns short) from build.py (Ruins of Lordaeron)."""
import re
s = open('build.py', encoding='utf-8').read()

def sub(a, b, count=1):
    global s
    assert a in s, a
    s = s.replace(a, b, count)

sub('World Of Warcraft 2026.09.21 - 15.05.07.08.mp4', 'World Of Warcraft 2026.09.21 - 23.57.05.09.mp4')
sub("WORK = os.path.join(HERE, 'build')", "WORK = os.path.join(HERE, 'build_wc')")
sub("MUS = os.path.join(HERE, 'music')", "MUS = os.path.join(HERE, 'music_wc')")
sub("'lordaeron_short.mp4'", "'wailing_caverns_short.mp4'")

bosses = '''BOSSES = [
    dict(num='I', name='LADY ANACONDRA', lvl=20, kind='Fang Lord', shots=[
        (268, 3), (271, 2.5), (280, 2.5), (289, 2.5), (298.0, 2.4, 'kill', 299.2)]),
    dict(num='II', name='LORD COBRAHN', lvl=20, kind='Fang Lord', shots=[
        (825, 2.5), (827, 3), (832, 2.5), (842, 2.5), (844.0, 2.4, 'kill', 845.2)]),
    dict(num='III', name='KRESH', lvl=20, kind='Giant Turtle', shots=[
        (934, 3), (938, 2.5), (950, 2.5), (952.5, 2.5), (958.0, 2.4, 'kill', 959.2)]),
    dict(num='IV', name='LORD PYTHAS', lvl=21, kind='Fang Lord', shots=[
        (1348, 3), (1351, 2.5), (1359, 2.5), (1369, 2.5), (1375.8, 2.4, 'kill', 1377.0)]),
    dict(num='V', name='SKUM', lvl=21, kind='Thunder Lizard', shots=[
        (1952, 3), (1958, 2.5), (1961, 2.5), (1965, 2.5), (1980.5, 2.4, 'kill', 1981.7)]),
    dict(num='VI', name='LORD SERPENTIS', lvl=21, kind='Fang Lord', shots=[
        (2124, 2.5), (2127, 3), (2131, 2.5), (2140, 2.5), (2148.0, 2.4, 'kill', 2149.2)]),
    dict(num='VII', name='VERDAN THE EVERLIVING', lvl=21, kind='Ancient Lasher', shots=[
        (2189, 3), (2194, 2.5), (2202, 2.5), (2218, 2.5), (2223.8, 2.4, 'kill', 2225.0)]),
    dict(escort=True, name='THE AWAKENING', top='ESCORT EVENT', sub='Protect the Disciple of Naralex', card_shot=1,
         lead='Now wake the dreamer...', shots=[
        (2292, 2.5), (2348, 3), (2368, 2.5), (2458, 2.5), (2478, 2.5),
        (2615, 2.5), (2644, 2.5), (2701, 2.5), (2749, 2.5)]),
    dict(num='VIII', name='MUTANUS THE DEVOURER', lvl=22, kind='Final Boss', card_shot=1,
         lead='...but the Nightmare answers.', shots=[
        (2790, 2.5), (2794, 3), (2800, 2.5), (2806, 2.5), (2814, 2.5), (2826, 2.5), (2832.3, 2.4, 'kill', 2833.5)]),
]
NB = sum(1 for b in BOSSES if not b.get('escort'))
INTRO = [(2804, 2.0), (9, 2.6, 'still'), (20, 2.5), (44, 2.5), (76, 2.5)]  # [0] = hook
OUTRO = [(2845, 3.5), (2856, 4.0)]
'''
s = re.sub(r"BOSSES = \[\n.*?\]\nINTRO = .*?\nOUTRO = .*?\n", lambda m: bosses, s, count=1, flags=re.S)

sub("ROMAN[len(BOSSES)]", "ROMAN[NB]")
sub("DONE_TXT = f'{len(BOSSES)} / {len(BOSSES)}  BOSSES DEFEATED'", "DONE_TXT = f'{NB} / {NB}  BOSSES DEFEATED'")
sub("    n, gap, y = len(BOSSES), 70, 118", "    n, gap, y = NB, 64, 118")
sub("    lab = 'RUINS OF LORDAERON'", "    lab = 'WAILING CAVERNS'")
# boss card: escort variant
sub("""    top = f'BOSS  {b["num"]}  /  ' + ROMAN[NB]""",
    """    top = b['top'] if b.get('escort') else f'BOSS  {b["num"]}  /  ' + ROMAN[NB]""")
sub("""    sub = f'Level {b["lvl"]}  ·  {b["kind"]}'""",
    """    sub = b['sub'] if b.get('escort') else f'Level {b["lvl"]}  ·  {b["kind"]}'""")
# title / outro / hook texts
for fn in ('title', 'outro'):
    pass
s = s.replace("'LORDAERON'", "'WAILING CAVERNS'")
s = s.replace("'THE RUINS OF'", "'THE'")
sub("f'Tirisfal Glades  ·  {len(BOSSES)} bosses'", "f'The Barrens  ·  {NB} bosses'")
s = s.replace("'6 BOSSES.'", "'8 BOSSES.'").replace("'ONE CURSED CITY.'", "'ONE NIGHTMARE.'")
sub("'At the gates of the Undercity,\\nthe dead city never sleeps.'", "'Deep in the Barrens,\\na druid dreams a nightmare.'")
sub("'Six guardians. One way through.'", "'Eight guardians stand in the way.'")
# progress: count only real bosses
sub("""        pp = os.path.join(WORK, f'prog_{k}.png'); progress_png(k, k).save(pp)""",
    """        bi = sum(1 for bb in BOSSES[:k] if not bb.get('escort'))
        pp = os.path.join(WORK, f'prog_{k}.png'); progress_png(bi, None if b.get('escort') else bi).save(pp)""")
sub("progress_png(len(BOSSES), None)", "progress_png(NB, None)")
# music: EnchantedForest01 -> 03 (long) -> 05
sub("'UndercityIntro.mp3'", "'wc_main_1.mp3'")
sub("'Undercity02.mp3'", "'wc_main_2.mp3'")
sub("'Undercity01.mp3'", "'wc_main_3.mp3'")
sub("atrim=0:{intro_end + cf - 0.2}", "atrim=0:79.5")
open('build_wc.py', 'w', encoding='utf-8').write(s)
print('ok')
