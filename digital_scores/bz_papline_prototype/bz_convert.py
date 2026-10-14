import sys, json; sys.path.insert(0,'.')
import pymupdf, bz_extract as bx
BASE={'F047':'PetastiPlusHypsiliRight','F073':'Oligon','F06A':'Apostrophos','F061':'Ison','F063':'KentemataPlusOligon','F0CE':'KentemataPlusOligon',
 'F066':'OligonPlusKentimaAbove','F064':'OligonPlusKentimaBelow','F053':'Petasti','F04A':'PetastiPlusApostrophos',
 'F044':'PetastiPlusOligon','F046':'PetastiPlusKentimaAbove','F06C':'ElaphronPlusApostrophos','F02D':'OligonPlusApostrophosPlusKentemata','F05F':'OligonPlusIsonPlusKentemata','F0A2':'OligonPlusKentimaBelow','F067':'OligonPlusHypsiliRight','F07A':'OligonPlusKentemata','F03B':'Hamili','F076':'OligonPlusKentemata','F078':'Kentemata',
 'F027':'Hyporoe','F06B':'Elaphron','F068':'RunningElaphron','F041':'PetastiPlusIson?','F03D':'DoubleApostrophos','F02B':'IsonPlusApostrophos'}
BASEL={'F073':'OligonPlusHypsiliLeft','F03D':'OligonPlusElaphronPlusApostrophos','F029':'OligonPlusApostrophos','F064':'OligonPlusHypsiliPlusKentimaHorizontal','F061':'OligonPlusKentemataPlusHypsiliRight','F03F':'OligonPlusKentimaBelow','F070':'OligonPlusElaphronPlusKentemata'}  # BZLoipa bases
LOIPA_VOCAL={'F07D':'Heteron','F03F':'Antikenoma'}
# BZFthores (font, code) -> Neanes Fthora stem; names from the CTAN package,
# shapes checked against the psaltis' theory book (Μέθοδος, pp. 101-103).
FTHORA={}
for codes,name in (('F066 F046 F056 F076 F087','DiatonicPa'),('F067 F047','DiatonicVou'),('F068 F048','DiatonicGa'),
    ('F06A F04A F04D F06D F086','DiatonicThi'),('F06B F04B F02C F03C F081','DiatonicKe'),('F06C F04C','DiatonicZo'),
    ('F064 F044 F063 F043','DiatonicNiLow'),('F03B F03A F02F F03F','DiatonicNiHigh'),
    ('F031 F021 F051 F071','HardChromaticPa'),('F034 F024 F052 F072','HardChromaticThi'),
    ('F032 F040 F057 F077 F085','SoftChromaticThi'),('F033 F023 F045 F065','SoftChromaticPa'),
    ('F039 F028 F049 F069','Zygos'),('F02D F05F F050 F070','Kliton'),('F060 F07E','Spathi')):
    for c in codes.split(): FTHORA[c]=name
for c in ('F029','F06F'): FTHORA[c]='GeneralFlat'   # \zwanwyfesh: flat of Zo
FTH_MART={'F073':'Ke','F07A':'Ga','F061':'Thi'}          # martyria letters drawn in BZFthores
FTH_MARTSIGN={'F053','F05A','F041','F058','F078','F07C'}
GORGON={'F072','F065','F0D8','F0D0','F045','F052'}
KLASMA={'F055','F075','F069','F091','F049'}
TIME={'F02A':'Hapli','F038':'Hapli','F028':'Dipli','F039':'Dipli','F029':'Tripli','F030':'Tripli'}
VOCAL={'F02C':'Homalon','F03C':'Homalon','F0F9':'Heteron','F05D':'Homalon','F02F':'Psifiston','F06D':'Antikenoma','F04D':'Antikenoma'}
VAREIA={'F05C'}
ISOKR={}
for names,val in (('F066 F046 F052','Ison.Pa'),('F064 F045','Ison.Ni'),('F073 F053 F04C F04F F06C','Ison.Zo'),('F067 F047 F054','Ison.Vou'),('F068 F048 F059','Ison.Ga'),('F06A F055 F04A','Ison.Thi'),('F06B F049 F04B','Ison.Ke'),('F027 F022','Ison.KeLow'),('F03B F03A','Ison.ThiLow'),('F061 F041','Ison.Unison')):
    for c in names.split(): ISOKR[c]=val
