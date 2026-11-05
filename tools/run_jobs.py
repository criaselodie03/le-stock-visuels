"""Traite les fichiers jobs/*.json : télécharge l'image source (URL publique), compose les logos si demandé, range le résultat dans le dépôt."""
import glob, json, os, subprocess, sys, urllib.request
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(R, 'tools')
for jf in sorted(glob.glob(os.path.join(R, 'jobs', '*.json'))):
    for job in json.load(open(jf)):
        raw = os.path.join(R, job['raw'])
        os.makedirs(os.path.dirname(raw), exist_ok=True)
        if job.get('url') and not os.path.exists(raw):
            req = urllib.request.Request(job['url'], headers={'User-Agent': 'Mozilla/5.0'})
            open(raw, 'wb').write(urllib.request.urlopen(req, timeout=120).read())
            print('fetched', job['raw'], os.path.getsize(raw))
        if job.get('out'):
            out = os.path.join(R, job['out'])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            subprocess.check_call([sys.executable, os.path.join(T, 'mois.py'), raw, out] + [str(x) for x in job['args']], cwd=T)
            if job.get('friends'):
                subprocess.check_call([sys.executable, os.path.join(T, 'friends_add.py'), out] + [str(x) for x in job['friends']], cwd=T)
            for p in glob.glob(out + '.prev.jpg'):
                os.remove(p)
            print('composed', job['out'])
    os.remove(jf)
