"""Reserve outcome-blind raw replay groups; not a confirmation acceptance gate."""
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
SALT='clashbot-l72-replay-reservation-20261005-v1:'


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def assignment(row):
    if 'exact_icebow' in row['strata']:return 'confirmation'
    bucket=int.from_bytes(hashlib.sha256((SALT+row['signature']).encode()).digest()[:8],'big')%100
    return 'training' if bucket<70 else 'development' if bucket<85 else 'confirmation'


def main():
    report=HERE/'replay_reservation.json'
    inventory=HERE/'unused_hf_inventory.json'
    meta=json.loads(inventory.read_text())
    source=Path(meta['candidates']);output=source.with_name('reserved_groups.jsonl')
    if report.exists() or output.exists():raise ValueError('Fresh reservation required')
    if sha(source)!=meta['candidates_sha256']:raise ValueError('Candidate source changed')
    exposed=set(json.loads((HERE/'historical_exposure_tags_v2.json').read_text()))
    counts=Counter();strata=defaultdict(Counter);tags=set();signatures=set()
    exact=[]
    with source.open() as stream,output.open('x') as dest:
        for line in stream:
            row=json.loads(line)
            if row['tag'].lower() in exposed or row['tag'] in tags or row['signature'] in signatures:
                raise ValueError('Exposed or duplicate candidate')
            split=assignment(row);counts[split]+=1;strata[split].update(row['strata'])
            tags.add(row['tag']);signatures.add(row['signature'])
            dest.write(json.dumps(dict(tag=row['tag'],signature=row['signature'],split=split))+'\n')
            if 'exact_icebow' in row['strata']:exact.append(row['tag'])
    # Independent output recount; every source candidate appears exactly once.
    with output.open() as f:reserved=[json.loads(line) for line in f]
    assert len(reserved)==len(tags)==meta['unused_unique_command_groups']
    assert {r['tag'] for r in reserved}==tags
    assert dict(Counter(r['split'] for r in reserved))==dict(counts)
    assert all(r['split']=='confirmation' for r in reserved if r['tag'] in set(exact))
    result=dict(schema=1,salt=SALT,assignment='all exact Icebow confirmation; other groups70/15/15 hash buckets',
        counts=dict(counts),strata={k:dict(v) for k,v in strata.items()},
        exact_icebow_confirmation_tags=sorted(exact),source_report_sha256=sha(inventory),
        candidate_commands_sha256=sha(source),reservation_file=str(output),reservation_sha256=sha(output),
        script_sha256=sha(__file__),confirmation_qualified=False,successor_training_authorized_by_reservation=False)
    report.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='exact_icebow_confirmation_tags'}))
    print('REPLAY_GROUPS_RESERVED_NOT_YET_QUALIFIED')


if __name__=='__main__':main()
