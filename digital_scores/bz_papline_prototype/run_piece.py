"""Convert several music lines (page, line) of a papline PDF into one private draft + .byzx.
usage: run_piece.py <pdf> <tag> <page:line,line,...;page:...>"""
import sys, json; sys.path.insert(0,'.'); sys.path.insert(0,'pylib'); sys.path.insert(0,'/root/projects/kihem')
import pymupdf, bz_convert as bc
pdf,tag,spec=sys.argv[1:4]
d=pymupdf.open(pdf); events=[]; report=[]
for part in spec.split(';'):
    p,ls=part.split(':'); p=int(p)
    for li in ls.split(','):
        li=int(li); ev,w=bc.convert(d[p-1],li)
        report.append((p,li,len(ev),w)); events+=[e for e,_ in ev]
draft={'purpose':'private-confirmed-ez-neanes-event-draft; not-a-complete-byzx-score','review_state':'needs_score_and_auditory_review',
 'auto_generated':True,'source':'papline %s pages/lines %s (private research)'%(pdf.rsplit('/',1)[-1],spec),
 'opening_martyria':{'note':'Pa','rootSign':'Alpha','scale':'Diatonic'},'events':events}
out='/tmp/kihem-ez-pilot/papline-pilot/'+tag
json.dump(draft,open(out+'-draft.json','w'),ensure_ascii=False,indent=1)
from src.neanes_byzx_bridge import write_private_byzx
write_private_byzx(draft,output_path=out+'.byzx',title='papline '+tag,neanes_source='/tmp/kihem-neanes-source')
for r in report: print(r)
print(len(events),'events')
