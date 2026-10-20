"""Independently recompute report statistics and area objectives from saved logits."""
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def average(values, mask):
    return float(values[mask].mean()) if mask.any() else None


def equal(actual, expected):
    if expected is None:
        assert actual is None
    else:
        assert np.isclose(actual, expected, atol=1e-11, rtol=1e-11), (actual, expected)


def statistics(prob, top_prob, z):
    n = len(prob); ix = np.arange(n)
    top = top_prob.argmax(1)
    valid = z['y_play'] & z['allowed'].any(1) & (z['y_slot'] >= 0)
    confident = valid & (top_prob.max(1) >= .6)
    changed = 1-prob[ix, top]
    rocket = np.sum(prob * (z['hand'] == int(z['rocket_id'])), axis=1)
    result = dict(agreement=average(prob[ix, np.maximum(z['y_slot'], 0)], valid),
                  agreement_n=int(valid.sum()), changed_probability=average(changed, valid),
                  confident_override=average(changed, confident), confident_n=int(confident.sum()),
                  rocket_recall=average(rocket, z['mask_pro_rocket']),
                  rocket_false_fire=average(rocket, z['mask_other_pro_play']),
                  rocket_on_pro_wait=average(rocket, ~z['y_play'] & z['allowed'].any(1)), contexts={})
    for key in z.files:
        if key.startswith('mask_'):
            mask = z[key]
            result['contexts'][key[5:]] = dict(n=int(mask.sum()), rocket_choice=average(rocket, mask),
                gate_pass_035=average((z['gate'] > .35).astype(float), mask),
                rocket_gated_035=average(rocket*(z['gate'] > .35), mask),
                rocket_gated_027=average(rocket*(z['gate'] > .27), mask))
    return result


def compare_stats(recorded, expected):
    for key, value in expected.items():
        if isinstance(value, dict):
            compare_stats(recorded[key], value)
        else:
            equal(recorded[key], value)


def verify_model(model, radius):
    assert sha(ROOT/model['checkpoint']) == model['checkpoint_sha256']
    assert sha(ROOT/model['cache']) == model['cache_sha256']
    with np.load(ROOT/model['cache'], allow_pickle=False) as z:
        x = np.where(z['allowed'], z['logits'].astype(float), -np.inf)
        has = np.isfinite(x).any(1)
        shift = np.zeros(len(x)); shift[has] = x[has].max(1)
        weights = np.exp(x-shift[:, None]); totals = weights.sum(1)
        prob = np.divide(weights, totals[:, None], out=np.zeros_like(weights), where=totals[:, None] > 0)
        greedy = np.zeros_like(prob); greedy[np.arange(len(x)), prob.argmax(1)] = has
        baseline = statistics(greedy, prob, z)
        compare_stats(model['baseline'], baseline)
        assert {(c['ratio'],c['temperature']) for c in model['candidates']} == {(.5,.7),(.5,1.),(.7,.7),(.7,1.)}
        for candidate in model['candidates']:
            keep = z['allowed'] & (prob > 0) & (prob >= candidate['ratio'] * prob.max(1, keepdims=True))
            tempered = np.where(keep, prob ** (1/candidate['temperature']), 0)
            denominator = tempered.sum(1, keepdims=True)
            distribution = np.divide(tempered, denominator, out=np.zeros_like(tempered), where=denominator > 0)
            expected = statistics(distribution, prob, z)
            compare_stats(candidate, expected)
            delta = 100*(expected['agreement']-baseline['agreement'])
            equal(candidate['agreement_delta_pp'], delta)
            assert candidate['passes_offline'] == (delta >= -1-1e-10 and expected['confident_override'] <= 1e-12)
        # Geometry oracle uses explicit shifted arrays, independent of torch convolution.
        cell_logits = z['cell_logits'].astype(float)
        p = np.exp(cell_logits-cell_logits.max(1, keepdims=True)); p /= p.sum(1, keepdims=True)
        p = p.reshape(-1, 64, 36); pad = int(np.ceil(radius*2))
        padded = np.pad(p, ((0,0),(pad,pad),(pad,pad)))
        score = np.zeros_like(p)
        for dy in range(-pad,pad+1):
            for dx in range(-pad,pad+1):
                if (dx/2)**2 + (dy/2)**2 <= radius**2:
                    score += padded[:,pad+dy:pad+dy+64,pad+dx:pad+dx+36]
        score = score.reshape(-1,2304); selected = z['area_cell']
        assert np.all(score[np.arange(len(score)),selected] >= score.max(1)-1e-6)
        np.testing.assert_array_equal(z['old_cell'],cell_logits.argmax(1))
        ri=z['rocket_rows']; targets=z['pro_xy']*[18,32]
        for label, mask in [('all_pro_rocket',np.ones(len(ri),bool)),
                            ('tower',z['mask_pro_tower_rocket'][ri]),
                            ('finishing',z['mask_pro_finishing_rocket'][ri])]:
            stat=model['aim'][label]; assert stat['n']==int(mask.sum())
            for key, cells in [('argmax',z['old_cell']),('area',selected)]:
                xy=np.c_[cells%36/2,cells//36/2]
                covered=np.linalg.norm(xy-targets,axis=1)<=radius+1e-6
                equal(stat[key+'_target_coverage'],average(covered,mask))


def main():
    report=json.loads((HERE/'report.json').read_text())
    assert set(report['models'])=={'r1e','r1'}
    assert sha(ROOT/report['dataset'])==report['dataset_sha256']
    catalog=json.loads((ROOT/'research/ext/Royale/RoyaleSim/data/derived/cards.json').read_text())
    radius=next(c['area_damage_radius_milli']/1000 for c in catalog['cards'] if c['name']=='Rocket')
    equal(report['rocket_radius_tiles'],radius)
    assert report['models']['r1e']['vocabulary_mapping']['identity_mapping'] is True
    assert report['models']['r1']['vocabulary_mapping']['identity_mapping'] is False
    assert any(x['card']=='the-log' and x['source_id']!=x['model_id']
               for x in report['models']['r1']['vocabulary_mapping']['changed_ids'])
    for model in report['models'].values():
        verify_model(model,radius)
    corrupted=copy.deepcopy(report['models']['r1e'])
    corrupted['candidates'][0]['agreement']+=.1
    try:
        verify_model(corrupted,radius)
    except AssertionError:
        pass
    else:
        raise AssertionError('Corrupted result was accepted')
    before=json.loads((HERE/'before.json').read_text())
    for name,digest in before['protected_sha256'].items():
        assert sha(ROOT/name)==digest, name
    print('Both checkpoints: independent statistics, acceptance, geometry and corruption control pass.')
    print('DECISION_REPORT_VERIFIED')


if __name__=='__main__':
    main()
