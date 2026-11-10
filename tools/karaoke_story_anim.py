import sys, numpy as np, subprocess
from PIL import Image, ImageFilter, ImageDraw
src, dur, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
FPS=30; W,H=1080,1920; BPM=120; beat=60/BPM
im=Image.open(src).convert('RGB')
s=H/im.height; big=im.resize((round(im.width*s),H),Image.LANCZOS)
x0=(big.width-W)//2; base=np.asarray(big.crop((x0,0,x0+W,H))).astype(np.float32)
# pre-scaled versions for zoom done via PIL per frame
baseimg=Image.fromarray(base.astype(np.uint8))
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
rng=np.random.default_rng(7)
sp=[(rng.uniform(80,1000),rng.uniform(300,1500),rng.uniform(0,6.28),rng.uniform(1.5,3.5),rng.uniform(6,14)) for _ in range(28)]
n=int(dur*FPS)
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','veryfast',out],stdin=subprocess.PIPE)
for i in range(n):
    t=i/FPS
    # zoom: intro 1.10->1.0 in 1.2s, then slow push 1.0->1.04, last 2s settle to 1.0
    if t<1.2: z=1.10-0.10*(1-(1-t/1.2)**3)
    elif t<dur-2: z=1.0+0.035*(t-1.2)/(dur-3.2)
    else: z=1.035*(1-min(1,(t-(dur-2))/1.0))+1.0*min(1,(t-(dur-2))/1.0)
    cw,ch=W/z,H/z; l=(W-cw)/2; tp=(H-ch)/2
    fr=np.asarray(baseimg.resize((W,H),Image.BICUBIC,box=(l,tp,l+cw,tp+ch))).astype(np.float32)
    end=t>dur-2
    # beat pulse
    ph=(t%beat)/beat; pulse=0 if end or t<1.2 else 0.10*np.exp(-ph*6)
    fr*=1+pulse
    if not end and t>=1.2:
        # two sweeping spotlight beams from top corners
        for k,(ox,sgn) in enumerate(((60,1),(1020,-1))):
            ang=np.deg2rad(sgn*(18+14*np.sin(2*np.pi*(t/3.2)+k*1.7)))
            dx=xx-ox; dy=yy+40
            a=np.arctan2(dx,dy)-ang
            beam=np.exp(-(a/0.09)**2)*np.clip(1-dy/2100,0,1)
            fr+=beam[...,None]*np.array([255,205,120],np.float32)*0.28
        # diagonal shine every 4 beats
        cyc=(t-1.2)%(beat*8)/(beat*8)
        pos=-600+cyc*3200
        d=(xx*0.6+yy*0.8)-pos
        fr+=np.exp(-(d/70)**2)[...,None]*np.array([255,235,170],np.float32)*0.30
        # sparkles
        for (sx,sy,ph0,f,r) in sp:
            v=max(0,np.sin(ph0+t*f))**6
            if v<0.05: continue
            x1,x2,y1,y2=int(sx-r*3),int(sx+r*3),int(sy-r*3),int(sy+r*3)
            gx,gy=xx[y1:y2,x1:x2]-sx,yy[y1:y2,x1:x2]-sy
            st=(np.exp(-(gx/r)**2*8-(gy/1.5)**2)+np.exp(-(gy/r)**2*8-(gx/1.5)**2)+np.exp(-(gx**2+gy**2)/(r*r*0.15)))*v
            fr[y1:y2,x1:x2]+=st[...,None]*np.array([255,240,200],np.float32)*0.9
    # fade in from black
    if t<0.5: fr*=t/0.5
    p.stdin.write(np.clip(fr,0,255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait()
