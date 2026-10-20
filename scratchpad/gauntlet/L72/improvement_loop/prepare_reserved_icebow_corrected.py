"""Freeze and independently verify a small outcome-blind native collection batch."""
from collections import Counter,defaultdict
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ['POLARS_MAX_THREADS']='2'
import polars as pl
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'icebow/data/bench/native_confirmation_20261005/reserved_icebow_corrected'
sys.path.insert(0,str(ROOT))
from tools.hf_to_crawl import to_crawl,write_crawl
from audit_unused_hf import base,signature


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    if OUT.exists():raise ValueError('Fresh pilot output required')
    compat=json.loads((HERE/'native_compatibility_corrected.json').read_text())
    source=Path(compat['compatible_file'])
    assert sha(source)==compat['compatible_sha256']
    reservation=json.loads((HERE/'replay_reservation.json').read_text())
    assert sha(reservation['reservation_file'])==reservation['reservation_sha256']
    reserved={r['tag']:r for line in Path(reservation['reservation_file']).read_text().splitlines()
              if (r:=json.loads(line))}
    old=json.loads((HERE/'native_compatibility.json').read_text(encoding='utf-8'))
    original_exact={r['tag'] for r in old['exact_icebow'] if r['compatible']}
    assert len(original_exact)==11
    groups=[]
    with source.open(encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)
            if 'exact_icebow' in row['strata'] and row['tag'] not in original_exact:groups.append(row)
    groups.sort(key=lambda r:r['tag'])
    salt='all-newly-compatible-exact-icebow-in-tag-order-no-outcome-filter'
    reasons={r['tag']:['newly_compatible_original_elite_evolution'] for r in groups}
    selected=groups
    expected={r['tag'] for r in compat['exact_icebow'] if r['compatible']}-original_exact
    assert {r['tag'] for r in selected}==expected and expected
    assert all(r['split']=='confirmation' for r in selected)
    for row in selected:
        bound=reserved[row['tag']]
        assert (row['split'],row['signature'])==(bound['split'],bound['signature'])
    by_tag={r['tag']:r for r in selected}
    OUT.mkdir(parents=True)
    (OUT/'selected.json').write_text(json.dumps(selected,indent=2))
    (OUT/'selection_reasons.json').write_text(json.dumps(reasons,indent=2))
    manifest=json.loads((ROOT/'tools/hf_manifest.json').read_text())
    parts={Path(r['path']).name:r for r in manifest['files'] if r['path'].startswith('replays/')}
    converted={};payloads={};raw_hashes={}
    for name in sorted({r['part'] for r in selected}):
        path=ROOT/'scratchpad/gauntlet/L67/hf/replays'/name
        assert path.stat().st_size==parts[name]['bytes']
        digest=sha(path);assert digest==parts[name]['sha256'];raw_hashes[name]=digest
        for tag,raw in pl.read_parquet(path,columns=['replay_tag','payload_json']).iter_rows():
            if tag not in by_tag:continue
            assert tag not in converted
            assert by_tag[tag]['part']==name
            p=json.loads(raw)
            sides={s:p['battle'][s]['players'][0] for s in ('team','opponent')}
            decks={s:[c['card_key'] for c in sides[s]['deck']] for s in sides}
            assert [decks[s] for s in ('team','opponent')]==by_tag[tag]['decks']
            seq=[(int(e['source_fields']['data_t']),base(e['card_key']))
                 for e in p['events'] if e['kind']=='play_card']
            assert signature(list(decks.values()),seq)==by_tag[tag]['signature']
            converted[tag]=to_crawl(tag,p,sides,decks,'team')
            payloads[tag]=dict(sha256=hashlib.sha256(raw.encode()).hexdigest(),payload=p)
        print(name,'selected converted',len(converted),flush=True)
    assert set(converted)==set(by_tag)
    jobs=[];csv_hashes={};command_count=0
    for index,row in enumerate(selected):
        tag=row['tag'];folder=OUT/'crawl'/tag
        battle,plays=converted[tag]
        write_crawl(folder,[battle],plays,[tag])
        actual=list(csv.DictReader((folder/'plays_ext.csv').open(encoding='utf-8',newline='')))
        events=sorted(payloads[tag]['payload']['events'],
                      key=lambda e:(int(e['source_fields']['data_t']),e['source_index']))
        assert len(actual)==len(events)
        for n,(output,event) in enumerate(zip(actual,events)):
            sf=event['source_fields'];ability=event['kind']!='play_card'
            expected=dict(replay_tag=tag,play_index=str(n),tick=str(int(sf['data_t'])),
                attr_t=str(int(sf['data_t'])),attr_s={'team':'blue','opponent':'red'}[event['side']],
                attr_i=str(int(sf.get('data_i') or 0)),attr_card='_invalid' if ability else event['card_key'],
                attr_ability=str(int(ability)),x_units='' if ability else str(int(sf['data_x'])),
                y_units='' if ability else str(int(sf['data_y'])))
            assert all(output[k]==v for k,v in expected.items()),(tag,n)
            command_count+=1
        written=list(csv.DictReader((folder/'battles.csv').open(encoding='utf-8',newline='')))[0]
        for side in ('team','opponent'):
            assert written[side+'_deck'].split(',')==sorted(by_tag[tag]['decks'][0 if side=='team' else 1])
        for name in ('plays_ext.csv','battles.csv'):
            file=folder/name;csv_hashes[str(file.relative_to(ROOT))]=sha(file)
        jobs.append(dict(row,index=index,crawl=str(folder.relative_to(ROOT)),plays_file='plays_ext.csv',
            raw_payload_sha256=payloads[tag]['sha256'],repeat=index%10==0))
    jobs_file=OUT/'jobs.json';jobs_file.write_text(json.dumps(jobs,indent=2))
    (OUT/'csv_hashes.json').write_text(json.dumps(csv_hashes,indent=2))
    report=dict(complete=True,selected=len(jobs),splits=dict(Counter(j['split'] for j in jobs)),
        strata={split:dict(Counter(s for j in jobs if j['split']==split for s in j['strata']))
                for split in ('training','development','confirmation')},
        exact_icebow=sum('exact_icebow' in j['strata'] for j in jobs),commands_verified=command_count,
        repeat_count=sum(j['repeat'] for j in jobs),salt=salt,jobs_path=str(jobs_file),jobs_sha256=sha(jobs_file),
        csv_hashes_path=str(OUT/'csv_hashes.json'),csv_hashes_sha256=sha(OUT/'csv_hashes.json'),
        selection_sha256=sha(OUT/'selected.json'),reasons_sha256=sha(OUT/'selection_reasons.json'),
        compatible_sha256=sha(source),reservation_sha256=sha(reservation['reservation_file']),raw_parts=raw_hashes,
        converter_sha256=sha(ROOT/'tools/hf_to_crawl.py'),script_sha256=sha(__file__),
        plan_sha256=sha(HERE/'NATIVE_CATALOG_CORRECTION_PLAN.md'),native_capture_started=False,original_compatibility_sha256=sha(HERE/'native_compatibility.json'),corrected_compatibility_sha256=sha(HERE/'native_compatibility_corrected.json'),
        model_predictions=0,training_authorized_by_this_report=False)
    (HERE/'reserved_icebow_corrected_prepared.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('raw_parts','strata')}))
    print('RESERVED_ICEBOW_CORRECTED_PREPARED_VERIFIED')


if __name__=='__main__':main()
