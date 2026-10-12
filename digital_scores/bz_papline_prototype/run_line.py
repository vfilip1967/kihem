import sys, json; sys.path.insert(0,'.'); sys.path.insert(0,'pylib'); sys.path.insert(0,'/root/projects/kihem')
import pymupdf, bz_convert as bc, bz_extract as bx
from PIL import Image, ImageDraw, ImageFont
pdf,pno,li,tag=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
d=pymupdf.open(pdf); pg=d[pno]
ev,warn=bc.convert(pg,li)
draft={'purpose':'private-confirmed-ez-neanes-event-draft; not-a-complete-byzx-score','review_state':'needs_score_and_auditory_review',
 'auto_generated':True,'source':'papline cherubika_a4.pdf p.%d line %d (private research)'%(pno+1,li),
 'opening_martyria':{'note':'Pa','rootSign':'Alpha','scale':'Diatonic'},'events':[e for e,_ in ev]}
out='/tmp/kihem-ez-pilot/papline-pilot/'+tag
json.dump(draft,open(out+'-draft.json','w'),ensure_ascii=False,indent=1)
from src.neanes_byzx_bridge import write_private_byzx
write_private_byzx(draft,output_path=out+'.byzx',title='papline test '+tag,neanes_source='/tmp/kihem-neanes-source')
# review image
ry,gg,ll=bx.lines(pg)[li]
x0=min(a['x0'] for a in gg)-6; x1=max(a['x1'] for a in gg)+6; S=3
clip=pymupdf.Rect(x0,ry-45,x1,ry+14)
pix=pg.get_pixmap(matrix=pymupdf.Matrix(S,S),clip=clip,alpha=False)
im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
dr=ImageDraw.Draw(im); f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',16)
bases=sorted([a for a in gg if a['code'] in bc.BASE and a['font']=='BZByzantina'],key=lambda a:a['x0'])
for i,b in enumerate(bases,1):
    X=((b['x0']+b['x1'])/2-x0)*S
    dr.text((X-8,2+(i%2)*18),str(i),fill=(0,0,200),font=f)
im.save('/root/projects/kihem/debug/%s-source.png'%tag)
names={'Oligon':'ολίγον','Apostrophos':'απόστροφος','Ison':'ίσον','KentemataPlusOligon':'ολίγον + κεντήματα κάτω','OligonPlusKentemata':'ολίγον + κεντήματα πάνω','OligonPlusKentimaAbove':'ολίγον + κέντημα πάνω','OligonPlusKentimaBelow':'ολίγον + κέντημα κάτω','Elaphron':'ελαφρόν','Hyporoe':'υπορροή','Petasti':'πεταστή','PetastiPlusApostrophos':'πεταστή + απόστροφος','PetastiPlusOligon':'πεταστή + ολίγον','PetastiPlusKentimaAbove':'πεταστή + κέντημα','ElaphronPlusApostrophos':'ελαφρόν + απόστροφος'}
L=['# Αυτόματη μετατροπή · '+tag,'','Εικόνα: `%s-source.png` (οι αριθμοί αντιστοιχούν στις βάσεις).'%tag,'Διόρθωσε μόνο ό,τι είναι λάθος.','','| # | Βάση | Προσαρτήματα | Συλλαβή | Κωδικοί |','|---|---|---|---|---|']
an={'gorgonNeume':'γοργό','timeNeume':'χρόνος','vocalExpressionNeume':'τροπικό','vareia':'βαρεία','ison':'ισοκράτημα'}
for i,(e,codes) in enumerate(ev,1):
    att=', '.join(f'{an[k]}: {v if v is not True else "ναι"}' for k,v in e.items() if k in an)
    L.append(f"| {i} | {names.get(e['quantitativeNeume'],e['quantitativeNeume'])} | {att or '—'} | {e.get('lyrics','')} | {' '.join(codes)} |")
L+=['','Προειδοποιήσεις: '+str(warn)]
open('/root/projects/kihem/debug/%s-review.md'%tag,'w').write('\n'.join(L)+'\n')
print(len(ev),'events',warn)
