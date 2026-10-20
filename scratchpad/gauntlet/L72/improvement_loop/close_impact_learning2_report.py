"""Bind already completed auxiliary work and its one delivered report."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'impact_learnability_2_recovery'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    assert not (HERE/'reviewed_results.json').exists()
    e=read(HERE/'reviewed_evidence.json');v=read(HERE/'results_verified.json')
    assert e['complete'] and not e['continuation_pass'] and e['filters']==v['filters']
    assert e['results_verifier_sha256']==sha(HERE/'results_verified.json')
    receipts={}
    for name in ('l72-impact-learning2-recovery-reviewed-evidence','l72-impact-learning2-aux-discord'):
        p=CHECKS/(name+'.json');r=read(p);o=p.with_suffix('.out')
        assert r['exit_code']==0 and r['matched']
        assert hashlib.sha256(o.read_text(encoding='utf-8').encode()).hexdigest()==r['output_sha256']
        receipts[name]=dict(receipt_sha256=sha(p),output_sha256=sha(o),seconds=r['seconds'])
    delivery=ROOT/'reports/discord/deliveries/model-impact-learning2-aux-final/delivery.json'
    d=read(delivery);assert d['status']=='delivered' and len(d['chunks'])==3
    assert d['text_sha256']==sha(HERE/'message.md')
    assert all(x['status']=='delivered' and x['http_status']==200 and x['message_id'] for x in d['chunks'])
    assert len({x['message_id'] for x in d['chunks']})==3
    out=dict(complete=True,reviewed_evidence_sha256=sha(HERE/'reviewed_evidence.json'),receipts=receipts,
        message_sha256=sha(HERE/'message.md'),delivery_path=str(delivery.relative_to(ROOT)),delivery_sha256=sha(delivery),
        message_ids=[x['message_id'] for x in d['chunks']],continuation_pass=False,policy_acceptance=False,deployed=False,
        sources={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'trained.json',HERE/'results_verified.json',HERE/'reviewed_evidence.json']})
    (HERE/'reviewed_results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print('IMPACT_LEARNING_REPORT_REVIEWED')
if __name__=='__main__':main()