MART={'F031':'Pa','F032':'Vou','F033':'Ga','F034':'Thi','F035':'Ke','F036':'Zo','F037':'Ni'}
MARTSIGN={'F021','F023','F026','F040','F05E','F060'}  # F060: two red dots of a martyria
IGNORE={'F020','F04F','F0FA','F07E','F06F'}  # F06F: diastole (bar line)
# Yfesis (flat), drawn in red right of or over the neume: plain (\yfesh,
# \yfeshD in BZByzantina) and digrammos (\digryfesh in BZFthores).
YFESIS={('BZByzantina','F074'):'Flat_2_Right',('BZByzantina','F079'):'Flat_2_Right',
        ('BZFthores','F074'):'Flat_6_Right',('BZFthores','F079'):'Flat_6_Right',
        ('BZFthores','F06E'):'Sharp_2_Left'}  # \dieshMD: plain diesis (sharp)
def isbase(a): return (a['font']=='BZByzantina' and a['code'] in BASE) or (a['font']=='BZLoipa' and a['code'] in BASEL)
def basename(a): return BASE[a['code']] if a['font']=='BZByzantina' else BASEL[a['code']]
def convert(page, line_index):
    ry,gg,ll=bx.lines(page)[line_index]
    gg=[a for a in gg if a['font'] in ('BZByzantina','BZLoipa','BZIson','BZFthores')]
    bases=[a for a in gg if isbase(a)]
    bases.sort(key=lambda a:a['x0'])
    notes=[dict(base=b,att=[]) for b in bases]
    warn=[]
    pending_vareia=False; mfth={}
    marts=[a for a in gg if (a['font']=='BZByzantina' and a['code'] in MART) or (a['font']=='BZFthores' and a['code'] in FTH_MART)]
    for a in sorted(gg,key=lambda a:a['x0']):
        c=a['code']
        if isbase(a): continue
        if a['font']=='BZByzantina' and (c in MART or (c in MARTSIGN and any(abs((m['x0']+m['x1'])/2-(a['x0']+a['x1'])/2)<25 for m in marts))): continue
        if a['font']=='BZFthores' and (a['font'],c) not in YFESIS:
            if c in FTH_MART or c in FTH_MARTSIGN: continue
            if c not in FTHORA: warn.append(('fthora-unmapped',c,round(a['x0'])));continue
            cx=(a['x0']+a['x1'])/2
            near=[m for m in marts if abs((m['x0']+m['x1'])/2-cx)<25]
            if near: mfth[id(near[0])]=FTHORA[c]+'_Top'; continue
        if a['font']=='BZIson' and c not in ISOKR: warn.append(('bzison-unmapped',c,round(a['x0'])));continue
        if c in IGNORE: warn.append(('ignored',c,round(a['x0'])));continue
        # best base by x overlap
        best=None;bo=0
        for n in notes:
            b=n['base']; o=min(a['x1'],b['x1'])-max(a['x0'],b['x0'])
            if o>bo: bo=o;best=n
        if c in VAREIA:
            # vareia precedes its base: next base to the right
            nxt=[n for n in notes if n['base']['x0']>=a['x0']-1]
            best=nxt[0] if nxt else None
        if best is None and ((a['font'],c) in YFESIS or (a['font'],c)==('BZByzantina','F043')):
            # a flat right of its neume: the nearest base ending just before it
            left=[n for n in notes if n['base']['x1']<=a['x0']+3 and a['x0']-n['base']['x1']<15]
            best=max(left,key=lambda n:n['base']['x1']) if left else None
        if best is None: warn.append(('no-base',c,round(a['x0'])));continue
        best['att'].append(a)
    # lyric syllables
    syl=[];cur=None
    for l in sorted(ll,key=lambda l:l['x']):
        if cur and l['x']-cur['x1']<2.5: cur['t']+=l['c'];cur['x1']=l['x1']
        else:
            cur=dict(t=l['c'],x0=l['x'],x1=l['x1']);syl.append(cur)
    assign={}
    for s in syl:
        cx=(s['x0']+s['x1'])/2
        j=min(range(len(notes)),key=lambda i:abs((notes[i]['base']['x0']+notes[i]['base']['x1'])/2-cx))
        assign.setdefault(j,[]).append(s['t'])
    events=[]
    for i,n in enumerate(notes):
        b=n['base']; e={'elementType':'Note','quantitativeNeume':basename(b)}
        if (b['font'],b['code']) in (('BZLoipa','F03F'),('BZByzantina','F07A')): e['vocalExpressionNeume']='Antikenoma'
        by=(b['y0']+b['y1'])/2
        for a in n['att']:
            c=a['code']; ay=(a['y0']+a['y1'])/2; top=ay<by
            if (a['font'],c) in YFESIS: e['accidental']=YFESIS[(a['font'],c)]
            elif (a['font'],c)==('BZByzantina','F043') and e['quantitativeNeume']=='Oligon':
                # a separate kentima at the right end of the oligon (up two),
                # the slanted stroke of F064; read from the martyria, unconfirmed.
                # vfilip once read the bare glyph as hyporoe; in context it is not.
                e['quantitativeNeume']='OligonPlusKentimaBelow'
            elif a['font']=='BZFthores': e['fthora']=FTHORA[c]+('_Top' if top else '_Bottom')
            elif a['font']=='BZIson': e['ison']=ISOKR[c]
            elif a['font']=='BZLoipa' and c=='F0A5': e['gorgonNeume']='Digorgon'
            elif a['font']=='BZLoipa' and c=='F060': e['gorgonNeume']='GorgonDottedLeft'  # \pg
            elif a['font']=='BZLoipa' and c=='F021': e['gorgonNeume']='GorgonDottedRight'  # \gpPD
            elif a['font']=='BZLoipa' and c=='F0A8': e['gorgonNeume']='Trigorgon'
            elif a['font']=='BZByzantina' and c=='F03F': e['vocalExpressionNeume']='HeteronConnecting'  # syndesmos
            elif a['font']=='BZByzantina' and c=='F077': e['gorgonNeume']='Argon'
            elif c in GORGON: e['gorgonNeume']='Gorgon_Top' if top else 'Gorgon_Bottom'
            elif c in KLASMA: e['timeNeume']='Klasma_Top' if top else 'Klasma_Bottom'
            elif c in TIME: e['timeNeume']=TIME[c]
            elif a['font']=='BZLoipa' and c in LOIPA_VOCAL: e['vocalExpressionNeume']=LOIPA_VOCAL[c]
            elif c in VOCAL: e['vocalExpressionNeume']=VOCAL[c]
            elif c in VAREIA: e['vareia']=True
            else: warn.append(('unmapped',a['font'],c,round(a['x0'])))
        if i in assign: e['lyrics']=''.join(assign[i])
        events.append((e,[b['code']]+[a['code'] for a in n['att']],b['x0']))
    for m in marts:
        me={'elementType':'Martyria','source_note':(MART if m['font']=='BZByzantina' else FTH_MART)[m['code']]}
        if id(m) in mfth: me['fthora']=mfth[id(m)]
        events.append((me,['MART '+m['code']],m['x0']))
    events.sort(key=lambda t:t[2])
    return [(e,c) for e,c,_ in events],warn
if __name__=='__main__':
    d=pymupdf.open(sys.argv[1]); ev,w=convert(d[int(sys.argv[2])],int(sys.argv[3]))
    for e,codes in ev: print(codes, json.dumps({k:v for k,v in e.items() if k!='elementType'},ensure_ascii=False))
    print('WARN',w)
