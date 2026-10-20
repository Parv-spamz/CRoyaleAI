"""Check reconstruction availability, never model predictions or match outcomes."""
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    out=HERE/'candidate_reconstruction_inventory.json'
    if out.exists():raise ValueError('Fresh report required')
    audit=HERE/'unused_hf_inventory.json'
    manifest=json.loads(audit.read_text())
    source=Path(manifest['candidates'])
    if sha(source)!=manifest['candidates_sha256']:raise ValueError('Candidate source changed')
    candidates={}
    with source.open() as stream:
        for line in stream:
            r=json.loads(line)
            if 'exact_icebow' in r['strata']:candidates[r['tag']]=r
    seen=defaultdict(list);inputs=[]
    for path in sorted((ROOT/'scratchpad/gauntlet/ext').glob('corpus_*/**/summary.jsonl')):
        found=False
        for line in path.open():
            if not line.strip():continue
            r=json.loads(line);tag=r.get('tag',r.get('replay_tag'))
            if tag not in candidates:continue
            found=True
            seen[tag].append(dict(source=str(path.relative_to(ROOT)),ok=r.get('ok'),
                                 error_type=r.get('error_type'),error=r.get('error')))
        if found:inputs.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
    errors=Counter();status=Counter();rows=[]
    for tag,candidate in sorted(candidates.items()):
        attempts=seen[tag]
        state=('prior_success' if any(r['ok'] for r in attempts) else
               'prior_failed' if attempts else 'no_local_attempt_receipt')
        status[state]+=1
        for error in sorted({r['error'] for r in attempts if r['error']}):errors[error]+=1
        rows.append(dict(tag=tag,status=state,strata=candidate['strata'],attempts=attempts))
    report=dict(exact_icebow_candidates=len(candidates),status=dict(status),
        unique_replays_by_error=dict(errors),raw_availability_report_sha256=sha(audit),
        script_sha256=sha(__file__),summary_sources=inputs,candidates=rows,
        limitations=['Prior reconstruction error is not model exposure or evidence of current support.',
            'No match outcome, tower damage or model prediction inspected.',
            'Successful public feature reconstruction is required before confirmation can qualify.'])
    out.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('summary_sources','candidates')}))
    print('CANDIDATE_RECONSTRUCTION_AUDITED')


if __name__=='__main__':main()
