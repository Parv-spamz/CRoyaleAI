"""Close the already independently verified terminal policy comparison; no replay."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'terminal_wrapper_policy'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed_results.json').exists()
    r=read(HERE/'report.json');v=read(HERE/'verified.json')
    assert r['complete'] and v['complete'] and read(HERE/'chain_complete.json')['complete']
    assert sha(HERE/'report.json')==v['report_sha256']
    assert sha(HERE/'setups_verified.json')==r['setups_sha256']
    assert len(r['records'])==32 and len(v['pairs'])==16
    assert v['fulltime_pairs']==sum(p['fulltime'] for p in v['pairs'])==2
    assert v['removed_decisions']==sum(p['removed_decisions'] for p in v['pairs'])==30
    assert v['native_neutral'] and not v['production_changed'] and not v['policy_deployment_accepted']
    assert v['controls']==dict(positive=1,negative=7)
    for p,h in r['sources'].items():assert sha(ROOT/p)==h,p
    for x in r['records']:assert sha(ROOT/x['path'])==x['sha256']
    receipts={}
    for name,script,token in [('collection','collect.py','TERMINAL_POLICY_COLLECTION_COMPLETE'),('independent','verify.py','TERMINAL_POLICY_VERIFIED')]:
        p=CHECKS/f'l72-terminal-policy-{name}.json';q=read(p)
        assert q['exit_code']==0 and q['matched'] and q['expected']==token
        assert Path(q['command'][-1]).resolve()==(HERE/script).resolve()
        assert hashlib.sha256(p.with_suffix('.out').read_text().encode()).hexdigest()==q['output_sha256']
        receipts[name]=dict(receipt_sha256=sha(p),output_sha256=sha(p.with_suffix('.out')),seconds=q['seconds'])
    out=dict(complete=True,report_sha256=sha(HERE/'report.json'),verified_sha256=sha(HERE/'verified.json'),receipts=receipts,
             games=32,pairs=16,fulltime_pairs=2,removed_decisions=30,engineering_only=True,production_changed=False,new_models=0,deployment_accepted=False)
    (HERE/'reviewed_results.json').write_text(json.dumps(out,indent=2)+'\n')
    print('TERMINAL_POLICY_REVIEW_COMPLETE')
if __name__=='__main__':main()
