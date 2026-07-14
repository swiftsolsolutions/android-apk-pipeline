#!/usr/bin/env python3
"""
gen-play-graphics.py — generate Play Store graphics at exact Play specs.

Produces, into the fastlane `supply` image layout so they can be committed AND
auto-uploaded:

  <out>/icon.png                     512x512  32-bit PNG (alpha OK)
  <out>/featureGraphic.png          1024x500  24-bit PNG (NO alpha)
  <out>/phoneScreenshots/<n>.png    1080x1920 24-bit (>=2 required)
  <out>/sevenInchScreenshots/<n>.png 1200x1920
  <out>/tenInchScreenshots/<n>.png  1600x2560

Screenshots are built by FRAMING source images (real captures from the
`screengrab`/screenshots lane, or hand-made UI mockups) inside a phone frame on
a branded background with a caption. The icon + feature graphic are generated
from brand config; pass icon_src to use the app's real launcher art instead of
the built-in monogram/QR motif.

Play spec notes baked in:
  - feature graphic MUST be 1024x500 with NO transparency (flattened to RGB).
  - screenshots: 24-bit PNG/JPEG, each side 320..3840 px, ratio within 9:16..16:9.
  - icon: 512x512, 32-bit PNG, <=1 MB.

Usage:  python3 gen-play-graphics.py --config play-graphics.config.json
Config keys: app_name, subtitle, tagline, brand{c1,c2,accent}, motif("qr"|"mono"),
  icon_src(optional path), out_dir, screenshots[{src, caption}].
Deps: Pillow (required), qrcode[pil] (only if motif=="qr" and no icon_src).
"""
import argparse, json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---- fonts (fall back to default if DejaVu missing) ----
_FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def font(sz, bold=True):
    try:
        return ImageFont.truetype(_FB if bold else _FR, sz)
    except Exception:
        return ImageFont.load_default()

def grad(w, h, c1, c2):
    im = Image.new("RGB", (w, h)); px = im.load()
    for y in range(h):
        for x in range(w):
            t = (x + y) / (w + h)
            px[x, y] = tuple(int(c1[i] + (c2[i]-c1[i])*t) for i in range(3))
    return im

def rr(d, box, r, **kw): d.rounded_rectangle(box, radius=r, **kw)
def ctext(d, cx, y, s, fnt, fill):
    d.text((cx - d.textlength(s, font=fnt)/2, y), s, font=fnt, fill=fill)

