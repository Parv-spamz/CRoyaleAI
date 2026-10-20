"""Create a separately registered fixed-weight diagnostic; never execute old jobs."""
from pathlib import Path

P = Path(__file__).resolve().parent
old = P/'training_fit_audit'
new = P/'extended_fit_audit'
assert not new.exists()
new.mkdir()
def save(name, text): (new/name).write_text(text, encoding='utf-8')
def source(name): return (old/name).read_text(encoding='utf-8')

s = source('shared.py').replace('training_fit_audit_20261006', 'extended_fit_audit_20261006')
s = s.replace("CKPT = BASE/'ordinary_v5/candidate_portable.pt'\nDEV = BASE/'ordinary_v5_eval_v2/predictions.npz'", """SCHEDULE = ROOT/'icebow/data/bench/development_iteration_9_20261006/schedule.npz'
MODELS = {}
for arm, iteration in [('ordinary_extended_v5', 9), ('ordinary_no_dropout_v5', 10)]:
    leaf = HERE.parent/('development_iteration_'+str(iteration))
    folder = ROOT/('icebow/data/bench/development_iteration_'+str(iteration)+'_20261006')
    MODELS[arm] = dict(leaf=leaf, checkpoint=folder/'candidate.pt', development=folder/'predictions.npz')""")
a=s.index('def sources():'); b=s.index('def check():',a)
s=s[:a]+'''def sources():
    paths = list((ROOT/'pipeline').glob('*.py')) + list(HERE.glob('*.py'))
    paths += [HERE/'PLAN.md', HERE/'METRICS.md', c.HERE/'common.py', c.HERE/'prepared.json',
              c.HERE/'verified.json', c.DATA, c.SOURCE, BASE/'indices.npz', SCHEDULE]
    for spec in MODELS.values():
        paths += [spec['checkpoint'], spec['development']]
        paths += [spec['leaf']/f for f in ('prepared.json','trained.json','training_verified.json',
                  'evaluated.json','results_verified.json','reviewed_results.json')]
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}
''' +s[b:]
s=s.replace("arrays(BASE/'draws.npz')", 'arrays(SCHEDULE)').replace('(1000, 128)', '(8000, 128)').replace('(1000,)', '(8000,)')
save('shared.py',s)

s=source('prepare.py'); a=s.index("    assert read(HERE.parent/'development_rl_3"); b=s.index("    z = arrays(BASE/'indices.npz')",a)
s=s[:a]+'''    for spec in MODELS.values():
        assert read(spec['leaf']/'reviewed_results.json')['complete']
        assert sha(spec['checkpoint']) == read(spec['leaf']/'trained.json')['checkpoint_sha256']
        assert sha(spec['development']) == read(spec['leaf']/'evaluated.json')['predictions_sha256']
''' +s[b:]
s=s.replace('128000','1024000').replace('TRAINING_FIT_PREPARED','EXTENDED_FIT_PREPARED')
s=s.replace('proof = controls();', """schedule = arrays(SCHEDULE); rng = np.random.default_rng(2026100609)
    for rows, mirror in zip(schedule['rows'], schedule['mirror']):
        assert np.array_equal(rows, train[rng.choice(len(train), 128)])
        assert bool(mirror) == bool(rng.random() < .5)
    proof = controls();""")
save('prepare.py',s)

