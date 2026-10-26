"""Short vertical 'presentation du donjon' : Ruins of Lordaeron, 6 boss, musique de Fossoyeuse."""
import os, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FF = r"C:\Users\d2460n\AppData\Local\Programs\Python\Python311\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
IN = r"C:\Users\d2460n\Videos\World Of Warcraft\World Of Warcraft 2026.09.21 - 15.05.07.08.mp4"
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'build'); os.makedirs(WORK, exist_ok=True)
MUS = os.path.join(HERE, 'music_undercity')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'lordaeron_short.mp4')
PREVIEW = '--preview' in sys.argv
CINZEL = r"C:\Users\d2460n\Documents\aout\output\paris_paloma_lyrics\fonts\Cinzel.ttf"
GEORGIA_I = r"C:\Windows\Fonts\georgiai.ttf"
W, H = 1080, 1920
FPS = 60

# (src_start, src_dur, speed, flags)  flags: 'kill' => slow-mo + stamp, 'mute', 'still'
BOSSES = [
    dict(num='I', name='WITHERFANG', lvl=17, kind='Giant Spider', shots=[
        (194, 3.5), (200, 3), (224, 3), (230, 3), (234.2, 2.4, 'kill', 235.4), (245, 2.5)]),
    dict(num='II', name='THE BARON', lvl=17, kind='Abomination', shots=[
        (444, 4), (452.5, 3), (465, 3), (472, 3), (487, 3), (500.5, 2.4, 'kill', 501.7), (511, 2.5)]),
    dict(num='III', name='VIKTOR THE VILE', lvl=19, kind='Ghoul', card_shot=4,
         lead='Wave after wave, the dead rise...', shots=[
        (962, 2.5), (1003, 2.5), (1033, 2.5), (1063, 2.5),
        (1136, 3.5), (1141, 3), (1151, 3), (1161, 2.5), (1168, 2.5), (1173, 3), (1180.8, 2.2, 'kill', 1182.6)]),
    dict(num='IV', name='THE ABANDONED', lvl=18, kind='Undead', shots=[
        (1323.5, 3.5), (1330, 3), (1340, 3), (1347, 3), (1352, 3), (1356.2, 2.4, 'kill', 1357.4), (1360, 2.5)]),
    dict(num='V', name='BJORK', lvl=19, kind='Colossus', shots=[
        (1556, 4), (1560, 3), (1564, 3), (1571, 3), (1592, 3), (1604.5, 2.4, 'kill', 1605.7), (1613, 2.5)]),
    dict(num='VI', name="RATH'MAEL", lvl=20, kind='Final Boss', shots=[
        (1686, 4), (1693, 3), (1699, 3), (1705, 3), (1717, 3), (1727.7, 2.4, 'kill', 1728.9), (1731.5, 3)]),
]
INTRO = [(5.1, 3.1, 'still'), (30, 3), (350, 3), (422, 3), (662, 3), (722, 3), (1382, 2.5)]
OUTRO = [(1744, 3.5), (1851, 4.5)]
SLOW = 0.5
ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']
DONE_TXT = f'{len(BOSSES)} / {len(BOSSES)}  BOSSES DEFEATED'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(' '.join(cmd)); print(r.stderr[-3000:]); raise SystemExit(1)


