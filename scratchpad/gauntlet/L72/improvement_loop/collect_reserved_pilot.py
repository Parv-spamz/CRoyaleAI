"""Collect only the fixed reserved pilot after full local mechanics qualification."""
from collections import Counter,defaultdict
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
NATIVE=ROOT/'research/ext/cr-native-sandbox'
OUT=ROOT/'icebow/data/bench/native_confirmation_20261005/reserved_pilot'
sys.path[:0]=[str(ROOT),str(NATIVE)]
from research.sandbox_tools import replay_drive
from research.sandbox_tools.validate_public_capture import inspect
from native_core.client import request
from native_capture_identity import canonical_frames


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def qualification(rec):
    grade=rec['grade'];reasons=[]
    if grade['plays_total'] != grade['plays_driven']:reasons.append('undriven_commands')
    if grade['accepted'] != grade['plays_driven'] or grade['rejected_by_reason']:reasons.append('rejected_commands')
    if grade['skipped']:reasons.append('skipped_commands')
    if grade['invalid_placement']:reasons.append('invalid_placement')
    if grade['elixir_delays']['n'] or grade['elixir_delays']['sum_ticks']:reasons.append('elixir_delay')
    if grade['crowns_match'] is not True:reasons.append('crown_mismatch')
    if rec['final']['terminated'] is not True:reasons.append('nonterminal')
    return reasons


def self_test():
    good=dict(grade=dict(plays_total=5,plays_driven=5,accepted=5,rejected_by_reason={},
        skipped=[],invalid_placement=0,elixir_delays=dict(n=0,sum_ticks=0),crowns_match=True),
        final=dict(terminated=True))
    assert qualification(good)==[]
    mutations=[('undriven_commands',lambda r:r['grade'].update(plays_driven=4)),
        ('rejected_commands',lambda r:r['grade'].update(accepted=4)),
        ('skipped_commands',lambda r:r['grade'].update(skipped=[{}])),
        ('invalid_placement',lambda r:r['grade'].update(invalid_placement=1)),
        ('elixir_delay',lambda r:r['grade'].update(elixir_delays=dict(n=1,sum_ticks=1))),
        ('crown_mismatch',lambda r:r['grade'].update(crowns_match=False)),
        ('nonterminal',lambda r:r['final'].update(terminated=False))]
    for name,mutate in mutations:
        altered=copy.deepcopy(good);mutate(altered)
        assert name in qualification(altered),name
    print('RESERVED_PILOT_QUALIFICATION_CONTROLS_PASS: 1 positive and 7 negatives')


def prerequisites():
    receipt=ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-native-capture-v2.json'
    result=json.loads(receipt.read_text())
    assert result['exit_code']==0 and result['matched'] is True
    assert result['expected']=='NATIVE_CAPTURE_V2_PREFLIGHT_PASS'
    # run_check hashes decoded combined output; the output file uses native newlines.
    output=receipt.with_suffix('.out').read_text()
    assert hashlib.sha256(output.encode()).hexdigest()==result['output_sha256']
    report=json.loads((HERE/'native_capture_v2_verified.json').read_text())
    assert report['complete'] is True and report['replays']==20 and report['repeats']==4
    assert report['negative_control_passed'] is True
    for name in ('inputs','remote_hashes','progress','fields'):
        assert sha(HERE/f'native_capture_v2_{name}.json')==report[name+'_sha256']
    fields=json.loads((HERE/'native_capture_v2_fields.json').read_text())
    assert fields['status']=='PASS' and not fields['errors']
    progress=json.loads((HERE/'native_capture_v2_progress.json').read_text())
    assert len(progress)==20 and all(r['ok'] for r in progress)
    for row in progress:
        if 'repeat_equal' in row:assert all(row['repeat_equal'].values())
    manifest=json.loads((HERE/'native_capture_v2_inputs.json').read_text())
    for name,digest in manifest.items():assert sha(ROOT/name)==digest,name
    return sha(receipt),sha(HERE/'native_capture_v2_verified.json')


