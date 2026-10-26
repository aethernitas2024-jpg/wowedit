"""Short teaser: entrance of The Shaper's Terrace (WoW Forever, Un'Goro Crater, lvl 58-60), Un'Goro music."""
import os, sys, json, subprocess
from PIL import Image, ImageDraw, ImageFilter
import build as B

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'build_st'); os.makedirs(WORK, exist_ok=True)
B.WORK = WORK
FF, W, H, FPS = B.FF, B.W, B.H, 60
IN = r"C:\Users\d2460n\Videos\World Of Warcraft\World Of Warcraft 2026.09.22 - 12.02.46.02.mp4"
MUSIC = os.path.join(HERE, 'music_ug', 'ungoro_1.mp3')
OUT = sys.argv[1]
CROP = 'crop=759:1350:2180:30'      # inside the game window (1356..3762 x 30..1380) of the 5120x1440 desktop capture
SLOW = 0.5

# (src, dur, flag)
SHOTS = [
    (43.3, 2.2),                     # 0 hook: the portal
    (27.8, 3.0),                     # 1 title
    (4.3, 5.0, 'map'),               # 2 world map
    (22.5, 2.5), (24.2, 2.4),        # 3-4 jungle path
    (30.4, 2.5), (35.8, 2.6),        # 5-6 stairs
    (38.4, 2.4), (40.6, 2.4),        # 7-8 titan gate
    (44.0, 1.8, 'slow'),             # 9 into the portal
    (46.0, 2.2),                     # 10 glimpse inside
    (52.2, 2.4), (62.0, 4.2),        # 11-12 outro
]
# world map inside the game window (source px) and player marker
MAP_X, MAP_Y, MAP_W, MAP_H = 1606, 110, 1910, 1270
PIN = (2598, 186)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2500:]); raise SystemExit(1)


def render(i, s):
    src, dur = s[0], s[1]
    slow = len(s) > 2 and s[2] == 'slow'
    out = os.path.join(WORK, f'shot_{i:02d}.mp4')
    od = dur / SLOW if slow else dur
    if len(s) > 2 and s[2] == 'map':
        fh = round(MAP_H * 1080 / MAP_W / 2) * 2
        fc = (f'[0:v]crop=2406:1350:1356:30,scale=-2:1920,crop=1080:1920,boxblur=40:2,eq=brightness=-0.18[bg];'
              f'[0:v]crop={MAP_W}:{MAP_H}:{MAP_X}:{MAP_Y},scale=1080:{fh}:flags=lanczos,unsharp=5:5:0.6[fg];'
              f'[bg][fg]overlay=0:(H-h)/2,fps=60,format=yuv420p[v]')
        run([FF, '-v', 'error', '-y', '-ss', str(src), '-t', str(dur), '-i', IN, '-filter_complex', fc, '-map', '[v]', '-map', '0:a',
             '-c:v', 'h264_nvenc', '-preset', 'p5', '-rc', 'vbr', '-cq', '16', '-b:v', '0', '-c:a', 'aac', '-b:a', '256k', '-ac', '2', out])
        return out, round(dur * FPS) / FPS
    vf = [CROP]
    if slow:
        vf += [f'setpts=PTS/{SLOW}', 'minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1']
    z = 0.02
    vf += ['scale=1080:1920:flags=lanczos', 'fps=60',
           f"scale=w='trunc(1080*(1+{z}*t)/2)*2':h=-2:eval=frame:flags=bicubic", 'crop=1080:1920',
           'eq=gamma=1.18:contrast=1.08:saturation=1.15', 'colorbalance=rs=-0.02:gs=0.02:bs=0.03:rh=0.03:bh=-0.02',
           'unsharp=5:5:0.5', 'format=yuv420p']
    af = (['atempo=0.5'] if slow else []) + ['aresample=48000']
    run([FF, '-v', 'error', '-y', '-ss', str(src), '-t', str(dur), '-i', IN, '-vf', ','.join(vf), '-af', ','.join(af),
         '-t', str(od), '-c:v', 'h264_nvenc', '-preset', 'p5', '-rc', 'vbr', '-cq', '16', '-b:v', '0',
         '-c:a', 'aac', '-b:a', '256k', '-ac', '2', out])
    return out, round(od * FPS) / FPS


