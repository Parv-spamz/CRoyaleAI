"""Independently compare saved press records with original parquet payloads."""
from collections import Counter
import gzip
import json
from pathlib import Path

import pyarrow.parquet as pq

OUT = Path(__file__).resolve().parent
DATA = OUT.parents[3]/'scratchpad/gauntlet/L67/hf/replays'


def main():
    original = {}
    sample_battles = 0
    for path in sorted(DATA.glob('*.parquet')):
        batch = next(pq.ParquetFile(path).iter_batches(batch_size=8,columns=['payload_json'],use_threads=False))
        for row,raw in enumerate(batch.column(0).to_pylist()):
            battle = json.loads(raw)
            tag = battle['source']['replay_tag']
            for ei,e in enumerate(battle['events']):
                if e['kind']=='activate_ability':
                    original[(path.name,row,ei)] = (tag,e,battle['events'])
            sample_battles += 1
    compared = 0
    got = set()
    with gzip.open(OUT/'presses.jsonl.gz','rt',encoding='utf-8') as f:
        for line in f:
            saved = json.loads(line)
            key = (saved['file'],saved['row'],saved['event_index'])
            if key not in original:
                continue
            assert key not in got
            got.add(key)
            tag,e,events = original[key]
            assert tag == saved['replay_tag']
            assert e['side'] == saved['side']
            assert list(dict.fromkeys(e['ability_source_candidates'])) == saved['candidates']
            assert e['replay_tick_20hz'] == saved['tick']
            assert e['time_seconds'] == saved['time_seconds']
            if saved['card']:
                assert saved['card'] in saved['candidates']
                following = [(x['replay_tick_20hz'],i) for i,x in enumerate(events)
                             if x['kind']=='play_card' and x['side']==e['side'] and
                             (x['replay_tick_20hz'],i) > (e['replay_tick_20hz'],saved['event_index'])]
                expected_combo = bool(following and min(following)[0]-e['replay_tick_20hz'] <= 20)
                assert expected_combo == saved['combo_within_1s']
                if 'deployment_event_index' in saved:
                    dep = events[saved['deployment_event_index']]
                    assert dep['kind']=='play_card' and dep['side']==e['side']
                    assert abs((e['replay_tick_20hz']-dep['replay_tick_20hz'])/20-saved['delay_seconds']) < 1e-6
                    actual = (dep.get('coordinates') or {}).get('native_world_units')
                    if saved['deployment_position']:
                        assert actual['x']==saved['deployment_position']['x'] and actual['y']==saved['deployment_position']['y']
            compared += 1
    assert compared == len(original), (compared,len(original))
    result = {'sample_battles':sample_battles,'presses_compared':compared,'files_sampled':len(list(DATA.glob('*.parquet')))}
    (OUT/'source_verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('ABILITY_SOURCE_COMPARISON_PASSED',result,flush=True)


if __name__=='__main__':
    main()
