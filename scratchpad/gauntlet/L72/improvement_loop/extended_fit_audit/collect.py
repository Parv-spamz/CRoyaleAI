import gc
import os
import torch
from shared import *


def infer(model, rows, sub, positions, mirrored, cv):
    from pipeline.opp_elixir_count import card_cost
    costs = np.array([card_cost(k.replace('-', '_')) or 0 for k in cv])
    n = len(positions); allow = (sub['hand_card'][positions] > 0) & (costs[sub['hand_card'][positions]] <= np.floor(sub['sc'][positions, 3]*10+1e-3)[:, None])
    p = dict(allowed=allow, gate=np.empty(n, np.float32), chosen_card=np.empty(n, np.int32),
             card_logits=np.empty((n, 4), np.float32), expert_cell=np.empty(n, np.int32))
    with torch.inference_mode():
        for lo in range(0, n, 128):
            cutoff(); ix = np.arange(lo, min(lo+128, n)); b = c.augment(rows.batch(positions[ix]), mirrored)
            enc = model.encode_gen(b); h = model.heads_gen(enc, b)
            p['gate'][ix] = h['gate'].sigmoid().cpu().numpy(); p['card_logits'][ix] = h['card'].cpu().numpy()
            slot = np.where(allow[ix], p['card_logits'][ix], -np.inf).argmax(1)
            p['chosen_card'][ix] = sub['hand_card'][positions[ix], slot]
            p['expert_cell'][ix] = model.cell_logits_gen(enc, b['card'], b['form']).argmax(-1).cpu().numpy()
            if lo % 12800 == 0: write(HERE/'progress.json', dict(mirrored=mirrored, done=int(lo), total=n))
    return p


def collect_one(arm, spec):
    from pipeline.model_gen import load_model
    model, state = load_model(spec['checkpoint'], 'cuda'); model.eval()
    assert all(not module.training for module in model.modules())
    assert state['args']['feature_version'] == 5 and state['args']['grid'] == 'lattice'
    destination = OUT/arm; destination.mkdir(exist_ok=False)
    before = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    ids, sub, meta, rows = c.load_part('train', 'cuda'); cv = meta['card_vocab']; assert cv == state['card_vocab']
    fn, fm = frequencies(ids); result = {}; artifacts = {}
    for name, positions, mirrored in [('native', np.arange(len(ids)), False), ('mirrored', np.flatnonzero(fm), True)]:
        p = infer(model, rows, sub, positions, mirrored, cv)
        s = labels(ids[positions], {k: sub[k][positions] for k in ('rep', 'tick', 'y_gate', 'y_card', 'y_xy', 'hand_card')}, mirrored)
        w = fm[positions] if mirrored else fn
        np.savez_compressed(destination/(name+'.npz'), **s, **p, frequency=w)
        artifacts[name] = sha(destination/(name+'.npz'))
        if mirrored:
            result['drawn_mirrored'] = summarize(s, p, np.ones(len(positions), np.int64), cv)
            result['weighted_mirrored_draws'] = summarize(s, p, w, cv)
        else:
            result['native_train'] = summarize(s, p, np.ones(len(ids), np.int64), cv)
            result['drawn_native'] = summarize(s, p, (fn > 0).astype(np.int64), cv)
            result['undrawn_native'] = summarize(s, p, ((fn+fm) == 0).astype(np.int64), cv)
            result['weighted_native_draws'] = summarize(s, p, w, cv)
    assert all(torch.equal(before[k], v.detach().cpu()) for k, v in model.state_dict().items())
    assert all(p.grad is None for p in model.parameters())
    del rows, sub, model, before; gc.collect(); torch.cuda.empty_cache()
    dids, dsub, dmeta, drows = c.load_part('development', 'cpu'); cached = arrays(spec['development'])
    assert np.array_equal(dids, cached['ids']) and dmeta['card_vocab'] == cv
    s = labels(dids, dsub); result['development_cached'] = summarize(s, cached, np.ones(len(dids), np.int64), cv)
    # Store literal labels only for independent joining; no development inference.
    np.savez_compressed(destination/'development_labels.npz', **s); artifacts['development_labels'] = sha(destination/'development_labels.npz')
    write(destination/'counts.json', result); check()
    return dict(complete=True, artifacts=artifacts, counts_sha256=sha(destination/'counts.json'),
          card_vocab=cv, prepared_sha256=sha(HERE/'prepared.json'), weights_unchanged=True, optimizer_updates=0,
          development_inference=0, fresh_inference_rows=len(ids)+int((fm > 0).sum()))


def main():
    cutoff(); check(); assert not (HERE/'collected.json').exists(); c.setup()
    assert not (HERE/'collection_started.json').exists()
    write(HERE/'collection_started.json', dict(pid=os.getpid(), utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    results = {}
    for arm, spec in MODELS.items():
        write(HERE/'active_model.json', dict(arm=arm))
        results[arm] = collect_one(arm, spec)
    check()
    write(HERE/'collected.json', dict(complete=True, models=results,
          prepared_sha256=sha(HERE/'prepared.json'), optimizer_updates=0, development_inference=0,
          fresh_inference_rows=sum(x['fresh_inference_rows'] for x in results.values())))
    print('EXTENDED_FIT_COLLECTED')


if __name__ == '__main__': main()
