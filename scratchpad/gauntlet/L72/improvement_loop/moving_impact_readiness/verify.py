"""Independent saved-frame recount; imports no engine, model or producer."""
import copy
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ARMS = ('wait', 'wait_repeat', 'snapshot', 'forward2', 'forward4', 'sideways6')


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def entities(frame):
    assert not frame['game_over'] and frame['winner'] == -1 and frame['crowns'] == [0, 0]
    assert len(frame['elixir']) == 2 and all(type(v) is int and 0 <= v <= 10000 for v in frame['elixir'])
    out = {}
    towers = set()
    for e in frame['entities']:
        assert e['uid'] not in out
        assert type(e['hp']) is int and 0 < e['hp'] <= e['max_hp']
        assert all(type(e[f]) is int for f in ('uid', 'team', 'x', 'y', 'card_id', 'max_hp'))
        out[e['uid']] = e
        if e['card_id'] == -1:
            k = (e['team'], e['tower_slot'])
            assert k not in towers and e['kind'] == (2 if k[1] == 0 else 3)
            towers.add(k)
    assert towers == set(itertools.product((0, 1), (0, 1, 2)))
    return out


def check_root(r, branches, cat):
    assert set(branches) == set(ARMS)
    side, enemy = r['side'], 1-r['side']
    lane, count = r['lane'], r['count']
    original = entities(r['root_frame'])
    assert r['root_frame']['tick'] == 240 and len(original) == 6+count
    body = {uid: e for uid, e in original.items() if e['card_id'] != -1}
    assert set(body) == set(r['troop_ids']) and len(body) == count
    assert sorted(e['card_id'] for e in body.values()) == sorted(
        [cat['Knight']['card_id']] + ([cat['Giant']['card_id']] if count == 2 else []))
    assert all(e['team'] == enemy and e['level'] == r['level'] and e['hp'] == e['max_hp'] for e in body.values())
    target = body[r['target_uid']]
    assert target['card_id'] == cat['Knight']['card_id']
    assert r['before_setup']['tick'] == r['after_setup']['tick'] == 180
    assert len(r['setup_commands']) == len(r['setup_results']) == count
    for index, (cmd, result) in enumerate(zip(r['setup_commands'], r['setup_results'], strict=True)):
        x = (81000 if lane == 0 else 243000) + (index*(18000 if lane == 0 else -18000))
        y = 72000 if enemy == 0 else 504000
        assert cmd == dict(team=enemy, hand_slot=index+1, x=x, y=y)
        assert result['team'] == enemy and result['hand_slot'] == index+1 and result['status'] == 0
        assert result['card_id'] == cat['Knight' if index == 0 else 'Giant']['card_id']
        assert result['tick'] == 180 and (result['x'], result['y']) == (x, y)
    assert r['before_setup']['elixir'][enemy] - r['after_setup']['elixir'][enemy] == 1000*(
        cat['Knight']['cost'] + (cat['Giant']['cost'] if count == 2 else 0))
    wait = branches['wait']['frames']
    assert wait == branches['wait_repeat']['frames']
    assert branches['wait']['final_sha256'] == branches['wait_repeat']['final_sha256']
    for f in wait:
        assert {k: e['hp'] for k, e in entities(f).items()} == {k: e['hp'] for k, e in original.items()}
        assert not f['spells'] and not f['projectiles']
    final = entities(wait[-1])
    displacement = {str(uid): (e['x']-final[uid]['x'])**2 + (e['y']-final[uid]['y'])**2
                    for uid, e in body.items()}
    assert all(v > 0 for v in displacement.values())
    summaries = {}
    for arm, b in branches.items():
        assert b['root_id'] == r['root_id'] and b['arm'] == arm and b['root_sha256'] == r['root_sha256']
        assert [f['tick'] for f in b['frames']] == list(range(240, 447))
        assert b['frames'][:26] == wait[:26] and b['before'] == wait[26]
        curves = {uid: [] for uid in original}
        for f, baseline in zip(b['frames'], wait, strict=True):
            current = entities(f)
            reference = entities(baseline)
            assert current.keys() == original.keys()
            assert f['elixir'][enemy] == baseline['elixir'][enemy]
            for uid, e in current.items():
                assert all(e[k] == original[uid][k] for k in ('uid', 'team', 'kind', 'card_id', 'max_hp', 'level'))
                delta = reference[uid]['hp'] - e['hp']
                assert delta >= 0
                if uid not in body:
                    assert delta == 0
                    assert (e['x'], e['y'], e['tower_slot']) == (
                        original[uid]['x'], original[uid]['y'], original[uid]['tower_slot'])
                curves[uid].append(delta)
            assert not f['projectiles']  # Any ordinary attack projectile invalidates isolation.
            assert all(s['card_id'] == cat['Rocket']['card_id'] and s['team'] == side for s in f['spells'])
        cost = b['before']['elixir'][side]-b['frames'][26]['elixir'][side]
        if arm.startswith('wait'):
            assert b['command'] is b['result'] is None and cost == 0
        else:
            dx = (108000 if lane == 0 else -108000) if arm == 'sideways6' else 0
            dy = (int(arm[-1])*18000*(1 if enemy == 0 else -1)) if arm.startswith('forward') else 0
            command = dict(team=side, hand_slot=0, x=target['x']+dx, y=target['y']+dy)
            assert b['command'] == command
            result = b['result']
            assert result['status'] == 0 and result['card_id'] == cat['Rocket']['card_id'] and result['tick'] == 266
            assert all(result[k] == v for k, v in command.items())
            assert cost == cat['Rocket']['cost']*1000
        assert not b['frames'][-1]['spells']
        effects = {}
        for uid, values in curves.items():
            assert all(a <= c for a, c in zip(values, values[1:])) and len(set(values[-10:])) == 1
            effects[str(uid)] = dict(final=values[-1], first_tick=next(
                (240+i for i, v in enumerate(values) if v > 0), None), curve_sha256=
                hashlib.sha256(json.dumps(values, separators=(',', ':')).encode()).hexdigest())
        summaries[arm] = dict(effects=effects, bodies_damaged=sum(effects[str(u)]['final'] > 0 for u in body), cost_milli=cost)
    assert summaries == r['summary']
    return dict(root_id=r['root_id'], effects=summaries, wait_displacement_squared=displacement)


