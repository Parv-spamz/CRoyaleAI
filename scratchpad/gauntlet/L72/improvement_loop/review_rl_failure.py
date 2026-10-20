"""Bind completed cached RL diagnosis receipts; no predictions or optimization."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];BASE=Path(__file__).resolve().parent
HERE=BASE/'rl_failure_audit';OUT=ROOT/'icebow/data/bench/rl_failure_audit_20261005'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed.json').exists();r=read(HERE/'report.json');v=read(HERE/'verified.json')
    assert r['complete'] and v['complete'] and v['report_sha256']==sha(HERE/'report.json')
    assert v['rows']==54723 and v['rocket_records']==955 and v['predictions']==v['optimizer_updates']==0
    assert v['source_sha256']==sha(HERE/'verify.py') and v['controls']['positive']>=1 and v['controls']['negative']>=8
    for name in ('by_replay','rocket_rows'):assert sha(OUT/(name+'.json'))==v[name+'_sha256']==r[name+'_sha256']
    for path,digest in v['inputs'].items():
        if path.startswith('scratchpad/'):assert sha(ROOT/path)==digest
    receipts={}
    for name,token in [('l72-rl-failure-audit','RL_FAILURE_AUDIT_COMPLETE'),('l72-rl-failure-independent','RL_FAILURE_AUDIT_VERIFIED')]:
        p=CHECKS/(name+'.json');e=read(p);out=p.with_suffix('.out');text=out.read_text(encoding='utf-8')
        assert e['exit_code']==0 and e['matched'] and token in text and hashlib.sha256(text.encode()).hexdigest()==e['output_sha256']
        receipts[name]=dict(receipt_sha256=sha(p),output_sha256=sha(out),seconds=e['seconds'])
    review=dict(complete=True,receipts=receipts,report_sha256=sha(HERE/'report.json'),verified_sha256=sha(HERE/'verified.json'),source_sha256=sha(Path(__file__)),counts=r['counts'],controls=v['controls'],no_new_model=True,model_report_already_delivered=True,accepted=False)
    (HERE/'reviewed.json').write_text(json.dumps(review,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('RL_FAILURE_REVIEWED')
if __name__=='__main__':main()
