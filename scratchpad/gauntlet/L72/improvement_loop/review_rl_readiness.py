"""Receipt/source binding of completed sampled readiness, no inference."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent/'rl_readiness'
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed_results.json').exists();v=read(HERE/'verified.json');r=read(HERE/'report.json')
    assert v['complete'] and r['complete'] and read(HERE/'chain_complete.json')['complete']
    assert v['report_sha256']==sha(HERE/'report.json') and v['controls']==dict(positive=1,negative=9)
    assert r['optimizer_updates']==r['new_models']==0 and not r['deployment_accepted']
    for p,h in r['sources'].items():assert sha(ROOT/p)==h,p
    for x in r['records']:
        for kind in ('result','trajectory'):assert sha(ROOT/x[kind])==x[kind+'_sha256']
    receipts={}
    for stage,token in [('collection','RL_READINESS_COLLECTION_COMPLETE'),('independent','RL_READINESS_VERIFIED')]:
        p=ROOT/f'scratchpad/gauntlet/L71/integration/checks/l72-rl-readiness-{stage}.json';q=read(p)
        assert q['exit_code']==0 and q['matched'] and q['expected']==token
        assert hashlib.sha256(p.with_suffix('.out').read_text().encode()).hexdigest()==q['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(p),output_file_sha256=sha(p.with_suffix('.out')),seconds=q['seconds'])
    assert sum(x['rows'] for x in v['totals'].values())==2406
    out=dict(complete=True,report_sha256=sha(HERE/'report.json'),verified_sha256=sha(HERE/'verified.json'),receipts=receipts,totals=v['totals'],optimizer_updates=0,new_models=0,engineering_only=True,deployment_accepted=False)
    (HERE/'reviewed_results.json').write_text(json.dumps(out,indent=2)+'\n');print('RL_READINESS_REVIEW_COMPLETE')
if __name__=='__main__':main()
