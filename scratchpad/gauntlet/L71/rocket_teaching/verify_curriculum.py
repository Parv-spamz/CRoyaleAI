"""Independent row/count/split reconciliation plus real training smoke receipt."""
import json
from pathlib import Path
import sys
from collections import Counter, defaultdict
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from pipeline.rocket_teaching import sha

HERE = Path(__file__).resolve().parent
ART = ROOT/'icebow/data/bench/rocket_teaching_20261004'
DATA = ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'


def main():
    m = json.loads((ART/'manifest.json').read_text())
    assert m['trainable'] and m['public_only'] and m['expert_targets_unchanged']
    assert m['dataset_sha256'] == sha(DATA)
    assert m['cohorts_sha256'] == sha(ART/'cohorts.npz')
    assert m['annotator_sha256'] == sha(ROOT/'pipeline/rocket_teaching.py')
    with np.load(ART/'cohorts.npz') as z:
        c = {k: z[k] for k in z.files}
    with np.load(DATA) as z:
        meta = json.loads(str(z['meta']))
        v = {k: z[k] for k in ('split', 'rep', 'tags', 'tick', 'side', 'y_gate', 'y_card', 'deck_id')}
    pool = np.isin(v['deck_id'], [d['id'] for d in meta['decks'] if set(d['cards']) ==
                                 {'ice-wizard', 'knight', 'rocket', 'skeletons', 'tesla', 'the-log', 'tornado', 'x-bow'}])
    np.testing.assert_array_equal(c['pool'], pool)
    assert m['counts']['replays'] == len(np.unique(v['rep'][pool]))
    assert not set(v['rep'][pool & (v['split'] == 0)]) & set(v['rep'][pool & (v['split'] == 1)])
    for key, mask in c.items():
        assert mask.dtype == bool and len(mask) == m['rows'] and not (mask & ~pool).any()
        for name, code in [('train', 0), ('validation', 1)]:
            rows = mask & (v['split'] == code)
            actual = dict(rows=int(rows.sum()), pro_play=int((rows & (v['y_gate'] == 1)).sum()),
                          pro_wait=int((rows & (v['y_gate'] == 0)).sum()),
                          cards=dict(Counter(meta['card_vocab'][int(k)] for k in v['y_card'][rows & (v['y_gate'] == 1)])))
            assert actual == m['cohorts'][key][name]
    expected = {k: np.zeros(len(pool), bool) for k in ('sequence', 'combo', 'finish')}
    index = defaultdict(list)
    for i in np.flatnonzero(pool):
        index[(str(v['tags'][v['rep'][i]]), int(v['side'][i]))].append(i)
    labels = ROOT/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/labels.jsonl'
    assert sha(labels) == m['labels_sha256']
    for line in labels.open():
        e = json.loads(line)
        if e['card'] != 'rocket' or e.get('landing_tick') is None:
            continue
        ids = np.asarray(index.get((e['tag'], e['side']), []), dtype=int)
        ids = ids[(v['tick'][ids] >= e['tick'] - 40) & (v['tick'][ids] <= e['landing_tick'] + 20)]
        expected['sequence'][ids] = True
        if e['rocket_then_tornado']:
            expected['combo'][ids] = True
        if any(t['finish'] for t in e['tower_hits']):
            expected['finish'][ids] = True
    for k in expected:
        np.testing.assert_array_equal(expected[k], c[k])
    train = pool & (v['split'] == 0)
    p = np.zeros(len(pool))
    for mass, mask in ((.8, train), (.1, train & c['opportunity']), (.1, train & c['sequence'])):
        p[mask] += mass / mask.sum()
    assert abs(p.sum() - 1) < 1e-12 and p[v['split'] != 0].sum() == 0
    for k in c:
        assert abs(float(p[c[k]].sum()) - m['sampling_mass'][k]) < 1e-12
    smoke_dir = ROOT/'icebow/data/bench/rocket_teaching_smoke_train_20261004'
    smoke = json.loads((smoke_dir/'smoke.json').read_text())
    run = json.loads((smoke_dir/'run.json').read_text())
    assert smoke['status'] == 'ROCKET_TRAIN_SMOKE_PASS' and np.isfinite(smoke['loss'])
    assert smoke['deployment_evidence'] is False and not list(smoke_dir.glob('*.pt'))
    assert run['curriculum_sha256'] == sha(ART/'manifest.json')
    assert run['trainer_sha256'] == sha(ROOT/'pipeline/train_rocket_curriculum.py')
    before = json.loads((HERE.parent/'decision_options/before.json').read_text())
    for path, digest in before['protected_sha256'].items():
        assert sha(ROOT/path) == digest, path
    report = {k: v for k, v in m.items() if k != 'replay_evidence'}
    report.update(manifest_path=str(ART.relative_to(ROOT)), manifest_sha256=sha(ART/'manifest.json'),
                  smoke=smoke, smoke_run=run, checkpoint_trained=False, live_deployed=False,
                  expected_training_rocket_play_share=float(p[(v['y_gate'] == 1) &
                      (v['y_card'] == meta['card_vocab'].index('rocket'))].sum() / p[v['y_gate'] == 1].sum()),
                  uniform_rocket_play_share=float(((v['y_gate'] == 1) & train &
                      (v['y_card'] == meta['card_vocab'].index('rocket'))).sum() / ((v['y_gate'] == 1) & train).sum()))
    (HERE/'report.json').write_text(json.dumps(report, indent=2))
    print('ROCKET_CURRICULUM_VERIFIED')


if __name__ == '__main__':
    main()
