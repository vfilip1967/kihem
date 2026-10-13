import sys, json; sys.path.insert(0,'.')
import pymupdf, bz_extract as bx
BASE={'F073':'Oligon','F06A':'Apostrophos','F061':'Ison','F063':'KentemataPlusOligon','F0CE':'KentemataPlusOligon',
 'F066':'OligonPlusKentimaAbove','F064':'OligonPlusKentimaBelow','F053':'Petasti','F04A':'PetastiPlusApostrophos',
 'F044':'PetastiPlusOligon','F046':'PetastiPlusKentimaAbove','F06C':'ElaphronPlusApostrophos','F02D':'OligonPlusApostrophosPlusKentemata','F05F':'OligonPlusIsonPlusKentemata','F0A2':'OligonPlusKentimaBelow','F076':'OligonPlusKentemata','F078':'Kentemata',
 'F027':'Hyporoe','F043':'Hyporoe','F06B':'Elaphron','F068':'RunningElaphron','F041':'PetastiPlusIson?','F03D':'DoubleApostrophos','F02B':'IsonPlusApostrophos'}
GORGON={'F072','F065','F0D8','F0D0','F045','F052'}
KLASMA={'F075','F069','F091','F049'}
TIME={'F02A':'Hapli','F038':'Hapli','F028':'Dipli','F039':'Dipli','F029':'Tripli','F030':'Tripli'}
VOCAL={'F0F9':'Heteron','F05D':'Homalon','F02F':'Psifiston','F06D':'Antikenoma','F04D':'Antikenoma'}
VAREIA={'F05C'}
ISOKR={}
for names,val in (('F066 F046 F052','Ison.Pa'),('F064 F045','Ison.Ni'),('F073 F053 F04C F04F F06C','Ison.Zo'),('F067 F047 F054','Ison.Vou'),('F068 F048 F059','Ison.Ga'),('F06A F055 F04A','Ison.Thi'),('F06B F049 F04B','Ison.Ke'),('F027 F022','Ison.KeLow'),('F03B F03A','Ison.ThiLow'),('F061 F041','Ison.Unison')):
    for c in names.split(): ISOKR[c]=val
MART={'F031':'Pa','F032':'Vou','F033':'Ga','F034':'Thi','F035':'Ke','F036':'Zo','F037':'Ni'}
MARTSIGN={'F021','F023','F026','F040','F05E'}
IGNORE={'F020','F04F','F0FA','F07E'}
def convert(page, line_index):
    ry,gg,ll=bx.lines(page)[line_index]
    gg=[a for a in gg if a['font'] in ('BZByzantina','BZLoipa','BZIson')]
    bases=[a for a in gg if a['code'] in BASE and a['font']=='BZByzantina']
    bases.sort(key=lambda a:a['x0'])
    notes=[dict(base=b,att=[]) for b in bases]
    warn=[]
    pending_vareia=False
    marts=[a for a in gg if a['font']=='BZByzantina' and a['code'] in MART]
    for a in sorted(gg,key=lambda a:a['x0']):
        c=a['code']
        if c in BASE and a['font']=='BZByzantina': continue
        if a['font']=='BZByzantina' and (c in MART or (c in MARTSIGN and any(abs((m['x0']+m['x1'])/2-(a['x0']+a['x1'])/2)<25 for m in marts))): continue
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
        b=n['base']; e={'elementType':'Note','quantitativeNeume':BASE[b['code']]}
        by=(b['y0']+b['y1'])/2
        for a in n['att']:
            c=a['code']; ay=(a['y0']+a['y1'])/2; top=ay<by
            if a['font']=='BZIson': e['ison']=ISOKR[c]
            elif c in GORGON: e['gorgonNeume']='Gorgon_Top' if top else 'Gorgon_Bottom'
            elif c in KLASMA: e['timeNeume']='Klasma_Top' if top else 'Klasma_Bottom'
            elif c in TIME: e['timeNeume']=TIME[c]
            elif c in VOCAL: e['vocalExpressionNeume']=VOCAL[c]
            elif c in VAREIA: e['vareia']=True
            else: warn.append(('unmapped',a['font'],c,round(a['x0'])))
        if i in assign: e['lyrics']=''.join(assign[i])
        events.append((e,[b['code']]+[a['code'] for a in n['att']],b['x0']))
    for m in marts:
        events.append(({'elementType':'Martyria','source_note':MART[m['code']]},['MART '+m['code']],m['x0']))
    events.sort(key=lambda t:t[2])
    return [(e,c) for e,c,_ in events],warn
if __name__=='__main__':
    d=pymupdf.open(sys.argv[1]); ev,w=convert(d[int(sys.argv[2])],int(sys.argv[3]))
    for e,codes in ev: print(codes, json.dumps({k:v for k,v in e.items() if k!='elementType'},ensure_ascii=False))
    print('WARN',w)