# ---------------- ICON (512) ----------------
def make_icon(cfg, out):
    S, SS = 512, 2048
    c1 = tuple(cfg["brand"]["c1"]); c2 = tuple(cfg["brand"]["c2"])
    bg = grad(SS, SS, c1, c2)
    if cfg.get("icon_src") and os.path.exists(cfg["icon_src"]):
        fg = Image.open(cfg["icon_src"]).convert("RGBA")
        pad = int(SS*0.16); box = SS - 2*pad
        fg.thumbnail((box, box), Image.LANCZOS)
        bg = bg.convert("RGBA")
        bg.paste(fg, ((SS-fg.width)//2, (SS-fg.height)//2), fg)
    else:
        mask = Image.new("L", (SS, SS), 0); d = ImageDraw.Draw(mask)
        sc = SS/512.0
        def R(x,y,w,h,r,fill): d.rounded_rectangle([x*sc,y*sc,(x+w)*sc,(y+h)*sc], radius=r*sc, fill=fill)
        if cfg.get("motif","qr") == "qr":
            def finder(ox,oy,size=104):
                gap=size*0.20
                R(ox,oy,size,size,size*0.28,255)
                R(ox+gap,oy+gap,size-2*gap,size-2*gap,size*0.20,0)
                inn=size*0.34; ic=ox+size/2-inn/2
                R(ic,oy+size/2-inn/2,inn,inn,inn*0.32,255)
            gl,gt,area=96,96,320
            finder(gl,gt); finder(gl+area-104,gt); finder(gl,gt+area-104)
            m,pitch,rad=30,40,9
            for (cx,cy) in [(5,5),(6,5),(7,5),(5,6),(7,6),(6,7),(7,7),(5,8),(6,8),
                            (8,6),(8,7),(8,8),(6,6),(4,7),(7,4),(8,4),(4,8),(8,5)]:
                x=96+cx*pitch; y=96+cy*pitch
                if x+m<=96+area and y+m<=96+area: R(x,y,m,m,rad,255)
        else:  # monogram
            letters = "".join(w[0] for w in cfg["app_name"].split()[:2]).upper()
            fnt = font(int(SS*0.42))
            tw = ImageDraw.Draw(mask).textlength(letters, font=fnt)
            ImageDraw.Draw(mask).text(((SS-tw)/2, SS*0.24), letters, font=fnt, fill=255)
        white = Image.new("RGB", (SS, SS), (255,255,255))
        bg = Image.composite(white, bg, mask)
    bg = bg.resize((S, S), Image.LANCZOS).convert("RGBA")
    bg.save(os.path.join(out, "icon.png"))

# ---------------- FEATURE GRAPHIC (1024x500, no alpha) ----------------
def make_feature(cfg, out):
    W,H = 1024,500
    fg = grad(W, H, tuple(cfg["brand"]["c1"]), tuple(cfg["brand"]["c2"]))
    d = ImageDraw.Draw(fg); acc = tuple(cfg["brand"]["c2"])
    # brand mark (3 finders + dots) on the left
    mx,my,fs = 90,120,120
    for (dx,dy) in [(0,0),(190,0),(0,190)]:
        rr(d,[mx+dx,my+dy,mx+dx+fs,my+dy+fs],fs*0.28,fill=(255,255,255))
        g=fs*0.22; rr(d,[mx+dx+g,my+dy+g,mx+dx+fs-g,my+dy+fs-g],fs*0.16,fill=acc)
        inn=fs*0.30; ic=mx+dx+fs/2-inn/2; ir=my+dy+fs/2-inn/2
        rr(d,[ic,ir,ic+inn,ir+inn],inn*0.3,fill=(255,255,255))
    for (cx,cy) in [(320,230),(360,270),(320,310),(400,230),(360,350),(400,310)]:
        rr(d,[mx+cx,my+cy,mx+cx+34,my+cy+34],8,fill=(255,255,255))
    # auto-fit centered text block in the right zone
    zx0,zx1=470,992; zcx=(zx0+zx1)/2; zw=zx1-zx0
    def fit(t,mx_,start,bold=True):
        sz=start
        while sz>16 and d.textlength(t,font=font(sz,bold))>mx_: sz-=2
        return font(sz,bold)
    tf=fit(cfg["app_name"],zw,92,True)
    sf=fit(cfg.get("subtitle",""),zw,44,False)
    gf=fit(cfg.get("tagline",""),zw,36,False)
    th=tf.size+12+sf.size+10+gf.size; ty=(H-th)/2-6
    ctext(d,zcx,ty,cfg["app_name"],tf,(255,255,255)); ty+=tf.size+12
    if cfg.get("subtitle"): ctext(d,zcx,ty,cfg["subtitle"],sf,(230,248,246)); ty+=sf.size+10
    if cfg.get("tagline"):  ctext(d,zcx,ty,cfg["tagline"],gf,(200,238,234))
    fg.convert("RGB").save(os.path.join(out, "featureGraphic.png"))  # flatten: no alpha

# ---------------- SCREENSHOT FRAMER ----------------
def frame_shot(src, cw, ch, caption, brand):
    bg = grad(cw, ch, tuple(brand["c1"]), tuple(brand["c2"])); d = ImageDraw.Draw(bg)
    cap_f = font(int(cw*0.058))
    words=caption.split(); lines=[]; cur=""
    for wd in words:
        if d.textlength((cur+" "+wd).strip(),font=cap_f) < cw*0.86: cur=(cur+" "+wd).strip()
        else: lines.append(cur); cur=wd
    if cur: lines.append(cur)
    ty=ch*0.055
    for ln in lines: ctext(d,cw/2,ty,ln,cap_f,(255,255,255)); ty+=cw*0.075
    ui = Image.open(src).convert("RGB")
    top=ty+ch*0.02; ph_h=ch-top-ch*0.05; ratio=ui.width/ui.height; ph_w=ph_h*ratio
    if ph_w>cw*0.80: ph_w=cw*0.80; ph_h=ph_w/ratio
    ph_w,ph_h=int(ph_w),int(ph_h); px=int((cw-ph_w)//2); py=int(top); bez=max(10,int(ph_w*0.035))
    sh=Image.new("RGBA",(cw,ch),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    rr(sd,[px-bez,py-bez,px+ph_w+bez,py+ph_h+bez],int(ph_w*0.11),fill=(0,0,0,90))
    sh=sh.filter(ImageFilter.GaussianBlur(int(ph_w*0.03))); bg.paste(sh,(0,0),sh)
    d.rounded_rectangle([px-bez,py-bez,px+ph_w+bez,py+ph_h+bez],radius=int(ph_w*0.11),fill=(18,24,26))
    uimg=ui.resize((ph_w,ph_h),Image.LANCZOS)
    mask=Image.new("L",(ph_w,ph_h),0); ImageDraw.Draw(mask).rounded_rectangle([0,0,ph_w,ph_h],radius=int(ph_w*0.08),fill=255)
    bg.paste(uimg,(px,py),mask)
    return bg.convert("RGB")

def make_screenshots(cfg, out):
    shots=cfg.get("screenshots",[]); brand=cfg["brand"]
    dirs={"phoneScreenshots":(1080,1920),"sevenInchScreenshots":(1200,1920),"tenInchScreenshots":(1600,2560)}
    for name,(w,h) in dirs.items():
        dd=os.path.join(out,name); os.makedirs(dd,exist_ok=True)
        # phone gets all; tablets get first 2 (>=2 required)
        subset = shots if name=="phoneScreenshots" else shots[:2]
        for i,s in enumerate(subset,1):
            if not os.path.exists(s["src"]): 
                print("  ! missing source:", s["src"]); continue
            frame_shot(s["src"], w, h, s.get("caption",""), brand).save(os.path.join(dd,f"{i}.png"))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",required=True)
    a=ap.parse_args(); cfg=json.load(open(a.config))
    out=cfg.get("out_dir","fastlane/metadata/android/en-US/images"); os.makedirs(out,exist_ok=True)
    make_icon(cfg,out);      print("icon.png")
    make_feature(cfg,out);   print("featureGraphic.png")
    make_screenshots(cfg,out);print("screenshots done ->", out)

if __name__=="__main__": main()
