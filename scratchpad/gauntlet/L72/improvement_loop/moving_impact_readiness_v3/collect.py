"""Fixed isolated moving-body measurement fixtures. No policy or optimizer."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from pipeline.royale_runtime import activate
STAMP = activate()
from royalegym.rust_engine import RustEngine
from royalegym.protocol import MatchSetup, ShuffleMode, DeployCommand, DeployStatus

OUT = ROOT / 'icebow/data/bench/moving_impact_readiness_v3_20261005'
ARMS = ('wait', 'wait_repeat', 'snapshot', 'forward2', 'forward4', 'sideways6')
NAMES = ['Rocket', 'Knight', 'Giant', 'Log', 'Tesla', 'IceWizard', 'Tornado', 'Xbow']


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(p, x):
    p.write_text(json.dumps(x, allow_nan=False, separators=(',', ':')) + '\n', encoding='utf-8')


def item(value):
    return {key: getattr(value, key) for key in value.__struct_fields__}


def frame(core):
    s = core.state()
    assert not s.projectiles and all(e.attack_phase == 0 for e in s.entities)
    return dict(tick=s.tick, entities=[item(e) for e in s.entities],
                spells=[item(e) for e in s.spells], projectiles=[item(e) for e in s.projectiles],
                elixir=[p.elixir_milli for p in s.players], crowns=[p.crowns for p in s.players],
                game_over=s.game_over, winner=s.winner)


def sources():
    paths = list(HERE.glob('*.py')) + [HERE/'PLAN.md', HERE/'METRICS.md',
        ROOT/'scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness/collect.py',
        ROOT/'scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness/verify.py',
        ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-moving-impact-collection.json',
        ROOT/'scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness_v2/collect.py',
        ROOT/'scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness_v2/verify.py',
        ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-moving-impact-v2-collection.json',
        ROOT/'pipeline/royale_runtime.py', ROOT/'scratchpad/gauntlet/L71/royale_update_20261005/build_manifest.json']
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}


def describe(frames, wait, troop_ids, side):
    curves = {e['uid']: [] for e in wait[0]['entities']}
    for a, b in zip(frames, wait, strict=True):
        assert a['tick'] == b['tick']
        hp = {e['uid']: e['hp'] for e in a['entities']}
        assert set(hp) == set(curves)
        for entity in b['entities']:
            curves[entity['uid']].append(entity['hp'] - hp[entity['uid']])
    result = {}
    for uid, values in curves.items():
        assert min(values) >= 0 and all(a <= b for a, b in zip(values, values[1:]))
        assert len(set(values[-10:])) == 1
        original = next(e for e in wait[0]['entities'] if e['uid'] == uid)
        if original['team'] == side:
            assert max(values) == 0
        result[str(uid)] = dict(final=values[-1], first_tick=next(
            (frames[i]['tick'] for i, v in enumerate(values) if v), None), curve_sha256=
            hashlib.sha256(json.dumps(values, separators=(',', ':')).encode()).hexdigest())
    assert not frames[-1]['spells'] and not frames[-1]['projectiles']
    return result


def main():
    assert not (HERE/'report.json').exists()
    OUT.mkdir(exist_ok=False)
    bound = sources()
    write(HERE/'started.json', dict(sources=bound, runtime=STAMP, models_loaded=0, optimizer_updates=0))
    catalog = {c.name: c for c in RustEngine().cards()}
    deck = [catalog[n].card_id for n in NAMES]
    catalogue = {n: dict(card_id=catalog[n].card_id, cost=catalog[n].elixir) for n in NAMES}
    write(OUT/'catalogue.json', catalogue)
    records = []
    positive = misses = multi = 0
    for side in (0, 1):
      for lane in (0, 1):
       for level in (11, 14):
        for count in (1, 2):
            rid = f's{side}_p{lane}_l{level}_n{count}'
            seed = 2026100900 + len(records)
            enemy = 1-side
            core = RustEngine()
            setup = MatchSetup(decks=[deck, deck], shuffle=ShuffleMode.NONE,
                forms=[[0]*8, [0]*8], levels=[[level]*8, [level]*8], tower_levels=[level]*2)
            core.reset(seed, setup)
            core.step([], 180)
            before_setup = frame(core)
            x, y = (81000 if lane == 0 else 243000), (72000 if enemy == 0 else 504000)
            cmds = [DeployCommand(team=enemy, hand_slot=1, x=x, y=y)]
            if count == 2:
                cmds.append(DeployCommand(team=enemy, hand_slot=2,
                                         x=x+(18000 if lane == 0 else -18000), y=y))
            results = core.step(cmds, 0)
            assert len(results) == count and all(r.status == DeployStatus.OK for r in results)
            after_setup = frame(core)
            assert before_setup['elixir'][enemy]-after_setup['elixir'][enemy] == 1000*(
                catalogue['Knight']['cost']+(catalogue['Giant']['cost'] if count == 2 else 0))
            core.step([], 60)
            root_frame = frame(core)
            bodies = [e for e in root_frame['entities'] if e['card_id'] != -1]
            assert len(bodies) == count and all(e['team'] == enemy and e['hp'] > 0 for e in bodies)
            target, = [e for e in bodies if e['card_id'] == catalogue['Knight']['card_id']]
            troop_ids = [e['uid'] for e in bodies]
            root_bytes = bytes(core.save_state())
            root_path = OUT/(rid+'_root.bin')
            root_path.write_bytes(root_bytes)
            setup_record = dict(decks=[deck,deck], forms=[[0]*8,[0]*8], levels=[[level]*8,[level]*8], tower_levels=[level]*2, shuffle='NONE')
            metadata = dict(root_id=rid, seed=seed, setup=setup_record, before_setup=before_setup, after_setup=after_setup, setup_commands=[item(c) for c in cmds], setup_results=[item(r) for r in results], root_frame=root_frame, root_sha256=sha(root_path))
            metadata_path = OUT/(rid+'_root.json')
            write(metadata_path, metadata)
            branches = {}
            for arm in ARMS:
                core.load_state(root_bytes)
                assert bytes(core.save_state()) == root_bytes
                frames = [frame(core)]
                for _ in range(25):
                    core.step([], 1)
                    frames.append(frame(core))
                core.step([], 1)
                before = frame(core)
                command = result = None
                if not arm.startswith('wait'):
                    dx = (108000 if lane == 0 else -108000) if arm == 'sideways6' else 0
                    dy = ((36000 if arm == 'forward2' else 72000) * (1 if enemy == 0 else -1)
                          if arm in ('forward2', 'forward4') else 0)
                    command = dict(team=side, hand_slot=0, x=target['x']+dx, y=target['y']+dy)
                    r, = core.step([DeployCommand(**command)], 0)
                    result = item(r)
                    assert r.status == DeployStatus.OK
                frames.append(frame(core))
                for _ in range(130):
                    core.step([], 1)
                    frames.append(frame(core))
                final = OUT/(rid+'_'+arm+'_final.bin')
                final.write_bytes(bytes(core.save_state()))
                data = dict(root_id=rid, arm=arm, root_sha256=sha(root_path), before=before,
                            command=command, result=result, frames=frames, final_sha256=sha(final))
                p = OUT/(rid+'_'+arm+'.json')
                write(p, data)
                branches[arm] = dict(path=str(p.relative_to(ROOT)), sha256=sha(p),
                    final_path=str(final.relative_to(ROOT)), final_sha256=sha(final), data=data)
            wait = branches['wait']['data']['frames']
            assert wait == branches['wait_repeat']['data']['frames']
            assert branches['wait']['final_sha256'] == branches['wait_repeat']['final_sha256']
            root_hp = {e['uid']: e['hp'] for e in root_frame['entities']}
            for f in wait:
                assert {e['uid']: e['hp'] for e in f['entities']} == root_hp
                assert not f['projectiles'] and not f['spells']
            final_bodies = {e['uid']: e for e in wait[-1]['entities']}
            assert all((e['x'], e['y']) != (final_bodies[e['uid']]['x'], final_bodies[e['uid']]['y']) for e in bodies)
            summaries = {}
            for arm, b in branches.items():
                frames = b['data']['frames']
                cost = b['data']['before']['elixir'][side] - frames[26]['elixir'][side]
                assert cost == (0 if arm.startswith('wait') else catalogue['Rocket']['cost']*1000)
                effects = describe(frames, wait, troop_ids, side)
                hit_count = sum(effects[str(uid)]['final'] > 0 for uid in troop_ids)
                crown_hits = sum(v['final'] > 0 for uid,v in effects.items() if int(uid) not in troop_ids)
                category = ('body_and_crown' if crown_hits else 'body_only') if hit_count else ('crown_only' if crown_hits else 'no_damage')
                summaries[arm] = dict(effects=effects, bodies_damaged=hit_count, crowns_damaged=crown_hits, category=category, cost_milli=cost)
                if not arm.startswith('wait'):
                    positive += hit_count > 0
                    misses += not hit_count and not crown_hits
                    multi += hit_count == 2
                del b['data']
            records.append(dict(root_id=rid, seed=seed, side=side, lane=lane, level=level, count=count,
                setup_commands=[item(c) for c in cmds], setup_results=[item(r) for r in results],
                before_setup=before_setup, after_setup=after_setup, root_frame=root_frame,
                setup=setup_record, metadata_path=str(metadata_path.relative_to(ROOT)), metadata_sha256=sha(metadata_path),
                target_uid=target['uid'], troop_ids=troop_ids, root_path=str(root_path.relative_to(ROOT)),
                root_sha256=sha(root_path), branches=branches, summary=summaries))
            print('ROOT', rid, {a: summaries[a]['bodies_damaged'] for a in ARMS})
    assert positive and misses and multi
    assert sources() == bound
    write(HERE/'report.json', dict(complete=True, sources=bound, runtime=STAMP,
        catalogue=catalogue, catalogue_sha256=sha(OUT/'catalogue.json'), roots=records,
        casts_with_body_damage=positive, casts_without_damage=misses, casts_with_two_hits=multi,
        models_loaded=0, optimizer_updates=0, native_client_parity=False, policy_acceptance=False))
    print('MOVING_IMPACT_V3_COLLECTED')


if __name__ == '__main__':
    main()
