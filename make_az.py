"""Derive build_az.py (Alcaz Prison info short) from build_ex.py."""
s = open('build_ex.py', encoding='utf-8').read()


def sub(a, b):
    global s
    assert a in s, a
    s = s.replace(a, b, 1)


sub("WORK = os.path.join(HERE, 'build_ex')", "WORK = os.path.join(HERE, 'build_az')")
sub('FILES = [V + "14.21.48.04.mp4", V + "14.27.59.05.mp4", V + "14.30.41.06.mp4"]',
    'FILES = [V + "15.56.53.07.mp4", V + "15.59.25.08.mp4"]')
sub("MUSIC = os.path.join(HERE, 'music_wl', 'wl_1.mp3')", "MUSIC = os.path.join(HERE, 'music_wc', 'wc_mists_2.mp3')")
# UI is visible in these captures: crop above the action bar, clear of unit frames
sub("CROP = 'crop=759:1350:2180:30'", "CROP = 'crop=675:1200:2222:30'")
i = s.index('SHOTS = ['); j = s.index('# world map inside')
s = s[:i] + '''SHOTS = [
    ('1@27.4', 2.2),                   # 0 hook: the portal
    ('1@2.4', 3.0),                    # 1 title: jungle ruins
    ('0@14.2', 5.5, 'map'),            # 2 map (frozen)
    ('0@3.0', 2.3),                   # 3 the pier
    ('1@0.4', 2.4),                    # 4 the island
    ('1@5.0', 2.5), ('1@7.0', 2.2),    # 5-6 steps to the gate
    ('1@13.4', 2.3), ('1@22.4', 2.5),  # 7-8 inside, the portal
    ('1@24.6', 5.4),                   # 9 info card
    ('1@27.9', 1.8, 'slow'),           # 10 portal slow
    ('1@32.0', 2.4), ('1@38.4', 3.6),  # 11-12 first look inside + outro
]
''' + s[j:]
sub("PIN = (2524, 828)", "PIN = (3036, 300)")
i = s.index("    ovs.append((big_text([('NEW DUNGEON'"); j = s.index("    music = os.path.join(WORK, 'music.wav')")
s = s[:i] + '''    ovs.append((big_text([('NEW DUNGEON', C, 150, 900, BONE, 8), ('WHERE IS IT?', C, 96, 900, SICK, 8)], 330, 'hook'), 0, h0, 0, 0.12))
    ovs.append((wp, h0 - 0.04, h0 + 0.35, 0.04, 0.3))
    ovs.append((big_text([('ALCAZ', C, 170, 900, BONE, 10), ('PRISON', C, 96, 900, GOLD, 16),
                          ('Level 48-53  ·  WoW Forever', G, 48, None, SICK, 0)], 740, 'title'), h0 + 0.1, h0 + 2.9, 0.3, 0.4))
    ms, md = tl[2]
    fh = round(MAP_H * 1080 / MAP_W / 2) * 2
    px = (PIN[0] - MAP_X) * 1080 / MAP_W; py = (1920 - fh) / 2 + (PIN[1] - MAP_Y) * 1080 / MAP_W
    ovs.append((pin_png(px, py), ms + 0.3, ms + md, 0.25, 0.2))
    ovs.append((info_png([('ZONE', 'Dustwallow Marsh'), ('ISLAND', 'Alcaz Island (NE coast)'), ('COORDS', '74.9, 14.9'),
                          ('LEVEL', '48 - 53')], 1400, 'info'), ms + 0.9, ms + md, 0.35, 0.2))
    steps = [(3, 3, '1.  Head to the pier\\nnear 70, 19.'),
             (4, 4, '2.  Cross over to Alcaz Island.'),
             (5, 6, '3.  Climb the steps\\nto the old prison gate.'),
             (7, 8, '4.  The portal waits deep inside.')]
    for a_, b_, txt in steps:
        ovs.append((B.caption_png(txt, f'step{a_}'), tl[a_][0] + 0.2, tl[b_][0] + tl[b_][1] - 0.15, 0.25, 0.25))
    bs, bd = tl[9]
    ovs.append((info_png([('ZONE', 'Dustwallow Marsh'), ('COORDS', '74.9, 14.9'), ('LEVEL', '48 - 53'),
                          ('BOSSES', 'Not revealed yet')], 760, 'card2', title='ALCAZ PRISON'), bs + 0.2, bs + bd, 0.35, 0.3))
    sp_, dp = tl[10]
    ovs.append((wp, sp_ + dp - 0.5, sp_ + dp + 0.4, 0.3, 0.35))
    o0 = tl[11][0]
    ovs.append((big_text([('ALCAZ PRISON', C, 120, 900, BONE, 6), ('Dustwallow Marsh  ·  74.9, 14.9', G, 50, None, SICK, 0),
                          ('Level 48-53', G, 50, None, SICK, 0), ('SAVE THIS FOR YOUR RUN', C, 52, 800, GOLD, 6)],
                         700, 'outro'), o0 + 0.4, total, 0.5, 0.9))

''' + s[j:]
s = s.replace('"EXCAVATION SITE"', '"ALCAZ PRISON"')
open('build_az.py', 'w', encoding='utf-8').write(s)
print('ok')
