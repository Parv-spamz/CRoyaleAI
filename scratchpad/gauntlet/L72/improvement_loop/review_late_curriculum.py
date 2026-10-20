"""Outside closeout, once all five frozen curriculum jobs succeed."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent/'development_rl_3';CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed_evidence.json').exists()
    p=read(HERE/'prepared.json');t=read(HERE/'trained.json');v=read(HERE/'training_verified.json');r=read(HERE/'results_verified.json')
    assert p['complete'] and t['complete'] and v['complete'] and r['complete'] and read(HERE/'chain_complete.json')['complete']
    assert p['controls']==dict(positive=7,negative=8) and p['optimizer_steps']==0
    assert t['total_games']==v['games']==2048 and t['total_optimizer_steps']==v['optimizer_steps']==512
    assert v['controls']==dict(positive=32,negative=17) and v['trained_sha256']==sha(HERE/'trained.json')
    assert r['training_verified_sha256']==sha(HERE/'training_verified.json') and r['rows']==54723 and not r['deployment_accepted']
    for f,h in p['sources'].items():assert sha(ROOT/f)==h,f
    for a,x in t['arms'].items():assert sha(ROOT/x['checkpoint'])==x['checkpoint_sha256'] and r['checkpoints'][a]==x
    receipts={}
    for stage in ('prepare','train','training-independent','eval','results-independent'):
        f=CHECKS/f'l72-late-curriculum-{stage}.json';a=read(f);o=f.with_suffix('.out')
        assert a['exit_code']==0 and a['matched']
        assert hashlib.sha256(o.read_text(encoding='utf-8').encode()).hexdigest()==a['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(f),output_sha256=sha(o),seconds=a['seconds'])
    out=dict(complete=True,receipts=receipts,results_verified_sha256=sha(HERE/'results_verified.json'),training_verified_sha256=sha(HERE/'training_verified.json'),
        prepared_sha256=sha(HERE/'prepared.json'),trained_sha256=sha(HERE/'trained.json'),verdicts=r['verdicts'],source_sha256=sha(Path(__file__)),accepted=False,deployed=False)
    (HERE/'reviewed_evidence.json').write_text(json.dumps(out,indent=2)+'\n');print('LATE_CURRICULUM_EVIDENCE_REVIEWED')
if __name__=='__main__':main()
