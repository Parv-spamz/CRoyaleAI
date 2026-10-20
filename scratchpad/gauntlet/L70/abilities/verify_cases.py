"""Small deterministic fixtures for attribution and aggregation; no engine imports."""
import json
from pathlib import Path
import time

import pyarrow as pa
import pyarrow.parquet as pq
import mine_abilities as m


def event(kind, seconds, card=None, candidates=None, side='team', xy=None):
    d = {'kind': kind, 'replay_tick_20hz': round(seconds*20), 'time_seconds': seconds,
         'card_key': card, 'side': side, 'ability_source_candidates': candidates or [],
         'ability_source_authoritative': False if kind == 'activate_ability' else None}
    if xy:
        d['coordinates'] = {'native_world_units': dict(zip(['x','y'],xy))}
    return d


def play(t, c='knight', side='team', xy=(3500,5000)):
    return event('play_card',t,c,side=side,xy=xy)


def press(t, cs=('knight-hero',), side='team', xy=None):
    return event('activate_ability',t,candidates=list(cs),side=side,xy=xy)


def battle(tag, events, deck=('knight-hero','monk'), crowns=(0,0)):
    return {'schema_version':'royaleapi-battle-actions.v1','source':{'replay_tag':tag},
            'battle':{s:{'crowns':crowns[i], 'players':[{'deck':[{'card_key':c} for c in deck]}]}
                      for i,s in enumerate(['team','opponent'])}, 'events':events}


def main():
    root = Path(__file__).resolve().parent
    fixtures = root/'verification_fixtures'
    assert fixtures.resolve().is_relative_to(root.resolve())
    fixtures.mkdir(exist_ok=True)
    m.OUT = fixtures
    m.DATA = fixtures
    m.START = time.monotonic()
    deck = ('knight-hero','musketeer-hero')
    records = [
        battle('repeat', [play(10), press(15),play(16,'the-log'),press(25),play(50),press(55)]),
        battle('resolve', [play(0),play(20,'musketeer'),press(25,deck)],deck),
        battle('tie', [play(20),play(20,'musketeer'),press(25,deck)],deck),
        battle('expired', [play(0),press(100,deck)],deck),
        battle('empty', [press(12,())]),
        battle('unlinked', [press(12)]),
        battle('same-tick', [play(10),play(15,'the-log'),press(15),play(15,'zap'),press(60),
                              play(61.05,'zap'),press(120),press(180)],crowns=(1,0)),
        battle('opponent', [play(10,side='opponent',xy=(15000,30000)),
                             press(11,side='opponent',xy=(15000,15000)),play(11.5,'zap')]),
    ]
    path = fixtures/'fixture.parquet'
    pq.write_table(pa.table({'payload_json':[json.dumps(r) for r in records]}), path)
    inventory = m.calibrate([path])
    for v in inventory['calibration'].values():
        v['window_seconds'] = 10
    total, _, a = m.analyse([path], inventory)
    m.enrich_repeat_evidence(a)
    assert total['presses'] == 13, total
    assert total['unresolved'] == 3, total
    assert total['resolved_multiple'] == 1
    assert a['musketeer-hero']['presses'] == 1
    k = a['knight-hero']
    assert k['presses'] == 9
    assert k['unlinked_presses'] == 1
    assert k['deployment_press_distribution']['counts'] == {'0':3,'1':2,'2+':2}, k
    assert k['combo_within_1s']['count'] == 2  # inclusive 1s and later same-tick, not opposite side / 1.05s
    assert k['combo_within_1s']['same_tick_count'] == 1
    assert k['repeat_gap_seconds'] == m.quantiles([10,45,60,60])
    assert k['repeat_deployment_attribution_evidence'] == {'all_single_candidate':2,'includes_heuristic_attribution':0}
    assert k['phase']['counts'] == {'0-60':6,'60-120':1,'120-180':1,'OT':1,'unknown':0}
    assert k['crowns_at_press']['counts'] == {'ahead':0,'behind':0,'tied':5,'unknown':4}
    assert k['press_coordinates']['counts']['right/enemy'] == 1
    assert k['unresolved_candidate_mentions'] == 2
    assert a['monk']['presses'] == a['monk']['deployments'] == 0
    assert a['monk']['n_deck_battles'] > 0
    print('ABILITY_CASES_PASSED',flush=True)


if __name__ == '__main__':
    main()
