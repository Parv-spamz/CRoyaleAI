"""Read-only fresh expert-reference inventory. No policy calls or optimization."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pipeline.dataset_gen import card_key
from pipeline.public_outcomes import label_recording

FIELDS = ('tag', 'side', 'tick', 'card', 'x', 'y', 'landing_tick',
          'landing_source', 'landing_point', 'hp_window_known',
          'hp_confirmation_within_two_ticks', 'tower_hits',
          'rocket_then_tornado', 'tornado_then_rocket')


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(p, obj):
    p.write_text(json.dumps(obj, indent=2) + '\n')


def summarize(rows):
    flags = {
        'all_casts': lambda r: True,
        'landing_unobserved': lambda r: r['landing_tick'] is None,
        'hp_window_known': lambda r: r['hp_window_known'] is True,
        'hp_confirmation_within_two_ticks': lambda r: r['hp_confirmation_within_two_ticks'] is True,
        'princess_geometric_reference': lambda r: any(h['tower'][1] == 'princess' for h in r['tower_hits']),
        'princess_observed_hp_drop': lambda r: any(h['tower'][1] == 'princess' and h['hp_confirmed'] for h in r['tower_hits']),
        'princess_observed_finish': lambda r: any(h['tower'][1] == 'princess' and h['finish'] for h in r['tower_hits']),
        'princess_repeat_reference': lambda r: any(h['tower'][1] == 'princess' and h['prior_rockets'] > 0 for h in r['tower_hits']),
        'rocket_then_tornado': lambda r: r['rocket_then_tornado'] is True,
        'tornado_then_rocket': lambda r: r['tornado_then_rocket'] is True,
    }
    return dict(metrics={k: dict(casts=sum(fn(r) for r in rows),
                    replay_clusters=len({r['tag'] for r in rows if fn(r)})) for k, fn in flags.items()},
                landing_sources=dict(sorted(Counter(r['landing_source'] for r in rows).items())))


def main():
    assert not (HERE / 'started.json').exists(), 'Fresh invocation required'
    inventory_path = HERE.parent / 'void_capacity/inventory.json'
    inventory = json.loads(inventory_path.read_bytes())
    assert inventory['complete'] and not inventory['N2_complete'] and inventory['model_predictions'] == 0
    sources = {str(inventory_path.relative_to(ROOT)): sha(inventory_path)}
    for p, expected in inventory['sources'].items():
        assert sha(ROOT / p) == expected, p
    for rel in ('pipeline/public_outcomes.py', 'pipeline/public_geometry.py',
                'pipeline/projectile_observation.py', 'pipeline/obs_contract.py',
                'pipeline/dataset_gen.py', 'pipeline/opp_elixir_count.py', 'pipeline/vocab.py',
                'research/ext/Royale/RoyaleSim/data/derived/cards.json',
                'research/ext/cr-native-sandbox/native_core/data/live_card_catalog.json'):
        sources[rel] = sha(ROOT / rel)
    for name in ('run.py', 'verify.py', 'PLAN.md'):
        sources[str((HERE / name).relative_to(ROOT))] = sha(HERE / name)
    # Bind the inventory's completed receipt; no validation chain is rerun.
    receipt_path = ROOT / 'scratchpad/gauntlet/L71/integration/checks/l72-void-capacity-independent.json'
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt['exit_code'] == 0 and receipt['matched']
    assert hashlib.sha256(receipt_path.with_suffix('.out').read_text().encode()).hexdigest() == receipt['output_sha256']
    sources[str(receipt_path.relative_to(ROOT))] = sha(receipt_path)
    exact = inventory['exact_sides']
    qualified = {r['tag']: r for r in inventory['qualified']}
    members = [qualified[t] for t in sorted({r['tag'] for r in exact})]
    assert all(m['split'] == 'confirmation' for m in members)
    assert len(members) == inventory['exact_icebow_qualified_replays']['confirmation']
    assert len({m['signature'] for m in members}) == len(members)
    for m in members:
        assert sha(ROOT / m['path']) == m['sha256'], m['tag']
    started = dict(sources=sources, members=members, exact_sides=exact,
                   policy_predictions=0, optimizer_updates=0, trainable=False)
    write(HERE / 'started.json', started)
    output = []
    for i, m in enumerate(members, 1):
        rec = json.loads((ROOT / m['path']).read_bytes())
        sides = [s for s in exact if s['tag'] == m['tag']]
        accepted = [p for p in rec['log'] if p.get('accepted') is True and
                    not p.get('skipped') and not p.get('ability') and p.get('card')]
        for s in sides:
            count = sum(int(p['side']) == s['side'] and card_key(p['card']) == 'rocket' for p in accepted)
            assert count == s['own_commands'].get('rocket', 0), m['tag']
        # Only reference spells enter the existing labeler; no X-Bow labels.
        view = dict(rec, log=[p for p in accepted if card_key(p['card']) in ('rocket', 'tornado')])
        labels = label_recording(view, xbow_rule=None, reconstruct_rocket_landing=True)
        own = {s['side'] for s in sides}
        output.extend({k: r.get(k) for k in FIELDS} for r in labels['rockets'] if r['side'] in own)
        write(HERE / 'progress.json', dict(completed=i, total=len(members), casts=len(output)))
        print(f'{i}/{len(members)} {m["tag"]} casts={len(output)}', flush=True)
    assert len(output) == sum(s['own_commands'].get('rocket', 0) for s in exact)
    assert len({(r['tag'], r['side'], r['tick']) for r in output}) == len(output)
    for p, h in sources.items():
        assert sha(ROOT / p) == h, p
    write(HERE / 'references.json', output)
    report = dict(complete=True, N2_complete=False, trainable=False,
                  policy_predictions=0, optimizer_updates=0,
                  selected_replays=len(members), selected_sides=len(exact),
                  started_sha256=sha(HERE / 'started.json'),
                  references_sha256=sha(HERE / 'references.json'), **summarize(output))
    write(HERE / 'report.json', report)
    print(json.dumps(report))
    print('ROCKET_REFERENCE_CAPACITY_COMPLETE')


if __name__ == '__main__':
    main()
