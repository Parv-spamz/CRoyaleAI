"""Frozen offline hand audit. Private truth belongs only to this scorer."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'icebow/data/bench/opponent_hand_reader_20261006'
sys.path.insert(0, str(ROOT))
from pipeline.dataset_gen import card_key
from pipeline.native_recording import tag_native_recording
from pipeline.opponent_hand import PublicHandObserver, from_public_plays


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False))


def hand(names):
    if not isinstance(names, list) or len(names) != 4:
        return None
    cards = [card_key(n) for n in names]
    return sorted(cards) if all(cards) and len(set(cards)) == 4 else None


def add(c, prediction, truth):
    inside, outside, actual = set(prediction['in_hand']), set(prediction['out_of_hand']), set(truth)
    c['queries'] += 1
    c['full_predictions'] += int(prediction['full_hand'])
    c['full_exact'] += int(prediction['full_hand'] and inside == actual)
    c['full_errors'] += int(prediction['full_hand'] and inside != actual)
    c['in_claims'] += len(inside)
    c['in_correct'] += len(inside & actual)
    c['out_claims'] += len(outside)
    c['out_correct'] += len(outside - actual)
    c['unrevealed_slots'] += prediction['unrevealed_slots']
    c['issue_queries'] += bool(prediction['issues'])


def main():
    if OUT.exists() or (HERE/'collected.json').exists():
        raise ValueError('Fresh collection only')
    assignment_path = HERE.parent/'development_iteration_1/prepared.json'
    binding_path = HERE.parent/'match_adaptation/prepared.json'
    assignment = read(assignment_path)['assignment']
    binding = read(binding_path)['sources']
    chosen = [(part, tag) for part, n in [('training',32), ('development',128)]
              for tag in sorted(t for t, p in assignment.items() if p == part)[:n]]
    assert len(chosen) == 160 and len(set(t for _,t in chosen)) == 160
    sources = [dict(binding[t], part=p) for p,t in chosen]
    files = [assignment_path, binding_path, HERE/'PLAN.md', HERE/'METRICS.md',
             HERE/'collect.py', HERE/'verify.py', ROOT/'pipeline/opponent_hand.py',
             ROOT/'pipeline/tests/test_opponent_hand.py'] + list((ROOT/'pipeline').glob('*.py'))
    frozen = {str(p.relative_to(ROOT)):sha(p) for p in files}
    OUT.mkdir(parents=True)
    write(HERE/'started.json', dict(sources=sources, bindings=frozen,
        no_model_calls=True, no_optimization=True, no_live=True))
    total = defaultdict(Counter)
    by_replay = []
    accounting = Counter()
    with (OUT/'predictions.jsonl').open('w') as predictions, (OUT/'events.jsonl').open('w') as events:
        for ri, source in enumerate(sources):
            path = ROOT/source['path']
            assert sha(path) == source['sha256']
            rec = read(path)
            assert rec['record_native'] and rec['record_full']
            # Projection BEFORE any detector call. No players, decks, commands,
            # opening hand, elixir or command-timed frames cross this boundary.
            public = dict(record_native=True, frames=[
                {k:f[k] for k in ('tick','entities','projectiles','effects','public_objects') if k in f}
                for f in rec['frames']])
            tagged = tag_native_recording(public, {})
            observers = [PublicHandObserver(0), PublicHandObserver(1)]
            for f in tagged['frames']:
                for observer in observers:
                    observer.update(f, source='native')
            ideal = [dict(tick=int(e.get('engine_tick', e['tick'])), side=int(e['side']),
                          card=e['card'], event_id=str(i))
                     for i,e in enumerate(rec['log'])
                     if e.get('accepted') and not e.get('ability') and e.get('card')]
            streams = dict(ideal=ideal, public=[o.observer.plays for o in observers])
            events.write(json.dumps(dict(tag=source['tag'], **streams))+'\n')
            pframes = {int(f['play_index']): f for f in rec.get('play_frames', [])}
            local = defaultdict(Counter)
            first = {}
            for li, e in enumerate(rec['log']):
                accounting['log_entries'] += 1
                truth = hand(e.get('hand_before'))
                if truth is None:
                    accounting['missing_or_non_four_card_hand'] += 1
                    continue
                side = int(e['side'])
                tick = int(e.get('engine_tick', e['tick']))
                pf = pframes.get(int(e['play_index']))
                corroboration = None
                if pf:
                    player = next((p for p in pf.get('players',[]) if int(p['side']) == side), None)
                    corroboration = hand(player.get('hand')) if player else None
                if corroboration is None:
                    accounting['missing_play_frame_hand'] += 1
                elif corroboration != truth:
                    accounting['conflicting_play_frame_hand'] += 1
                    continue
                else:
                    accounting['matching_play_frame_hand'] += 1
                same_tick_prior = any(int(p['event_id']) < li and p['side'] == side and p['tick'] == tick
                                      for p in ideal)
                cohort = 'same_tick_ambiguous' if same_tick_prior else 'primary'
                accounting[cohort] += 1
                outputs = dict(ideal=from_public_plays(ideal, tick, 1-side, complete_events=True),
                               public=observers[1-side].hand_at(tick))
                for arm, output in outputs.items():
                    assert arm != 'public' or not output['certified']
                    key = '/'.join([source['part'], cohort, arm])
                    add(total[key], output, truth)
                    add(local[cohort+'/'+arm], output, truth)
                    if output['full_hand']:
                        first.setdefault(str(side)+'/'+arm, tick)
                predictions.write(json.dumps(dict(tag=source['tag'], part=source['part'],
                    log_index=li, play_index=e['play_index'], side=side, tick=tick,
                    cohort=cohort, truth=truth, corroborated=corroboration is not None,
                    predictions=outputs))+'\n')
            detail = dict(tag=source['tag'], part=source['part'], queries=dict(local),
                first_full_ticks=first, accepted_plays=len(ideal),
                detected_plays=sum(len(o.observer.plays) for o in observers),
                frames=len(rec['frames']), final_tick=int(rec['frames'][-1]['tick']))
            by_replay.append(detail)
            if (ri+1)%10 == 0:
                predictions.flush(); events.flush()
                write(HERE/'progress.json', dict(replays=ri+1, total=160))
                print('REPLAYS',ri+1,flush=True)
    assert all(sha(ROOT/p) == h for p,h in frozen.items()), 'Source drift'
    write(OUT/'by_replay.json', by_replay)
    result = dict(complete=True, replays=160, accounting=dict(accounting), summary=dict(total),
        outputs={p.name:sha(p) for p in OUT.iterdir()}, started_sha256=sha(HERE/'started.json'),
        scope='Recorded native re-drives; conditional public estimates; no model change')
    write(HERE/'collected.json', result)
    print(json.dumps(dict(accounting=accounting, summary=total)))
    print('OPPONENT_HAND_COLLECTED')


if __name__ == '__main__':
    main()
