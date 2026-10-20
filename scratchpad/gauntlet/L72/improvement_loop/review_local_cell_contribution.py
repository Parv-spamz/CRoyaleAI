"""Outside closeout for the cached aim audit; no inference."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'local_cell_contribution'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed.json').exists()
    c=read(HERE/'collected.json'); v=read(HERE/'verified.json')
    assert c['complete'] and v['complete'] and read(HERE/'chain_complete.json')['complete']
    assert c['forward_views']==2048 and c['play_records']==1024
    assert v['controls']==dict(positive=3,negative=13)
    assert v['collected_sha256']==sha(HERE/'collected.json') and c['report_sha256']==v['report_sha256']
    assert v['backward']==c['backward']==v['optimizer_updates']==c['optimizer_updates']==0 and c['weights_unchanged']
    for p,h in c['sources'].items(): assert sha(ROOT/p)==h
    receipts={}
    for stage in ('collect','independent'):
        f=CHECKS/('l72-local-cell-contribution-'+stage+'.json'); q=read(f); out=f.with_suffix('.out')
        assert q['exit_code']==0 and q['matched'] and hashlib.sha256(out.read_text(encoding='utf-8').encode()).hexdigest()==q['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(f),output_sha256=sha(out),seconds=q['seconds'])
    result=dict(complete=True,receipts=receipts,collected_sha256=sha(HERE/'collected.json'),verified_sha256=sha(HERE/'verified.json'),
        source_sha256=sha(Path(__file__)),forward_views=2048,backward=0,optimizer_updates=0,accepted=False,deployed=False)
    (HERE/'reviewed.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('LOCAL_CELL_CONTRIBUTION_REVIEWED')
if __name__=='__main__': main()