s=source('collect.py'); a=s.index('def main():'); b=s.index("if __name__ == '__main__':",a)
body=s[a:b]
body=body.replace('def main():\n    cutoff(); check(); assert not (HERE/\'collected.json\').exists(); c.setup()', 'def collect_one(arm, spec):')
body=body.replace("model, state = load_model(CKPT, 'cuda'); model.eval()", "model, state = load_model(spec['checkpoint'], 'cuda'); model.eval()\n    assert state['args']['feature_version'] == 5 and state['args']['grid'] == 'lattice'\n    destination = OUT/arm; destination.mkdir(exist_ok=False)")
body=body.replace("OUT/", "destination/")
body=body.replace('destination = destination/arm','destination = OUT/arm')
body=body.replace('arrays(DEV)',"arrays(spec['development'])")
body=body.replace("write(HERE/'collected.json', dict(", 'return dict(')
body=body.replace("fresh_inference_rows=len(ids)+int((fm > 0).sum())))\n    print('TRAINING_FIT_COLLECTED')", "fresh_inference_rows=len(ids)+int((fm > 0).sum()))")
s=s[:a]+body+'''def main():
    cutoff(); check(); assert not (HERE/'collected.json').exists(); c.setup()
    results = {}
    for arm, spec in MODELS.items():
        write(HERE/'active_model.json', dict(arm=arm))
        results[arm] = collect_one(arm, spec)
    check()
    write(HERE/'collected.json', dict(complete=True, models=results,
          prepared_sha256=sha(HERE/'prepared.json'), optimizer_updates=0, development_inference=0,
          fresh_inference_rows=sum(x['fresh_inference_rows'] for x in results.values())))
    print('EXTENDED_FIT_COLLECTED')


''' +s[b:]
save('collect.py',s)

s=source('verify.py').replace('OUT, BASE, DEV, c,', 'OUT, BASE, MODELS, SCHEDULE, c,')
a=s.index('def main():'); b=s.index("if __name__ == '__main__':",a)
body=s[a:b].replace("def main():\n    cutoff(); check(); assert not (HERE/'verified.json').exists(); report = read(HERE/'collected.json')", "def verify_one(arm, spec, report):\n    destination = OUT/arm")
body=body.replace('OUT/', 'destination/').replace('destination = destination/arm','destination = OUT/arm')
body=body.replace("arrays(BASE/'draws.npz')",'arrays(SCHEDULE)').replace('128000','1024000').replace('arrays(DEV)',"arrays(spec['development'])")
body=body.replace("    assert not set(raw['rep']", """    with np.load(c.SOURCE, allow_pickle=False) as original:
        for key in ('rep', 'tick', 'y_gate', 'y_card', 'y_xy', 'hand_card', 'split'):
            assert np.array_equal(raw[key], original[key]), key
    rng = np.random.default_rng(2026100609)
    assert d['rows'].shape == (8000, 128) and d['mirror'].shape == (8000,)
    for row, flag in zip(d['rows'], d['mirror']):
        assert np.array_equal(row, ids['train'][rng.choice(len(ids['train']), 128)])
        assert bool(flag) == bool(rng.random() < .5)
    assert not set(raw['rep']""")
body=body.replace("check(); write(HERE/'verified.json', dict(", 'check(); return dict(')
body=body.replace("collected_sha256=sha(HERE/'collected.json'),", "collected_sha256=sha(HERE/'collected.json'),")
body=body.replace("source_sha256=sha(HERE/'verify.py')))\n    print('TRAINING_FIT_VERIFIED')", "source_sha256=sha(HERE/'verify.py'))")
s=s[:a]+body+'''def main():
    cutoff(); check(); assert not (HERE/'verified.json').exists()
    report = read(HERE/'collected.json')
    assert report['complete'] and report['optimizer_updates'] == report['development_inference'] == 0
    assert report['prepared_sha256'] == sha(HERE/'prepared.json')
    assert set(report['models']) == set(MODELS)
    verified = {arm: verify_one(arm, spec, report['models'][arm]) for arm,spec in MODELS.items()}
    assert report['fresh_inference_rows'] == sum(x['fresh_inference_rows'] for x in verified.values())
    check(); write(HERE/'verified.json', dict(complete=True, models=verified,
        collected_sha256=sha(HERE/'collected.json'), fresh_inference_rows=report['fresh_inference_rows'],
        optimizer_updates=0, development_inference=0, accepted=False, deployed=False))
    print('EXTENDED_FIT_VERIFIED')


''' +s[b:]
save('verify.py',s)
s=source('run_chain.py').replace('TRAINING_FIT','EXTENDED_FIT').replace('l72-training-fit','l72-extended-fit')
save('run_chain.py',s)
save('launch.ps1',source('launch.ps1').replace('training_fit_audit','extended_fit_audit'))
print('Extended fit sources created, not executed.')
