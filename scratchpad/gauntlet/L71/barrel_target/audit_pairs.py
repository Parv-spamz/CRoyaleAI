"""Separate simultaneous opposite-lane Barrel flights from target corruption."""
from collections import Counter
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from pipeline.dataset_gen import card_key
from pipeline.projectile_observation import objects
from pipeline.rocket_teaching import sha

HERE = Path(__file__).parent
first = json.loads((HERE/'native_audit.json').read_text())
counts = Counter()
examples = []
for source in first['source_evidence']:
    path = ROOT/source['path']
    assert sha(path) == source['sha256']
    rec = json.loads(path.read_text())
    plays = [p for p in rec['log'] if p.get('accepted') and card_key(p.get('card', '')) == 'goblin-barrel']
    frames = {f['tick']: f for f in rec['frames']+rec.get('play_frames', [])}
    for tick, frame in sorted(frames.items()):
        shots = [q for q in objects(frame, source='native')['projectiles'] if q[0] == 'goblin-barrel']
        for q in shots:
            _, owner, x, y, tx, ty, _ = q
            counts['projectile_observations'] += 1
            if tx is None or ty is None:
                counts['unknown'] += 1
                continue
            prior = [p for p in plays if p['side'] == owner and 0 <= tick-p['tick'] <= 160]
            if not prior:
                counts['unlinked'] += 1
                continue
            p = min(prior, key=lambda p: math.hypot(p['x']-tx, p['y']-ty))
            distance = math.hypot(p['x']-tx, p['y']-ty)
            if distance <= 500:
                counts['near_cast_target'] += 1
                continue
            opposite = (p['x'] < 9000) != (tx < 9000)
            reflected = math.hypot(18000-p['x']-tx, p['y']-ty) <= 500
            sibling = any(s != q and s[1] == owner and s[4] is not None and s[5] is not None
                          and math.hypot(s[4]-p['x'], s[5]-p['y']) <= 500 for s in shots)
            counts['opposite_cast_lane'] += opposite
            counts['reflected_target_with_simultaneous_cast_target'] += reflected and sibling
            counts['unexplained_far_target'] += not (reflected and sibling)
            if len(examples) < 5:
                examples.append(dict(tag=rec['tag'], tick=tick, cast=p, shots=shots,
                                     reflected=reflected, simultaneous_cast_target=sibling))
assert counts['projectile_observations'] == first['counts']['projectile_observations']
report = dict(counts=dict(counts), examples=examples, initial_audit_sha256=sha(HERE/'native_audit.json'),
              interpretation='A second reflected projectile is observed, not inferred from a wrong-lane policy action.',
              limitations=['This does not identify which observed flight deserves the best response.',
                'Shared parent card IDs do not identify a decoy; no secret true-target flag is used.',
                'Reader offsets remain unverified on saved live Goblin Barrel flights.'])
(HERE/'paired_flights.json').write_text(json.dumps(report, indent=2))
print(json.dumps(dict(counts=report['counts'])))
print('BARREL_PAIRED_FLIGHTS_AUDIT_PASS')