# ---------------------------------------------------------------- shots
def render_shot(i, s):
    src, dur = s[0], s[1]
    flags = s[2:] if len(s) > 2 else ()
    kill = 'kill' in flags
    still = 'still' in flags
    out = os.path.join(WORK, 'shot_' + '_'.join(str(v) for v in s).replace('.', 'p') + '.mp4')
    outdur = dur / SLOW if kill else dur
    if os.path.exists(out) and not PREVIEW:
        return out, outdur
    vf = ['delogo=x=1140:y=962:w=100:h=122', 'split[m][p]', '[p]crop=200:220:1090:915,boxblur=30:3[pb]', '[m][pb]overlay=1090:915',
          'crop=680:1210:862:0']
    if kill:
        vf += ['setpts=PTS/%g' % SLOW, 'minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1']
    z = 0.012 if still else (0.018 if not kill else 0.03)
    vf += ['scale=1080:1920:flags=lanczos', 'fps=60',
           f"scale=w='trunc(1080*(1+{z}*t)/2)*2':h=-2:eval=frame:flags=bicubic", 'crop=1080:1920',
           'eq=gamma=1.14:contrast=1.07:saturation=1.12',
           'colorbalance=rs=-0.02:gs=0.03:bs=0.02:rh=0.02:bh=-0.02',
           'unsharp=5:5:0.55', 'format=yuv420p']
    if PREVIEW:
        vf.append('scale=540:960')
    af = ['atempo=%g' % SLOW] if kill else []
    af += ['volume=0'] if still else []
    af += ['aresample=48000']
    run([FF, '-v', 'error', '-y', '-ss', str(src), '-t', str(dur), '-i', IN,
         '-filter_complex', '[0:v]' + ','.join(vf).replace(',split[m][p],', ',split[m][p];').replace('[pb],', '[pb];').replace('overlay=1090:915,', 'overlay=1090:915,') + '[vo]', '-map', '[vo]', '-map', '0:a', '-af', ','.join(af), '-t', str(outdur),
         '-c:v', 'h264_nvenc', '-preset', 'p5', '-rc', 'vbr', '-cq', '16', '-b:v', '0',
         '-c:a', 'aac', '-b:a', '256k', '-ac', '2', out])
    return out, outdur


# ---------------------------------------------------------------- graphics
def font(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f


def fit(path, text, maxw, size, wght=None, spacing=0):
    while size > 20:
        f = font(path, size, wght)
        if text_w(f, text, spacing) <= maxw: return f
        size -= 4
    return font(path, size, wght)


def text_w(f, text, spacing=0):
    return sum(f.getlength(c) for c in text) + spacing * (len(text) - 1)


def draw_spaced(d, xy, text, f, fill, spacing=0, anchor_center=True):
    x, y = xy
    if anchor_center:
        x -= text_w(f, text, spacing) / 2
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + spacing


def glow_layer(draw_fn, radius, color):
    m = Image.new('L', (W, H), 0)
    draw_fn(ImageDraw.Draw(m), 255)
    m = m.filter(ImageFilter.GaussianBlur(radius))
    g = Image.new('RGBA', (W, H), color)
    g.putalpha(m.point(lambda v: min(255, int(v * 1.6))))
    return g


def backdrop(im, cy, rx, ry, alpha=150):
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).ellipse([W / 2 - rx, cy - ry, W / 2 + rx, cy + ry], fill=alpha)
    m = m.filter(ImageFilter.GaussianBlur(70))
    b = Image.new('RGBA', (W, H), (2, 6, 4, 255)); b.putalpha(m); im.alpha_composite(b)


GOLD = (214, 180, 104, 255)
BONE = (236, 232, 218, 255)
SICK = (150, 214, 120, 255)
RED = (200, 36, 30, 255)


def frame_png():
    """Global framing: dark gradients top/bottom + vignette, applied on the whole short."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = im.load()
    import math
    for y in range(H):
        top = max(0.0, 1 - y / 330) ** 1.6 * 0.78
        bot = min(0.86, max(0.0, (y - (H - 700)) / 520) ** 1.5 * 0.86)
        a_row = max(top, bot)
        for x in range(0, W):
            dx = (x - W / 2) / (W / 2)
            vig = max(0.0, abs(dx) - 0.55) / 0.45 * 0.45
            a = min(1.0, a_row + vig)
            if a > 0:
                px[x, y] = (4, 8, 6, int(a * 255))
    p = os.path.join(WORK, 'frame.png'); im.save(p); return p


def progress_png(done, current):
    """6 runes at the top : defeated bosses filled, current one glowing."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    n, gap, y = len(BOSSES), 70, 118
    x0 = W / 2 - gap * (n - 1) / 2
    def shape(dd, fillv, k, r):
        cx = x0 + k * gap
        dd.polygon([(cx, y - r), (cx + r, y), (cx, y + r), (cx - r, y)], fill=fillv)
    if current is not None:
        im.alpha_composite(glow_layer(lambda dd, v: shape(dd, v, current, 20), 12, (150, 214, 120, 255)))
    for k in range(n):
        cx = x0 + k * gap
        r = 14
        pts = [(cx, y - r), (cx + r, y), (cx, y + r), (cx - r, y)]
        if k < done:
            d.polygon(pts, fill=GOLD)
        elif k == current:
            d.polygon(pts, fill=SICK)
        else:
            d.polygon(pts, outline=(214, 180, 104, 200), width=3)
    f = font(CINZEL, 30, 700)
    lab = 'RUINS OF LORDAERON'
    draw_spaced(d, (W / 2, 52), lab, f, (214, 180, 104, 210), spacing=6)
    return im


