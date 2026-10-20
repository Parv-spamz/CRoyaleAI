from shared import *


def controls():
    s = dict(ids=np.arange(5), y_gate=np.array([1, 1, 1, 1, 0]), y_card=np.ones(5, int),
             hand_card=np.tile([1, 2, 0, 0], (5, 1)), y_xy=np.zeros((5, 2)))
    p = dict(gate=np.array([.9, .1, .9, .9, .1]), chosen_card=np.array([1, 1, 2, 1, 1]),
             expert_cell=np.array([0, 0, 0, 100, 0]), allowed=np.tile([True, True, False, False], (5, 1)),
             card_logits=np.array([[2, 1, -np.inf, -np.inf], [2, 1, -np.inf, -np.inf], [1, 2, -np.inf, -np.inf],
                                   [2, 1, -np.inf, -np.inf], [2, 1, -np.inf, -np.inf]]))
    v = values(s, p)
    assert [int(v[k].sum()) for k in ('play_success', 'gate_failure', 'card_failure', 'aim_failure', 'wait_correct')] == [1]*5
    from verify import recount
    fixture = dict(s, **p, rep=np.array([0, 0, 1, 1, 1]), tick=np.array([0, 4800, 4800, 4800, 4800]))
    got = recount(fixture, np.array([2, 1, 1, 1, 3]), ['pad', 'rocket', 'knight'])
    assert [got['all'][k] for k in ('play_success', 'gate_failure', 'card_failure', 'aim_failure', 'wait_correct')] == [2, 1, 1, 1, 3]
    assert got['all']['views'] == 5 and got['all']['weight'] == 8 and got['all']['replays'] == 2
    assert got['late_rocket']['weight'] == 3 and got['all']['by_replay']['1']['weight'] == 5
    bad = 0
    for key, item in [('gate', np.full(5, np.nan)), ('gate', np.full(5, 1.1)),
                      ('chosen_card', np.full(5, 2)), ('expert_cell', np.full(5, 2304)),
                      ('allowed', np.ones((5, 3), bool)), ('card_logits', np.full((5, 4), np.nan))]:
        try: values(s, dict(p, **{key: item}))
        except (AssertionError, ValueError): bad += 1
        else: raise AssertionError('Malformed prediction accepted')
    return dict(positive=2, negative=bad)


def main():
    cutoff(); assert not (HERE/'prepared.json').exists(); OUT.mkdir(exist_ok=False)
    assert read(HERE.parent/'development_rl_3/reviewed_results.json')['complete']
    assert sha(CKPT) == read(c.HERE/'ordinary_v5_portable.json')['portable_sha256']
    assert sha(DEV) == read(HERE.parent/'development_rl_3/results_verified.json')['hashes']['ordinary_v5']['cache']
    z = arrays(BASE/'indices.npz'); train = z['train']; dev = z['development']
    assert len(train) == 213995 and len(dev) == 54723 and not np.intersect1d(train, dev).size
    fn, fm = frequencies(train); assert int(fn.sum()+fm.sum()) == 128000
    proof = controls(); assert proof == dict(positive=2, negative=6)
    write(HERE/'prepared.json', dict(complete=True, sources=sources(), controls=proof, native_rows=len(train),
          mirrored_rows=int((fm > 0).sum()), native_draws=int(fn.sum()), mirrored_draws=int(fm.sum()),
          native_drawn_unique=int((fn > 0).sum()), all_drawn_unique=int(((fn+fm) > 0).sum()),
          development_rows=len(dev), optimizer_updates=0))
    print('TRAINING_FIT_PREPARED')


if __name__ == '__main__': main()
