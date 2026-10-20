"""Independently reconstruct the fixed first ten emitted records before queueing."""
import itertools
from verify import reconstruct,compare,state
from io_utils import *

def main():
    binding=check_binding();a=load_rows();lookup={int(x):i for i,x in enumerate(a['ids'])}
    with (OUT/'rows_v2.jsonl').open() as f:rows=[json.loads(x) for x in itertools.islice(f,10)]
    assert len(rows)==10 and len(set(r['tag'] for r in rows))==1
    tag=rows[0]['tag'];src=binding['sources'][tag];assert sha(ROOT/src['path'])==src['sha256']
    rec=read(ROOT/src['path']);frames=[]
    for f in rec['frames']:
        if not frames or f!=frames[-1]:frames.append(f)
    labels={}
    for line in LABELS.open():
        x=json.loads(line)
        if x['tag']==tag and x['card']=='x-bow':labels[(x['side'],x['tick'])]=x
    for row in rows:
        i=lookup[row['id']];base={k:a[k][i] for k in FIELDS}
        expected=reconstruct(base,rec,frames,labels,binding['card_vocab'])
        compare(expected,{k:row[k] for k in expected})
    synthetic={'towers':[[s,k,None if k=='king' else lane,x,0,hp,mx]
        for s in (0,1) for k,lane,x,hp,mx in
        [('king','king',9000,2000,10000 if s==0 else 4000),
         ('princess','left',3500,1000 if s==0 else 900,2000 if s==0 else 1000),
         ('princess','right',14500,3000,3052)]]}
    assert state(synthetic,0)['margin']==100 and state(synthetic,0)['fraction_margin']<0
    write(HERE/'verify_preflight.json',dict(complete=True,original_rows=10,absolute_fraction_control=True,
        verifier_sha256=sha(HERE/'verify.py'),source_sha256=sha(HERE/'verify_preflight.py')))
    print('MATCH_ADAPTATION_VERIFY_PREFLIGHT_PASS')

if __name__=='__main__':main()
