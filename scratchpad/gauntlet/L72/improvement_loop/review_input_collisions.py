import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'input_collision_audit'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed.json').exists()
    c=read(HERE/'collected.json');v=read(HERE/'verified.json');s=read(HERE/'started.json')
    assert c['complete'] and v['complete'] and read(HERE/'chain_complete.json')['complete']
    assert c['summary']==v['summary'] and c['summary']['rows']==213995
    assert c['controls']==dict(label_fixture=1,input_mutations=16,label_exclusion=1)
    assert v['controls']==dict(positive=2,negative=7)
    assert c['model_inference']==c['optimizer_updates']==v['model_inference']==v['optimizer_updates']==0
    assert v['collected_sha256']==sha(HERE/'collected.json') and c['started_sha256']==sha(HERE/'started.json')
    for path,h in s['sources'].items():assert sha(ROOT/path)==h,path
    receipts={}
    for stage in ('collect','independent'):
        f=CHECKS/('l72-input-collisions-'+stage+'.json');r=read(f);out=f.with_suffix('.out')
        assert r['exit_code']==0 and r['matched']
        assert hashlib.sha256(out.read_text(encoding='utf-8').encode()).hexdigest()==r['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(f),output_sha256=sha(out),seconds=r['seconds'])
    result=dict(complete=True,receipts=receipts,summary=v['summary'],source_sha256=sha(Path(__file__)),
        bindings={f:sha(HERE/f) for f in ('started.json','collected.json','verified.json','chain_complete.json')},
        model_inference=0,optimizer_updates=0,accepted=False,deployed=False)
    (HERE/'reviewed.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('INPUT_COLLISIONS_REVIEWED')
if __name__=='__main__':main()
