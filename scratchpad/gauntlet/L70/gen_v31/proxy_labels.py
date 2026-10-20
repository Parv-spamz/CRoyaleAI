"""Owner-authorized geometric proxies; causal truth remains a separate null.

These are label-side diagnostics. Future frames/commands never become features.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE))
from mine_xbows import xy, rate


def rocket_label(tower,troop):
    if (tower['tag'],tower['play_index'])!=(troop['tag'],troop['play_index']):
        raise ValueError('Mismatched Rocket event')
    targets=tower['targets']
    changes=[t['hp_drop_around_flight'] for t in targets if t.get('hp_drop_around_flight') is not None]
    flight_known=not troop['flight_ambiguous'] and troop.get('last_flight_tick') is not None
    candidates=troop['enemy_units_last_flight'] if flight_known else []
    return dict(tag=tower['tag'],play_index=tower['play_index'],side=tower['side'],tick=tower['tick'],
        proxy_tower_rocket=bool(targets),
        proxy_troop_rocket=bool(candidates) if flight_known else None,
        proxy_defensive_rocket=bool(candidates) and troop['target_half']=='own' if flight_known else None,
        proxy_rocket_then_tornado=any(c['order']=='rocket_then_tornado' and c['cast_window_prior'] for c in troop['combos']),
        proxy_tornado_then_rocket=any(c['order']=='tornado_then_rocket' and c['cast_window_prior'] for c in troop['combos']),
        audit_tower_hp_change_observed=bool(changes),
        audit_tower_positive_hp_loss=any(d>0 for d in changes),
        audit_tower_all_observed_nonpositive=bool(changes) and all(d<=0 for d in changes),
        audit_tower_edge_only=bool(targets) and all(t['distance_tiles']>2 for t in targets),
        audit_troop_damage_or_disappearance=any(c.get('disappearance') or (c.get('hp_drop') or 0)>0 for c in troop['compatible_hp_changes']),
        causal_tower_hit=None,causal_troop_hits=None,actual_elixir_value_hit=None)


def read_rows(path):
    with path.open() as f:return [json.loads(line) for line in f]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run(out):
    out.mkdir(parents=True,exist_ok=False)
    tp=HERE/'native_mining_1552/rockets.jsonl';up=HERE/'native_rocket_tornado_2140/rockets.jsonl'
    towers=read_rows(tp);troops=read_rows(up)
    keyed={(r['tag'],r['play_index']):r for r in troops}
    if len(keyed)!=len(troops) or len(towers)!=len(troops):raise ValueError('Duplicate/missing Rocket event')
    labels=[rocket_label(t,keyed[t['tag'],t['play_index']]) for t in towers]
    (out/'rocket_proxy_labels.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in labels))
    names=[n for n in labels[0] if n.startswith('proxy_')]
    report=dict(status='OWNER_AUTHORIZED_PROXY_LABELS_WITH_OBSERVABLE_DISAGREEMENT_AUDIT',
        inputs={str(p.relative_to(ROOT)):sha(p) for p in (tp,up,Path(__file__))},
        accepted_rocket_events=len(labels),
        labels={n:rate(labels,lambda r:r[n] is not None,lambda r:r[n]) for n in names},
        audit=dict(tower_no_hp_loss=rate(labels,lambda r:r['proxy_tower_rocket'] and r['audit_tower_hp_change_observed'],lambda r:r['audit_tower_all_observed_nonpositive']),
                   tower_edge_only=rate(labels,lambda r:r['proxy_tower_rocket'],lambda r:r['audit_tower_edge_only']),
                   tower_without_hp_evidence=rate(labels,lambda r:r['proxy_tower_rocket'],lambda r:not r['audit_tower_hp_change_observed']),
                   troop_without_compatible_change=rate(labels,lambda r:r['proxy_troop_rocket'] is True,lambda r:not r['audit_troop_damage_or_disappearance'])),
        causal_false_positive_rate=None,causal_false_negative_rate=None,
        contract={'tower':'Enemy living crown tower within the existing 3.5-tile audit envelope at accepted cast.',
                  'troop':'Enemy troop candidate within existing audit radius at last uniquely observed flight; ambiguous flights are unknown.',
                  'defensive':'Troop proxy plus own-half aim. This is a geometric defensive proxy, not player intent.',
                  'combo':'Existing 2.5-second/0.11 normalized-distance cast prior, each order separate; not confirmed pull/hit causality.',
                  'error':'No observed HP loss and edge sensitivity are diagnostic disagreements, not causal error rates. Missing evidence remains unknown.'})
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    # Deterministic, stratified examples; every board is loaded from the verified manifest.
    xp=HERE/'native_xbows_2020/xbows.jsonl';bows=read_rows(xp)
    manifest={r['tag']:r for r in json.loads((HERE/'native_mining_1552/manifest.json').read_text())}
    strata=[('common_row',lambda r:abs(r['xy'][1]-.609375)<1e-8),
            ('deep_row',lambda r:r['xy'][1]>=.70),('near_river',lambda r:r['xy'][1]<=.58),
            ('enemy_princess_down_dead_lane',lambda r:r['enemy_princess_down'] and r['lane_state']=='dead'),
            ('enemy_princess_down_alive_lane',lambda r:r['enemy_princess_down'] and r['lane_state']=='alive'),
            ('overtime_tower_rocket_10s',lambda r:r['phase']=='overtime' and r['tower_rocket_candidates_within_10s'])]
    examples=[];used=set()
    for label,predicate in strata:
        candidates=sorted((r for r in bows if predicate(r) and (r['tag'],r['play_index']) not in used),
            key=lambda r:hashlib.sha256(f"xbow-review:{r['tag']}:{r['play_index']}".encode()).hexdigest())[:2]
        for row in candidates:
            used.add((row['tag'],row['play_index']))
            entry=manifest[row['tag']];p=ROOT/entry['path']
            if sha(p)!=entry['sha256']:raise ValueError('Source changed')
            rec=json.loads(p.read_bytes())
            frames=[f for f in rec.get('play_frames',[]) if f.get('play_index')==row['play_index'] and f['tick']==row['context_tick']]
            if not frames:frames=[f for f in rec['frames'] if f['tick']==row['context_tick']]
            if not frames:raise ValueError('Missing audited board')
            f=frames[0];units=[]
            for e in f['entities']:
                if e[4]<=0 or e[-2]<0:continue
                units.append(dict(relation='own' if e[0]==row['side'] else 'enemy',name=e[3],
                    xy=xy(e[1],e[2],row['side']),hp=e[4],max_hp=e[5],native_id=e[-2],entity_id=e[-1]))
            examples.append(dict(stratum=label,source=entry,placement=row,public_units=units,
                strategic_label=None,review_status='OWNER_LEAD_REVIEW_REQUIRED'))
    (out/'xbow_examples.json').write_text(json.dumps(examples,indent=2)+'\n')
    lines=['# Defensive X-Bow review examples','',
        'Twelve deterministic native-census examples; full public board coordinates/HP and source hashes are in xbow_examples.json. Forward is decreasing normalized y. No strategic label has been approved.','',
        '| Stratum / replay / play | Placement x,y; river tiles | Crowns; enemy princess HP L/R | Visible enemy bodies (HP) | Tower-Rocket candidate within 10s |',
        '|---|---|---|---|---|']
    for e in examples:
        r=e['placement'];hp=r['tower_hp']
        units=', '.join(f"{u['name']} {u['hp']} @({u['xy'][0]:.2f},{u['xy'][1]:.2f})" for u in e['public_units'] if u['relation']=='enemy') or 'none'
        seq=', '.join(str(x['gap_s'])+'s' for x in r['tower_rocket_candidates_within_10s']) or 'none'
        lines.append(f"| {e['stratum']} / {r['tag']} / {r['play_index']} | {r['xy'][0]:.3f},{r['xy'][1]:.6f}; {r['river_distance_tiles']:.1f} | {r['crowns_ours_enemy']}; {hp.get('enemy_left')}/{hp.get('enemy_right')} | {units} | {seq} |")
    lines+=['','Assessment: the same placement depth appears with different threats, tower states and follow-on actions. Geometry alone is insufficient to approve a universal tactical-defense label. The y>0.58 bucket includes the common 0.609375 row; keep it geometric. Request Tuesday lead/owner review of the board examples before fitting the defensive-X-Bow target. Lane and exact placement distributions remain measured.',
        '', 'Rocket proxies are separately authorized now. Their observable disagreement audit does not create causal truth, and does not resolve the X-Bow label approval.']
    (out/'XBOW_REVIEW.md').write_text('\n'.join(lines)+'\n')
    print('PROXY_LABELS_AND_XBOW_EXAMPLES_WRITTEN',len(labels),len(examples))


if __name__=='__main__':
    import argparse
    from audit_runtime import lower_own_priority
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=HERE/'proxy_labels_2230')
    args=parser.parse_args()
    lower_own_priority();run(args.out)
