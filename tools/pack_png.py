# Emballe un fichier (mp4, mp3...) dans un PNG sans perte, pour le déposer dans Trello
# via une balise image + canvas (le fetch direct depuis trello.com est bloqué).
# Format : 4 octets de longueur (big endian) + données, en pixels RGB, largeur 2048.
import sys, math, hashlib, numpy as np
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read(); data = len(b).to_bytes(4, 'big') + b
W = 2048; H = math.ceil(math.ceil(len(data) / 3) / W)
arr = np.zeros(W * H * 3, np.uint8); arr[:len(data)] = np.frombuffer(data, np.uint8)
Image.fromarray(arr.reshape(H, W, 3), 'RGB').save(dst)
print(len(b), hashlib.sha256(b).hexdigest())
