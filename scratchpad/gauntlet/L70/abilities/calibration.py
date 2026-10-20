"""Offline intercept-only candidates. Does not replace the policy or launch R1e.

Fit deployment pressed share on non-test replays; evaluate fixed offsets on the
existing held-out replays. Phase-1 targets include those replays, so comparison
to phase 1 is descriptive, not a fully independent generalization estimate.
Uses phase2_fit's seeded first/second press simulation and cadence convention.
"""
import os
for _name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_name] = '1'

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from ability_policy import sigmoid, tree_values

HERE = Path(__file__).resolve().parent


def model_scores(model, x):
    z = (x - np.asarray(model['mean'])) / np.asarray(model['scale'])
    score = np.full(len(x), model['intercept'], dtype=float)
    if model['type'] == 'logistic':
        score += z @ np.asarray(model['coefficients'])
    elif model['type'] == 'gradient_boosted_trees':
        for tree in model['trees']:
            score += model['learning_rate'] * tree_values(tree, z)
    else:
        raise ValueError('Intercept calibration requires logistic or GBT model')
    return score


def prepare(ability, model, data, deployments, replays, replay_ids):
    selected = np.flatnonzero(np.isin(data['replay'], list(replay_ids)))
    selected = selected[np.lexsort((data['tick'][selected], data['deployment'][selected]))]
    ids, starts = np.unique(data['deployment'][selected], return_index=True)
    rows, groups, uniforms, intervals, kept = [], [], [], [], []
    for di, ii in zip(ids, np.split(selected, starts[1:])):
        dep = deployments[int(di)]
        if dep['censored']:
            continue
        if len(np.unique(data['tick'][ii])) != len(ii):
            raise ValueError('Duplicate frame tick within deployment')
        if not np.all(data['replay'][ii] == dep['replay']):
            raise ValueError('Deployment/replay identity mismatch')
        seed = int.from_bytes(hashlib.sha256(
            f'phase2:{ability}:{replays[dep["replay"]]}:{dep["side"]}:{dep["play_index"]}'.encode()
        ).digest()[:8], 'little')
        rows.extend(ii)
        groups.extend([len(kept)] * len(ii))
        uniforms.extend(np.random.default_rng(seed).random(len(ii)))
        intervals.extend(np.r_[np.clip(np.diff(data['tick'][ii]) / 20., .05, 1.), 1.])
        kept.append(dep)
    if not kept:
        raise ValueError('No uncensored visible deployments')
    rows = np.asarray(rows, dtype=int)
    return dict(ability=ability, scores=model_scores(model, data['X'][rows].astype(float)),
                groups=np.asarray(groups), ticks=data['tick'][rows], u=np.asarray(uniforms),
                dt=np.asarray(intervals), start=np.array([d['tick'] for d in kept]),
                replay=np.array([d['replay'] for d in kept]),
                observed=[[(t-d['tick'])/20. for t in d['context_press_ticks']] for d in kept])


def simulate(seq, offset):
    """One use except Boss Bandit's two charges, with existing 60-tick proxy cooldown."""
    n = len(seq['start'])
    p = sigmoid(seq['scores'] + offset)
    p = -np.expm1(seq['dt'] * np.log1p(-np.minimum(p, np.nextafter(1., 0.))))
    hit = seq['u'] < p
    first = np.full(n, np.inf)
    np.minimum.at(first, seq['groups'][hit], seq['ticks'][hit])
    second = np.full(n, np.inf)
    if seq['ability'] == 'boss-bandit':
        hit &= seq['ticks'] >= first[seq['groups']] + 60
        np.minimum.at(second, seq['groups'][hit], seq['ticks'][hit])
    result = (np.column_stack([first, second]) - seq['start'][:, None]) / 20.
    result[~np.isfinite(result)] = np.nan
    return result


def fit_offset(seq, target):
    if not 0 < target < 1:
        raise ValueError('Target share must be strictly between zero and one')
    lo, hi = -40., 40.
    share = lambda x: float(np.isfinite(simulate(seq, x)[:, 0]).mean())
    if not share(lo) <= target <= share(hi):
        raise ValueError('Target outside reachable intercept range')
    for _ in range(40):
        mid = (lo + hi) / 2
        if share(mid) < target:
            lo = mid
        else:
            hi = mid
    return min((lo, hi), key=lambda x: (abs(share(x)-target), abs(x)))


def median(values):
    values = np.asarray(values)
    values = values[np.isfinite(values)]
    return float(np.median(values)) if len(values) else None


def summary(delays):
    return dict(deployments=len(delays), pressed=int(np.isfinite(delays[:, 0]).sum()),
                share=float(np.isfinite(delays[:, 0]).mean()),
                median_first_s=median(delays[:, 0]), median_all_s=median(delays.ravel()),
                repeat_share=float(np.isfinite(delays[:, 1]).mean()))


