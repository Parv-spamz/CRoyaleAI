"""Serial training-only native controls; preserved raw inputs and original exclusions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
LOOP=HERE.parent
OUT=ROOT/'icebow/data/bench/native_confirmation_20261005/deal_recovery_training_v2'
sys.path[:0]=[str(LOOP),str(ROOT)]
from native_catalog_overlay import activate
_,CATALOG=activate()
from native_core.client import request
from research.sandbox_tools.validate_public_capture import inspect
from native_capture_identity import canonical_frames
from driver_patch_v2 import load
from solver import UnresolvedDeal

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def qualify(rec):
    g=rec['grade'];reasons=[]
    if g['plays_total']!=g['plays_driven']:reasons.append('undriven_commands')
    if g['accepted']!=g['plays_driven'] or g['rejected_by_reason']:reasons.append('rejected_commands')
    if g['skipped']:reasons.append('skipped_commands')
    if g['invalid_placement']:reasons.append('invalid_placement')
    if g['elixir_delays']['n'] or g['elixir_delays']['sum_ticks']:reasons.append('elixir_delay')
    if g['crowns_match'] is not True:reasons.append('crown_mismatch')
    if rec['final']['terminated'] is not True:reasons.append('nonterminal')
    return reasons

def main():
    assert not OUT.exists() and not (HERE/'complete_v2.json').exists()
    audit=read(HERE/'audit.json');assert audit['complete']
    remote=read(LOOP/'native_capture_v2_remote_hashes.json')
    def attest():
        r=subprocess.run(['C:/Android/Sdk/platform-tools/adb.exe','-s','emulator-5560','shell','sha256sum',*remote],
            text=True,capture_output=True,check=True)
        assert {x.split()[1]:x.split()[0] for x in r.stdout.splitlines()}==remote
        assert request({'op':'observe'},port=38031,timeout=10)['state']['state_hash_scope']=='public-observe-v6'
    attest();driver=load()
    paths=[*HERE.glob('*.py'),HERE/'audit.json',LOOP/'DEAL_RECOVERY_PLAN.md',HERE/'RESET_CORRECTION.md',LOOP/'native_catalog_overlay.py',
        LOOP/'native_catalog_corrected.json',LOOP/'native_capture_identity.py',
        ROOT/'research/sandbox_tools/replay_drive.py',ROOT/'research/sandbox_tools/validate_public_capture.py',
        ROOT/'pipeline/projectile_motion.py',*(ROOT/p for p in CATALOG['corrected_hashes'])]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}
    OUT.mkdir(parents=True)
    (HERE/'started_v2.json').write_text(json.dumps(dict(sources=hashes,remote=remote,
        patched_driver=driver.patch_provenance,selected=[x['tag'] for x in audit['training_trials']],
        started=time.time(),training_only=True,model_predictions=0),indent=2))
    rows=[]
    for item in audit['training_trials']:
        assert item['split']=='training'
        for path,value in hashes.items():assert sha(ROOT/path)==value,path
        assert sha(ROOT/item['recording'])==item['recording_sha256']
        job=item['job']
        for name,value in item['csv_hashes'].items():assert sha(ROOT/job['crawl']/name)==value
        driver.set_crawl(str(ROOT/job['crawl']));driver.set_plays_file('plays_ext.csv')
        row=dict(tag=item['tag'],role=item['role'],split='training',attempts=[])
        try:
            captured=[]
            for attempt in range(2):
                try:
                    rec=driver.drive(item['tag'],port=38031,seed=item['seed'],level=item['level'],
                        elixir_slack=40,tail_cap=7200,run_label=f'l72_deal_training_{attempt}',
                        verbose=False,record_every=10,record_full=True,record_plays=True,
                        drive_abilities=True,record_native=True,record_public_objects=True)
                except UnresolvedDeal as e:
                    failure=dict(error=str(e),reset_history=e.history,budget=64,source_unchanged=True)
                    path=OUT/f"{item['tag']}_{attempt}_unresolved.json"
                    path.write_text(json.dumps(failure,indent=2))
                    row['attempts'].append(dict(status='unresolved_opening',path=str(path.relative_to(ROOT)),sha256=sha(path)))
                    captured.append(failure);continue
                path=OUT/f"{item['tag']}_{attempt}.json";path.write_text(json.dumps(rec,separators=(',',':')))
                fields=inspect(rec);assert not fields['errors'],fields['errors']
                reasons=qualify(rec)
                if not reasons:assert all(p['engine_tick']==p['tick'] for p in rec['log'])
                row['attempts'].append(dict(status='captured',path=str(path.relative_to(ROOT)),sha256=sha(path),
                    grade=rec['grade'],reasons=reasons,usable=not reasons,
                    solver_resets=rec.get('deal_recovery',{}).get('resets',0)))
                captured.append(rec)
            a,b=captured
            assert row['attempts'][0]['status']==row['attempts'][1]['status']
            if row['attempts'][0]['status']=='unresolved_opening':
                assert a==b;row['usable']=False
            else:
                for k in ('final','log','grade','opening_deal_verified'):assert a[k]==b[k],k
                for k in ('frames','play_frames'):assert canonical_frames(a[k])==canonical_frames(b[k]),k
                if item['role']=='unchanged_control':
                    original=read(ROOT/item['recording'])
                    for k in ('final','log','grade'):assert a[k]==original[k],('control',k)
                    for k in ('frames','play_frames'):assert canonical_frames(a[k])==canonical_frames(original[k]),('control',k)
                row['usable']=row['attempts'][0]['usable']
            row['repeated_equal']=True
        except BaseException as error:
            row.update(fatal=repr(error),traceback=traceback.format_exc(),usable=False)
            rows.append(row)
            (HERE/'progress_v2.json').write_text(json.dumps(rows,indent=2))
            raise
        rows.append(row);(HERE/'progress_v2.json').write_text(json.dumps(rows,indent=2))
        print(json.dumps(dict(tag=row['tag'],role=row['role'],usable=row['usable'],attempts=row['attempts'])),flush=True)
    for path,value in hashes.items():assert sha(ROOT/path)==value,path
    attest()
    result=dict(complete=True,training_only=True,model_predictions=0,rows=rows,
        started_sha256=sha(HERE/'started_v2.json'),source_audit_sha256=sha(HERE/'audit.json'),
        usable_recovered=sum(r['usable'] for r in rows if r['role']=='fallback'),
        controls_unchanged=sum(r['role']=='unchanged_control' for r in rows),
        original_collections_modified=False,confirmation_replayed=False,N2_complete=False)
    (HERE/'complete_v2.json').write_text(json.dumps(result,indent=2))
    print('DEAL_RECOVERY_TRAINING_COMPLETE')

if __name__=='__main__':main()
