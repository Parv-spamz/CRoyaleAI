"""One serial, frozen twenty-replay historical native qualification batch."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'icebow/data/bench/native_confirmation_20261005/preflight_v2'
NATIVE = ROOT/'research/ext/cr-native-sandbox'
sys.path[:0] = [str(ROOT),str(NATIVE)]
from research.sandbox_tools import replay_drive
from research.sandbox_tools.validate_public_capture import inspect, validate
from native_core.client import request
from native_capture_identity import canonical_frames


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def main():
    OUT.mkdir(parents=True,exist_ok=False)
    jobs_path = ROOT/'.foreman/codex_autopilot/native_redrive_2300/sample_jobs.json'
    jobs = json.loads(jobs_path.read_text())
    assert len(jobs) == len({j['tag'] for j in jobs}) == 20
    rebuilt = json.loads((HERE/'native_worker_rebuild.json').read_text())
    assert rebuilt['complete'] is True
    build = OUT.parent/'runtime/build_current'
    inputs = [Path(__file__),HERE/'native_capture_identity.py',NATIVE/'native_core/data/live_card_catalog.json',jobs_path,HERE/'NATIVE_CAPTURE_PREFLIGHT.md',
        HERE/'native_worker_rebuild.json',build/'libnative_core_probe.so',
        build/'lifecycle-probe.jar',build/'jni_bridge.cpp',
        ROOT/'research/sandbox_tools/replay_drive.py',ROOT/'pipeline/projectile_motion.py',
        ROOT/'research/sandbox_tools/validate_public_capture.py',
        *sorted((NATIVE/'native_core').glob('*.py')),
        *sorted((NATIVE/'runtime/x86_64-libs').glob('*.so')),
        *sorted((NATIVE/'runtime/apks').glob('*.apk')),
        *sorted(p for p in (NATIVE/'runtime/extracted-assets').rglob('*') if p.is_file())]
    comparisons = {}
    for job in jobs:
        source = ROOT/job['source']['path']
        assert sha(source) == job['source']['sha256']
        comparison = ROOT/'scratchpad/gauntlet/ext/public_preflight_remaining'/f"replay_{job['tag']}.json"
        assert comparison.exists()
        comparisons[job['tag']] = comparison
        inputs.extend([source,comparison,ROOT/job['crawl']/'battles.csv',
                       ROOT/job['crawl']/job['plays_file']])
    manifest = {str(p.relative_to(ROOT)):sha(p) for p in inputs}
    (HERE/'native_capture_v2_inputs.json').write_text(json.dumps(manifest,indent=2))

    def frozen():
        for name,digest in manifest.items():
            assert sha(ROOT/name) == digest, f'Input changed: {name}'

    adb = 'C:/Android/Sdk/platform-tools/adb.exe'

    def remote(*args):
        return subprocess.check_output([adb,'-s','emulator-5560',*args],text=True).strip()

    remote_hashes = {}
    for local,guest in [(p,f'/data/local/tmp/cr-native-direct-0/{p.name}')
                        for p in (NATIVE/'runtime/x86_64-libs').glob('*.so')] + [
            (build/'libnative_core_probe.so','/data/local/tmp/cr-native-direct-0/libnative_host_bridge.so'),
            (build/'lifecycle-probe.jar','/data/local/tmp/cr-native-direct-0/lifecycle-probe.jar')]:
        digest = remote('shell','sha256sum',guest).split()[0]
        assert digest == sha(local), guest
        remote_hashes[guest] = digest
    for package in remote('shell','pm','path','com.supercell.clashroyale').splitlines():
        guest = package.removeprefix('package:').strip()
        digest = remote('shell','sha256sum',guest).split()[0]
        assert digest == sha(NATIVE/'runtime/apks'/Path(guest).name), guest
        remote_hashes[guest] = digest
    (HERE/'native_capture_v2_remote_hashes.json').write_text(json.dumps(remote_hashes,indent=2))
    state = request({'op':'observe'},port=38031,timeout=10)['state']
    assert state['state_hash_scope'] == 'public-observe-v6'
    rows=[]
    for index, job in enumerate(jobs):
        started=time.monotonic()
        row=dict(index=index,tag=job['tag'])
        try:
            frozen()
            replay_drive.set_crawl(str(ROOT/job['crawl']))
            replay_drive.set_plays_file(job['plays_file'])

            def capture(label):
                return replay_drive.drive(job['tag'],port=38031,seed=424242,level=11,
                    elixir_slack=40,tail_cap=7200,run_label=label,verbose=False,
                    record_every=1,record_full=True,record_plays=True,
                    drive_abilities=True,record_native=True,record_public_objects=True)

            rec=capture('l72_native_preflight')
            target=OUT/f"replay_{job['tag']}.json"
            target.write_bytes(encoded(rec))
            row=dict(index=index,tag=job['tag'],recording_sha256=sha(target),
                     bytes=target.stat().st_size,fields=inspect(rec),grade=rec['grade'])
            previous=json.loads(comparisons[job['tag']].read_text())
            row['historical_log_equal'] = rec['log'] == previous['log']
            row['historical_grade_equal'] = rec['grade'] == previous['grade']
            row['historical_final_hash_equal'] = rec['final']['state_hash'] == previous['final']['state_hash']
            assert not row['fields']['errors'], row['fields']['errors']
            assert all(row[k] for k in ('historical_log_equal','historical_grade_equal',
                                        'historical_final_hash_equal')), 'Historical mismatch'
            if index in (0,5,10,15):
                repeat=capture('l72_native_preflight_repeat')
                repeat_dir=OUT/'repeats';repeat_dir.mkdir(exist_ok=True)
                repeated=repeat_dir/target.name
                repeated.write_bytes(encoded(repeat))
                row['repeat_sha256']=sha(repeated)
                row['repeat_raw_frames_equal']=rec['frames'] == repeat['frames']
                row['repeat_equal']={key:rec[key] == repeat[key] for key in ('final','log','grade')}
                row['repeat_equal']['canonical_frames']=canonical_frames(rec['frames']) == canonical_frames(repeat['frames'])
                assert all(row['repeat_equal'].values()), row['repeat_equal']
            row['ok']=True
        except BaseException as error:
            row=locals().get('row',dict(index=index,tag=job['tag']))
            row.update(ok=False,error=repr(error),traceback=traceback.format_exc())
        row['seconds']=round(time.monotonic()-started,2)
        rows.append(row)
        (HERE/'native_capture_v2_progress.json').write_text(json.dumps(rows,indent=2))
        print(json.dumps({k:row.get(k) for k in ('index','tag','ok','seconds','error')}),flush=True)
        if not row['ok']:
            raise RuntimeError('Native preflight failed; preserve output, do not collect reserved data')
    frozen()
    result=validate(OUT,[j['tag'] for j in jobs])
    (HERE/'native_capture_v2_fields.json').write_text(json.dumps(result,indent=2))
    assert result['status'] == 'PASS', result['errors']
    negative=copy.deepcopy(rec)
    negative['frames'][0]['public_objects'].pop('projectiles')
    assert inspect(negative)['errors'].get('projectiles_export_missing',0)>0
    receipt=dict(complete=True,replays=len(rows),repeats=4,
        inputs_sha256=sha(HERE/'native_capture_v2_inputs.json'),
        remote_hashes_sha256=sha(HERE/'native_capture_v2_remote_hashes.json'),
        progress_sha256=sha(HERE/'native_capture_v2_progress.json'),
        fields_sha256=sha(HERE/'native_capture_v2_fields.json'),negative_control_passed=True)
    (HERE/'native_capture_v2_verified.json').write_text(json.dumps(receipt,indent=2))
    print('NATIVE_CAPTURE_V2_PREFLIGHT_PASS',flush=True)


if __name__ == '__main__':
    main()
