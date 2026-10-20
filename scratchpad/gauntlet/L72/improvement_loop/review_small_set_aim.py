"""Outside closeout for the cached aim audit; no inference."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'small_set_aim_audit'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed.json').exists()
    c=read(HERE/'collected.json'); v=read(HERE/'verified.json')
    assert c['complete'] and v['complete'] and c['rows']==v['rows']==3072
    assert v['controls']==dict(positive=1,negative=10) and v['patch_buffer_cells']==2304 and v['synthetic_same_patch_controls']==144
    assert v['collected_sha256']==sha(HERE/'collected.json') and c['counts_sha256']==v['counts_sha256']
    assert v['inference']==c['inference']==v['optimizer_updates']==c['optimizer_updates']==0 and v['weights_unchanged']
    for p,h in c['sources'].items(): assert sha(ROOT/p)==h
    receipts={}
    for stage in ('collect','independent'):
        f=CHECKS/('l72-small-set-aim-'+stage+'.json'); q=read(f); out=f.with_suffix('.out')
        assert q['exit_code']==0 and q['matched'] and hashlib.sha256(out.read_text(encoding='utf-8').encode()).hexdigest()==q['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(f),output_sha256=sha(out),seconds=q['seconds'])
    result=dict(complete=True,receipts=receipts,collected_sha256=sha(HERE/'collected.json'),verified_sha256=sha(HERE/'verified.json'),
        source_sha256=sha(Path(__file__)),inference=0,optimizer_updates=0,accepted=False,deployed=False)
    (HERE/'reviewed.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('SMALL_SET_AIM_REVIEWED')
if __name__=='__main__': main()
