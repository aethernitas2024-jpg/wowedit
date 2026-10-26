"""Short vertical 'presentation du donjon' : Ruins of Lordaeron, 6 boss, musique de Fossoyeuse."""
import os, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FF = r"C:\Users\d2460n\AppData\Local\Programs\Python\Python311\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
IN = r"C:\Users\d2460n\Videos\World Of Warcraft\World Of Warcraft 2026.09.21 - 23.57.05.09.mp4"
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'build_wc'); os.makedirs(WORK, exist_ok=True)
MUS = os.path.join(HERE, 'music_wc')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'wailing_caverns_short.mp4')
PREVIEW = '--preview' in sys.argv
CINZEL = r"C:\Users\d2460n\Documents\aout\output\paris_paloma_lyrics\fonts\Cinzel.ttf"
GEORGIA_I = r"C:\Windows\Fonts\georgiai.ttf"
W, H = 1080, 1920
FPS = 60

# (src_start, src_dur, speed, flags)  flags: 'kill' => slow-mo + stamp, 'mute', 'still'
BOSSES = [
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
SLOW = 0.5
ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']
DONE_TXT = f'{NB} / {NB}  BOSSES DEFEATED'


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
    spot = Image.new('L', (W, H), 0)
    ImageDraw.Draw(spot).ellipse([521 - 230, 1628 - 210, 521 + 230, 1628 + 210], fill=235)
    spot = spot.filter(ImageFilter.GaussianBlur(60))
    sp = Image.new('RGBA', (W, H), (4, 8, 6, 255)); sp.putalpha(spot); im.alpha_composite(sp)
    p = os.path.join(WORK, 'frame.png'); im.save(p); return p


def progress_png(done, current):
    """6 runes at the top : defeated bosses filled, current one glowing."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    n, gap, y = NB, 64, 118
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
    lab = 'WAILING CAVERNS'
    draw_spaced(d, (W / 2, 52), lab, f, (214, 180, 104, 210), spacing=6)
    return im


def boss_card(b, idx):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    yb = 1380
    f_top = font(CINZEL, 40, 700)
    top = b['top'] if b.get('escort') else f'BOSS  {b["num"]}  /  ' + ROMAN[NB]
    f_name = fit(CINZEL, b['name'], 980, 132, 900, spacing=4)
    f_sub = font(GEORGIA_I, 44)
    sub = b['sub'] if b.get('escort') else f'Level {b["lvl"]}  ·  {b["kind"]}'
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
    f1 = font(CINZEL, 54, 700); f2 = fit(CINZEL, 'WAILING CAVERNS', 1000, 170, 900, spacing=6)
    f3 = font(GEORGIA_I, 46)
    backdrop(im, y + 190, 620, 300, 185)
    im.alpha_composite(glow_layer(lambda dd, v: draw_spaced(dd, (W / 2, y + 70), 'WAILING CAVERNS', f2, v, spacing=6), 28, (120, 200, 90, 255)))
    d = ImageDraw.Draw(im)
    draw_spaced(d, (W / 2, y), 'THE', f1, GOLD, spacing=16)
    draw_spaced(d, (W / 2 + 5, y + 77), 'WAILING CAVERNS', f2, (0, 0, 0, 220), spacing=6)
    draw_spaced(d, (W / 2, y + 70), 'WAILING CAVERNS', f2, BONE, spacing=6)
    d.line([(250, y + 290), (W - 250, y + 290)], fill=GOLD, width=3)
    d.text((W / 2, y + 320), f'The Barrens  ·  {NB} bosses', font=f3, fill=SICK, anchor='ma')
    p = os.path.join(WORK, 'title.png'); im.save(p); return p


def hook_png():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    backdrop(im, 470, 620, 260, 200)
    f1 = fit(CINZEL, '8 BOSSES.', 1000, 190, 900, spacing=8)
    f2 = fit(CINZEL, 'ONE NIGHTMARE.', 1000, 96, 900, spacing=6)
    im.alpha_composite(glow_layer(lambda dd, v: draw_spaced(dd, (W / 2, 300), '8 BOSSES.', f1, v, spacing=8), 26, (160, 10, 10, 255)))
    d = ImageDraw.Draw(im)
    draw_spaced(d, (W / 2 + 5, 307), '8 BOSSES.', f1, (0, 0, 0, 230), spacing=8)
    draw_spaced(d, (W / 2, 300), '8 BOSSES.', f1, BONE, spacing=8)
    draw_spaced(d, (W / 2, 530), 'ONE NIGHTMARE.', f2, SICK, spacing=6)
    p = os.path.join(WORK, 'hook.png'); im.save(p); return p


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
    f1 = font(CINZEL, 50, 700); f2 = fit(CINZEL, 'WAILING CAVERNS', 1000, 160, 900, spacing=6)
    f3 = fit(CINZEL, DONE_TXT, 980, 64, 800, spacing=6)
    backdrop(im, y + 190, 620, 300, 200)
    im.alpha_composite(glow_layer(lambda dd, v: draw_spaced(dd, (W / 2, y + 60), 'WAILING CAVERNS', f2, v, spacing=6), 28, (120, 200, 90, 255)))
    d = ImageDraw.Draw(im)
    draw_spaced(d, (W / 2, y), 'THE', f1, GOLD, spacing=16)
    draw_spaced(d, (W / 2, y + 60), 'WAILING CAVERNS', f2, BONE, spacing=6)
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
    hook_end = timeline[0]['dur']
    ovs.append((hook_png(), 0.0, hook_end, 0, 0.12))
    ovs.append((white_png(), hook_end - 0.04, hook_end + 0.35, 0.04, 0.3))
    ovs.append((title_png(), hook_end + 0.1, hook_end + 2.7, 0.3, 0.4))
    intro_end = max(x['start'] + x['dur'] for x in timeline if x['ch'] == 'intro')
    ovs.append((caption_png('Deep in the Barrens,\na druid dreams a nightmare.', 'cap1'), hook_end + 2.8, hook_end + 5.5, 0.35, 0.4))
    ovs.append((caption_png('Eight guardians stand in the way.', 'cap2'), hook_end + 5.8, intro_end - 0.2, 0.35, 0.4))
    wp, kp = white_png(), kill_png()
    for k, b in enumerate(BOSSES):
        segs = [x for x in timeline if x['ch'] == k]
        c0, c1 = segs[0]['start'], segs[-1]['start'] + segs[-1]['dur']
        bi = sum(1 for bb in BOSSES[:k] if not bb.get('escort'))
        pp = os.path.join(WORK, f'prog_{k}.png'); progress_png(bi, None if b.get('escort') else bi).save(pp)
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
    pp = os.path.join(WORK, 'prog_done.png'); progress_png(NB, None).save(pp)
    ovs.append((pp, o0, total, 0.4, 0.8))
    ovs.append((outro_png(), o0 + 0.6, total, 0.7, 1.0))

    # ---- music: Intro (trimmed) -> Undercity02 -> Undercity01
    music = os.path.join(WORK, 'music.wav')
    cf = 3.0
    run([FF, '-v', 'error', '-y', '-i', os.path.join(MUS, 'wc_main_1.mp3'), '-i', os.path.join(MUS, 'wc_main_2.mp3'),
         '-i', os.path.join(MUS, 'wc_main_3.mp3'), '-filter_complex',
         f'[0:a]atrim=0:79.5,asetpts=PTS-STARTPTS[a0];[a0][1:a]acrossfade=d={cf}:c1=tri:c2=tri[a01];'
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
    fc.append(f'{last}fade=t=in:st=0:d=0.08,fade=t=out:st={total - 1.2:.3f}:d=1.2,format=yuv420p,setsar=1[vout]')
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