def boss_card(b, idx):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    yb = 1380
    f_top = font(CINZEL, 40, 700)
    top = f'BOSS  {b["num"]}  /  ' + ROMAN[len(BOSSES)]
    f_name = fit(CINZEL, b['name'], 980, 132, 900, spacing=4)
    f_sub = font(GEORGIA_I, 44)
    sub = f'Level {b["lvl"]}  ·  {b["kind"]}'
    backdrop(im, yb + 90, 620, 230, 150)
    def name_draw(dd, v):
        draw_spaced(dd, (W / 2, yb), b['name'], f_name, v, spacing=4)
    im.alpha_composite(glow_layer(name_draw, 22, (120, 200, 90, 255)))
    d = ImageDraw.Draw(im)
    # shadow + name
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_spaced(ImageDraw.Draw(sh), (W / 2 + 4, yb + 6), b['name'], f_name, (0, 0, 0, 230), spacing=4)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
    draw_spaced(d, (W / 2, yb), b['name'], f_name, BONE, spacing=4)
    # top label with rules
    draw_spaced(d, (W / 2, yb - 70), top, f_top, GOLD, spacing=10)
    tw = text_w(f_top, top, 10)
    for sgn in (-1, 1):
        x1 = W / 2 + sgn * (tw / 2 + 24); x2 = W / 2 + sgn * (tw / 2 + 150)
        d.line([(x1, yb - 46), (x2, yb - 46)], fill=GOLD, width=3)
    nh = f_name.getbbox('A')[3]
    d.text((W / 2, yb + nh + 40), sub, font=f_sub, fill=SICK, anchor='ma')
    p = os.path.join(WORK, f'card_{idx}.png'); im.save(p); return p


def kill_png():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    txt = 'DEFEATED'
    f = fit(CINZEL, txt, 960, 150, 900, spacing=14)
    y = 820
    backdrop(im, y + 100, 560, 190, 170)
    im.alpha_composite(glow_layer(lambda dd, v: draw_spaced(dd, (W / 2, y), txt, f, v, spacing=14), 30, (160, 10, 10, 255)))
    d = ImageDraw.Draw(im)
    draw_spaced(d, (W / 2 + 5, y + 7), txt, f, (0, 0, 0, 220), spacing=14)
    draw_spaced(d, (W / 2, y), txt, f, (232, 60, 48, 255), spacing=14)
    d.line([(160, y + 190), (W - 160, y + 190)], fill=(232, 60, 48, 200), width=4)
    p = os.path.join(WORK, 'kill.png'); im.save(p); return p


def title_png():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    y = 780
    f1 = font(CINZEL, 54, 700); f2 = fit(CINZEL, 'LORDAERON', 1000, 170, 900, spacing=6)
    f3 = font(GEORGIA_I, 46)
    backdrop(im, y + 190, 620, 300, 185)
    im.alpha_composite(glow_layer(lambda dd, v: draw_spaced(dd, (W / 2, y + 70), 'LORDAERON', f2, v, spacing=6), 28, (120, 200, 90, 255)))
    d = ImageDraw.Draw(im)
    draw_spaced(d, (W / 2, y), 'THE RUINS OF', f1, GOLD, spacing=16)
    draw_spaced(d, (W / 2 + 5, y + 77), 'LORDAERON', f2, (0, 0, 0, 220), spacing=6)
    draw_spaced(d, (W / 2, y + 70), 'LORDAERON', f2, BONE, spacing=6)
    d.line([(250, y + 290), (W - 250, y + 290)], fill=GOLD, width=3)
    d.text((W / 2, y + 320), f'Tirisfal Glades  ·  {len(BOSSES)} bosses', font=f3, fill=SICK, anchor='ma')
    p = os.path.join(WORK, 'title.png'); im.save(p); return p


