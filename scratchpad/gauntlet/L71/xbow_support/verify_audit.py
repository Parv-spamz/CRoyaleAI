"""Independent witness, source and aggregate verification for the support audit."""
import argparse
from bisect import bisect_right
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from pipeline.dataset_gen import card_key
from pipeline.opp_elixir_count import card_cost
from pipeline.rocket_teaching import sha


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=Path,required=True);a=ap.parse_args()
    report=json.loads((Path(__file__).parent/'audit.json').read_text())
    assert sha(a.source_root/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/manifest.json')==report['source_manifest_sha256']
    assert sha(a.source_root/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/labels.jsonl')==report['labels_sha256']
    sources={}
    for s in report['pro_sources']+report['live_sources']:
        path=a.source_root/s['path'];assert sha(path)==s['sha256']
        if 'tag' in s:sources[s['tag']]=json.loads(path.read_text())
    for row in report['pro_rows']:
        rec=sources[row['tag']]
        frames={f['tick']:f for f in rec['frames']+rec.get('play_frames',[])}
        ticks=sorted(frames)
        at=lambda tick:frames[ticks[bisect_right(ticks,tick)-1]]
        bow=row['bow'];fr=at(bow['tick'])
        targets=[t for t in fr['towers'] if t[0]!=bow['side'] and t[1]=='princess' and (t[3]<9000)==(bow['x']<9000)]
        assert len(targets)==1 and targets[0][5]<=0
        if not row['linked']:continue
        born=frames[row['birth']]
        assert any(e[-1]==row['entity_id'] and e[0]==bow['side'] and card_key(e[3])=='x-bow' for e in born['entities'])
        for p in row['support']:
            assert row['birth']<=p['tick']<=row['last_seen']
            assert math.hypot(p['x']-bow['x'],p['y']-bow['y'])<=report['distance_milli']
            assert p['cost']==card_cost(p['card'].replace('-','_'))
            assert any(q.get('accepted') and q['tick']==p['tick'] and q['side']==bow['side'] and
                card_key(q.get('card',''))==p['card'] and q['x']==p['x'] and q['y']==p['y'] for q in rec['log'])
    linked=[r for r in report['pro_rows'] if r['linked']]
    support=[p for r in linked for p in r['support']]
    no_target=[p for p in support if p['no_reachable_target_now']]
    measured=dict(dead_lane_bows=len(report['pro_rows']),linked=len(linked),
        crown_reachable=sum(r['crown_reachable'] for r in linked),
        defensive_contact_during_life=sum(r['defensive_contact'] for r in linked),
        no_observed_reachable_target_during_life=sum(not r['crown_reachable'] and not r['defensive_contact'] for r in linked),
        nearby_support_plays=len(support),nearby_support_elixir=sum(p['cost'] for p in support),
        no_target_support_plays=len(no_target),no_target_support_elixir=sum(p['cost'] for p in no_target),
        no_target_support_opposite_threat_6s=sum(p['next_opposite_threat_tick'] is not None for p in no_target),
        no_target_support_opposite_damage_6s=sum((p['opposite_tower_hp_drop_6s'] or 0)>0 for p in no_target),
        no_target_support_outcome_unknown=sum(not p['outcome_coverage'] for p in no_target))
    assert measured==report['pro']
    assert report['live']==dict(dead_lane_bows=len(report['live_rows']))
    print(json.dumps(measured));print('XBOW_AUDIT_WITNESSES_VERIFIED')


if __name__=='__main__':main()
