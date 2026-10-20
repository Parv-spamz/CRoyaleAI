"""Outside closeout for the frozen additional ordinary-fit experiment."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'development_iteration_10'
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
    assert p['dropout_controls']==dict(positive=2,negative=1) and p['initial_eval_exact'] and p['roundtrip_exact'] and p['prior_schedule_exact']
    assert v['optimizer_parameters']==96 and v['optimizer_parameter_step_range']==[8000,8000]
    assert v['controls']==dict(positive=1,negative=9) and r['controls']==dict(positive=2,negative=10)
    assert t['finite_updates']==v['finite_updates']==8000 and v['draws']==p['draws']==1024000
    assert v['trained_sha256']==sha(HERE/'trained.json') and e['training_verified_sha256']==sha(HERE/'training_verified.json')
    assert r['evaluated_sha256']==sha(HERE/'evaluated.json') and r['rows']==e['rows']==54723
    assert r['checkpoint_sha256']==e['checkpoint_sha256']==v['checkpoint_sha256']==t['checkpoint_sha256']
    for path,h in p['sources'].items(): assert sha(ROOT/path)==h,path
    receipts={}
    for stage in ('prepare','train','training-independent','eval','results-independent'):
        f=CHECKS/('l72-development10-'+stage+'.json'); q=read(f); out=f.with_suffix('.out')
        assert q['exit_code']==0 and q['matched']
        assert hashlib.sha256(out.read_text(encoding='utf-8').encode()).hexdigest()==q['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(f),output_sha256=sha(out),seconds=q['seconds'])
    assert r['continuation_passed']==all(all(v.values()) for v in r['filters'].values()) and not r['accepted'] and not r['deployed']
    write=dict(complete=True,receipts=receipts,bindings={name:sha(HERE/name) for name in
        ('prepared.json','trained.json','training_verified.json','evaluated.json','results_verified.json','chain_complete.json')},
        source_sha256=sha(Path(__file__)),continuation_passed=r['continuation_passed'],accepted=False,deployed=False)
    (HERE/'reviewed_evidence.json').write_text(json.dumps(write,indent=2)+'\n',encoding='utf-8')
    print('ORDINARY_NO_DROPOUT_EVIDENCE_REVIEWED')


if __name__=='__main__': main()
