"""Outside review of the frozen fit assay; never performs model work."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'dropout_free_fit'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    assert not (HERE/'reviewed_evidence.json').exists()
    p=read(HERE/'prepared.json'); t=read(HERE/'trained.json'); v=read(HERE/'training_verified.json')
    e=read(HERE/'evaluated.json'); r=read(HERE/'results_verified.json')
    assert all(x['complete'] for x in (p,t,v,e,r,read(HERE/'chain_complete.json')))
    assert p['controls']==dict(positive=2,negative=6) and p['optimizer_updates']==0 and p['probe_weights_unchanged']
    assert v['controls']==dict(positive=1,negative=8) and r['controls']==dict(positive=9,negative=12)
    assert t['finite_updates']==v['finite_updates']==4096 and v['draws']==p['draws']==524288
    assert v['trained_sha256']==sha(HERE/'trained.json') and e['training_verified_sha256']==sha(HERE/'training_verified.json')
    assert r['evaluated_sha256']==sha(HERE/'evaluated.json') and e['total_views']==2048 and e['reused_control_views']==6144
    assert e['checkpoints']['dropout_free_final']==v['checkpoint_sha256']==t['checkpoint_sha256']
    assert r['quarantined'] and not r['eligible_policy_parent'] and e['development_inference']==r['development_inference']==0
    assert e['diagnostic_fit']==r['diagnostic_fit']==all(all(r['filters']['dropout_free_final/'+o].values()) for o in ('native','mirrored'))
    for path,h in p['sources'].items(): assert sha(ROOT/path)==h,path
    assert p['dropout_controls']==dict(positive=3,negative=1) and all(p['mechanism'].values())
    receipts={}
    for stage in ('prepare','train','training-independent','eval','results-independent'):
        f=CHECKS/('l72-dropout-free-fit-'+stage+'.json'); q=read(f); out=f.with_suffix('.out')
        assert q['exit_code']==0 and q['matched']
        assert hashlib.sha256(out.read_text(encoding='utf-8').encode()).hexdigest()==q['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(f),output_sha256=sha(out),seconds=q['seconds'])
    data=dict(complete=True,receipts=receipts,bindings={name:sha(HERE/name) for name in
        ('prepared.json','trained.json','training_verified.json','evaluated.json','results_verified.json','chain_complete.json')},
        source_sha256=sha(Path(__file__)),diagnostic_fit=r['diagnostic_fit'],quarantined=True,eligible_policy_parent=False,accepted=False,deployed=False)
    (HERE/'reviewed_evidence.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print('DROPOUT_FREE_FIT_EVIDENCE_REVIEWED')

if __name__=='__main__': main()