def big_text(lines, y, name, glow=(120, 200, 90, 255), back=True):
    """lines: [(text, font_path, size, weight, fill, spacing)]"""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if back:
        B.backdrop(im, y + 120, 620, 260, 185)
    d = ImageDraw.Draw(im)
    yy = y
    for txt, fp, size, wg, fill, sp in lines:
        f = B.fit(fp, txt, 1000, size, wg, spacing=sp)
        if size >= 100:
            im.alpha_composite(B.glow_layer(lambda dd, v, t=txt, f=f, yy=yy, sp=sp: B.draw_spaced(dd, (W / 2, yy), t, f, v, spacing=sp), 24, glow))
            d = ImageDraw.Draw(im)
            B.draw_spaced(d, (W / 2 + 5, yy + 6), txt, f, (0, 0, 0, 220), spacing=sp)
        B.draw_spaced(d, (W / 2, yy), txt, f, fill, spacing=sp)
        yy += f.getbbox('Ag')[3] + 26
    p = os.path.join(WORK, name + '.png'); im.save(p); return p


def pin_png(px, py):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for r, a in ((70, 90), (52, 160)):
        d.ellipse([px - r, py - r, px + r, py + r], outline=(255, 70, 40, a), width=8)
    d.ellipse([px - 14, py - 14, px + 14, py + 14], fill=(255, 70, 40, 255))
    lx, ly = px, py + 150
    d.line([(px, py + 70), (lx, ly - 10)], fill=(255, 220, 120, 255), width=5)
    f = B.fit(B.CINZEL, "THE SHAPER'S TERRACE", 900, 60, 900, spacing=3)
    bw = B.text_w(f, "THE SHAPER'S TERRACE", 3) + 60
    d.rounded_rectangle([W / 2 - bw / 2, ly, W / 2 + bw / 2, ly + 90], 16, fill=(10, 14, 8, 225), outline=(214, 180, 104, 255), width=3)
    B.draw_spaced(d, (W / 2, ly + 12), "THE SHAPER'S TERRACE", f, B.BONE, spacing=3)
    p = os.path.join(WORK, 'pin.png'); im.save(p); return p


def info_png(rows, y, name):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([90, y, W - 90, y + 70 + 78 * len(rows)], 26, fill=(8, 12, 8, 215), outline=(214, 180, 104, 230), width=3)
    fk = B.font(B.CINZEL, 40, 800); fv = B.font(B.GEORGIA_I, 46)
    for k, (key, val) in enumerate(rows):
        yy = y + 40 + 78 * k
        d.text((140, yy + 6), key, font=fk, fill=B.GOLD)
        d.text((400, yy), val, font=fv, fill=(255, 120, 90, 255) if key == 'STATUS' else B.BONE)
    p = os.path.join(WORK, name + '.png'); im.save(p); return p


