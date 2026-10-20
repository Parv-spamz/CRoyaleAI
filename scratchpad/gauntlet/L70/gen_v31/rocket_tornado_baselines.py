"""Paired policy cast-order priors; flight/pull/hit synergy remains unmeasured."""
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import behavior_baselines as B
from xbow_baselines import accepted_tick, named
from audit_runtime import lower_own_priority

ROOT = B.ROOT
SOURCES = dict(B.SOURCES, **{f'r1t_u{u}':f'scratchpad/gauntlet/L70/rl/r1t_v3_accept/train_rseries_r1t_v3_u{u}.jsonl'
                           for u in ('0080', '0155')})
NAMES = ['accepted_plays_per_min', 'rocket_share_pct', 'rocket_then_tornado_prior_pct_of_rockets',
         'tornado_then_rocket_prior_pct_of_rockets']


def vector(row, grid):
    if grid not in ('lattice', 'floor'):
        raise ValueError('Unsupported grid')
    plays = [(i, p) for i, p in enumerate(row['plays']) if p.get('accepted')]
    rockets = [(i, p) for i, p in plays if p['card'] == 'rocket']
    tornados = [(i, p) for i, p in plays if p['card'] == 'tornado']
    counts = [0, 0]
    for ri, rocket in rockets:
        found = set()
        for ni, nado in tornados:
            gap = abs(accepted_tick(nado)-accepted_tick(rocket))*.05
            # Same grid offset on both casts cancels in the normalized distance.
            rc, nc = int(rocket['cell']), int(nado['cell'])
            if not 0 <= rc < 2304 or not 0 <= nc < 2304:
                raise ValueError('Invalid spell cell')
            distance = math.hypot((rc % 36-nc % 36)/36, (rc//36-nc//36)/64)
            if gap <= 2.5 and distance <= .11:
                found.add(0 if (accepted_tick(rocket), ri) < (accepted_tick(nado), ni) else 1)
        for order in found:
            counts[order] += 1
    return np.array([len(plays), row['end_tick']/1200, len(rockets), *counts], float)


def metrics(v):
    a = v.sum(axis=-2)
    def div(n, d):
        return np.divide(n, d, out=np.full_like(np.asarray(n, float), np.nan), where=d != 0)
    return np.stack([div(a[..., 0], a[..., 1]), div(100*a[..., 2], a[..., 0]),
                     div(100*a[..., 3], a[..., 2]), div(100*a[..., 4], a[..., 2])], axis=-1)


def labeled(point, samples):
    out = {}
    for i, name in enumerate(NAMES):
        finite = samples[:, i][np.isfinite(samples[:, i])]
        out[name] = dict(value=float(point[i]) if np.isfinite(point[i]) else None,
                         ci95=np.quantile(finite, [.025, .975]).tolist() if len(finite) else None)
    return out


def report():
    lower_own_priority()
    sys.path.insert(0, str(ROOT/'.foreman/codex_autopilot'))
    from acceptance_report import validate_pair
    tables = {name:B.load(ROOT/path) for name, path in SOURCES.items()}
    keys = sorted(tables['u0155']); arrays = {}; samples = {}; models = {}; inputs = {}
    ix = np.random.default_rng(20261003).integers(len(keys), size=(2000, len(keys)))
    for name, table in tables.items():
        validate_pair(tables['u0155'], table)
        path = ROOT/SOURCES[name]; meta_path = path.with_suffix('.run.json')
        meta = json.loads(meta_path.read_text()); grid = meta['cfg']['grid']
        assert grid == meta['model']['grid']
        a = np.stack([vector(table[k], grid) for k in keys]); arrays[name] = a; samples[name] = metrics(a[ix])
        elixir = [p.get('elixir_exact', p.get('elixir')) for r in table.values() for p in r['plays']
                  if p.get('accepted') and p['card'] == 'rocket']
        models[name] = dict(matches=len(keys), accepted_plays=int(a[:, 0].sum()), rockets=int(a[:, 2].sum()),
            rocket_then_tornado_prior=int(a[:, 3].sum()), tornado_then_rocket_prior=int(a[:, 4].sum()),
            rocket_elixir_median=float(np.median(elixir)) if elixir and all(x is not None for x in elixir) else None,
            metrics=labeled(metrics(a), samples[name]),
            unmeasured={k:dict(value=None, reason=v) for k, v in B.MISSING.items()})
        for p in (path, meta_path):
            inputs[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    paired = {name:labeled(metrics(a)-metrics(arrays['u0155']), samples[name]-samples['u0155'])
              for name, a in arrays.items() if name != 'u0155'}
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() != h for p, h in inputs.items()):
        raise ValueError('Source changed')
    return dict(status='MEASURED_PAIRED_CAST_PRIORS_NOT_CONFIRMED_SYNERGY', models=models, paired_vs_live=paired,
        source_hashes=inputs, bootstrap=dict(seed=20261003, repeats=2000, unit='paired replay key'),
        limitations=['Both directions use the historical2.5s/0.11 normalized-distance CAST prior.',
            'No ghost flight/landing/pull telemetry: these are order/proximity proxies, not confirmed combos.',
            'Both directions use accepted Rockets as denominator; one Rocket may match both directions.',
            'Conditional Rocket elixir medians are descriptive, not a paired treatment effect.',
            'Zero-event bootstrap intervals are degenerate; [0,0] is not a population upper confidence bound.',
            'All11 full behaviour gaps remain explicit; no policy or acceptance rule is changed.'])


if __name__ == '__main__':
    r = report(); path = Path(__file__).with_name('rocket_tornado_baselines_2140.json')
    with path.open('x') as stream:
        json.dump(r, stream, indent=2)
    print(json.dumps({k:{q:v[q] for q in ('rockets', 'rocket_then_tornado_prior', 'tornado_then_rocket_prior', 'rocket_elixir_median')}
                      for k, v in r['models'].items()}, indent=2))
