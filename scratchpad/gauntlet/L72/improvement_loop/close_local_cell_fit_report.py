"""Bind one delivered final-model report to the independently reviewed results."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'local_cell_fit'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
REPORT_ID='model-local-cell-fit-v5-diagnostic'


def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    assert not (HERE/'reviewed_results.json').exists()
    e=read(HERE/'reviewed_evidence.json'); r=read(HERE/'results_verified.json')
    assert e['complete'] and r['complete']
    assert e['bindings']['results_verified.json']==sha(HERE/'results_verified.json')
    assert e['diagnostic_fit']==r['diagnostic_fit']==all(all(r['filters']['local_cell_final/'+o].values()) for o in ('native','mirrored'))
    assert r['quarantined'] and not r['eligible_policy_parent']
    receipts={}
    for stage in ('prepare','train','training-independent','eval','results-independent','reviewed-evidence','discord'):
        f=CHECKS/('l72-local-cell-fit-'+stage+'.json'); q=read(f); out=f.with_suffix('.out')
        assert q['exit_code']==0 and q['matched']
        assert hashlib.sha256(out.read_text(encoding='utf-8').encode()).hexdigest()==q['output_sha256']
        receipts[stage]=dict(receipt_sha256=sha(f),output_sha256=sha(out),seconds=q['seconds'])
    directory=ROOT/'reports/discord/deliveries'/REPORT_ID
    delivery=read(directory/'delivery.json'); text=(HERE/'message.md').read_text(encoding='utf-8')
    assert delivery['report_id']==REPORT_ID and delivery['status']=='delivered'
    assert delivery['text_sha256']==hashlib.sha256(text.encode()).hexdigest()
    assert (directory/'message.md').read_text(encoding='utf-8')==text
    chunks=delivery['chunks']
    assert chunks and all(x['status']=='delivered' and x['http_status']==200 and x['message_id'] for x in chunks)
    assert len({x['message_id'] for x in chunks})==len(chunks)
    paths=[Path(__file__),HERE/'message.md',HERE/'reviewed_evidence.json',HERE/'prepared.json',HERE/'trained.json',
        HERE/'training_verified.json',HERE/'evaluated.json',HERE/'results_verified.json',HERE/'chain_complete.json']
    result=dict(complete=True,receipts=receipts,diagnostic_fit=r['diagnostic_fit'],filters=r['filters'],quarantined=True,eligible_policy_parent=False,
        sources={str(p.relative_to(ROOT)):sha(p) for p in paths},delivery_path=str((directory/'delivery.json').relative_to(ROOT)),
        delivery_sha256=sha(directory/'delivery.json'),message_sha256=sha(HERE/'message.md'),
        message_ids=[x['message_id'] for x in chunks],accepted=False,deployed=False)
    (HERE/'reviewed_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('LOCAL_CELL_FIT_REPORT_REVIEWED')


if __name__=='__main__': main()
