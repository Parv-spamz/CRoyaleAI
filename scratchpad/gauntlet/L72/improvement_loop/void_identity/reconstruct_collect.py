"""One serial source-reconstruction batch on the isolated native worker."""
import hashlib,json,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
LOOP=HERE.parent
OUT=ROOT/'icebow/data/bench/native_confirmation_20261005/reserved_void/recordings'
sys.path[:0]=[str(HERE),str(LOOP),str(LOOP/'deal_recovery'),str(ROOT)]
from driver import load

def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(rec):
    g=rec['grade'];why=[]
    if g['plays_total']!=g['plays_driven']:why.append('undriven_commands')
    if g['accepted']!=g['plays_driven'] or g['rejected_by_reason']:why.append('rejected_commands')
    if g['skipped']:why.append('skipped_commands')
    if g['invalid_placement']:why.append('invalid_placement')
    if g['elixir_delays']['n'] or g['elixir_delays']['sum_ticks']:why.append('elixir_delay')
    if g['crowns_match'] is not True:why.append('crown_mismatch')
    if rec['final']['terminated'] is not True:why.append('nonterminal')
    return why

def main():
    assert not OUT.exists() and not (HERE/'collection_complete.json').exists()
    driver,catalog=load()
    from native_core.card_catalog import validate_deck
    from research.sandbox_tools.validate_public_capture import inspect
    from native_capture_identity import canonical_frames
    from solver import UnresolvedDeal
    prepared=read(HERE/'prepared.json');assert prepared['complete']
    assert sha(prepared['jobs_path'])==prepared['jobs_sha256'];jobs=read(prepared['jobs_path'])
    for p,h in prepared['sources'].items():assert sha(ROOT/p)==h,p
    for p,h in prepared['csv_hashes'].items():assert sha(ROOT/p)==h,p
    for job in jobs:
        assert job['split']=='confirmation' and job['repeat']
        driver.set_crawl(str(ROOT/job['crawl']));driver.set_plays_file('plays_ext.csv')
        b,_=driver.load_battle(job['tag'])
        for side in (0,1):validate_deck(driver.deck_for_side(b,side))
    sources=[*HERE.glob('*.py'),HERE/'RECONSTRUCTION_PLAN.md',HERE/'prepared.json',HERE/'verified.json',
        LOOP/'deal_recovery/driver_patch_v3.py',LOOP/'deal_recovery/solver.py',
        LOOP/'native_capture_identity.py',LOOP/'native_catalog_overlay.py',LOOP/'native_catalog_corrected.json',
        ROOT/'research/sandbox_tools/replay_drive.py',ROOT/'research/sandbox_tools/validate_public_capture.py',
        ROOT/'pipeline/projectile_motion.py',*(ROOT/p for p in catalog['corrected_hashes'])]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sources};remote=read(LOOP/'native_capture_v2_remote_hashes.json')
    def attest():
        r=subprocess.run(['C:/Android/Sdk/platform-tools/adb.exe','-s','emulator-5560','shell','sha256sum',*remote],text=True,capture_output=True,check=True)
        assert {x.split()[1]:x.split()[0] for x in r.stdout.splitlines()}==remote
        for p,h in hashes.items():assert sha(ROOT/p)==h,p
    attest();OUT.mkdir()
    started=dict(sources=hashes,guest_hashes=remote,prepared_sha256=sha(HERE/'prepared.json'),
        original_form_validated_decks=len(jobs)*2,patch=driver.patch_provenance,started=time.time(),model_predictions=0)
    (HERE/'collection_started.json').write_text(json.dumps(started,indent=2));rows=[]
    for job in jobs:
        for p,h in hashes.items():assert sha(ROOT/p)==h,p
        driver.set_crawl(str(ROOT/job['crawl']));driver.set_plays_file('plays_ext.csv')
        row=dict(tag=job['tag'],split=job['split'],attempts=[]);records=[]
        try:
            for repeat in range(2):
                try:
                    rec=driver.drive(job['tag'],port=38031,seed=424242,level=11,elixir_slack=40,tail_cap=7200,
                        run_label=f'l72_void_{repeat}',verbose=False,record_every=10,record_full=True,record_plays=True,
                        drive_abilities=True,record_native=True,record_public_objects=True)
                except UnresolvedDeal as e:
                    rec=dict(error=str(e),reset_history=e.history,budget=61,total_reset_budget=64)
                    path=OUT/f"{job['tag']}_{repeat}_unresolved.json";path.write_text(json.dumps(rec,indent=2))
                    row['attempts'].append(dict(status='unresolved_opening',path=str(path.relative_to(ROOT)),sha256=sha(path)))
                    records.append(rec);continue
                assert not inspect(rec)['errors'];why=qualify(rec)
                if not why:assert all(p['engine_tick']==p['tick'] for p in rec['log'])
                path=OUT/f"{job['tag']}_{repeat}.json";path.write_text(json.dumps(rec,separators=(',',':')))
                row['attempts'].append(dict(status='captured',path=str(path.relative_to(ROOT)),sha256=sha(path),
                    grade=rec['grade'],reasons=why,usable=not why));records.append(read(path))
            a,b=records;assert row['attempts'][0]['status']==row['attempts'][1]['status']
            if row['attempts'][0]['status']=='unresolved_opening':assert a==b;row['usable']=False
            else:
                for k in ('final','log','grade','opening_deal_verified'):assert a[k]==b[k],k
                for k in ('frames','play_frames'):assert canonical_frames(a[k])==canonical_frames(b[k]),k
                row['usable']=row['attempts'][0]['usable']
            row['repeat_equal']=True
        except BaseException as e:
            row.update(fatal=repr(e),traceback=traceback.format_exc());rows.append(row)
            (HERE/'collection_progress.json').write_text(json.dumps(rows,indent=2));raise
        rows.append(row);(HERE/'collection_progress.json').write_text(json.dumps(rows,indent=2))
        print(json.dumps(dict(tag=row['tag'],usable=row['usable'])),flush=True)
    attest();result=dict(complete=True,rows=rows,usable=sum(r['usable'] for r in rows),
        started_sha256=sha(HERE/'collection_started.json'),prepared_sha256=sha(HERE/'prepared.json'),model_predictions=0,N2_complete=False)
    (HERE/'collection_complete.json').write_text(json.dumps(result,indent=2));print('VOID_RECONSTRUCTION_CAPTURE_COMPLETE')

if __name__=='__main__':main()
