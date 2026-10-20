import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'il_gradient_audit'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed.json').exists()
    c=read(HERE/'collected.json');v=read(HERE/'verified.json');s=read(HERE/'started.json')
    assert c['complete'] and v['complete'] and read(HERE/'chain_complete.json')['complete']
    assert v['model_batches']==32 and v['model_row_views']==4096 and len(c['records'])==32
    assert c['controls']==dict(positive=3) and v['controls']==dict(positive=3,negative=7)
    assert c['optimizer_updates']==v['optimizer_updates']==c['development_predictions']==0
    assert not c['new_checkpoint'] and not v['new_checkpoint']
    assert v['collected_sha256']==sha(HERE/'collected.json') and c['started_sha256']==sha(HERE/'started.json')
    for path,h in s['sources'].items():assert sha(ROOT/path)==h,path
    receipts={}
    for stage in ('collect','independent'):
        f=CHECKS/('l72-il-gradient-'+stage+'.json');r=read(f);out=f.with_suffix('.out')
        assert r['exit_code']==0 and r['matched']
        assert hashlib.sha256(out.read_text(encoding='utf-8').encode()).hexdigest()==r['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(f),output_sha256=sha(out),seconds=r['seconds'])
    result=dict(complete=True,receipts=receipts,source_sha256=sha(Path(__file__)),
        bindings={f:sha(HERE/f) for f in ('started.json','collected.json','verified.json','chain_complete.json')},
        optimizer_updates=0,new_checkpoint=False,accepted=False,deployed=False)
    (HERE/'reviewed.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('IL_GRADIENT_REVIEWED')
if __name__=='__main__':main()
