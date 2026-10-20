"""Five authorized proxy targets, public features, replay-disjoint evaluation.

Fixed maximum weight 2 is the owner's overnight setting, not a tuned result.
Defensive-X-Bow tactical labels are explicitly absent. Labels may use future
outcomes; features are only the already-sanitized pre-action public dataset.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import torch
import torch.nn.functional as F

TARGETS = ['tower_rocket', 'xbow_lane', 'defensive_rocket', 'rocket_then_tornado', 'tornado_then_rocket']
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()


def public_features(arrays, meta):
    # Columns 7:52 were deck-slot one-hots; the builder zeros them. Do not use
    # row labels, replay IDs, future crowns, target coordinates or private data.
    sc = arrays['sc']
    if not np.all(sc[:, 6] == 1) or not np.isfinite(sc).all():
        raise ValueError('Public counter contract missing')
    card_ids = {n: i for i, n in enumerate(meta['card_vocab'])}
    own_hand = np.stack([(arrays['hand_card'] == card_ids.get(k, -1)).any(1)
                         for k in ('rocket', 'x-bow', 'tornado', 'the-log')], 1)
    return np.concatenate([sc[:, :7], sc[:, 52:], own_hand], 1).astype(np.float32)


def labels(arrays, tags, meta, rocket_rows, xbow_rows):
    n = len(arrays['y_gate'])
    y = np.zeros((n, 5), np.float32)
    known = np.ones_like(y)
    ids = {name: i for i, name in enumerate(meta['card_vocab'])}
    candidates = np.flatnonzero((arrays['y_gate'] == 1) &
                               np.isin(arrays['y_card'], [ids.get('rocket'), ids.get('x-bow')]))
    index = {}
    for i in candidates:
        key = (str(tags[arrays['rep'][i]]), int(arrays['side'][i]), int(arrays['tick'][i]), int(arrays['y_card'][i]))
        if key in index: raise ValueError('Ambiguous same-tick event join')
        index[key] = int(i)
    matched = Counter()
    missed = Counter()
    mapped = set()
    for kind, rows in [('rocket', rocket_rows), ('x-bow', xbow_rows)]:
        for row in rows:
            key = (row['tag'], row['side'], row['tick'], ids[kind])
            i = index.get(key)
            if i is None:
                missed[kind] += 1
                continue
            if i in mapped: raise ValueError('Duplicate source label')
            mapped.add(i); matched[kind] += 1
            if kind == 'rocket':
                for j, field in [(0, 'proxy_tower_rocket'), (2, 'proxy_defensive_rocket'),
                                 (3, 'proxy_rocket_then_tornado'), (4, 'proxy_tornado_then_rocket')]:
                    value = row[field]
                    if value is None: known[i, j] = 0
                    else: y[i, j] = bool(value)
            else:
                # All observed left/right placements with known tower geometry
                # are retained, INCLUDING dead lanes. No invented tactical rule.
                known[i, 1] = row['lane'] in ('left', 'right') and row['lane_state'] in ('alive', 'dead')
                y[i, 1] = known[i, 1]
    uncovered = set(index.values()) - mapped
    if uncovered:
        raise ValueError(f'{len(uncovered)} dataset Rocket/X-Bow rows lack audited labels')
    return y, known, dict(matched=dict(matched), source_events_without_dataset_row=dict(missed),
                         positives=y.sum(0).astype(int).tolist(), unknown=(1-known).sum(0).astype(int).tolist())


def evaluate(p, y, known, reps, base, draws=1000):
    rng = np.random.default_rng(20261004)
    unique, inv = np.unique(reps, return_inverse=True)
    out = {}
    for j, name in enumerate(TARGETS):
        eligible = known[:, j] > 0
        count = np.bincount(inv, weights=eligible, minlength=len(unique))
        diff = ((p[:, j]-y[:, j])**2 - (base[j]-y[:, j])**2)*eligible
        sums = np.bincount(inv, weights=diff, minlength=len(unique))
        boot = []
        for _ in range(draws):
            ix = rng.integers(0, len(unique), len(unique))
            boot.append(sums[ix].sum()/max(1, count[ix].sum()))
        out[name] = dict(n=int(eligible.sum()), positives=int(y[eligible, j].sum()),
                         prevalence=float(y[eligible, j].mean()), mean_score=float(p[eligible, j].mean()),
                         brier=float(np.mean((p[eligible, j]-y[eligible, j])**2)),
                         brier_delta_vs_fit_prevalence=float(diff.sum()/eligible.sum()),
                         paired_replay_ci95=np.quantile(boot, [.025, .975]).tolist())
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--data', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(exist_ok=False)
    torch.set_num_threads(1); torch.manual_seed(20261004)
    z = np.load(a.data, allow_pickle=False); meta = json.loads(str(z['meta']))
    if meta.get('feature_version') != 4 or meta.get('opponent_elixir') != 'public_counter_strictly_prior_sightings':
        raise ValueError('Requires verified public-input v4 dataset')
    tags = z['tags']; names = ['sc', 'hand_card', 'rep', 'split', 'tick', 'side', 'y_gate', 'y_card']
    arrays = {k: z[k] for k in names}
    x = public_features(arrays, meta)
    rocket = HERE/'proxy_labels_2300/rocket_proxy_labels.jsonl'
    xbow = HERE/'native_xbows_2020/xbows.jsonl'
    y, known, coverage = labels(arrays, tags, meta,
                               [json.loads(s) for s in rocket.open()], [json.loads(s) for s in xbow.open()])
    # Reserve classifier evaluation within policy TRAIN only. Policy VAL is
    # untouched by fit/tuning, and retains its original independent evaluation.
    buckets = np.asarray([int(hashlib.sha256(('context-v1:'+str(t)).encode()).hexdigest()[:8], 16)%10 for t in tags])
    masks = {name: (arrays['split']==0) & pred[buckets[arrays['rep']]]
             for name, pred in [('fit', np.arange(10)<8), ('tune', np.arange(10)==8), ('test', np.arange(10)==9)]}
    ix = np.flatnonzero(masks['fit'])
    mean, std = x[ix].mean(0), x[ix].std(0).clip(.01)
    x -= mean; x /= std; np.clip(x, -20, 20, out=x)
    xt, yt, kt = map(torch.from_numpy, (x, y, known))
    base = ((y[ix]*known[ix]).sum(0)/known[ix].sum(0)).clip(1e-5, 1-1e-5)
    model = torch.nn.Linear(x.shape[1], 5)
    with torch.no_grad():
        model.weight.zero_(); model.bias.copy_(torch.from_numpy(np.log(base/(1-base))))
    opt = torch.optim.Adam(model.parameters(), lr=.01)
    rng = np.random.default_rng(20261004)
    for epoch in range(8):
        rng.shuffle(ix)
        for start in range(0, len(ix), 8192):
            ids = ix[start:start+8192]
            loss = (F.binary_cross_entropy_with_logits(model(xt[ids]), yt[ids], reduction='none')*kt[ids]).sum()/kt[ids].sum()
            opt.zero_grad(); loss.backward(); opt.step()
        print(json.dumps(dict(epoch=epoch+1, loss=float(loss))), flush=True)
    p = np.empty_like(y)
    with torch.no_grad():
        for start in range(0, len(x), 32768): p[start:start+32768] = model(xt[start:start+32768]).sigmoid().numpy()
    probability = p.max(1)
    np.save(a.out/'probability.npy', probability)
    torch.save(dict(state=model.state_dict(), mean=mean.tolist(), std=std.tolist(), targets=TARGETS), a.out/'classifier.pt')
    report = dict(status='MEASURED_PROXY_CLASSIFIER', coverage=coverage, targets=TARGETS,
                  fixed_weight=2.0, weight_selection='owner_fixed_overnight_no_sweep',
                  features='sanitized sc[0:7,52:70] plus own hand Rocket/XBow/Tornado/Log availability',
                  joint_score='maximum of five predicted probabilities',
                  defensive_xbow_excluded=True,
                  label_limitations='Geometric/temporal proxies; no causal hit or strategic defense truth. Unknown defensive labels masked.',
                  xbow_geometry=dict(Counter((r['lane']+'_'+r['lane_state']) for r in map(json.loads, xbow.open()))),
                  weight_quantiles=np.quantile(1+probability, [0,.5,.9,.99,1]).tolist(),
                  heldout={name:evaluate(p[m], y[m], known[m], arrays['rep'][m], base) for name,m in masks.items() if name!='fit'},
                  sources={str(q):sha(q) for q in (rocket, xbow, Path(__file__))})
    (a.out/'heldout_report.json').write_text(json.dumps(report, indent=2))
    evidence = dict(public_only=True, context_targets=TARGETS, defensive_xbow_excluded=True, selected_weight=2.0,
                    weight_selection='owner_fixed_overnight_no_sweep', classifier_sha256=sha(a.out/'classifier.pt'),
                    heldout_report_sha256=sha(a.out/'heldout_report.json'), dataset_sha256=sha(a.data),
                    probability_sha256=sha(a.out/'probability.npy'),
                    **{name+'_tags':sorted(str(t) for t in tags[np.unique(arrays['rep'][m])]) for name,m in masks.items()})
    (a.out/'artifact.json').write_text(json.dumps(evidence, indent=2))
    print('CONTEXT_ARTIFACT_VERIFIED', flush=True)


if __name__ == '__main__': main()
