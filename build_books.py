"""Erudite's Amulet route — vertical TikTok guide, no voice, game audio muted, music bed."""
import os, sys, subprocess
from PIL import Image, ImageDraw, ImageFilter
import build as B

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'build_books'); os.makedirs(WORK, exist_ok=True)
B.WORK = WORK
FF, W, H, FPS = B.FF, B.W, B.H, 60
V = r"C:\Users\d2460n\Videos\World Of Warcraft\World Of Warcraft 2026.09.23 - "
MUSIC = os.path.join(HERE, 'music', 'Undercity02.mp3')
OUT = sys.argv[1]

# ref -> (file, game-window crop x,y,w,h)
SRC = {
    '01': ('08.46.24.01', (1617, 176, 1886, 1062)),
    '02': ('08.54.28.02', (1617, 176, 1886, 1062)),
    '07': ('09.15.05.07', (1617, 176, 1886, 1062)),
    '08': ('09.30.52.08', (0, 0, 1886, 1062)),
    '10': ('10.30.56.10', (0, 0, 1886, 1062)),
    '11': ('11.07.31.11', (0, 0, 1886, 1062)),
    '12': ('11.17.39.12', (0, 0, 1886, 1062)),
    '13': ('11.27.35.13', (0, 0, 1886, 1062)),
    '14': ('11.36.30.14', (0, 0, 1886, 1062)),
    '15': ('11.40.19.15', (0, 0, 1886, 1062)),
    '17': ('13.19.32.17', (0, 0, 1886, 1062)),
    '18': ('13.27.55.18', (0, 0, 1886, 1062)),
    '19': ('13.32.28.19', (0, 0, 1886, 1062)),
}

