"""Bind the completed paired curriculum evidence and its single compound report."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent / 'development_rl_3'
CHECKS = ROOT / 'scratchpad/gauntlet/L71/integration/checks'
REPORT_ID = 'model-late-curriculum-pair-final'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    assert not (HERE / 'reviewed_results.json').exists()
    evidence = read(HERE / 'reviewed_evidence.json')
    results = read(HERE / 'results_verified.json')
    assert evidence['complete'] and results['complete']
    assert evidence['results_verified_sha256'] == sha(HERE / 'results_verified.json')
    assert evidence['verdicts'] == results['verdicts']
    assert all(not v['continuation_passed'] for v in results['verdicts'].values())
    receipts = {}
    for stage in ('prepare', 'train', 'training-independent', 'eval', 'results-independent',
                  'reviewed-evidence', 'discord'):
        path = CHECKS / ('l72-late-curriculum-' + stage + '.json')
        receipt = read(path)
        output = path.with_suffix('.out')
        assert receipt['exit_code'] == 0 and receipt['matched']
        assert hashlib.sha256(output.read_text(encoding='utf-8').encode()).hexdigest() == receipt['output_sha256']
        receipts[stage] = dict(receipt_sha256=sha(path), output_sha256=sha(output), seconds=receipt['seconds'])
    directory = ROOT / 'reports/discord/deliveries' / REPORT_ID
    delivery = read(directory / 'delivery.json')
    assert delivery['report_id'] == REPORT_ID and delivery['status'] == 'delivered'
    text = (HERE / 'message.md').read_text(encoding='utf-8')
    assert delivery['text_sha256'] == hashlib.sha256(text.encode()).hexdigest()
    assert (directory / 'message.md').read_text(encoding='utf-8') == text
    chunks = delivery['chunks']
    assert chunks and all(x['status'] == 'delivered' and x['http_status'] == 200 and x['message_id'] for x in chunks)
    assert len({x['message_id'] for x in chunks}) == len(chunks)
    paths = [Path(__file__), HERE / 'prepared.json', HERE / 'trained.json', HERE / 'training_verified.json',
             HERE / 'evaluated.json', HERE / 'results_verified.json', HERE / 'reviewed_evidence.json',
             HERE / 'chain_complete.json', HERE / 'message.md']
    out = dict(complete=True, receipts=receipts, verdicts=results['verdicts'],
               sources={str(p.relative_to(ROOT)): sha(p) for p in paths},
               delivery_path=str((directory / 'delivery.json').relative_to(ROOT)),
               delivery_sha256=sha(directory / 'delivery.json'), message_sha256=sha(HERE / 'message.md'),
               message_ids=[x['message_id'] for x in chunks], accepted=False, deployed=False)
    (HERE / 'reviewed_results.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
    print('LATE_CURRICULUM_REPORT_REVIEWED')


if __name__ == '__main__':
    main()
