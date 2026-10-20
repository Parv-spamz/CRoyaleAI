"""Prepare all previously Void-blocked exact-Icebow groups without outcomes."""
import csv,hashlib,json,os,sys
from pathlib import Path
os.environ['POLARS_MAX_THREADS']='2'
import polars as pl
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
LOOP=HERE.parent
OUT=ROOT/'icebow/data/bench/native_confirmation_20261005/reserved_void'
sys.path[:0]=[str(HERE),str(LOOP),str(ROOT)]
from driver import load,controls
from tools.hf_to_crawl import to_crawl,write_crawl
from audit_unused_hf import base,signature

def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    assert not OUT.exists() and not (HERE/'prepared.json').exists()
    driver,catalog=load();control=controls(driver)
    old=read(LOOP/'native_compatibility_corrected.json')
    excluded=[r for r in old['exact_icebow'] if not r['compatible']]
    assert len(excluded)==10 and all(r['errors']==['Unverified native card mapping: void'] for r in excluded)
    expected={r['tag'] for r in excluded};reservation=read(LOOP/'replay_reservation.json')
    assert sha(reservation['reservation_file'])==reservation['reservation_sha256']
    reserved={r['tag']:r for line in Path(reservation['reservation_file']).read_text().splitlines() if (r:=json.loads(line))}
    source=ROOT/'icebow/data/bench/confirmation_discovery_20261005/candidate_commands.jsonl'
    assert sha(source)==reservation['candidate_commands_sha256']
    selected=sorted([r for line in source.read_text().splitlines() if (r:=json.loads(line))['tag'] in expected],key=lambda r:r['tag'])
    assert len(selected)==len(expected) and {r['tag'] for r in selected}==expected
    for row in selected:
        r=reserved[row['tag']];assert row['signature']==r['signature'] and r['split']=='confirmation'
        row['split']=r['split'];assert 'exact_icebow' in row['strata']
    prior=read(LOOP/'deal_recovery/audit.json');assert not expected & {r['tag'] for r in prior['records']}
    parts={Path(r['path']).name:r for r in read(ROOT/'tools/hf_manifest.json')['files'] if r['path'].startswith('replays/')}
    by_tag={r['tag']:r for r in selected};converted={};raw_hashes={};payloads={}
    for name in sorted({r['part'] for r in selected}):
        path=ROOT/'scratchpad/gauntlet/L67/hf/replays'/name
        assert path.stat().st_size==parts[name]['bytes'] and sha(path)==parts[name]['sha256'];raw_hashes[name]=sha(path)
        for tag,raw in pl.read_parquet(path,columns=['replay_tag','payload_json']).iter_rows():
            if tag not in by_tag:continue
            assert tag not in converted and by_tag[tag]['part']==name
            p=json.loads(raw);sides={s:p['battle'][s]['players'][0] for s in ('team','opponent')}
            decks={s:[c['card_key'] for c in sides[s]['deck']] for s in sides}
            assert [decks[s] for s in ('team','opponent')]==by_tag[tag]['decks']
            seq=[(int(e['source_fields']['data_t']),base(e['card_key'])) for e in p['events'] if e['kind']=='play_card']
            assert signature(list(decks.values()),seq)==by_tag[tag]['signature']
            converted[tag]=to_crawl(tag,p,sides,decks,'team');payloads[tag]=(hashlib.sha256(raw.encode()).hexdigest(),p)
    assert set(converted)==expected
    OUT.mkdir(parents=True);jobs=[];csv_hashes={};commands=0
    for row in selected:
        tag=row['tag'];folder=OUT/'crawl'/tag;battle,plays=converted[tag]
        write_crawl(folder,[battle],plays,[tag])
        with (folder/'plays_ext.csv').open(encoding='utf-8',newline='') as f:actual=list(csv.DictReader(f))
        events=sorted(payloads[tag][1]['events'],key=lambda e:(int(e['source_fields']['data_t']),e['source_index']))
        assert len(actual)==len(events)
        for n,(out,event) in enumerate(zip(actual,events)):
            sf=event['source_fields'];ability=event['kind']!='play_card'
            want=dict(replay_tag=tag,play_index=str(n),tick=str(int(sf['data_t'])),attr_t=str(int(sf['data_t'])),
                attr_s={'team':'blue','opponent':'red'}[event['side']],attr_i=str(int(sf.get('data_i') or 0)),
                attr_card='_invalid' if ability else event['card_key'],attr_ability=str(int(ability)),
                x_units='' if ability else str(int(sf['data_x'])),y_units='' if ability else str(int(sf['data_y'])))
            assert all(out[k]==v for k,v in want.items()),(tag,n);commands+=1
        driver.set_crawl(str(folder));driver.set_plays_file('plays_ext.csv');b,_=driver.load_battle(tag)
        for side in (0,1):assert len(driver.deck_for_side(b,side))==8
        for name in ('plays_ext.csv','battles.csv'):csv_hashes[str((folder/name).relative_to(ROOT))]=sha(folder/name)
        jobs.append(dict(row,crawl=str(folder.relative_to(ROOT)),raw_payload_sha256=payloads[tag][0],repeat=True))
    jobs_path=OUT/'jobs.json';jobs_path.write_text(json.dumps(jobs,indent=2))
    sources=[Path(__file__),HERE/'driver.py',HERE/'verified.json',HERE/'RECONSTRUCTION_PLAN.md',
        LOOP/'native_compatibility_corrected.json',LOOP/'replay_reservation.json',ROOT/'tools/hf_to_crawl.py']
    report=dict(complete=True,selected=len(jobs),commands_verified=commands,repeat_count=len(jobs),
        jobs_path=str(jobs_path),jobs_sha256=sha(jobs_path),csv_hashes=csv_hashes,raw_part_hashes=raw_hashes,
        controls=control,sources={str(p.relative_to(ROOT)):sha(p) for p in sources},
        model_predictions=0,trainable=False,N2_complete=False)
    (HERE/'prepared.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['selected','commands_verified','repeat_count','controls']}));print('VOID_RECONSTRUCTION_PREPARED')

if __name__=='__main__':main()