# (ref, src_start, dur, badge, zone, info, warn)
SHOTS = [
    ('15', 45.0, 3.0, None, None, None, None),                       # hook: amulet in bags
    ('14', 145.0, 3.0, None, 'OWEN THADD', 'Magic Quarter  ·  73.4, 33.0', None),
    ('14', 150.0, 4.0, None, '10 BOOKS', 'Bring a book first, or no quest', None),
    ('11', 80.0, 3.0, '1/10', 'BRILL', 'Tirisfal Glades  ·  59.4, 52.3', None),
    ('11', 106.0, 3.0, '1/10', 'BRILL', 'Alchemy shop', None),
    ('13', 45.0, 3.0, '2/10', 'AMBERMILL', 'Silverpine  ·  63.5, 63.1', None),
    ('13', 65.5, 2.5, '2/10', 'AMBERMILL', 'Town hall  ·  mobs 17-18', None),
    ('17', 5.0, 3.0, '3/10', 'THE SLUDGE FEN', 'The Barrens  ·  56.3, 8.8', None),
    ('17', 40.0, 3.0, '3/10', 'THE SLUDGE FEN', 'Oil rig  ·  control room', None),
    ('18', 0.0, 2.5, '4/10', 'RATCHET', 'The Barrens  ·  62.7, 36.3', None),
    ('18', 15.0, 3.0, '4/10', 'RATCHET', 'Engineering shop', 'GO UPSTAIRS'),
    ('01', 175.0, 3.0, '5/10', 'LUSHWATER OASIS', 'The Barrens  ·  46.0, 36.5', 'GO UNDERGROUND'),
    ('02', 30.0, 2.0, '5/10', 'LUSHWATER OASIS', 'Down to the Wailing Caverns portal', None),
    ('02', 129.5, 2.5, '5/10', 'LUSHWATER OASIS', 'Scrolls on the ground', None),
    ('19', 2.0, 2.5, '6/10', 'ORGRIMMAR', "Ta'zo Mural  ·  38.7, 78.4", None),
    ('19', 16.0, 2.0, '6/10', 'ORGRIMMAR', "Ta'zo Mural  ·  38.7, 78.4", None),
    ('07', 20.0, 3.0, '7/10', 'GRIMTOTEM POST', 'Stonetalon  ·  74.4, 85.7', None),
    ('07', 190.0, 2.0, '7/10', 'GRIMTOTEM POST', 'Stonetalon  ·  74.4, 85.7', None),
    ('10', 1400.0, 3.5, '8/10', 'RAVEN HILL', 'Duskwood  ·  16.0, 38.5', 'LEFT CRYPT'),
    ('10', 1370.0, 3.0, '8/10', 'RAVEN HILL', 'Last room  ·  alchemy table', 'MOBS 27-28'),
    ('10', 1450.0, 2.5, '8/10', 'RAVEN HILL', 'Bring a group', None),
    ('10', 250.0, 3.0, '9/10', 'MOONBROOK', 'Westfall  ·  45.4, 70.4', None),
    ('10', 266.0, 2.5, '9/10', 'MOONBROOK', 'Next to the Deadmines entrance', None),
    ('08', 1040.0, 3.0, '10/10', 'DARKCLOUD PINNACLE', 'Thousand Needles  ·  34.4, 40.1', 'CLIMB FIRST'),
    ('08', 1070.0, 2.5, '10/10', 'DARKCLOUD PINNACLE', 'Path up starts 31.0, 37.0', None),
    ('08', 1330.0, 2.5, '10/10', 'DARKCLOUD PINNACLE', 'Biggest hut', None),
    ('12', 180.0, 3.0, None, 'TRAP', 'Sepulcher book: missing for now', 'SKIP IT'),
    ('15', 5.0, 3.5, None, 'TURN IN', 'One book at a time  ·  no level requirement', None),
    ('15', 38.0, 3.4, None, '10 BOOKS = YOUR PICK', "Erudite's Amulet  ·  +4 Agility  ·  +6 Stamina", None),
    ('15', 42.0, 3.2, None, 'OR', 'Scholarly Pendant  ·  +6 Stamina  ·  +4 Spirit', None),
    ('15', 30.0, 3.2, None, '20 BOOKS = A RING', 'Philanthropist  +6 Int  ·  Field Researcher (rogue)', 'WARRIORS: STOP AT 10'),
    ('15', 70.0, 3.0, None, None, None, None),                       # outro card
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(' '.join(str(c) for c in cmd)[:400]); print(r.stderr[-2500:]); raise SystemExit(1)


def render(i, s):
    ref, src, dur = s[0], s[1], s[2]
    f, (cx, cy, cw, ch) = SRC[ref]
    out = os.path.join(WORK, f'shot_{i:02d}.mp4')
    fh = round(1080 * ch / cw / 2) * 2          # 1080x608 for a 1886x1062 window
    fc = (f'[0:v]crop={cw}:{ch}:{cx}:{cy},split[a][b];'
          f'[a]scale=-2:1920,crop=1080:1920,boxblur=40:2,eq=brightness=-0.22:saturation=0.7[bg];'
          f'[b]scale=1080:{fh}:flags=lanczos,eq=gamma=1.06:saturation=1.08,unsharp=5:5:0.4[fg];'
          f'[bg][fg]overlay=0:(H-h)/2,fps={FPS},format=yuv420p[v]')
    run([FF, '-v', 'error', '-y', '-ss', str(src), '-t', str(dur), '-i', V + f + '.mp4',
         '-filter_complex', fc, '-map', '[v]', '-an', '-t', str(dur),
         '-c:v', 'h264_nvenc', '-preset', 'p5', '-rc', 'vbr', '-cq', '18', '-b:v', '0', out])
    return out, round(dur * FPS) / FPS


GOLD, BONE, SICK, RED = B.GOLD, B.BONE, (245, 205, 120, 255), (235, 70, 55, 255)


def card(s, idx):
    """Badge + zone + coords + warning, kept inside the TikTok safe zone."""
    badge, zone, info, warn = s[3], s[4], s[5], s[6]
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if badge:
        f = B.font(B.CINZEL, 92, 900)
        bw = B.text_w(f, badge, 6) + 90
        d.rounded_rectangle([60, 300, 60 + bw, 300 + 130], 24, fill=(120, 10, 10, 230), outline=GOLD, width=4)
        B.draw_spaced(d, (60 + bw / 2, 316), badge, f, BONE, spacing=6)
    if zone:
        f = B.fit(B.CINZEL, zone, 940, 84, 900, spacing=4)
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        B.draw_spaced(ImageDraw.Draw(sh), (W / 2 + 4, 466), zone, f, (0, 0, 0, 235), spacing=4)
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
        B.draw_spaced(d, (W / 2, 462), zone, f, BONE, spacing=4)
    if info:
        f = B.fit(B.GEORGIA_I, info, 900, 54)
        tw = B.text_w(f, info) + 80
        d.rounded_rectangle([(W - tw) / 2, 1340, (W + tw) / 2, 1436], 22, fill=(8, 10, 12, 220), outline=GOLD, width=3)
        d.text((W / 2, 1358), info, font=f, fill=SICK, anchor='ma')
    if warn:
        t = '!  ' + warn
        f = B.fit(B.CINZEL, t, 820, 64, 900, spacing=6)
        tw = B.text_w(f, t, 6) + 70
        d.rounded_rectangle([(W - tw) / 2, 1460, (W + tw) / 2, 1556], 20, fill=(120, 12, 8, 235), outline=(250, 190, 90, 255), width=4)
        B.draw_spaced(d, (W / 2, 1476), t, f, BONE, spacing=6)
    p = os.path.join(WORK, f'card_{idx}.png'); im.save(p); return p


def big(lines, y, name, glow=(200, 60, 40, 255)):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    B.backdrop(im, y + 130, 620, 270, 195)
    d = ImageDraw.Draw(im)
    yy = y
    for txt, fp, size, wg, fill, sp in lines:
        f = B.fit(fp, txt, 980, size, wg, spacing=sp)
        if size >= 90:
            im.alpha_composite(B.glow_layer(lambda dd, v, t=txt, f=f, yy=yy, sp=sp: B.draw_spaced(dd, (W / 2, yy), t, f, v, spacing=sp), 22, glow))
            d = ImageDraw.Draw(im)
            B.draw_spaced(d, (W / 2 + 4, yy + 5), txt, f, (0, 0, 0, 225), spacing=sp)
        B.draw_spaced(d, (W / 2, yy), txt, f, fill, spacing=sp)
        yy += f.getbbox('Ag')[3] + 24
    p = os.path.join(WORK, name + '.png'); im.save(p); return p


def main():
    files, tl, t = [], [], 0.0
    for i, s in enumerate(SHOTS):
        f, d = render(i, s)
        files.append(f); tl.append((t, d)); t += d
        print(f'shot {i:2d} {s[0]}@{s[1]} -> {t - d:5.1f}..{t:5.1f}', flush=True)
    total = t
    lst = os.path.join(WORK, 'list.txt')
    open(lst, 'w').write(''.join(f"file '{p.replace(os.sep, '/')}'\n" for p in files))
    base = os.path.join(WORK, 'base.mp4')
    run([FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', base])

    C, G = B.CINZEL, B.GEORGIA_I
    wp = B.white_png()
    ovs = [(B.frame_png(), 0, total, 0, 0)]
    h0 = tl[1][0]
    ovs.append((big([('BEST LEVEL 20', C, 74, 800, GOLD, 8), ('NECKLACE', C, 150, 900, BONE, 6),
                     ('without killing a single boss', G, 52, None, SICK, 0)], 300, 'hook'), 0.1, h0, 0.25, 0.15))
    ovs.append((B.caption_png('Beta - subject to change', 'beta'), 0.3, h0, 0.3, 0.3))
    for i, s in enumerate(SHOTS):
        if any((s[3], s[4], s[5], s[6])) and i not in (0, len(SHOTS) - 1):
            a, d = tl[i]
            ovs.append((card(s, i), a + 0.12, a + d, 0.22, 0.18))
    o0 = tl[-1][0]
    ovs.append((big([('FOLLOW FOR THE', C, 56, 800, GOLD, 8), ('FULL TANK BiS', C, 118, 900, BONE, 6),
                     ('What class are you playing?', G, 54, None, SICK, 0)], 560, 'outro'), o0 + 0.3, total, 0.4, 0.8))

    music = os.path.join(WORK, 'music.wav')
    run([FF, '-v', 'error', '-y', '-i', MUSIC, '-af',
         f'atrim=0:{total},asetpts=PTS-STARTPTS,volume=0.85,afade=t=in:d=0.6,afade=t=out:st={total - 3}:d=3,aresample=48000',
         '-ac', '2', music])

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
    fc.append(f'{last}fade=t=out:st={total - 0.8:.3f}:d=0.8,format=yuv420p,setsar=1[vout]')
    cmd += ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', f'{len(ovs) + 1}:a',
            '-c:v', 'h264_nvenc', '-preset', 'p7', '-tune', 'hq', '-rc', 'vbr', '-cq', '21', '-b:v', '0',
            '-maxrate', '14M', '-bufsize', '28M', '-r', str(FPS), '-c:a', 'aac', '-b:a', '192k',
            '-movflags', '+faststart', '-t', f'{total:.3f}', OUT]
    run(cmd)
    print('OK', OUT, round(total, 2))


if __name__ == '__main__':
    main()