def caption_png(text, name):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    f = font(GEORGIA_I, 60)
    d = ImageDraw.Draw(im)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((W / 2 + 3, 1500 + 4), text, font=f, fill=(0, 0, 0, 255), anchor='ma', align='center', spacing=14)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
    d.text((W / 2, 1500), text, font=f, fill=BONE, anchor='ma', align='center', spacing=14)
    p = os.path.join(WORK, name + '.png'); im.save(p); return p


def outro_png():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    y = 760
    f1 = font(CINZEL, 50, 700); f2 = fit(CINZEL, 'LORDAERON', 1000, 160, 900, spacing=6)
    f3 = fit(CINZEL, DONE_TXT, 980, 64, 800, spacing=6)
    backdrop(im, y + 190, 620, 300, 200)
    im.alpha_composite(glow_layer(lambda dd, v: draw_spaced(dd, (W / 2, y + 60), 'LORDAERON', f2, v, spacing=6), 28, (120, 200, 90, 255)))
    d = ImageDraw.Draw(im)
    draw_spaced(d, (W / 2, y), 'THE RUINS OF', f1, GOLD, spacing=16)
    draw_spaced(d, (W / 2, y + 60), 'LORDAERON', f2, BONE, spacing=6)
    d.line([(250, y + 270), (W - 250, y + 270)], fill=GOLD, width=3)
    draw_spaced(d, (W / 2, y + 300), DONE_TXT, f3, (232, 60, 48, 255), spacing=6)
    p = os.path.join(WORK, 'outro.png'); im.save(p); return p


def white_png():
    p = os.path.join(WORK, 'white.png')
    Image.new('RGBA', (W, H), (235, 245, 230, 255)).save(p); return p


