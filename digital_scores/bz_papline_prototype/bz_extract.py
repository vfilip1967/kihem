"""Prototype: extract lines of BZ glyphs + lyrics from a papline PDF page."""
import sys, re, json, pymupdf
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
FD='/tmp/kihem-ez-pilot/ctan-byz/byzantinemusic/fonts/'
_f={}
def ink(font,cp):
    if font not in _f:
        t=TTFont(FD+font+'.otf'); _f[font]=(t,t.getGlyphSet(),t.getBestCmap(),t['head'].unitsPerEm)
    t,gs,cm,upm=_f[font]; g=cm.get(cp)
    if g is None: return None
    bp=BoundsPen(gs); gs[g].draw(bp)
    return None if bp.bounds is None else tuple(v/upm for v in bp.bounds)+(gs[g].width/upm,)
def page_glyphs(pg):
    out=[]; lyr=[]
    for b in pg.get_text('rawdict')['blocks']:
        for l in b.get('lines',[]):
            for s in l['spans']:
                f=re.sub(r'^[A-Z]{6}\+','',s['font']); size=s['size']
                for c in s['chars']:
                    ch=c['c']; x,y=c['origin']
                    if f in ('BZByzantina','BZLoipa','BZFthores','BZIson','BZPalaia','BZXronos') and ch.strip():
                        bb=ink(f,ord(ch))
                        if bb is None: continue
                        out.append(dict(font=f,code=f'{ord(ch):04X}',x=x,y=y,size=size,x0=x+bb[0]*size,x1=x+bb[2]*size,y0=y-bb[3]*size,y1=y-bb[1]*size))
                    elif f.startswith(('GFS','TimesNew')) and ch.strip():
                        lyr.append(dict(c=ch,x=x,y=y,x1=c['bbox'][2]))
    return out,lyr
def lines(pg):
    g,lyr=page_glyphs(pg)
    ys=sorted({round(l['y'],0) for l in lyr}); ys=[y for y in ys if y<800]
    # cluster
    cl=[]
    for y in ys:
        if cl and y-cl[-1][-1]<6: cl[-1].append(y)
        else: cl.append([y])
    rows=[sum(c)/len(c) for c in cl]
    res=[]
    for i,ry in enumerate(rows):
        lo=ry-45; hi=ry+12
        gg=[a for a in g if lo<=a['y']<=hi]; ll=[a for a in lyr if abs(a['y']-ry)<6]
        res.append((ry,sorted(gg,key=lambda a:(a['x0'])),ll))
    return res
if __name__=='__main__':
    d=pymupdf.open(sys.argv[1]); pg=d[int(sys.argv[2])]
    ln=lines(pg)[int(sys.argv[3])]
    ry,gg,ll=ln
    print('lyric y',ry,'glyphs',len(gg))
    for a in gg: print(a['font'][:6],a['code'],f"x0={a['x0']:.1f} x1={a['x1']:.1f} y={a['y']:.1f} ink_y=({a['y0']:.1f},{a['y1']:.1f})")
    print(''.join(l['c'] for l in ll))
