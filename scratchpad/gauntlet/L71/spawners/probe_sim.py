"""Controlled accepted deployment and repeated-wave identity probe; CPU only."""
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from pipeline.royale_env import RoyaleSelfPlayEnv
from pipeline import vocab
from body_identity import resolve

results = {}
for name in ('Witch', 'DarkWitch', 'FirespiritHut'):
    env = RoyaleSelfPlayEnv(feature_version=4, tail_cap=800)
    try:
        deck = [name, 'Knight', 'Skeletons', 'Log', 'Rocket', 'Tesla', 'IceWizard', 'Tornado']
        obs = env.reset(deck, deck, seed=1)
        act = env.act(1, 0, 3500, 28500)
        assert act['accepted'], (name, act)
        seen = set()
        bodies = []
        for tick in range(100, 701, 10):
            obs = env.advance_to(tick)
            for entity in obs['entities']:
                if entity['side'] != 1 or entity['card_id'] < 0 or entity['hp'] <= 0:
                    continue
                eid = entity['entity_id']
                if eid in seen:
                    continue
                seen.add(eid)
                old = vocab.engine_unit_id(entity['name'], entity['max_hp'])
                new = resolve(entity['name'], entity['max_hp'])
                bodies.append(dict(tick=tick, name=entity['name'], max_hp=entity['max_hp'],
                    legacy=None if old is None else vocab.UNIT_VOCAB[old],
                    corrected=None if new.cls is None else vocab.UNIT_VOCAB[new.cls],
                    reason=new.reason))
        result = dict(seed=1, accepted=act, bodies=bodies,
                      counts=dict(Counter(b['corrected'] for b in bodies)))
        expected = {'Witch': 'skeletons', 'DarkWitch': 'bats', 'FirespiritHut': 'fire_spirit'}[name]
        assert result['counts'].get(expected, 0) >= 4, result
        assert len(set(b['tick'] for b in bodies if b['corrected'] == expected)) >= 2
        results[name] = result
    finally:
        env.close()
out = Path(__file__).parent/'sim_identity_probe_v2.json'
out.write_text(json.dumps(results, indent=2))
print(json.dumps({k: v['counts'] for k, v in results.items()}))
print('SPAWNER_SIM_WAVES_PASS')
