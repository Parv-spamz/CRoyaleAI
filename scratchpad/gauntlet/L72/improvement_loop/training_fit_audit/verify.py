"""Independent scalar raw-label and cached-prediction recount; no inference."""
import copy
import math
from collections import Counter
from shared import ROOT, HERE, OUT, BASE, DEV, c, read, write, sha, arrays, check, cutoff
import numpy as np

KEYS = ('play', 'wait_correct', 'called', 'card', 'aim1', 'play_success', 'action',
        'gate_failure', 'card_failure', 'aim_failure')


def validate(z, ids, raw, freq, mirrored, costs):
    assert np.array_equal(z['ids'], ids) and len(set(ids.tolist())) == len(ids)
    for k in ('rep', 'tick', 'y_gate', 'y_card', 'hand_card'):
        assert np.array_equal(z[k], raw[k][ids]), k
    xy = raw['y_xy'][ids].copy()
    if mirrored: xy[:, 0] = 1-xy[:, 0]
    assert np.array_equal(z['y_xy'], xy)
    assert np.array_equal(z['frequency'], freq)
    assert np.isfinite(z['gate']).all() and ((z['gate'] >= 0) & (z['gate'] <= 1)).all()
    assert z['allowed'].dtype == bool and z['allowed'].shape == (len(ids), 4)
    assert z['card_logits'].shape == (len(ids), 4) and not np.isnan(z['card_logits']).any()
    assert not np.isposinf(z['card_logits']).any()
    assert ((z['expert_cell'] >= 0) & (z['expert_cell'] < 2304)).all()
    elixir_bounds = np.floor(raw['sc'][ids, 3]*10+1e-3).astype(np.int64)
    for i, row in enumerate(ids):
        hand = raw['hand_card'][row]; elixir = int(elixir_bounds[i])
        allowed = [int(card) > 0 and costs[int(card)] <= elixir for card in hand]
        assert allowed == z['allowed'][i].tolist()
        choice = max(range(4), key=lambda j: float(z['card_logits'][i, j]) if allowed[j] else -math.inf)
        assert int(z['chosen_card'][i]) == int(hand[choice])


