"""Paired replay-cluster comparison of the two declared cast-window proxies."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
source = HERE / 'native_rocket_tornado_2140/rockets.jsonl'
rows = [json.loads(line) for line in source.read_text().splitlines()]
report = json.loads((source.parent / 'report.json').read_text())
out = {'status': 'MEASURED_PAIRED_CAST_PROXY_NOT_SYNERGY',
       'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
       'seed': 20261003, 'repeats': 2000, 'unit': 'replay tag', 'groups': {}}
for group, selected in [('all', rows), ('non_tower', [r for r in rows if not r['tower_candidate']])]:
    clusters = defaultdict(lambda: [0, 0, 0])
    for r in selected:
        v = clusters[r['tag']]
        v[0] += 1
        for index, order in enumerate(('rocket_then_tornado', 'tornado_then_rocket'), 1):
            v[index] += any(c['order'] == order and c['cast_window_prior'] for c in r['combos'])
    a = np.asarray([clusters[k] for k in sorted(clusters)], dtype=np.int64)
    totals = a.sum(axis=0)
    for i, order in enumerate(('rocket_then_tornado', 'tornado_then_rocket'), 1):
        assert totals[i] == report['groups'][group]['orders'][order]['cast_window_prior_rate']['count']
    rng = np.random.default_rng(out['seed'])
    samples = []
    for _ in range(out['repeats']):
        v = a[rng.integers(0, len(a), len(a))].sum(axis=0)
        samples.append(100 * (v[1] - v[2]) / v[0])
    out['groups'][group] = dict(rockets=int(totals[0]), replay_clusters=len(a),
        rocket_then_tornado=int(totals[1]), tornado_then_rocket=int(totals[2]),
        difference_pp=float(100 * (totals[1] - totals[2]) / totals[0]),
        ci95_pp=np.quantile(samples, [.025, .975]).tolist())
(HERE / 'combo_order_comparison_2140.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
