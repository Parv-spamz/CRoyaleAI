"""Native public Goblin Barrel aim -> own-frame and look-ahead audit, CPU only."""
from collections import Counter
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from pipeline.dataset_gen import card_key
from pipeline.projectile_observation import objects, tokens_from_objects
from pipeline.extrapolate import advance_public_objects
from pipeline.rocket_teaching import sha

HERE = Path(__file__).parent


def main():
    start = time.time()
    manifest = ROOT/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/manifest.json'
    sources = {x['tag']: x for x in json.loads(manifest.read_text())['sources']}
    teaching = json.loads((ROOT/'icebow/data/bench/rocket_teaching_20261004/manifest.json').read_text())
    counts = Counter()
    examples = []
    evidence = []
    for entry in teaching['replay_evidence']:
        src = sources[entry['tag']]
        path = ROOT/src['path']
        assert sha(path) == src['sha256']
        rec = json.loads(path.read_text())
        plays = [p for p in rec['log'] if p.get('accepted') and card_key(p.get('card','')) == 'goblin-barrel']
        if not plays:
            continue
        counts['replays'] += 1
        counts['accepted_barrel_plays'] += len(plays)
        seen = set()
        frames = {f['tick']: f for f in rec['frames']+rec.get('play_frames', [])}
        for tick, frame in sorted(frames.items()):
            shots = [q for q in objects(frame, source='native')['projectiles'] if q[0] == 'goblin-barrel']
            for q in shots:
                _, owner, x, y, tx, ty, _ = q
                counts['projectile_observations'] += 1
                if tx is None or ty is None:
                    counts['unknown_aim'] += 1
                    continue
                prior = [p for p in plays if p['side'] == owner and 0 <= tick-p['tick'] <= 160]
                if not prior:
                    counts['unlinked_aim'] += 1
                    continue
                closest = min(prior, key=lambda p: math.hypot(p['x']-tx, p['y']-ty))
                error = math.hypot(closest['x']-tx, closest['y']-ty)
                counts['target_within_half_tile_of_cast'] += error <= 500
                counts['target_opposite_lane_to_cast'] += (closest['x'] < 9000) != (tx < 9000)
                counts['target_exact_cast'] += error == 0
                seen.add(closest['play_index'])
                observed = dict(projectiles=[q], effects=[])
                projected, status = advance_public_objects(observed, None, 0, 26)
                counts['landed_in_26_tick_lookahead'] += status['landed_in_lookahead']
                for side in (0, 1):
                    token = tokens_from_objects(observed, side, {'goblin-barrel': 1})['projectiles'][0]
                    projected_token = tokens_from_objects(projected, side, {'goblin-barrel': 1})['projectiles'][0]
                    expected_x = tx/18000 if side == 0 else 1-tx/18000
                    expected_y = 1-ty/32000 if side == 0 else ty/32000
                    assert abs(token[4]-expected_x) < 1e-6 and abs(token[5]-expected_y) < 1e-6
                    assert (token[4:6] == projected_token[4:6]).all()
                    counts['orientation_and_lookahead_checks'] += 1
                if len(examples) < 8:
                    examples.append(dict(tag=rec['tag'], tick=tick, raw_projectile=q, cast=closest,
                                         target_error_milli=error))
        counts['barrel_plays_with_linked_flight'] += len(seen)
        evidence.append(src)
    report = dict(counts=dict(counts), examples=examples, source_manifest_sha256=sha(manifest),
                  source_evidence=evidence, seconds=time.time()-start,
                  limitations=['Cast linkage is nearest same-side accepted Barrel within 160 ticks; overlap may be ambiguous.',
                    'This validates native source and shared transforms, not historical live reader aim offsets.',
                    'Correct target encoding does not demonstrate that the learned Log head uses it.'])
    (HERE/'native_audit.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(counts=report['counts'], seconds=report['seconds'])))
    print('BARREL_NATIVE_TARGET_AUDIT_PASS')


if __name__ == '__main__':
    main()
