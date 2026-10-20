"""Review existing sequence results and receipts, without rerunning collection."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5];HERE=Path(__file__).resolve().parent/'sequence_data'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed.json').exists()
    s=read(HERE/'started.json');c=read(HERE/'collected.json');v=read(HERE/'verified.json');end=read(HERE/'chain_complete.json')
    assert c['complete'] and v['complete'] and end['complete']
    assert c['started_sha256']==sha(HERE/'started.json') and v['collected_sha256']==sha(HERE/'collected.json')
    assert c['rows']==v['rows']==268718 and c['replays']==v['replays']==1978
    assert v['controls']==dict(positive_prefixes=55,positive_windows=3,corruptions=18)
    assert v['original_labels_exact'] and v['all_features_exact'] and v['all_windows_exact'] and v['all_replays_exact']
    for p,h in s['sources'].items():assert sha(ROOT/p)==h,p
    receipts={}
    for stage in ('preflight','collect','verify'):
        p=CHECKS/('l72-hand-sequence-'+stage+'.json');r=read(p);out=p.with_suffix('.out')
        assert r['exit_code']==0 and r['matched'] and hashlib.sha256(out.read_text().encode()).hexdigest()==r['output_sha256']
        receipts[stage]=dict(seconds=r['seconds'],receipt_sha256=sha(p),output_sha256=sha(out))
    result=dict(complete=True,receipts=receipts,bindings={n:sha(HERE/n) for n in
        ('started.json','collected.json','verified.json','chain_complete.json')},source_sha256=sha(Path(__file__)),
        no_model=True,accepted=False,deployed=False)
    (HERE/'reviewed.json').write_text(json.dumps(result,indent=2));print('HAND_SEQUENCE_REVIEWED')
if __name__=='__main__':main()
