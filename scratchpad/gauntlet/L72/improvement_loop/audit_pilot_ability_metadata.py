"""Training-only audit of optional ability attribution lost by legacy CSV conversion."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
os.environ['POLARS_MAX_THREADS']='2'
import polars as pl
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from research.sandbox_tools.replay_drive import ability_candidates,split_slug


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    prepared=json.loads((HERE/'reserved_pilot_prepared.json').read_text())
    jobs_path=Path(prepared['jobs_path'])
    assert sha(jobs_path)==prepared['jobs_sha256']
    jobs={r['tag']:r for r in json.loads(jobs_path.read_text()) if r['split']=='training'}
    assert len(jobs)==209
    counts=Counter();differences=[];seen=set();payload_hashes={}
    for part in sorted({r['part'] for r in jobs.values()}):
        path=ROOT/'scratchpad/gauntlet/L67/hf/replays'/part
        assert sha(path)==prepared['raw_parts'][part]
        for tag,raw in pl.read_parquet(path,columns=['replay_tag','payload_json']).iter_rows():
            if tag not in jobs:continue
            seen.add(tag);p=json.loads(raw)
            payload_hashes[tag]=hashlib.sha256(raw.encode()).hexdigest()
            assert payload_hashes[tag]==jobs[tag]['raw_payload_sha256']
            for e in p['events']:
                if e['kind']=='play_card':continue
                counts['ability_events']+=1
                if 'ability_source_candidates' not in e:
                    counts['missing_candidate_field']+=1;continue
                candidates=e['ability_source_candidates']
                assert isinstance(candidates,list) and all(isinstance(c,str) for c in candidates)
                deck_index=0 if e['side']=='team' else 1
                deck=[dict(zip(('slug','form'),split_slug(token))) for token in jobs[tag]['decks'][deck_index]]
                source=ability_candidates({'ability_source_candidates':candidates},deck)
                fallback=ability_candidates({'attr_card':'_invalid'},deck)
                authority=e.get('ability_source_authoritative')
                counts['authoritative' if authority else 'non_authoritative']+=1
                counts['same_candidate_set' if set(source)==set(fallback) else 'different_candidate_set']+=1
                if source!=fallback:counts['different_candidate_order_or_set']+=1
                if not source:counts['explicit_empty_candidate_list']+=1
                if set(source)!=set(fallback):
                    differences.append(dict(tag=tag,source_index=e['source_index'],side=e['side'],
                        tick=e['replay_tick_20hz'],source_candidates=source,fallback_candidates=fallback,
                        source_authoritative=authority))
    assert seen==set(jobs)
    result=dict(training_replays=len(seen),counts=dict(counts),differences=differences,
        jobs_sha256=sha(jobs_path),prepared_sha256=sha(HERE/'reserved_pilot_prepared.json'),
        payload_hashes=payload_hashes,script_sha256=sha(__file__),
        converter_sha256=sha(ROOT/'tools/hf_to_crawl.py'),
        replay_driver_sha256=sha(ROOT/'research/sandbox_tools/replay_drive.py'),
        heldout_replays_read=0,model_predictions=0,
        note='Optional attribution is diagnostic metadata, not authoritative actual controller truth. No running source or data changed.')
    (HERE/'pilot_ability_metadata.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(training_replays=len(seen),counts=dict(counts))))
    print('TRAINING_PILOT_ABILITY_METADATA_AUDITED')


if __name__=='__main__':main()
