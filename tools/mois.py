"""Pose les logos officiels (Le Stock + Les apéros du Jeudi) sur un fond ChatGPT.
usage: python3 mois.py fond.png out.png W H stock_cx stock_y stock_w aper_cx aper_y aper_w R G B
Coordonnées en fraction de la largeur/hauteur (cx = centre, y = haut)."""
import sys
from PIL import Image, ImageDraw, ImageFilter
import compose as C


def glowed(lg, col, blur=18, sh_off=8, sh_col=None):
    pad = 40
    out = Image.new('RGBA', (lg.width + 2 * pad, lg.height + 2 * pad), (0, 0, 0, 0))
    a = lg.split()[3]
    sh = Image.new('RGBA', lg.size, (sh_col or (0, 0, 0)) + (255,)); sh.putalpha(a.point(lambda v: int(v * .85)))
    shl = Image.new('RGBA', out.size, (0, 0, 0, 0)); shl.alpha_composite(sh, (pad, pad + sh_off))
    out.alpha_composite(shl.filter(ImageFilter.GaussianBlur(10)))
    gl = Image.new('RGBA', lg.size, col + (255,)); gl.putalpha(a)
    gll = Image.new('RGBA', out.size, (0, 0, 0, 0)); gll.alpha_composite(gl, (pad, pad))
    gll = gll.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(gll); out.alpha_composite(gll)
    out.alpha_composite(lg, (pad, pad))
    return out, pad


def stock_block(width, col, shade=None):
    lg = C.LOGO.resize((width, int(C.LOGO.height * width / C.LOGO.width)), Image.LANCZOS)
    tmp = ImageDraw.Draw(Image.new('L', (1, 1)))
    size = 40
    bw = tmp.textlength('LA LOUVIÈRE', font=C.F('mont800', size))
    size = max(10, int(size * width * 0.86 / bw))
    font = C.F('mont800', size)
    bw = tmp.textlength('LA LOUVIÈRE', font=font)
    tracking = max(0, (width * 0.98 - bw) / 10)
    dark = shade or tuple(int(c * .35) for c in col)
    sub = C.text_layer('LA LOUVIÈRE', font, fill=col, glow=dark, glow_r=6, tracking=tracking, shadow=shade is None)
    if sub.width > width:
        sub = sub.resize((width, int(sub.height * width / sub.width)), Image.LANCZOS)
    gap = int(width * 0.01)
    W = max(lg.width, sub.width)
    out = Image.new('RGBA', (W, lg.height + gap + sub.height), (0, 0, 0, 0))
    out.alpha_composite(lg, ((W - lg.width) // 2, 0))
    out.alpha_composite(sub, ((W - sub.width) // 2, lg.height + gap))
    g, pad = glowed(out, shade or (0, 0, 0), blur=8, sh_off=4, sh_col=shade)
    return g, pad


def main():
    a = sys.argv[1:]
    bg = Image.open(a[0]).convert('RGBA')
    W, H = int(a[2]), int(a[3])
    bg = bg.resize((W, H), Image.LANCZOS)
    scx, sy, sw, acx, ay, aw = map(float, a[4:10])
    col = tuple(int(x) for x in a[10:13])
    shade = tuple(int(x) for x in a[13:16]) if len(a) >= 16 else None
    s, p = stock_block(int(sw * W), col, shade)
    bg.alpha_composite(s, (int(scx * W - s.width / 2), int(sy * H - p)))
    ap = C.APEROS.resize((int(aw * W), int(C.APEROS.height * aw * W / C.APEROS.width)), Image.LANCZOS)
    g, p = glowed(ap, col)
    bg.alpha_composite(g, (int(acx * W - g.width / 2), int(ay * H - p)))
    bg.convert('RGB').save(a[1])
    bg.convert('RGB').resize((600, int(600 * H / W))).save(a[1] + '.prev.jpg', quality=85)


if __name__ == '__main__':
    main()