# ---------------------------------------------------------------- build
def main():
    shots = []   # (shot_tuple, chapter)
    for s in INTRO: shots.append((s, 'intro'))
    for k, b in enumerate(BOSSES):
        for s in b['shots']: shots.append((s, k))
    for s in OUTRO: shots.append((s, 'outro'))

    files, t, timeline = [], 0.0, []
    for i, (s, ch) in enumerate(shots):
        f, d = render_shot(i, s)
        # align to frame grid
        n = round(d * FPS); d = n / FPS
        files.append(f); timeline.append(dict(ch=ch, start=t, dur=d, shot=s)); t += d
        print(f'shot {i:2d} ch={ch} src={s[0]} -> {t - d:6.2f}..{t:6.2f}', flush=True)
    total = t
    lst = os.path.join(WORK, 'list.txt')
    with open(lst, 'w') as fh:
        for f in files: fh.write(f"file '{f.replace(os.sep, '/')}'\n")
    base = os.path.join(WORK, 'base.mp4')
    run([FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', base])

    # ---- overlays: (png, start, end, fade_in, fade_out)
    ovs = [(frame_png(), 0, total, 0, 0)]
    ovs.append((title_png(), 0.35, 3.5, 0.5, 0.45))
    intro_end = max(x['start'] + x['dur'] for x in timeline if x['ch'] == 'intro')
    ovs.append((caption_png('At the gates of the Undercity,\nthe dead city never sleeps.', 'cap1'), 5.2, 11.0, 0.5, 0.6))
    ovs.append((caption_png('Six guardians. One way through.', 'cap2'), 12.5, intro_end - 0.4, 0.5, 0.5))
    wp, kp = white_png(), kill_png()
    for k, b in enumerate(BOSSES):
        segs = [x for x in timeline if x['ch'] == k]
        c0, c1 = segs[0]['start'], segs[-1]['start'] + segs[-1]['dur']
        pp = os.path.join(WORK, f'prog_{k}.png'); progress_png(k, k).save(pp)
        ovs.append((pp, c0, c1, 0.4, 0.3))
        cs = segs[b.get('card_shot', 0)]['start']
        ovs.append((boss_card(b, k), cs + 0.25, cs + 3.6, 0.35, 0.5))
        if b.get('lead'):
            ovs.append((caption_png(b['lead'], f'lead_{k}'), c0 + 0.3, cs - 0.2, 0.4, 0.4))
            ovs.append((wp, cs, cs + 0.4, 0.05, 0.33))
        ovs.append((wp, c0, c0 + 0.45, 0.06, 0.38))
        for x in segs:
            if 'kill' in x['shot']:
                kt = x['start'] + (x['shot'][3] - x['shot'][0]) / SLOW
                ovs.append((wp, kt - 0.05, kt + 0.5, 0.05, 0.45))
                ovs.append((kp, kt + 0.05, x['start'] + x['dur'] + 1.2, 0.15, 0.5))
    oseg = [x for x in timeline if x['ch'] == 'outro']
    o0 = oseg[0]['start']
    pp = os.path.join(WORK, 'prog_done.png'); progress_png(len(BOSSES), None).save(pp)
    ovs.append((pp, o0, total, 0.4, 0.8))
    ovs.append((outro_png(), o0 + 0.6, total, 0.7, 1.0))

    # ---- music: Intro (trimmed) -> Undercity02 -> Undercity01
    music = os.path.join(WORK, 'music.wav')
    cf = 3.0
    run([FF, '-v', 'error', '-y', '-i', os.path.join(MUS, 'UndercityIntro.mp3'), '-i', os.path.join(MUS, 'Undercity02.mp3'),
         '-i', os.path.join(MUS, 'Undercity01.mp3'), '-filter_complex',
         f'[0:a]atrim=0:{intro_end + cf - 0.2},asetpts=PTS-STARTPTS[a0];[a0][1:a]acrossfade=d={cf}:c1=tri:c2=tri[a01];'
         f'[a01][2:a]acrossfade=d={cf}[m];[m]atrim=0:{total},afade=t=in:d=0.8,afade=t=out:st={total - 4}:d=4,aresample=48000[out]',
         '-map', '[out]', '-ac', '2', music])

    # ---- final
    cmd = [FF, '-v', 'error', '-stats', '-y', '-i', base]
    for p, a, b, fi, fo in ovs:
        cmd += ['-loop', '1', '-framerate', str(FPS), '-t', f'{b - a:.3f}', '-i', p]
    cmd += ['-i', music]
    fc, last = ['[0:v]eq=gamma=1.1:brightness=0.012:saturation=1.04,setsar=1[g0]'], '[g0]'
    for j, (p, a, b, fi, fo) in enumerate(ovs, start=1):
        chain = f'[{j}:v]format=rgba'
        if PREVIEW: chain += ',scale=540:960'
        if fi: chain += f',fade=t=in:st=0:d={fi}:alpha=1'
        if fo: chain += f',fade=t=out:st={max(0, b - a - fo):.3f}:d={fo}:alpha=1'
        chain += f',setpts=PTS+{a:.3f}/TB[o{j}]'
        fc.append(chain)
        fc.append(f'{last}[o{j}]overlay=eof_action=pass:format=auto[v{j}]')
        last = f'[v{j}]'
    fc.append(f'{last}fade=t=in:st=0:d=0.6,fade=t=out:st={total - 1.2:.3f}:d=1.2,format=yuv420p,setsar=1[vout]')
    mi = len(ovs) + 1
    fc.append(f'[0:a]volume=0.32,highpass=f=90[ga];[{mi}:a]volume=0.95[ma];[ga][ma]amix=inputs=2:normalize=0:duration=longest,'
              f'alimiter=limit=0.95,atrim=0:{total}[aout]')
    cmd += ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]',
            '-c:v', 'h264_nvenc', '-preset', 'p7', '-tune', 'hq', '-rc', 'vbr', '-cq', '21', '-b:v', '0',
            '-maxrate', '14M', '-bufsize', '28M', '-profile:v', 'high', '-r', str(FPS),
            '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{total:.3f}', OUT]
    json.dump(dict(total=total, timeline=timeline), open(os.path.join(WORK, 'timeline.json'), 'w'), indent=1)
    run(cmd)
    print('OK', OUT, round(total, 2), 's')


if __name__ == '__main__':
    main()
