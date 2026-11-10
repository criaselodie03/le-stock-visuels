"""Anime un visuel statique (story 1080x1920) façon boîte de nuit, calé sur la voix off.
Seuls le mouvement et la lumière changent : le visuel n'est jamais redessiné.
Usage : python3 animate.py visuel.png voix.mp3 sortie.mp4 bands.json
bands.json : liste de [y0, y1, t_apparition] en fractions de hauteur / secondes."""
import sys, json, subprocess, math
import numpy as np
from PIL import Image

src, voice, dst, bands_path = sys.argv[1:5]
COL = [float(x) for x in sys.argv[5].split(",")] if len(sys.argv) > 5 else [0.18, 1.0, 0.6]
W, H, FPS = 1080, 1920, 30
BPM = 124
BEAT = 60 / BPM

dur_voice = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                           '-of', 'csv=p=0', voice]).decode())
T = min(20.0, max(15.0, dur_voice + 1.4))
N = int(T * FPS)
bands = json.load(open(bands_path))
reveal_times = [b[2] for b in bands]
def _mask(b0, b1, f=0.012):
    y = np.arange(H, dtype=np.float32) / H
    m = np.clip((y - b0) / f + 0.5, 0, 1) * np.clip((b1 - y) / f + 0.5, 0, 1)
    return np.repeat(m[:, None], W, axis=1)
MASKS = {(b[0], b[1]): _mask(b[0], b[1]) for b in bands}

base = np.asarray(Image.open(src).convert('RGB').resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def ease_out(x):
    x = min(max(x, 0), 1)
    return 1 - (1 - x) ** 3

def beam(cx, cy, ang, width, length):
    """Faisceau de lumière (cône) partant de (cx, cy), angle en radians (0 = vers le bas)."""
    dx, dy = xx - cx, yy - cy
    r = np.sqrt(dx * dx + dy * dy) + 1e-3
    a = np.arctan2(dx, dy) - ang
    cone = np.exp(-(a / width) ** 2) * np.exp(-r / length)
    return cone

GREEN = np.array(COL, np.float32)
WHITE = np.array([1.0, 1.0, 1.0], np.float32)

rng = np.random.default_rng(7)
sparks = [(rng.uniform(0, W), rng.uniform(0, H * 0.75), rng.uniform(0, T), rng.uniform(4, 10)) for _ in range(60)]

MUSIC = sys.argv[6] if len(sys.argv) > 6 else None
if MUSIC:
    ain = ['-i', voice, '-stream_loop', '-1', '-i', MUSIC]
    fc = ('[1:a]adelay=400|400,apad,asplit=2[v][sc];'
          f'[2:a]atrim=0:{T:.2f},volume=0.55,afade=t=in:d=0.3,afade=t=out:st={T-1.2:.2f}:d=1.2[m];'
          '[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];'
          '[v][md]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]')
else:
    ain = ['-i', voice]
    fc = '[1:a]adelay=400|400,apad[a]'
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                       '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-'] + ain + [
                       '-filter_complex', fc, '-map', '0:v', '-map', '[a]',
                       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
                       '-profile:v', 'high', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '192k',
                       '-t', f'{T:.2f}', dst], stdin=subprocess.PIPE)

calm = T - 2.2  # dernières secondes : visuel complet et stable
off = 0.4       # la voix démarre à 0,4 s
for i in range(N):
    t = i / FPS
    tv = t - off
    # --- mouvement : arrivée en zoom arrière puis légère pulsation sur le beat
    beat_phase = (t % BEAT) / BEAT
    pulse = math.exp(-beat_phase * 6) if t < calm else 0
    z = 1 + 0.07 * (1 - ease_out(t / 2.2)) + 0.006 * pulse
    if z > 1.0005:
        cw, ch = W / z, H / z
        x0, y0 = (W - cw) / 2, (H - ch) / 2
        img = Image.fromarray((base * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR,
                                                                    box=(x0, y0, x0 + cw, y0 + ch))
        frame = np.asarray(img).astype(np.float32) / 255
    else:
        frame = base.copy()

    # --- apparition des zones de texte en rythme (zone sombre puis révélée avec un flash)
    for (b0, b1, tr) in bands:
        k = ease_out((tv - tr) / 0.35) if tr > -0.5 else 1
        if k < 1:
            m = MASKS[(b0, b1)]
            frame *= (1 - m * (0.75 * (1 - k)))[..., None]

    # --- faisceaux de lumière qui balaient, intensité sur le beat
    if t < calm:
        fade = 1.0 if t < calm - 0.8 else (calm - t) / 0.8
        s1 = math.sin(t * 1.3) * 0.5
        s2 = math.sin(t * 1.1 + 2) * 0.5
        light = (beam(W * 0.15, -40, -0.35 + s1, 0.09, 1400) + beam(W * 0.85, -40, 0.35 + s2, 0.09, 1400)
                 + 0.7 * beam(W * 0.5, -60, math.sin(t * 0.8) * 0.6, 0.06, 1200))
        inten = (0.18 + 0.22 * pulse) * fade
        frame += light[..., None] * GREEN * inten
        # flashs aux moments clés de la voix
        fl = sum(math.exp(-max(0, tv - tr) * 9) for tr in reveal_times if tv >= tr) if t > off else 0
        fl += 0.35 * pulse * (1 if int(t / BEAT) % 4 == 0 else 0)
        if fl > 0.01:
            frame += (WHITE * 0.5 + GREEN * 0.5) * min(fl, 1.2) * 0.22 * fade
        # paillettes
        for (sx, sy, st, sr) in sparks:
            ph = (t - st) % 2.4
            if ph < 0.5:
                a = math.sin(ph / 0.5 * math.pi) * fade
                x0, x1 = int(max(0, sx - 3 * sr)), int(min(W, sx + 3 * sr))
                y0, y1 = int(max(0, sy - 3 * sr)), int(min(H, sy + 3 * sr))
                g = np.exp(-(((xx[y0:y1, x0:x1] - sx) ** 2 + (yy[y0:y1, x0:x1] - sy) ** 2) / (2 * sr * sr)))
                frame[y0:y1, x0:x1] += g[..., None] * np.array([1.0, 0.9, 0.55]) * 0.8 * a
    # --- fondu d'entrée
    if t < 0.25:
        frame *= t / 0.25
    ff.stdin.write((np.clip(frame, 0, 1) * 255).astype(np.uint8).tobytes())

ff.stdin.close(); ff.wait()
print(dst, f'{T:.2f}s', N, 'frames')
