"""Outside closeout for the separately registered full-history suffix readiness."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent/'late_game_readiness'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed.json').exists()
    r=read(HERE/'report.json');v=read(HERE/'verified.json')
    assert r['complete'] and v['complete'] and read(HERE/'chain_complete.json')['complete']
    assert v['report_sha256']==sha(HERE/'report.json') and v['totals']['games']==16
    assert v['totals']['late_games']>=4 and v['totals']['late_rows']>=256
    assert v['controls']==dict(positive=1,negative=15)
    assert r['optimizer_updates']==r['new_models']==v['optimizer_updates']==v['new_models']==0
    assert r['unchanged_parameters'] and not r['deployed'] and not v['deployed']
    for p,h in r['sources'].items():assert sha(ROOT/p)==h,p
    receipts={}
    for name in ('collection','independent'):
        p=CHECKS/f'l72-late-game-readiness-{name}.json';a=read(p);o=p.with_suffix('.out')
        assert a['exit_code']==0 and a['matched']
        assert hashlib.sha256(o.read_text(encoding='utf-8').encode()).hexdigest()==a['output_sha256']
        receipts[name]=dict(receipt_sha256=sha(p),output_sha256=sha(o),seconds=a['seconds'])
    out=dict(complete=True,report_sha256=sha(HERE/'report.json'),verified_sha256=sha(HERE/'verified.json'),receipts=receipts,
        totals=v['totals'],optimizer_updates=0,new_models=0,policy_accepted=False,deployed=False,source_sha256=sha(Path(__file__)))
    (HERE/'reviewed.json').write_text(json.dumps(out,indent=2)+'\n');print('LATE_GAME_READINESS_REVIEWED')
if __name__=='__main__':main()
