"""Outside receipt review for the diagnostic-only lattice correction."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'lattice_label_audit'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed.json').exists()
    c=read(HERE/'collected.json');v=read(HERE/'verified.json')
    assert c['complete'] and v['complete'] and read(HERE/'chain_complete.json')['complete']
    assert c['records']==v['records']==4096 and c['grid']==v['grid']=='lattice'
    assert v['controls']==dict(positive=3,negative=12) and v['original_aim_unchanged']
    assert v['collected_sha256']==sha(HERE/'collected.json')
    for p,h in c['sources'].items():assert sha(ROOT/p)==h
    for p,h in c['artifacts'].items():assert sha(ROOT/'icebow/data/bench/lattice_label_audit_20261006'/p)==h
    assert c['inference']==v['inference']==c['backward']==v['backward']==c['optimizer_updates']==v['optimizer_updates']==0
    receipts={}
    for stage in ('collect','independent'):
        p=ROOT/'scratchpad/gauntlet/L71/integration/checks'/('l72-lattice-label-audit-'+stage+'.json');r=read(p);out=p.with_suffix('.out')
        assert r['exit_code']==0 and r['matched'] and hashlib.sha256(out.read_text(encoding='utf-8').encode()).hexdigest()==r['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(p),output_sha256=sha(out),seconds=r['seconds'])
    (HERE/'reviewed.json').write_text(json.dumps(dict(complete=True,source_sha256=sha(Path(__file__)),collected_sha256=sha(HERE/'collected.json'),verified_sha256=sha(HERE/'verified.json'),receipts=receipts,original_fit_verdicts_unchanged=True,accepted=False,deployed=False),indent=2)+'\n',encoding='utf-8')
    print('LATTICE_LABEL_AUDIT_REVIEWED')
if __name__=='__main__':main()