def main():
    assert not (HERE/'verified.json').exists()
    report = read(HERE/'report.json')
    assert report['complete'] and report['models_loaded'] == report['optimizer_updates'] == 0
    assert not report['native_client_parity'] and not report['policy_acceptance']
    for path, expected in report['sources'].items():
        assert sha(ROOT/path) == expected
    catpath = ROOT/'icebow/data/bench/moving_impact_readiness_20261005/catalogue.json'
    assert sha(catpath) == report['catalogue_sha256'] and read(catpath) == report['catalogue']
    cat = report['catalogue']
    members = list(itertools.product((0, 1), (0, 1), (11, 14), (1, 2)))
    assert len(report['roots']) == len(members)
    summaries = []
    first = None
    for index, (r, member) in enumerate(zip(report['roots'], members, strict=True)):
        assert tuple(r[k] for k in ('side', 'lane', 'level', 'count')) == member
        assert r['seed'] == 2026100700+index
        assert r['root_id'] == 's%d_p%d_l%d_n%d' % member
        assert sha(ROOT/r['root_path']) == r['root_sha256']
        branches = {}
        for arm, source in r['branches'].items():
            assert sha(ROOT/source['path']) == source['sha256']
            assert sha(ROOT/source['final_path']) == source['final_sha256']
            branches[arm] = read(ROOT/source['path'])
            assert branches[arm]['final_sha256'] == source['final_sha256']
        summaries.append(check_root(r, branches, cat))
        if first is None:
            first = (r, branches)
    hits = sum(r['summary'][a]['bodies_damaged'] > 0 for r in report['roots'] for a in ARMS[2:])
    misses = sum(r['summary'][a]['bodies_damaged'] == 0 for r in report['roots'] for a in ARMS[2:])
    multi = sum(r['summary'][a]['bodies_damaged'] == 2 for r in report['roots'] for a in ARMS[2:])
    assert (hits, misses, multi) == (report['casts_with_damage'], report['casts_without_damage'], report['casts_with_two_hits'])
    assert hits > 0 and misses > 0 and multi > 0 and hits+misses == 64
    negative = 0
    for kind in range(12):
        r, b = copy.deepcopy(first)
        uid = r['target_uid']
        e = next(e for e in b['snapshot']['frames'][100]['entities'] if e['uid'] == uid)
        if kind == 0: del b['snapshot']
        if kind == 1: b['snapshot']['frames'].pop()
        if kind == 2: b['snapshot']['frames'][100]['entities'].remove(e)
        if kind == 3: e['uid'] = 0
        if kind == 4: e['card_id'] += 1
        if kind == 5: e['team'] = 1-e['team']
        if kind == 6: e['hp'] -= 1
        if kind == 7: b['snapshot']['result']['tick'] += 1
        if kind == 8: b['snapshot']['command']['x'] += 1
        if kind == 9: b['snapshot']['result']['status'] = 1
        if kind == 10: b['wait_repeat']['final_sha256'] = 'wrong'
        if kind == 11: r['summary']['snapshot']['cost_milli'] += 1
        try:
            check_root(r, b, cat)
        except (AssertionError, KeyError, ValueError, IndexError):
            negative += 1
        else:
            raise AssertionError(f'Corruption {kind} was not rejected')
    result = dict(complete=True, report_sha256=sha(HERE/'report.json'), roots=16, branches=96,
        frames=16*6*207, casts_with_damage=hits, casts_without_damage=misses, casts_with_two_hits=multi,
        controls=dict(positive=16, negative=negative), summary=summaries,
        models_loaded=0, optimizer_updates=0, native_client_parity=False, policy_acceptance=False)
    (HERE/'verified.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('MOVING_IMPACT_VERIFIED', hits, misses, multi, 'negative', negative)


if __name__ == '__main__':
    main()
