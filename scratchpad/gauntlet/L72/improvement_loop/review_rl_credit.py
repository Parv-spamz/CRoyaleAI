"""Receipt and source closeout only; no recount or model execution."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent/'rl_credit_audit';OUT=ROOT/'icebow/data/bench/rl_credit_audit_20261005'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed.json').exists();r=read(HERE/'report.json');v=read(HERE/'verified.json')
    assert r['complete'] and v['complete'] and read(HERE/'chain_complete.json')['complete']
    assert v['rows']==73783 and v['updates']==32 and v['matches']==256 and v['groups']==112
    assert v['controls']==dict(positive=5,negative=9) and r['model_inference']==r['optimizer_updates']==0
    assert sha(HERE/'report.json')==v['report_sha256'] and sha(HERE/'verify.py')==v['source_sha256']
    for p,h in dict(r['sources'],**r['inputs']).items():assert sha(ROOT/p)==h
    assert r['outputs']==v['outputs']
    for p,h in r['outputs'].items():assert sha(OUT/p)==h
    receipts={}
    for name,token in [('producer','RL_CREDIT_AUDIT_COMPLETE'),('independent','RL_CREDIT_VERIFIED')]:
        p=ROOT/f'scratchpad/gauntlet/L71/integration/checks/l72-rl-credit-{name}.json';e=read(p);out=p.with_suffix('.out');s=out.read_text(encoding='utf-8')
        assert e['exit_code']==0 and e['matched'] and token in s and hashlib.sha256(s.encode()).hexdigest()==e['output_sha256']
        receipts[name]=dict(receipt_sha256=sha(p),output_sha256=sha(out),seconds=e['seconds'])
    selected={k:x for k,x in r['groups'].items() if k in ('policy/all/all','policy/PLAY/all','policy/WAIT/all','policy/Rocket/all') or k.startswith('policy/Rocket/distance:')}
    result=dict(complete=True,receipts=receipts,report_sha256=sha(HERE/'report.json'),verified_sha256=sha(HERE/'verified.json'),source_sha256=sha(Path(__file__)),selected=selected,accepted=False,new_model=False)
    (HERE/'reviewed.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8');print('RL_CREDIT_REVIEWED')
if __name__=='__main__':main()