def main():
    files, tl, t = [], [], 0.0
    for i, s in enumerate(SHOTS):
        f, d = render(i, s)
        files.append(f); tl.append((t, d)); t += d
        print(f'shot {i} src={s[0]} -> {t - d:.2f}..{t:.2f}', flush=True)
    total = t
    lst = os.path.join(WORK, 'list.txt')
    open(lst, 'w').write(''.join(f"file '{f.replace(os.sep, '/')}'\n" for f in files))
    base = os.path.join(WORK, 'base.mp4')
    run([FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', base])

    C, G = B.CINZEL, B.GEORGIA_I
    GOLD, BONE, SICK = B.GOLD, B.BONE, B.SICK
    wp = B.white_png()
    h0 = tl[1][0]
    ovs = [(B.frame_png(), 0, total, 0, 0)]
    ovs.append((big_text([('NEW DUNGEON', C, 150, 900, BONE, 8), ('WHERE IS IT?', C, 96, 900, SICK, 8)], 330, 'hook'), 0, h0, 0, 0.12))
    ovs.append((wp, h0 - 0.04, h0 + 0.35, 0.04, 0.3))
    ovs.append((big_text([("THE SHAPER'S", C, 64, 700, GOLD, 14), ('TERRACE', C, 170, 900, BONE, 8),
                          ("Un'Goro Crater  ·  Level 58-60", G, 48, None, SICK, 0)], 760, 'title'), h0 + 0.1, h0 + 2.9, 0.3, 0.4))
    ms, md = tl[2]
    fh = round(MAP_H * 1080 / MAP_W / 2) * 2
    px = (PIN[0] - MAP_X) * 1080 / MAP_W; py = (1920 - fh) / 2 + (PIN[1] - MAP_Y) * 1080 / MAP_W
    ovs.append((pin_png(px, py), ms + 0.3, ms + md, 0.25, 0.2))
    ovs.append((info_png([('WHERE', "Un'Goro Crater  -  north rim"), ('SPOT', 'Lakkari Tar Pits  (52, 6)'),
                          ('LEVEL', '58 - 60'), ('STATUS', 'Not open yet')], 1420, 'info'), ms + 0.9, ms + md, 0.35, 0.2))
    steps = [(3, 4, '1.  From the Tar Pits, take\nthe jungle path north.'),
             (5, 6, '2.  Climb the great titan stairs.'),
             (7, 8, '3.  The gate opens onto the portal.')]
    for a_, b_, txt in steps:
        ovs.append((B.caption_png(txt, f'step{a_}'), tl[a_][0] + 0.25, tl[b_][0] + tl[b_][1] - 0.2, 0.3, 0.3))
    sp_, dp = tl[9]
    ovs.append((wp, sp_ + dp - 0.5, sp_ + dp + 0.4, 0.3, 0.35))
    ovs.append((big_text([('DUNGEON ENTRANCE', C, 44, 700, GOLD, 12), ("THE SHAPER'S TERRACE", C, 110, 900, BONE, 4),
                          ('Not implemented yet  -  Level 58-60', G, 46, None, SICK, 0)], 1330, 'card'), sp_ + 0.2, tl[10][0] + tl[10][1], 0.3, 0.3))
    o0 = tl[11][0]
    ovs.append((big_text([("THE SHAPER'S TERRACE", C, 80, 900, BONE, 4), ("Un'Goro Crater  -  (52, 6)", G, 50, None, SICK, 0),
                          ('Level 58-60  -  not open yet', G, 50, None, SICK, 0), ('FULL RUN WHEN IT OPENS', C, 56, 800, GOLD, 8)],
                         700, 'outro'), o0 + 0.5, total, 0.6, 0.9))

    music = os.path.join(WORK, 'music.wav')
    run([FF, '-v', 'error', '-y', '-i', MUSIC, '-af', f'atrim=0:{total},afade=t=in:d=0.4,afade=t=out:st={total - 2.5}:d=2.5,aresample=48000', '-ac', '2', music])

    cmd = [FF, '-v', 'error', '-y', '-i', base]
    for p, a, b, fi, fo in ovs:
        cmd += ['-loop', '1', '-framerate', str(FPS), '-t', f'{b - a:.3f}', '-i', p]
    cmd += ['-i', music]
    fc, last = ['[0:v]setsar=1[g0]'], '[g0]'
    for j, (p, a, b, fi, fo) in enumerate(ovs, start=1):
        ch = f'[{j}:v]format=rgba'
        if fi: ch += f',fade=t=in:st=0:d={fi}:alpha=1'
        if fo: ch += f',fade=t=out:st={max(0, b - a - fo):.3f}:d={fo}:alpha=1'
        fc.append(ch + f',setpts=PTS+{a:.3f}/TB[o{j}]')
        fc.append(f'{last}[o{j}]overlay=eof_action=pass:format=auto[v{j}]'); last = f'[v{j}]'
    fc.append(f'{last}fade=t=out:st={total - 1.0:.3f}:d=1.0,format=yuv420p,setsar=1[vout]')
    mi = len(ovs) + 1
    fc.append(f'[0:a]volume=0.25,highpass=f=90[ga];[{mi}:a]volume=1.0[ma];[ga][ma]amix=inputs=2:normalize=0,alimiter=limit=0.95,atrim=0:{total}[aout]')
    cmd += ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]', '-c:v', 'h264_nvenc', '-preset', 'p7',
            '-tune', 'hq', '-rc', 'vbr', '-cq', '21', '-b:v', '0', '-maxrate', '14M', '-bufsize', '28M', '-r', str(FPS),
            '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{total:.3f}', OUT]
    run(cmd)
    print('OK', OUT, round(total, 2))


if __name__ == '__main__':
    main()
