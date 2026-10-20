"""Close the diagnostic after its frozen three-stage chain succeeds."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent/'training_fit_audit'
CHECKS = ROOT/'scratchpad/gauntlet/L71/integration/checks'


def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    assert not (HERE/'reviewed.json').exists()
    p = read(HERE/'prepared.json'); c = read(HERE/'collected.json'); v = read(HERE/'verified.json')
    assert p['complete'] and c['complete'] and v['complete'] and read(HERE/'chain_complete.json')['complete']
    assert p['controls'] == dict(positive=2, negative=6) and v['controls'] == dict(positive=4, negative=10)
    assert c['weights_unchanged'] and c['optimizer_updates'] == c['development_inference'] == 0
    assert v['collected_sha256'] == sha(HERE/'collected.json') and c['prepared_sha256'] == sha(HERE/'prepared.json')
    assert p['native_rows'] == 213995 and p['development_rows'] == 54723
    assert c['fresh_inference_rows'] == p['native_rows'] + p['mirrored_rows'] == v['fresh_inference_rows']
    for path, h in p['sources'].items(): assert sha(ROOT/path) == h, path
    receipts = {}
    for stage in ('prepare', 'collect', 'independent'):
        f = CHECKS/('l72-training-fit-'+stage+'.json'); r = read(f); output = f.with_suffix('.out')
        assert r['exit_code'] == 0 and r['matched']
        assert hashlib.sha256(output.read_text(encoding='utf-8').encode()).hexdigest() == r['output_sha256']
        receipts[stage] = dict(receipt_sha256=sha(f), output_sha256=sha(output), seconds=r['seconds'])
    out = dict(complete=True, receipts=receipts, prepared_sha256=sha(HERE/'prepared.json'),
               collected_sha256=sha(HERE/'collected.json'), verified_sha256=sha(HERE/'verified.json'),
               source_sha256=sha(Path(__file__)), new_models=0, optimizer_updates=0,
               development_inference=0, diagnostic_only=True, accepted=False, deployed=False)
    (HERE/'reviewed.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
    print('TRAINING_FIT_REVIEWED')


if __name__ == '__main__': main()
