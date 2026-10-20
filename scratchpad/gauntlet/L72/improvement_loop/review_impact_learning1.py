"""Bind completed auxiliary-predictor evidence; no collection or inference."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent/'impact_learnability_1'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    assert not (HERE/'reviewed_evidence.json').exists()
    r=read(HERE/'collected.json');d=read(HERE/'data_verified.json');t=read(HERE/'trained.json');v=read(HERE/'results_verified.json')
    assert all(x['complete'] for x in (r,d,t,v)) and read(HERE/'chain_complete.json')['complete']
    assert sha(HERE/'collected.json')==d['report_sha256'] and sha(HERE/'trained.json')==v['trained_sha256']
    assert t['data_verifier_sha256']==sha(HERE/'data_verified.json') and t['data_sha256']==v['data_sha256']==d['data_sha256']==sha(ROOT/r['data_path'])
    assert d['roots']==192 and d['branches']==3456 and d['frames']==542592 and d['rows']==13824 and d['training_rows']==9216 and d['development_rows']==4608
    assert d['controls']==dict(positive=192,negative=16,private_invariance=4) and v['controls']==dict(positive=6,negative=8)
    assert v['updates']==6000 and v['predictions']==82944 and t['filters']==v['filters'] and t['continuation_pass']==v['continuation_pass']
    assert not t['policy_acceptance'] and not v['policy_acceptance'] and not t['deployed'] and not v['deployed']
    for p,h in t['sources'].items():assert sha(ROOT/p)==h
    receipts={}
    for stage in ('collect','data-independent','train','results-independent'):
        p=CHECKS/f'l72-impact-learning1-{stage}.json';a=read(p);o=p.with_suffix('.out')
        assert a['exit_code']==0 and a['matched']
        assert hashlib.sha256(o.read_text(encoding='utf-8').encode()).hexdigest()==a['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(p),output_sha256=sha(o),seconds=a['seconds'])
    for model in t['results']:
        for prefix in ('checkpoint','probability','trace','draw'):assert sha(ROOT/model[prefix+'_path'])==model[prefix+'_sha256']
    out=dict(complete=True,data_verifier_sha256=sha(HERE/'data_verified.json'),results_verifier_sha256=sha(HERE/'results_verified.json'),receipts=receipts,filters=v['filters'],continuation_pass=v['continuation_pass'],policy_acceptance=False,deployed=False,source_sha256=sha(Path(__file__)))
    (HERE/'reviewed_evidence.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('IMPACT_LEARNING_EVIDENCE_REVIEWED')
if __name__=='__main__':main()
