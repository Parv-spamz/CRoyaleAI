"""Outcome-blind availability audit of unused local replay commands, CPU only."""
from collections import Counter,defaultdict
import csv
import hashlib
import json
import os
from pathlib import Path
import re

os.environ['POLARS_MAX_THREADS']='2'
import polars as pl

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
HF=ROOT/'scratchpad/gauntlet/L67/hf/replays'
OUT=ROOT/'icebow/data/bench/confirmation_discovery_20261005'
FORM=re.compile(r'-(?:ev\d+|hero)$')
ICEBOW={'tornado','tesla','ice-wizard','x-bow','rocket','knight','the-log','skeletons'}


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def base(name):return FORM.sub('',str(name))


def signature(decks,seq):
    key=(sorted(tuple(sorted(base(c) for c in d)) for d in decks),len(seq),sorted(seq)[:12])
    return hashlib.sha256(json.dumps(key,separators=(',',':')).encode()).hexdigest()


def original_signatures():
    result=set();reports=[]
    for deck in ('icebow','hogeq'):
        folder=ROOT/deck/'data/royaleapi/crawl2'
        battles=folder/'battles.csv'
        if not battles.is_file():continue
        battle_rows=list(csv.DictReader(battles.open(encoding='utf-8-sig',newline='')))
        for path in sorted(folder.glob('plays_ext*.csv')):
            seqs=defaultdict(list)
            for r in csv.DictReader(path.open(encoding='utf-8-sig',newline='')):
                if r['attr_ability'] not in ('1','True'):
                    seqs[r['replay_tag']].append((int(r['tick']),base(r['attr_card'])))
            n=0
            for r in battle_rows:
                seq=seqs.get(r['replay_tag'])
                if seq:
                    result.add(signature([r['team_deck'].split(','),r['opponent_deck'].split(',')],seq));n+=1
            reports.append(dict(battles=str(battles.relative_to(ROOT)),battles_sha256=sha(battles),
                plays=str(path.relative_to(ROOT)),plays_sha256=sha(path),matched_battles=n))
    return result,reports


def strata(decks):
    out=set()
    for side in range(2):
        own,opp=set(map(base,decks[side])),set(map(base,decks[1-side]))
        if own==ICEBOW:out.add('exact_icebow')
        if {'rocket','tornado'}<=own:out.add('rocket_tornado_deck')
        if 'rocket' in own:out.add('rocket_deck')
        if 'x-bow' in own:out.add('xbow_deck')
        if 'the-log' in own and 'goblin-barrel' in opp:out.add('log_vs_barrel')
        for card in ('witch','night-witch','furnace'):
            if card in opp:
                out.add('versus_'+card)
                if own==ICEBOW:out.add('icebow_vs_'+card)
    return sorted(out)


def main():
    if OUT.exists():raise ValueError('Fresh discovery directory required')
    OUT.mkdir(parents=True)
    exposure_file=HERE/'historical_exposure_tags_v2.json'
    exposed=set(json.loads(exposure_file.read_text()))
    known,crawls=original_signatures()
    historical_found=set();candidates=[];counts=Counter();files=[]
    manifest=json.loads((ROOT/'tools/hf_manifest.json').read_text())
    expected={Path(r['path']).name:r for r in manifest['files'] if r['path'].startswith('replays/')}
    for path in sorted(HF.glob('*.parquet')):
        meta=expected[path.name];digest=sha(path)
        if path.stat().st_size!=meta['bytes'] or digest!=meta['sha256']:
            raise ValueError('Parquet provenance mismatch: '+path.name)
        files.append(dict(name=path.name,sha256=digest))
        df=pl.read_parquet(path,columns=['replay_tag','payload_json'])
        for tag,payload in df.iter_rows():
            counts['raw_replays']+=1
            p=json.loads(payload);battle=p['battle']
            players=[battle[s]['players'] for s in ('team','opponent')]
            if any(len(x)!=1 for x in players):counts['not_1v1']+=1;continue
            decks=[[c['card_key'] for c in x[0]['deck']] for x in players]
            events=[e for e in p['events'] if e['kind']=='play_card']
            seq=[(int(e['source_fields']['data_t']),base(e['card_key'])) for e in events]
            key=signature(decks,seq)
            if tag.lower() in exposed:
                known.add(key);historical_found.add(tag.lower());counts['known_id']+=1;continue
            if not events or any(e['source_fields'].get('data_x') is None or e['source_fields'].get('data_y') is None for e in events):
                counts['unpositioned_or_empty']+=1;continue
            if any(len(d)!=8 or len(set(map(base,d)))!=8 for d in decks):
                counts['invalid_deck']+=1;continue
            candidates.append(dict(tag=tag,part=path.name,signature=key,decks=decks,strata=strata(decks)))
        print(path.name,'read',counts['raw_replays'],flush=True)
    if set(expected)!=set(p['name'] for p in files):raise ValueError('Missing replay parts')
    groups={}
    for row in sorted(candidates,key=lambda x:x['tag']):
        if row['signature'] in known:counts['historical_command_duplicate']+=1;continue
        if row['signature'] in groups:counts['unused_command_duplicate']+=1;continue
        groups[row['signature']]=row
    output=OUT/'candidate_commands.jsonl'
    eligible=Counter()
    with output.open('x') as stream:
        for row in groups.values():
            eligible.update(row['strata']);stream.write(json.dumps(row)+'\n')
    expected_hf={t for t in exposed if len(t)==32}
    if expected_hf-historical_found:
        raise ValueError('Historical HF IDs not found in full raw corpus')
    report=dict(counts=dict(counts),historical_hf_ids=len(historical_found),
        historical_signatures=len(known),unused_unique_command_groups=len(groups),strata=dict(eligible),
        raw_parts=files,crawl_sources=crawls,exposure_sha256=sha(exposure_file),
        candidates=str(output),candidates_sha256=sha(output),script_sha256=sha(__file__),
        limitations=['Availability only; native reconstruction and final component denominators not established.',
                    'Conservative command-prefix deduplication may merge some distinct games.',
                    'Anonymous sources cannot establish player-disjointness.',
                    'No model predictions or win/finishing labels were inspected.'])
    (HERE/'unused_hf_inventory.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('raw_parts','crawl_sources')}))
    print('UNUSED_HF_INVENTORY_COMPLETE')


if __name__=='__main__':main()