def recount(z, w, cv):
    totals = {}; playcards = sorted(set(z['y_card'][z['y_gate'] == 1].tolist()))
    groups = ['all', 'play', 'rocket', 'late_rocket'] + ['card/'+cv[int(k)] for k in playcards]
    for g in groups: totals[g] = dict(views=0, weight=0, replays=0, **dict.fromkeys(KEYS, 0), by_replay={})
    for i, weight in enumerate(w):
        weight = int(weight)
        if not weight: continue
        isplay = int(z['y_gate'][i]) == 1
        has = any(bool(x) for x in z['allowed'][i]); called = float(z['gate'][i]) > .35 and has
        card = int(z['chosen_card'][i]) == int(z['y_card'][i]) and has
        cell = int(z['expert_cell'][i]); x, y = z['y_xy'][i]
        dx = (cell % 36 / 36-float(x))*18; dy = (cell // 36 / 64-float(y))*32
        aim = math.sqrt(dx*dx+dy*dy) <= 1
        success = isplay and called and card and aim
        v = dict(play=isplay, wait_correct=not isplay and not called, called=called,
                 card=isplay and card, aim1=isplay and aim, play_success=success,
                 action=success or (not isplay and not called), gate_failure=isplay and not called,
                 card_failure=isplay and called and not card, aim_failure=isplay and called and card and not aim)
        assert sum(v[k] for k in ('play_success', 'gate_failure', 'card_failure', 'aim_failure')) == int(isplay)
        membership = ['all']
        if isplay:
            membership += ['play', 'card/'+cv[int(z['y_card'][i])]]
            if cv[int(z['y_card'][i])] == 'rocket':
                membership += ['rocket']
                if int(z['tick'][i]) >= 4800: membership += ['late_rocket']
        for g in membership:
            t = totals[g]; rep = str(int(z['rep'][i]))
            if rep not in t['by_replay']: t['by_replay'][rep] = dict(views=0, weight=0, **dict.fromkeys(KEYS, 0))
            for dest in (t, t['by_replay'][rep]):
                dest['views'] += 1; dest['weight'] += weight
                for k in KEYS: dest[k] += weight*int(v[k])
    for t in totals.values(): t['replays'] = len(t['by_replay'])
    return totals


def main():
    cutoff(); check(); assert not (HERE/'verified.json').exists(); report = read(HERE/'collected.json')
    assert report['complete'] and report['weights_unchanged'] and report['optimizer_updates'] == report['development_inference'] == 0
    assert report['prepared_sha256'] == sha(HERE/'prepared.json') and report['counts_sha256'] == sha(OUT/'counts.json')
    for name, h in report['artifacts'].items(): assert sha(OUT/(name+'.npz')) == h
    cv = report['card_vocab']; ids = arrays(BASE/'indices.npz'); d = arrays(BASE/'draws.npz')
    counts = [Counter(), Counter()]
    for row, flag in zip(d['rows'], d['mirror']): counts[int(bool(flag))].update(int(x) for x in row)
    assert sum(map(lambda x: sum(x.values()), counts)) == 128000
    fn, fm = [np.array([counter[int(i)] for i in ids['train']], dtype=np.int64) for counter in counts]
    with np.load(c.DATA, allow_pickle=False) as source:
        import json
        assert json.loads(str(source['meta']))['card_vocab'] == cv
        raw = {k: source[k] for k in ('rep', 'tick', 'y_gate', 'y_card', 'y_xy', 'hand_card', 'sc', 'split')}
    assert not set(raw['rep'][ids['train']]) & set(raw['rep'][ids['development']])
    assert all(raw['split'][np.r_[ids['train'], ids['development']]] == 0)
    from pipeline.opp_elixir_count import card_cost
    costs = [card_cost(k.replace('-', '_')) or 0 for k in cv]
    n = arrays(OUT/'native.npz'); m = arrays(OUT/'mirrored.npz')
    validate(n, ids['train'], raw, fn, False, costs)
    mid = ids['train'][fm > 0]; validate(m, mid, raw, fm[fm > 0], True, costs)
    dl = arrays(OUT/'development_labels.npz'); dp = arrays(DEV); assert np.array_equal(dl['ids'], dp['ids'])
    dev = dict(dl, **{k: dp[k] for k in ('gate', 'allowed', 'card_logits', 'chosen_card', 'expert_cell')}, frequency=np.ones(len(dl['ids']), np.int64))
    validate(dev, ids['development'], raw, dev['frequency'], False, costs)
    specs = [('native_train', n, np.ones(len(fn), np.int64)), ('drawn_native', n, (fn > 0).astype(np.int64)),
             ('undrawn_native', n, ((fn+fm) == 0).astype(np.int64)), ('weighted_native_draws', n, fn),
             ('drawn_mirrored', m, np.ones(len(mid), np.int64)), ('weighted_mirrored_draws', m, fm[fm > 0]),
             ('development_cached', dev, dev['frequency'])]
    expected = read(OUT/'counts.json'); verified = {}
    for name, z, w in specs:
        got = recount(z, w, cv); assert got == expected[name], name; verified[name] = got
    # Exercise actual raw-label/prediction validation using a known valid native fragment.
    small = {k: v[:5].copy() for k, v in n.items()}; sid = ids['train'][:5]; sf = fn[:5]
    validate(small, sid, raw, sf, False, costs); rejected = 0
    cases = []
    for key, index, value in [('ids', 0, int(sid[1])), ('rep', 0, -99), ('y_gate', 0, 9),
                              ('y_card', 0, -1), ('frequency', 0, int(sf[0])+1),
                              ('gate', 0, float('nan')), ('expert_cell', 0, 2304), ('chosen_card', 0, -1)]:
        x = copy.deepcopy(small); x[key][index] = value; cases.append(x)
    x = copy.deepcopy(small); x['y_xy'][0, 0] += .01; cases.append(x)
    x = copy.deepcopy(small); x['allowed'][0, 0] = ~x['allowed'][0, 0]; cases.append(x)
    for x in cases:
        try: validate(x, sid, raw, sf, False, costs)
        except AssertionError: rejected += 1
        else: raise AssertionError('Corrupt raw join or prediction accepted')
    assert rejected == 10
    summary = {name: {g: {k: v for k, v in vals.items() if k != 'by_replay'} for g, vals in data.items()} for name, data in verified.items()}
    check(); write(HERE/'verified.json', dict(complete=True, controls=dict(positive=4, negative=10),
          collected_sha256=sha(HERE/'collected.json'), counts_sha256=sha(OUT/'counts.json'),
          summaries=summary, fresh_inference_rows=report['fresh_inference_rows'], optimizer_updates=0,
          development_inference=0, source_sha256=sha(HERE/'verify.py')))
    print('TRAINING_FIT_VERIFIED')


if __name__ == '__main__': main()
