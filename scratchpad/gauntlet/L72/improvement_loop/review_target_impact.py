"""Bind the completed impact instrument receipts; never recollect fixtures."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent/'target_impact_readiness'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    assert not (HERE/'reviewed.json').exists()
    r=read(HERE/'report.json');v=read(HERE/'verified.json')
    assert r['complete'] and v['complete'] and sha(HERE/'report.json')==v['report_sha256']
    assert len(r['roots'])==v['roots']==16 and v['branches']==112 and v['frames']==33712
    assert v['controls']==dict(positive=16,negative=12)
    assert r['models_loaded']==r['optimizer_updates']==v['models_loaded']==v['optimizer_updates']==0
    assert not r['native_client_parity'] and not r['policy_acceptance']
    for path,digest in r['sources'].items():assert sha(ROOT/path)==digest
    receipts={}
    for stage in ('collection','independent'):
        p=CHECKS/f'l72-target-impact-{stage}.json';x=read(p);o=p.with_suffix('.out')
        assert x['exit_code']==0 and x['matched']
        assert hashlib.sha256(o.read_text(encoding='utf-8').encode()).hexdigest()==x['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(p),output_file_sha256=sha(o),seconds=x['seconds'])
    matched=0
    for root,summary in zip(r['roots'],v['summary'],strict=True):
        assert root['root_id']==summary['root_id']
        assert sha(ROOT/root['root_path'])==root['root_sha256']
        for arm,b in root['branches'].items():
            assert sha(ROOT/b['path'])==b['sha256'] and sha(ROOT/b['final_path'])==b['final_sha256']
            assert root['summary'][arm]['effects'][root['target_key']]['final']==summary['effects'][arm]
            matched+=1
    assert matched==112
    evidence=dict(complete=True,report_sha256=sha(HERE/'report.json'),verified_sha256=sha(HERE/'verified.json'),receipts=receipts,roots=16,branches=112,frames=33712,controls=v['controls'],models_loaded=0,optimizer_updates=0,native_client_parity=False,policy_acceptance=False,source_sha256=sha(Path(__file__)))
    (HERE/'reviewed.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8');print('TARGET_IMPACT_REVIEWED')
if __name__=='__main__':main()
