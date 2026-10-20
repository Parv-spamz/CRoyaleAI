"""Independently recount cached held-out predictions; never run a model or select it.

Only archive slicing, card costs and class IDs are shared with production. Metric
logic does not import the evaluator. This also verifies prediction legality and
the exact validation membership before accepting a reported numerator.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from pipeline import vocab
from pipeline.opp_elixir_count import card_cost
from pipeline.rocket_teaching import sha
from pipeline.train_rocket_curriculum import load_subset

FAMILIES = ('witch', 'night_witch', 'furnace', 'goblin_hut', 'barbarian_hut', 'tombstone')
SOURCE = ROOT / 'icebow/data/pipeline/gen_dataset_v31_public.npz'
CONTEXTS = ROOT / 'icebow/data/bench/context_teaching_20261005'


def recount(sub, cohorts, cv, predictions):
    p = predictions
    n = len(sub['y_gate'])
    prices = np.array([card_cost(name.replace('-', '_')) or 0 for name in cv])
    budget = np.floor(10 * sub['sc'][:, 3] + 1e-3)
    legal = (sub['hand_card'] > 0) & (prices[sub['hand_card']] <= budget[:, None])
    if not np.array_equal(legal, p['allowed']):
        raise ValueError('Cached affordability differs from public hand and elixir')
    for key in ('gate', 'chosen_card', 'expert_cell', 'log_cell'):
        if p[key].shape != (n,) or not np.isfinite(p[key]).all():
            raise ValueError('Invalid cached prediction ' + key)
    if ((p['gate'] < 0) | (p['gate'] > 1)).any():
        raise ValueError('Gate outside probability range')
    for key in ('expert_cell', 'log_cell'):
        if not np.issubdtype(p[key].dtype, np.integer) or ((p[key] < 0) | (p[key] >= 36 * 64)).any():
            raise ValueError('Invalid placement cell')
    selected_legal = ((sub['hand_card'] == p['chosen_card'][:, None]) & legal).any(axis=1)
    if (legal.any(axis=1) & ~selected_legal).any():
        raise ValueError('Chosen card is absent or unaffordable')

    expert_play = sub['y_gate'].astype(bool)
    issued = (p['gate'] > .35) & legal.any(axis=1)
    correct_card = (p['chosen_card'] == sub['y_card']) & legal.any(axis=1)
    # Preserve the evaluator's floating-point boundary by using the same
    # normalized grid coordinates, but recount all events independently.
    dx = ((p['expert_cell'] % 36) / 36 - sub['y_xy'][:, 0]) * 18
    dy = ((p['expert_cell'] // 36) / 64 - sub['y_xy'][:, 1]) * 32
    distance = np.sqrt(dx * dx + dy * dy)
    action_correct = (~expert_play & ~issued) | (expert_play & issued & correct_card & (distance <= 1))
    rocket = expert_play & (sub['y_card'] == cv.index('rocket'))
    tornado = expert_play & (sub['y_card'] == cv.index('tornado'))

    def fraction(event, subset):
        den = int(np.count_nonzero(subset))
        hits = int(np.count_nonzero(event & subset))
        return dict(n=hits, denominator=den, rate=hits / den if den else None)

    masks = dict(cohorts)
    spans = zip(sub['off'][:-1], sub['off'][1:])
    present = [set(sub['tok'][lo:hi, 0].astype(int)) for lo, hi in spans]
    for name in FAMILIES:
        cid = vocab.unit_id(name)
        masks[name] = np.fromiter((cid in bodies for bodies in present), bool, count=n)
    masks['spawners'] = np.any([masks[name] for name in FAMILIES], axis=0)
    masks['xbow_useful'] = cohorts['xbow'] & ~cohorts['xbow_no_lifetime_target']
    masks['pro_rocket'] = rocket
    all_rows = np.ones(n, bool)
    result = dict(global_card_agreement=fraction(correct_card, expert_play),
                  global_action_agreement=fraction(action_correct, all_rows), contexts={})
    for name, mask in masks.items():
        result['contexts'][name] = dict(rows=int(mask.sum()), plays=int((mask & expert_play).sum()),
            card_agreement=fraction(correct_card, mask & expert_play),
            action_agreement=fraction(action_correct, mask), gate_play=fraction(issued, mask),
            rocket_gated=fraction(issued & (p['chosen_card'] == cv.index('rocket')), mask))
    result.update(rocket_recall=fraction(issued & correct_card, rocket),
        rocket_finish=fraction(issued & correct_card & (distance <= 2), rocket & cohorts['finish']),
        combo_rocket=fraction(issued & correct_card, rocket & cohorts['combo']),
        combo_tornado=fraction(issued & correct_card, tornado & cohorts['combo']))

    eligible = np.zeros(n, bool)
    pro_log = np.zeros(n, bool)
    same_lane = np.zeros(n, bool)
    log = cv.index('the-log')
    barrel = cv.index('goblin-barrel')
    for i, flights in enumerate(sub['projectiles']):
        targets = [shot[4:6] for shot in flights if shot[0] == barrel and shot[1] == 1]
        if len(targets) != 1:
            continue
        tx, ty = targets[0]
        if not (0 <= tx <= 1 and .5 <= ty <= 1 and (tx < .4 or tx > .6)):
            continue
        if not any(card == log and ok for card, ok in zip(sub['hand_card'][i], legal[i])):
            continue
        eligible[i] = True
        pro_log[i] = (expert_play[i] and sub['y_card'][i] == log
                      and ((sub['y_xy'][i, 0] < .5) == (tx < .5)))
        same_lane[i] = ((p['log_cell'][i] % 36) < 18) == (tx < .5)
    fired_log = issued & (p['chosen_card'] == log)
    result['barrel'] = dict(pro_same_lane_rows=int(pro_log.sum()),
        forced_log_same_lane=fraction(same_lane, pro_log),
        gated_correct_lane=fraction(fired_log & same_lane, pro_log),
        gated_wrong_lane=fraction(fired_log & ~same_lane, pro_log),
        known_playable_rows=int(eligible.sum()))
    return result


def verify_report(actual, expected):
    for key, value in expected.items():
        if actual.get(key) != value:
            raise ValueError('Independent metric mismatch: ' + key)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--heldout', type=Path, action='append', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    manifest = json.loads((CONTEXTS / 'manifest.json').read_text())
    source_hash = sha(SOURCE)
    if source_hash != manifest['source_dataset_sha256'] or sha(CONTEXTS / 'cohorts.npz') != manifest['cohorts_sha256']:
        raise ValueError('Changed source or cohorts')
    with np.load(CONTEXTS / 'cohorts.npz') as z:
        cohorts = {k: z[k] for k in z.files}
    with np.load(SOURCE) as z:
        ids = np.flatnonzero(cohorts['pool'] & (z['split'] == 1))
    if len(ids) != 38317:
        raise ValueError('Changed validation membership')
    cohorts = {k: mask[ids] for k, mask in cohorts.items()}
    sub, meta = load_subset(SOURCE, ids)
    results = []
    for folder in a.heldout:
        report = json.loads((folder / 'report.json').read_text())
        if report['source_dataset_sha256'] != source_hash or report['contexts_manifest_sha256'] != sha(CONTEXTS / 'manifest.json'):
            raise ValueError('Report source mismatch')
        predictions_hash = sha(folder / 'predictions.npz')
        if predictions_hash != report['predictions_sha256']:
            raise ValueError('Changed prediction cache')
        with np.load(folder / 'predictions.npz') as z:
            predictions = {k: z[k] for k in z.files}
        if not np.array_equal(predictions.pop('ids'), ids):
            raise ValueError('Cached validation row IDs differ')
        recounted = recount(sub, cohorts, meta['card_vocab'], predictions)
        verify_report(report, recounted)
        results.append(dict(heldout=str(folder), rows=len(ids), report_sha256=sha(folder / 'report.json'),
                            predictions_sha256=predictions_hash, matches=True))
    a.out.write_text(json.dumps(dict(source_sha256=source_hash, verifier_sha256=sha(__file__), results=results), indent=2))
    print(json.dumps(results))
    print('EXPERT_PREDICTIONS_INDEPENDENTLY_RECOUNTED')


if __name__ == '__main__':
    main()
