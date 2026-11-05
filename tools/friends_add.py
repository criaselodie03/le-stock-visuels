import sys
from PIL import Image, ImageFilter
p,cy,wf=sys.argv[1],float(sys.argv[2]),float(sys.argv[3])
bg=Image.open(p).convert('RGBA');W,H=bg.size
f=Image.open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'friends_logo.png'));w=int(W*wf);f=f.resize((w,int(f.height*w/f.width)),Image.LANCZOS)
sh=Image.new('RGBA',f.size,(0,0,0,255));sh.putalpha(f.split()[3].point(lambda v:int(v*.7)))
L=Image.new('RGBA',(f.width+40,f.height+40),(0,0,0,0));L.alpha_composite(sh,(20,23));L=L.filter(ImageFilter.GaussianBlur(5));L.alpha_composite(f,(20,20))
bg.alpha_composite(L,((W-L.width)//2,int(H*cy-L.height/2)))
bg.convert('RGB').save(p);bg.convert('RGB').resize((600,int(600*H/W))).save(p+'.prev.jpg',quality=88)