def main():
    preflight_receipt,preflight_report=prerequisites()
    prepared=json.loads((HERE/'reserved_pilot_prepared.json').read_text())
    assert prepared['complete'] is True
    assert sha(prepared['jobs_path'])==prepared['jobs_sha256']
    assert sha(prepared['csv_hashes_path'])==prepared['csv_hashes_sha256']
    assert sha(HERE/'RESERVED_PILOT_PLAN.md')==prepared['plan_sha256']
    csv_hashes=json.loads(Path(prepared['csv_hashes_path']).read_text())
    for name,digest in csv_hashes.items():assert sha(ROOT/name)==digest,name
    jobs=json.loads(Path(prepared['jobs_path']).read_text())
    assert len(jobs)==prepared['selected'] and len({j['tag'] for j in jobs})==len(jobs)
    records=OUT/'recordings';records.mkdir(exist_ok=False)
    lock=OUT/'collection_started.json'
    with lock.open('x') as stream:
        json.dump(dict(started_at=time.strftime('%Y-%m-%dT%H:%M:%S'),pid=__import__('os').getpid()),stream)
    sources=[Path(__file__),HERE/'native_capture_identity.py',
        ROOT/'research/sandbox_tools/replay_drive.py',ROOT/'research/sandbox_tools/validate_public_capture.py',
        ROOT/'pipeline/projectile_motion.py',*sorted((NATIVE/'native_core').glob('*.py')),
        NATIVE/'native_core/data/live_card_catalog.json',HERE/'RESERVED_PILOT_PLAN.md']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    provenance=dict(sources=hashes,jobs_sha256=prepared['jobs_sha256'],
        prepared_sha256=sha(HERE/'reserved_pilot_prepared.json'),
        preflight_receipt_sha256=preflight_receipt,preflight_report_sha256=preflight_report,
        model_predictions=0,device='one native CPU emulator; no GPU',record_every=10)
    (HERE/'reserved_collection_provenance.json').write_text(json.dumps(provenance,indent=2))
    totals=Counter();by_split=defaultdict(Counter);by_stratum=defaultdict(Counter)
    rows=[]
    for job in jobs:
        started=time.monotonic()
        row=dict(index=job['index'],tag=job['tag'],split=job['split'],strata=job['strata'])
        fatal=None
        try:
            for name,digest in hashes.items():assert sha(ROOT/name)==digest,name
            for name in ('battles.csv','plays_ext.csv'):
                p=ROOT/job['crawl']/name
                assert sha(p)==csv_hashes[str(p.relative_to(ROOT))]
            state=request({'op':'observe'},port=38031,timeout=10)['state']
            assert state['state_hash_scope']=='public-observe-v6'
            replay_drive.set_crawl(str(ROOT/job['crawl']))
            replay_drive.set_plays_file(job['plays_file'])

            def capture(label):
                return replay_drive.drive(job['tag'],port=38031,seed=424242,level=11,
                    elixir_slack=40,tail_cap=7200,run_label=label,verbose=False,record_every=10,
                    record_full=True,record_plays=True,drive_abilities=True,
                    record_native=True,record_public_objects=True)

            rec=capture('l72_reserved_pilot')
            file=records/f"replay_{job['tag']}.json"
            file.write_text(json.dumps(rec,separators=(',',':')))
            row.update(recording_sha256=sha(file),bytes=file.stat().st_size,
                       grade=rec['grade'],fields=inspect(rec),reasons=qualification(rec))
            if row['fields']['errors']:raise RuntimeError('Public capture fields failed: '+str(row['fields']['errors']))
            if job['repeat']:
                repeated=capture('l72_reserved_pilot_repeat')
                repeat_dir=OUT/'repeats';repeat_dir.mkdir(exist_ok=True)
                repeat_file=repeat_dir/file.name
                repeat_file.write_text(json.dumps(repeated,separators=(',',':')))
                row['repeat_sha256']=sha(repeat_file)
                row['repeat_equal']={k:rec[k]==repeated[k] for k in ('final','log','grade')}
                row['repeat_equal']['canonical_frames']=canonical_frames(rec['frames'])==canonical_frames(repeated['frames'])
                if not all(row['repeat_equal'].values()):raise RuntimeError('Native repeat nondeterminism')
            row['usable']=not row['reasons']
        except SystemExit as error:
            # Only known source/deal incompatibilities are ordinary exclusions.
            # Missing inputs, orientation failures and protocol errors stop the batch.
            row.update(usable=False,reasons=['unreconstructable_source'],error=repr(error),
                       traceback=traceback.format_exc())
            if not any(message in str(error) for message in (
                    'no (hand, queue) assignment reproduces the play sequence',
                    'plays cards outside its deck')):
                fatal=repr(error)
                row['reasons']=['fatal_source_or_runtime_error']
            else:
                try:
                    if not request({'op':'ping'},port=38031,timeout=10)['ok']:
                        raise RuntimeError('Native service unavailable')
                except BaseException as ping_error:fatal=repr(ping_error)
        except BaseException as error:
            row.update(usable=False,reasons=['fatal_runtime_or_evidence_error'],error=repr(error),
                       traceback=traceback.format_exc())
            fatal=repr(error)
        row['seconds']=round(time.monotonic()-started,2)
        rows.append(row)
        status='usable' if row['usable'] else 'excluded'
        totals[status]+=1;by_split[job['split']][status]+=1
        for stratum in job['strata']:by_stratum[job['split']+':'+stratum][status]+=1
        for reason in row.get('reasons',[]):totals['reason:'+reason]+=1
        with (OUT/'summary.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
        (HERE/'reserved_collection_progress.json').write_text(json.dumps(dict(
            attempted=len(rows),selected=len(jobs),totals=dict(totals),last_tag=job['tag'],
            by_split={k:dict(v) for k,v in by_split.items()},
            by_stratum={k:dict(v) for k,v in by_stratum.items()},fatal=fatal),indent=2))
        print(json.dumps(dict(index=job['index'],tag=job['tag'],usable=row['usable'],
                              reasons=row['reasons'],seconds=row['seconds'])),flush=True)
        if fatal:raise RuntimeError(fatal)
    for name,digest in hashes.items():assert sha(ROOT/name)==digest,name
    report=dict(complete=True,attempted=len(rows),selected=len(jobs),totals=dict(totals),
        by_split={k:dict(v) for k,v in by_split.items()},
        by_stratum={k:dict(v) for k,v in by_stratum.items()},
        summary_path=str(OUT/'summary.jsonl'),summary_sha256=sha(OUT/'summary.jsonl'),
        provenance_sha256=sha(HERE/'reserved_collection_provenance.json'),
        qualified_tags={s:[r['tag'] for r in rows if r['split']==s and r['usable']]
                        for s in ('training','development','confirmation')},
        new_model_trained=False,N2_complete=False)
    (HERE/'reserved_collection_complete.json').write_text(json.dumps(report,indent=2))
    print('RESERVED_PILOT_COLLECTION_COMPLETE',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:self_test()
    else:main()