def paired_intervals(before, after, replay, repeats=1000):
    """Resample whole replay clusters, preserving both sides and paired candidates."""
    clusters = [np.flatnonzero(replay == r) for r in np.unique(replay)]
    rng = np.random.default_rng(20261003)
    samples = {'share_delta_pp': [], 'first_median_delta_s': [], 'all_median_delta_s': []}
    for _ in range(repeats):
        ix = np.concatenate([clusters[i] for i in rng.integers(len(clusters), size=len(clusters))])
        b, a = summary(before[ix]), summary(after[ix])
        samples['share_delta_pp'].append(100*(a['share']-b['share']))
        for name, key in [('first_median_delta_s', 'median_first_s'), ('all_median_delta_s', 'median_all_s')]:
            if a[key] is not None and b[key] is not None:
                samples[name].append(a[key]-b[key])
    b, a = summary(before), summary(after)
    points = {'share_delta_pp': 100*(a['share']-b['share']),
              'first_median_delta_s': None if a['median_first_s'] is None or b['median_first_s'] is None else a['median_first_s']-b['median_first_s'],
              'all_median_delta_s': None if a['median_all_s'] is None or b['median_all_s'] is None else a['median_all_s']-b['median_all_s']}
    return {key: dict(delta=points[key], ci95=np.quantile(vals, [.025, .975]).tolist() if vals else None,
                     valid_bootstraps=len(vals)) for key, vals in samples.items()}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=HERE/'calibration_report.json')
    args = parser.parse_args()
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.windll.kernel32
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x4000):
            raise OSError('Could not set below-normal priority')
    files = ['abilities.json', 'ability_models.json', 'phase2_inventory.json', 'phase2_deployments.json',
             'ability_policy.py', 'calibration.py']
    source_hashes = {f: sha(HERE/f) for f in files}
    bundle = json.loads((HERE/'ability_models.json').read_text())
    phase1 = json.loads((HERE/'abilities.json').read_text())['abilities']
    inv = json.loads((HERE/'phase2_inventory.json').read_text())
    deps = json.loads((HERE/'phase2_deployments.json').read_text())
    test = set(inv['test_replay_ids'])
    fit = set(range(len(inv['replays']))) - test
    assert fit and test and not fit & test
    report = dict(status='OFFLINE_CANDIDATES_ONLY', fit_replays=len(fit), test_replays=len(test),
                  split_overlap=0, bootstrap_repeats=1000, source_hashes=source_hashes,
                  limitations=['Phase-1 target corpus overlaps heldout tags; target comparison is descriptive.',
                               'Boards omit ability effects. Phase-1 denominator is inferred deployments, not verified eligible lifetimes.',
                               'Delay is evaluated, not optimized. One intercept cannot generally fit two independent statistics.',
                               'Fixed seeded stochastic simulation; CIs resample replays, not RNG or phase-1 target uncertainty.',
                               'Cadence and Boss Bandit 60-tick cooldown are phase-2 proxies, not engine validation.'],
                  abilities={})
    for ability, model in sorted(bundle['models'].items()):
        file = HERE/f'phase2_data_{ability}.npz'
        source_hashes[file.name] = sha(file)
        with np.load(file) as z:
            data = {key: z[key] for key in z.files}
        if not np.array_equal(data['split'] == 2, np.isin(data['replay'], list(test))):
            raise ValueError('Holdout split mismatch')
        train_seq = prepare(ability, model, data, deps[ability], inv['replays'], fit)
        test_seq = prepare(ability, model, data, deps[ability], inv['replays'], test)
        dist = phase1[ability]['deployment_press_distribution']
        target = 1 - dist['counts']['0']/dist['n']
        offset = fit_offset(train_seq, target)
        before, after = simulate(test_seq, 0), simulate(test_seq, offset)
        result = dict(offset=offset, candidate_intercept=model['intercept']+offset,
                      phase1=dict(share=target, median_all_s=phase1[ability]['delay_seconds']['p50'],
                                  median_first_s=phase1[ability]['first_press_delay_seconds']['p50']),
                      fit=summary(simulate(train_seq, offset)), before=summary(before), after=summary(after),
                      paired=paired_intervals(before, after, test_seq['replay']))
        result['phase1_residual'] = dict(share_pp=100*(result['after']['share']-target),
            median_all_s=None if result['after']['median_all_s'] is None else result['after']['median_all_s']-result['phase1']['median_all_s'])
        report['abilities'][ability] = result
        print(ability, json.dumps(result['phase1_residual']), flush=True)
    for file, expected in source_hashes.items():
        if sha(HERE/file) != expected:
            raise RuntimeError('Source changed during calibration: '+file)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf8')
    print('CALIBRATION_REPORT_VERIFIED', len(report['abilities']), flush=True)


if __name__ == '__main__':
    main()
