"""Derive build_ex.py (Excavation Site: Wetlands info short) from build_st.py."""
s = open('build_st.py', encoding='utf-8').read()


def sub(a, b):
    global s
    assert a in s, a
    s = s.replace(a, b, 1)


sub("WORK = os.path.join(HERE, 'build_st')", "WORK = os.path.join(HERE, 'build_ex')")
i = s.index('IN = r"'); j = s.index('\n', i)
s = s[:i] + 'V = r"C:\\Users\\d2460n\\Videos\\World Of Warcraft\\World Of Warcraft 2026.09.22 - "\n' \
    'FILES = [V + "14.21.48.04.mp4", V + "14.27.59.05.mp4", V + "14.30.41.06.mp4"]' + s[j:]
sub("MUSIC = os.path.join(HERE, 'music_ug', 'ungoro_1.mp3')", "MUSIC = os.path.join(HERE, 'music_wl', 'wl_1.mp3')")
i = s.index('SHOTS = ['); j = s.index('# world map inside')
s = s[:i] + '''SHOTS = [
    ('2@19.6', 2.2),                 # 0 hook: into the portal
    ('2@12.2', 3.0),                 # 1 title
    ('2@38.6', 5.5, 'map'),          # 2 map (frozen frame)
    ('2@40.4', 2.4), ('2@13.8', 2.6),  # 3-4 approach
    ('2@15.6', 2.6), ('2@17.4', 2.0),  # 5-6 portal
    ('2@21.0', 5.6),                 # 7 bosses list
    ('2@23.5', 2.0, 'slow'),         # 8 portal slow
    ('2@41.6', 3.4), ('2@28.4', 3.6),  # 9-10 outro
]
''' + s[j:]
sub("PIN = (2598, 186)", "PIN = (2524, 828)")
sub("    src, dur = s[0], s[1]\n", "    src, dur = s[0], s[1]\n    fi, src = src.split('@'); IN = FILES[int(fi)]; src = float(src)\n")
# frozen map frame
sub("fc = (f'[0:v]crop=2406:1350:1356:30,", "fc = (f'[0:v]trim=end_frame=1,loop=loop=-1:size=1,setpts=N/60/TB,split[a0][b0];[a0]crop=2406:1350:1356:30,")
sub("f'[0:v]crop={MAP_W}:{MAP_H}:{MAP_X}:{MAP_Y},", "f'[b0]crop={MAP_W}:{MAP_H}:{MAP_X}:{MAP_Y},")
sub("run([FF, '-v', 'error', '-y', '-ss', str(src), '-t', str(dur), '-i', IN, '-filter_complex', fc, '-map', '[v]', '-map', '0:a',",
    "run([FF, '-v', 'error', '-y', '-ss', str(src), '-i', IN, '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-filter_complex', fc, '-map', '[v]', '-map', '1:a', '-t', str(dur),")
# overlays
i = s.index("    ovs.append((big_text([('NEW DUNGEON'"); j = s.index("    music = os.path.join(WORK, 'music.wav')")
s = s[:i] + '''    ovs.append((big_text([('NEW DUNGEON', C, 150, 900, BONE, 8), ('WHERE IS IT?', C, 96, 900, SICK, 8)], 330, 'hook'), 0, h0, 0, 0.12))
    ovs.append((wp, h0 - 0.04, h0 + 0.35, 0.04, 0.3))
    ovs.append((big_text([('EXCAVATION SITE', C, 64, 700, GOLD, 10), ('WETLANDS', C, 170, 900, BONE, 8),
                          ('Level 22-35  ·  WoW Forever', G, 48, None, SICK, 0)], 760, 'title'), h0 + 0.1, h0 + 2.9, 0.3, 0.4))
    ms, md = tl[2]
    fh = round(MAP_H * 1080 / MAP_W / 2) * 2
    px = (PIN[0] - MAP_X) * 1080 / MAP_W; py = (1920 - fh) / 2 + (PIN[1] - MAP_Y) * 1080 / MAP_W
    ovs.append((pin_png(px, py), ms + 0.3, ms + md, 0.25, 0.2))
    ovs.append((info_png([('ZONE', 'Wetlands'), ('COORDS', '48.1, 56.5'), ('AREA', 'South highlands, W of Dun Algaz'),
                          ('LEVEL', '22 - 35'), ('BOSSES', '4')], 1400, 'info'), ms + 0.9, ms + md, 0.35, 0.2))
    ovs.append((B.caption_png('Look for the lanterns\\nof the dig site...', 'c1'), tl[3][0] + 0.25, tl[4][0] + tl[4][1] - 0.2, 0.3, 0.3))
    ovs.append((B.caption_png('...the portal glows blue\\nunder the trees.', 'c2'), tl[5][0] + 0.25, tl[6][0] + tl[6][1] - 0.2, 0.3, 0.3))
    bs, bd = tl[7]
    ovs.append((info_png([('BOSS I', 'Saltspine'), ('BOSS II', 'Shadetooth'), ('BOSS III', 'Highland Horror'),
                          ('BOSS IV', 'Relic Guardian')], 760, 'bosses', title='THE BOSSES'), bs + 0.2, bs + bd, 0.35, 0.3))
    sp_, dp = tl[8]
    ovs.append((wp, sp_ + dp - 0.5, sp_ + dp + 0.4, 0.3, 0.35))
    o0 = tl[9][0]
    ovs.append((big_text([('EXCAVATION SITE', C, 60, 800, GOLD, 8), ('WETLANDS', C, 130, 900, BONE, 6), ('Wetlands  ·  48.1, 56.5', G, 50, None, SICK, 0),
                          ('Level 22-35  ·  4 bosses', G, 50, None, SICK, 0), ('SAVE THIS FOR YOUR RUN', C, 52, 800, GOLD, 6)],
                         680, 'outro'), o0 + 0.5, total, 0.6, 0.9))

''' + s[j:]
s = s.replace('"THE SHAPER\'S TERRACE"', '"EXCAVATION SITE"')
sub("def info_png(rows, y, name):", "def info_png(rows, y, name, title=None):")
sub("    d.rounded_rectangle([90, y, W - 90, y + 70 + 78 * len(rows)], 26,",
    "    if title:\n        ft = B.font(B.CINZEL, 58, 900); d.text((W / 2, y - 90), title, font=ft, fill=B.BONE, anchor='ma')\n"
    "    d.rounded_rectangle([90, y, W - 90, y + 70 + 78 * len(rows)], 26,")
sub("d.text((400, yy), val, font=fv,", "d.text((380, yy), val, font=B.fit(B.GEORGIA_I, val, 580, 46),")
open('build_ex.py', 'w', encoding='utf-8').write(s)
print('ok')
