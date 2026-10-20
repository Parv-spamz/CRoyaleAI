"""Paired saved-telemetry X-Bow geometry; no tower-state/defensive intent claims."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import behavior_baselines as B

ROOT = B.ROOT


def accepted_tick(play):
    return play['land_tick'] if play.get('land_tick') is not None else play['tick']


def vectors(row, grid):
    if grid not in ('floor', 'lattice'):
        raise ValueError('Missing supported placement grid')
    plays = [p for p in row['plays'] if p.get('accepted')]
    bows = [p for p in plays if p['card'].replace('-', '').replace('_', '') == 'xbow']
    rockets = [p for p in plays if p['card'] == 'rocket']
    ys = [(int(p['cell'])//36 + (.5 if grid == 'floor' else 0))/64 for p in bows]
    if any(not 0 <= int(p['cell']) < 2304 for p in bows):
        raise ValueError('Invalid X-Bow cell')
    late = [(p, y) for p, y in zip(bows, ys) if accepted_tick(p) >= 2400]
    follow = sum(any(0 < accepted_tick(q)-accepted_tick(p) <= 200 for q in rockets) for p in bows)
    # Counts first, then pooled rates. Last two ratios are deliberately proxies.
    return np.array([len(plays), row['end_tick']/1200, len(bows), len(late),
                     sum(y > .58 for _, y in late), follow], float), ys


def metrics(v):
    a = v.sum(axis=-2)
    def divide(n, d):
        return np.divide(n, d, out=np.full_like(np.asarray(n, dtype=float), np.nan), where=d != 0)
    return np.stack([divide(a[..., 0], a[..., 1]), divide(100*a[..., 2], a[..., 0]),
                     divide(100*a[..., 4], a[..., 3]), divide(100*a[..., 5], a[..., 2])], axis=-1)


NAMES = ['accepted_plays_per_min', 'xbow_share_pct', 'late_legacy_y_gt058_pct', 'xbow_then_any_rocket_10s_pct']


def named(point, samples):
    result = {}
    for i, name in enumerate(NAMES):
        valid = samples[:, i][np.isfinite(samples[:, i])]
        result[name] = dict(value=float(point[i]) if np.isfinite(point[i]) else None,
                           ci95=np.quantile(valid, [.025, .975]).tolist() if len(valid) else None,
                           valid_bootstrap_samples=len(valid))
    return result


def report():
    from audit_runtime import lower_own_priority
    lower_own_priority()
    sys.path.insert(0, str(ROOT/'.foreman/codex_autopilot'))
    from acceptance_report import validate_pair
    tables = {name: B.load(ROOT/path) for name, path in B.SOURCES.items()}
    keys = sorted(tables['gen_v1'])
    for table in tables.values():
        validate_pair(tables['gen_v1'], table)
    inputs, models, arrays, samples = {}, {}, {}, {}
    ix = np.random.default_rng(20261003).integers(len(keys), size=(2000, len(keys)))
    for name, table in tables.items():
        path = ROOT/B.SOURCES[name]
        meta_path = path.with_suffix('.run.json')
        meta = json.loads(meta_path.read_text())
        grid = meta['cfg']['grid']
        if grid != meta['model']['grid']:
            raise ValueError('Conflicting grid provenance')
        rows = [vectors(table[k], grid) for k in keys]
        a = np.stack([v for v, _ in rows]); arrays[name] = a
        samples[name] = metrics(a[ix])
        models[name] = dict(matches=len(keys), grid=grid,
            accepted_plays=int(a[:, 0].sum()), accepted_xbows=int(a[:, 2].sum()),
            late_xbows=int(a[:, 3].sum()), xbow_followed_by_any_rocket=int(a[:, 5].sum()),
            y_rows=dict(sorted(Counter(str(y) for _, ys in rows for y in ys).items())),
            metrics=named(metrics(a), samples[name]),
            required_but_unmeasured={k:dict(value=None, reason=v) for k, v in B.MISSING.items()})
        for p in (path, meta_path):
            inputs[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    paired = {}
    for baseline in ('gen_v1', 'u0155'):
        paired[baseline] = {candidate: named(metrics(a)-metrics(arrays[baseline]), samples[candidate]-samples[baseline])
                            for candidate, a in arrays.items() if candidate != baseline}
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() != h for p, h in inputs.items()):
        raise ValueError('Baseline input changed')
    return dict(status='MEASURED_PAIRED_GEOMETRY_PROXIES_NOT_FULL_BEHAVIOUR', models=models,
        paired_differences=paired, input_hashes=inputs,
        bootstrap=dict(seed=20261003, replicates=2000, unit='paired replay key'),
        limitations=[
            'Same 299 pinned ghost matches, historical runs; not live/reactive or causal evidence.',
            'Grid comes from each saved run metadata. Accepted cast time uses land_tick when present.',
            'y>0.58 is the inherited geometric bucket, not validated defensive intent.',
            'Any-Rocket sequences do not establish tower targeting or defensive X-Bow/Rocket cycling.',
            'All eight required behaviour gaps remain null; these spatial proxies do not close acceptance.',
            'Paired differences in percentages use percentage points; play-rate differences use plays/min.'])


if __name__ == '__main__':
    r = report()
    path = Path(__file__).with_name('xbow_baselines_2020.json')
    with path.open('x') as stream:
        json.dump(r, stream, indent=2)
    print(json.dumps({k:dict(xbows=v['accepted_xbows'], late=v['late_xbows'], y_rows=v['y_rows'], metrics=v['metrics'])
                      for k, v in r['models'].items()}, indent=2))
