"""Additional exact accounting of decisions committed before native freeze."""
import copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'terminal_wrapper'
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(a,b):
    for side in ('0','1'):
        old=[p for p in a['plays'][side] if p['tick']<a['boundary']]
        assert old==b['plays'][side]
        assert len(old)==1 and old[0]['tick']==5990 and old[0]['land_tick']==6016
        assert not old[0]['accepted']
        assert old[0]['reason']==('game_over' if a['cap']==7200 else 'match_over_before_landing')
def main():
    r=read(HERE/'report.json');v=read(HERE/'verified.json');assert v['complete'] and v['report_sha256']==sha(HERE/'report.json')
    rows={}
    for p,h in r['records'].items():
        assert sha(ROOT/p)==h;x=read(ROOT/p);rows[x['seed'],x['cap'],x['mode']]=x
    for seed,cap in {(s,c) for s,c,m in rows}:check(rows[seed,cap,'original'],rows[seed,cap,'enabled'])
    a,b=rows[0,7200,'original'],rows[0,7200,'enabled'];bad=[]
    for key,val in [('tick',6000),('land_tick',5999),('accepted',True),('reason','missing')]:
        q=copy.deepcopy(b);q['plays']['0'][0][key]=val;bad.append(q)
    q=copy.deepcopy(b);q['plays']['0']=[];bad.append(q)
    for q in bad:
        try:check(a,q)
        except AssertionError:pass
        else:raise AssertionError('Bad pending accounting accepted')
    (HERE/'pending_verified.json').write_text(json.dumps(dict(complete=True,cases=10,pending_commands=20,positive=1,corruptions=len(bad),report_sha256=sha(HERE/'report.json'),verified_sha256=sha(HERE/'verified.json'),source_sha256=sha(Path(__file__))),indent=2)+'\n')
    print('TERMINAL_PENDING_VERIFIED')
if __name__=='__main__':main()
