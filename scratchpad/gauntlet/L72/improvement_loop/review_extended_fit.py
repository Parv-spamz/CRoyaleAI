"""Once-only outside review after all fixed-weight diagnostic jobs complete."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'extended_fit_audit'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed.json').exists()
    p=read(HERE/'prepared.json'); c=read(HERE/'collected.json'); v=read(HERE/'verified.json')
    assert p['complete'] and c['complete'] and v['complete'] and read(HERE/'chain_complete.json')['complete']
    assert p['controls']==dict(positive=2,negative=6)
    assert c['prepared_sha256']==sha(HERE/'prepared.json') and v['collected_sha256']==sha(HERE/'collected.json')
    assert c['optimizer_updates']==c['development_inference']==v['optimizer_updates']==v['development_inference']==0
    assert set(c['models'])==set(v['models'])=={'ordinary_extended_v5','ordinary_no_dropout_v5'}
    for name,x in c['models'].items():
        y=v['models'][name]
        assert x['complete'] and y['complete'] and x['weights_unchanged']
        assert y['controls']==dict(positive=4,negative=10)
        assert x['optimizer_updates']==x['development_inference']==0
        assert y['collected_sha256']==sha(HERE/'collected.json')
        assert x['fresh_inference_rows']==y['fresh_inference_rows']==p['native_rows']+p['mirrored_rows']
        assert x['counts_sha256']==y['counts_sha256']
    assert c['fresh_inference_rows']==v['fresh_inference_rows']==2*(p['native_rows']+p['mirrored_rows'])
    for path,h in p['sources'].items():assert sha(ROOT/path)==h,path
    receipts={}
    for stage in ('prepare','collect','independent'):
        f=CHECKS/('l72-extended-fit-'+stage+'.json'); r=read(f); out=f.with_suffix('.out')
        assert r['exit_code']==0 and r['matched']
        assert hashlib.sha256(out.read_text(encoding='utf-8').encode()).hexdigest()==r['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(f),output_sha256=sha(out),seconds=r['seconds'])
    result=dict(complete=True,receipts=receipts,bindings={f:sha(HERE/f) for f in
        ('prepared.json','collected.json','verified.json','chain_complete.json')},
        source_sha256=sha(Path(__file__)),new_models=0,optimizer_updates=0,development_inference=0,
        accepted=False,deployed=False)
    (HERE/'reviewed.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('EXTENDED_FIT_REVIEWED')
if __name__=='__main__':main()
