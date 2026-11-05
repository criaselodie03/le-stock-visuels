"""Composition des visuels Apéros du Jeudi – DJ Tam – 7 janvier 2027.
Chaque format est construit en calques (fond + éléments RGBA positionnés),
réutilisés tels quels par l'animation."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os

D = os.path.dirname(os.path.abspath(__file__))
F = lambda n, s: ImageFont.truetype(os.path.join(D, 'fonts', n + '.ttf'), s)

GREEN = (46, 245, 150)
GREEN_D = (10, 120, 70)
WHITE = (255, 255, 255)
DARK = (4, 18, 12)

LOGO = Image.open(os.path.join(D, 'logo_blanc.png')).convert('RGBA')
LOGO = LOGO.crop(LOGO.getbbox())


def text_layer(txt, font, fill=WHITE, glow=None, glow_r=10, stroke=0, stroke_fill=DARK,
               shadow=True, tracking=0):
    """Texte sur calque transparent, avec ombre portée et halo optionnel."""
    pad = 40
    tmp = ImageDraw.Draw(Image.new('L', (1, 1)))
    if tracking:
        widths = [tmp.textlength(c, font=font) for c in txt]
        w = int(sum(widths) + tracking * (len(txt) - 1))
    else:
        w = int(tmp.textlength(txt, font=font))
    asc, desc = font.getmetrics()
    h = asc + desc
    W, H = w + 2 * pad, h + 2 * pad

    def draw_on(im, col, sw=0, sf=None):
        d = ImageDraw.Draw(im)
        if tracking:
            x = pad
            for c, cw in zip(txt, widths):
                d.text((x, pad), c, font=font, fill=col, stroke_width=sw, stroke_fill=sf)
                x += cw + tracking
        else:
            d.text((pad, pad), txt, font=font, fill=col, stroke_width=sw, stroke_fill=sf)

    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw_on(sh, (0, 0, 0, 200), stroke + 2, (0, 0, 0, 200))
        sh = sh.filter(ImageFilter.GaussianBlur(8))
        out.alpha_composite(sh, (0, 6))
    if glow:
        g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw_on(g, glow + (255,), stroke + 3, glow + (255,))
        g = g.filter(ImageFilter.GaussianBlur(glow_r))
        out.alpha_composite(g)
        out.alpha_composite(g)
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_on(t, fill + (255,) if len(fill) == 3 else fill, stroke, stroke_fill)
    out.alpha_composite(t)
    bb = out.split()[3].point(lambda a: 255 if a > 40 else 0).getbbox()
    return out.crop(bb)


def box_layer(w, h, radius=14, fill=(4, 20, 12, 200), outline=GREEN, width=4, glow=True):
    pad = 18
    im = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if glow:
        g = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).rounded_rectangle((pad, pad, pad + w, pad + h), radius, outline=outline + (255,), width=width + 6)
        g = g.filter(ImageFilter.GaussianBlur(12))
        im.alpha_composite(g)
    ImageDraw.Draw(im).rounded_rectangle((pad, pad, pad + w, pad + h), radius, fill=fill, outline=outline + (255,), width=width)
    return im


def on_box(content, padx=34, pady=14, **kw):
    b = box_layer(content.width + 2 * padx, content.height + 2 * pady, **kw)
    b.alpha_composite(content, ((b.width - content.width) // 2, (b.height - content.height) // 2))
    return b


def logo_block(width, sub_size=None):
    """Logo LE STOCK blanc plein + « LA LOUVIÈRE » sur toute la largeur du logo, collé dessous."""
    lg = LOGO.resize((width, int(LOGO.height * width / LOGO.width)), Image.LANCZOS)
    sh = Image.new('RGBA', (lg.width + 60, lg.height + 60), (0, 0, 0, 0))
    a = lg.split()[3].point(lambda v: int(v * 0.8))
    blk = Image.new('RGBA', lg.size, (0, 0, 0, 255)); blk.putalpha(a)
    sh.alpha_composite(blk, (30, 36)); sh = sh.filter(ImageFilter.GaussianBlur(9))
    # taille et interlettrage calculés pour couvrir la largeur du logo
    tmp = ImageDraw.Draw(Image.new('L', (1, 1)))
    size = 40
    base_w = tmp.textlength('LA LOUVIÈRE', font=F('mont800', size))
    size = max(10, int(size * width * 0.86 / base_w))
    font = F('mont800', size)
    base_w = tmp.textlength('LA LOUVIÈRE', font=font)
    tracking = max(0, (width * 0.98 - base_w) / 10)
    sub = text_layer('LA LOUVIÈRE', font, fill=GREEN, glow=GREEN_D, glow_r=6, tracking=tracking)
    if sub.width > width:
        sub = sub.resize((width, int(sub.height * width / sub.width)), Image.LANCZOS)
    W = max(sh.width, sub.width)
    gap = int(width * 0.01)
    H = 30 + lg.height + gap + sub.height
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.alpha_composite(sh, ((W - sh.width) // 2, 0))
    out.alpha_composite(lg, ((W - lg.width) // 2, 30))
    out.alpha_composite(sub, ((W - sub.width) // 2, 30 + lg.height + gap))
    return out


def stack(layers, gap=0, align='center'):
    W = max(l.width for l in layers)
    H = sum(l.height for l in layers) + gap * (len(layers) - 1)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    y = 0
    for l in layers:
        x = (W - l.width) // 2 if align == 'center' else 0
        out.alpha_composite(l, (x, y)); y += l.height + gap
    return out


APEROS = Image.open(os.path.join(D, 'logo_aperos_crop.png')).convert('RGBA')


def title_block(width):
    """Logo officiel « Les apéros du Jeudi » (blanc), mis en avant avec un halo vert."""
    lg = APEROS.resize((width, int(APEROS.height * width / APEROS.width)), Image.LANCZOS)
    pad = 40
    out = Image.new('RGBA', (lg.width + 2 * pad, lg.height + 2 * pad), (0, 0, 0, 0))
    a = lg.split()[3]
    sh = Image.new('RGBA', lg.size, (0, 0, 0, 255)); sh.putalpha(a.point(lambda v: int(v * .85)))
    shl = Image.new('RGBA', out.size, (0, 0, 0, 0)); shl.alpha_composite(sh, (pad, pad + 8))
    out.alpha_composite(shl.filter(ImageFilter.GaussianBlur(10)))
    gl = Image.new('RGBA', lg.size, GREEN + (255,)); gl.putalpha(a)
    gll = Image.new('RGBA', out.size, (0, 0, 0, 0)); gll.alpha_composite(gl, (pad, pad))
    gll = gll.filter(ImageFilter.GaussianBlur(18))
    out.alpha_composite(gll); out.alpha_composite(gll)
    out.alpha_composite(lg, (pad, pad))
    bb = out.split()[3].point(lambda v: 255 if v > 40 else 0).getbbox()
    return out.crop(bb)


def date_badge(scale, year=False):
    d = text_layer('7', F('anton', int(150 * scale)), glow=GREEN_D, glow_r=10)
    m = text_layer('JANVIER', F('mont900', int(40 * scale)), fill=GREEN, tracking=int(3 * scale))
    parts = [d, m]
    if year:
        parts.append(text_layer('2027', F('mont800', int(28 * scale)), tracking=int(6 * scale)))
    inner = stack(parts, gap=int(2 * scale))
    return on_box(inner, padx=int(26 * scale), pady=int(10 * scale), radius=int(18 * scale), width=max(3, int(4 * scale)))


def dj_block(scale):
    dj = text_layer('DJ TAM', F('anton', int(120 * scale)), glow=GREEN_D, glow_r=14)
    fr = text_layer('(FUN RADIO)', F('mont800', int(32 * scale)), fill=GREEN, tracking=int(4 * scale))
    return stack([dj, fr], gap=int(4 * scale))


def small(txt, size, fill=WHITE, tracking=None):
    return text_layer(txt, F('mont800', size), fill=fill, tracking=tracking if tracking is not None else int(size * 0.12))


def hours(scale):
    return on_box(text_layer('21H – 1H', F('anton', int(64 * scale)), tracking=int(3 * scale)),
                  padx=int(36 * scale), pady=int(6 * scale), radius=int(12 * scale), width=max(3, int(4 * scale)))


def free(scale):
    return small('ENTRÉE ET PARKING GRATUITS', int(26 * scale))


def ambiance(scale):
    return on_box(small('AMBIANCE GÉNÉRALISTE', int(24 * scale), fill=DARK),
                  padx=int(20 * scale), pady=int(6 * scale), radius=int(6 * scale),
                  fill=GREEN + (255,), outline=GREEN, width=2, glow=True)


def prep_bg(path, size, focus_y=0.5, darken_mid=True):
    bg = Image.open(path).convert('RGB')
    W, H = size
    s = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * s + .5), int(bg.height * s + .5)), Image.LANCZOS)
    x = (bg.width - W) // 2
    y = int((bg.height - H) * focus_y)
    bg = bg.crop((x, y, x + W, y + H))
    bg = ImageEnhance.Contrast(bg).enhance(1.08)
    bg = bg.convert('RGBA')
    if darken_mid:
        # léger voile sombre pour la lisibilité des textes
        v = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        dv = ImageDraw.Draw(v)
        for i in range(H):
            t = i / H
            a = int(110 * max(0, 1 - abs(t - 0.45) / 0.45))
            dv.line((0, i, W, i), fill=(0, 8, 4, a))
        bg.alpha_composite(v)
    return bg


def layout(fmt, bg_path):
    """Retourne (fond, [(nom, calque, (x, y))]) pour 'rect', 'carre' ou 'story'."""
    L = []
    if fmt == 'rect':
        W, H = 1200, 630
        bg = prep_bg(bg_path, (W, H), focus_y=0.5)
        s = 0.62
        logo = logo_block(200, 15)
        L.append(('logo', logo, (W - logo.width - 26, 22)))
        db = date_badge(s, year=True)
        L.append(('date', db, (34, 30)))
        tb = title_block(590)
        L.append(('titre', tb, ((W - tb.width) // 2 - 10, 40)))
        am = ambiance(0.8)
        L.append(('ambiance', am, ((W - am.width) // 2, 232)))
        dj = dj_block(0.9)
        L.append(('dj', dj, ((W - dj.width) // 2, 300)))
        hr = hours(0.7)
        fr = on_box(free(0.72), padx=18, pady=14, radius=10, width=3, fill=(4, 20, 12, 210))
        L.append(('horaire', hr, (W // 2 - hr.width - 2, 506)))
        L.append(('gratuit', fr, (W // 2 + 2, 508)))
    elif fmt == 'carre':
        W, H = 1080, 1080
        bg = prep_bg(bg_path, (W, H), focus_y=0.5)
        logo = logo_block(270, 20)
        L.append(('logo', logo, (W - logo.width - 34, 26)))
        db = date_badge(0.68, year=True)
        L.append(('date', db, (40, 34)))
        tb = title_block(880)
        L.append(('titre', tb, ((W - tb.width) // 2, 285)))
        am = ambiance(1.1)
        L.append(('ambiance', am, ((W - am.width) // 2, 575)))
        dj = dj_block(1.1)
        L.append(('dj', dj, ((W - dj.width) // 2, 630)))
        hr = hours(1.0)
        L.append(('horaire', hr, ((W - hr.width) // 2, 860)))
        fr = free(1.0)
        L.append(('gratuit', fr, ((W - fr.width) // 2, 990)))
    else:  # story
        W, H = 1080, 1920
        bg = prep_bg(bg_path, (W, H), focus_y=0.5)
        logo = logo_block(330, 24)
        L.append(('logo', logo, ((W - logo.width) // 2, 150)))
        dt = on_box(text_layer('JEUDI 7 JANVIER', F('anton', 62), tracking=4), padx=34, pady=8, radius=12)
        L.append(('date', dt, ((W - dt.width) // 2, 440)))
        tb = title_block(960)
        L.append(('titre', tb, ((W - tb.width) // 2, 600)))
        am = ambiance(1.2)
        L.append(('ambiance', am, ((W - am.width) // 2, 955)))
        dj = dj_block(1.3)
        L.append(('dj', dj, ((W - dj.width) // 2, 1015)))
        hr = hours(1.2)
        L.append(('horaire', hr, ((W - hr.width) // 2, 1290)))
        fr = on_box(free(1.15), padx=30, pady=16, radius=12, width=3, fill=(4, 20, 12, 220))
        L.append(('gratuit', fr, ((W - fr.width) // 2, 1700)))
    return bg, L


def flatten(bg, L):
    out = bg.copy()
    for _, im, pos in L:
        out.alpha_composite(im, pos)
    return out.convert('RGB')


if __name__ == '__main__':
    import sys
    fmt, src, dst = sys.argv[1:4]
    bg, L = layout(fmt, src)
    flatten(bg, L).save(dst)
    print(dst)
