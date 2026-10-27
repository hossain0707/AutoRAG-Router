"""Render a self-contained cinematic product-concept video and animated README preview.

Dependencies: pip install pillow numpy, plus FFmpeg on PATH. Video is illustrative;
the actual functional demo is the web UI at localhost:8000.
"""
from __future__ import annotations

import math
import os
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS, SEC = 960, 540, 18, 24
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if not Path(FONT).exists():
    FONT = BOLD = 'DejaVuSans.ttf'


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def text(d, xy, value, size=24, fill=(230, 242, 255), bold=False):
    d.text(xy, value, font=font(size, bold), fill=fill)


def rect(d, xy, fill, line=(40, 76, 119), radius=15):
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=line, width=2)


def background(t):
    y, x = np.ogrid[:H, :W]
    glow = np.maximum(0, 1-np.sqrt((x-(W*.7+70*math.sin(t*.25)))**2+(y-H*.1)**2)/700)
    base = np.zeros((H, W, 3), dtype=np.uint8)
    base[:,:,0] = (7+6*glow).astype('uint8')
    base[:,:,1] = (12+26*glow).astype('uint8')
    base[:,:,2] = (28+42*glow).astype('uint8')
    return Image.fromarray(base)


def draw_frame(t):
    im=background(t); d=ImageDraw.Draw(im)
    opacity=min(1, max(0, t*2))
    text(d,(54,32),'◈  AutoRAG Router',21,(112,215,255),True)
    text(d,(790,35),'ENGINE  v0.1',13,(114,153,197))
    d.line((52,77,910,77),fill=(38,66,100),width=2)
    scene=min(4,int(t//4.8)); local=(t%4.8)/4.8
    panels=[
        ('ONE QUERY.','THE RIGHT RETRIEVAL.', 'Why force every task through one RAG pipeline?'),
        ('ANALYZE INTENT.','ROUTE INTELLIGENTLY.', 'Complexity • evidence • data type • query intent'),
        ('PICK THE PATH.','NOT THE GUESS.', 'Hybrid • Graph • Agentic • Multimodal • Structured'),
        ('CHECK EVIDENCE.','FALL BACK SAFELY.', 'Transparent trace and grounded source snippets'),
        ('BUILD BETTER AI.','WITH AUTORAG.', 'Local-first • Open API • Explainable routing')]
    head,sub,desc=panels[scene]
    text(d,(57,109),head,39,(237,244,255),True)
    text(d,(57,159),sub,37,(100,211,252),True)
    text(d,(58,216),desc,16,(146,172,204))
    if scene in (0,1):
        rect(d,(56,288,904,444),(13,27,47))
        text(d,(79,307),'USER QUERY',14,(111,143,179),True)
        phrase = ('How are Atlas and Beacon connected?' if scene==0
                  else 'Detecting: relationship reasoning')
        maxchars=int(len(phrase)*min(1, local*2.2)); text(d,(79,349),phrase[:maxchars]+'▌',25,(231,243,255))
        text(d,(79,402),'INPUT → TASK ANALYSIS',12,(94,209,180))
    elif scene==2:
        chips=[('NO-RAG',67),('HYBRID',215),('GRAPH',363),('AGENTIC',511),('VISUAL',659),('DATA',807)]
        for i,(label,x) in enumerate(chips):
            active = (i==2)
            y=307+int(5*math.sin(t*3+i))
            rect(d,(x,y,x+126,y+75),(22,60,83) if active else (17,31,52),
                 (102,222,242) if active else (42,68,96),11)
            text(d,(x+13,y+24),label,14,(163,244,247) if active else (136,162,194),True)
        text(d,(355,412),'GRAPH SELECTED  •  confidence 0.82',14,(89,220,176))
    elif scene==3:
        rect(d,(57,280,904,463),(12,25,42))
        lines=['› policy: graph','› retrieved: 2 entity-linked documents','› evidence_check: pass','› answer: Atlas sends normalized records to Beacon']
        for i,line in enumerate(lines):
            if local>i*.12:text(d,(86,304+i*37),line,19,(117,237,191) if i<3 else (206,227,249))
    else:
        rect(d,(57,280,904,451),(11,28,47))
        text(d,(78,306),'GET STARTED',15,(122,221,246),True)
        text(d,(78,342),'pip install -e .',28,(236,241,255),True)
        text(d,(78,396),'github.com/hossain0707/AutoRAG-Router',16,(140,203,235))
    # Thin animated light trail at footer.
    d.rounded_rectangle((56,487,904,493),radius=3,fill=(38,59,89))
    d.rounded_rectangle((56,487,56+int(848*t/SEC),493),radius=3,fill=(94,212,242))
    text(d,(56,507),'SYNTHETIC PRODUCT DEMONSTRATION  •  NO EXTERNAL AI CALLS',11,(95,125,161))
    return im


def sound(path):
    rate=32000
    n=SEC*rate
    ts=np.arange(n)/rate
    # Quiet soft original synth bed; no commercial music samples.
    melody=[220,261.63,329.63,293.66,246.94,329.63,392,293.66]
    audio=np.zeros(n,dtype=np.float64)
    for ix,note in enumerate(melody):
        start=ix*3
        wave1=np.sin(2*np.pi*note*ts)+.23*np.sin(2*np.pi*note*2*ts)
        env=np.exp(-1.2*np.maximum(0,ts-start)) * (ts>=start)
        audio+=.13*wave1*env
    audio+=.012*np.sin(2*np.pi*55*ts)
    audio*=np.minimum(1,ts/1.5)*np.minimum(1,(SEC-ts)/1.6)
    audio=np.clip(audio,-.8,.8)
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate)
        wav.writeframes((audio*32767).astype('<i2').tobytes())


def main():
    wav=OUT/'promo_audio.wav'; video=OUT/'AutoRAG_Router_Promo.mp4'
    sound(wav)
    proc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}',
                           '-r',str(FPS),'-i','-','-i',str(wav),'-c:v','libx264','-preset','veryfast','-crf','24',
                           '-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',str(video)],stdin=subprocess.PIPE)
    preview=[]
    for frame in range(SEC*FPS):
        t=frame/FPS
        im=draw_frame(t)
        proc.stdin.write(im.tobytes())
        if frame%27==0:preview.append(im.resize((640,360)))
    proc.stdin.close()
    if proc.wait()!=0:raise RuntimeError('ffmpeg failed')
    preview[0].save(OUT/'router-demo.gif',save_all=True,append_images=preview[1:],duration=180,loop=0,optimize=True)
    wav.unlink()
    print(f'Created {video} ({video.stat().st_size:,} bytes) and router-demo.gif')


if __name__=='__main__':main()
