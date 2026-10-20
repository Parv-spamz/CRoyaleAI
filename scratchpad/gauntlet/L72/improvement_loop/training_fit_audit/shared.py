import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('fit_original_common', HERE.parent/'development_iteration_1/common.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
OUT = ROOT/'icebow/data/bench/training_fit_audit_20261006'
BASE = c.OUT
CKPT = BASE/'ordinary_v5/candidate_portable.pt'
DEV = BASE/'ordinary_v5_eval_v2/predictions.npz'


def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, d): p.write_text(json.dumps(d, allow_nan=False, separators=(',', ':'))+'\n', encoding='utf-8')
def arrays(p):
    with np.load(p, allow_pickle=False) as z: return {k: z[k] for k in z.files}
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def cutoff():
    assert datetime.datetime.now(datetime.timezone.utc) < datetime.datetime(2026, 10, 6, 13, tzinfo=datetime.timezone.utc), 'Owner cutoff'
def sources():
    paths = list((ROOT/'pipeline').glob('*.py')) + list(HERE.glob('*.py'))
    paths += [HERE/'PLAN.md', c.HERE/'common.py', c.HERE/'prepared.json', c.HERE/'verified.json',
              c.HERE/'ordinary_v5_portable.json', c.HERE/'results_verified_v2.json',
              HERE.parent/'development_rl_3/reviewed_results.json', CKPT, DEV, c.DATA,
              BASE/'indices.npz', BASE/'draws.npz']
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}
def check():
    p = read(HERE/'prepared.json'); assert p['complete'] and p['sources'] == sources(); return p
def labels(ids, sub, mirrored=False):
    xy = sub['y_xy'].copy()
    if mirrored: xy[:, 0] = 1-xy[:, 0]
    return dict(ids=ids, rep=sub['rep'], tick=sub['tick'], y_gate=sub['y_gate'], y_card=sub['y_card'], y_xy=xy, hand_card=sub['hand_card'])
def frequencies(ids):
    z = arrays(BASE/'draws.npz'); draws = z['rows']; mir = np.asarray(z['mirror'], bool)
    assert draws.shape == (1000, 128) and mir.shape == (1000,)
    pos = np.searchsorted(ids, draws); assert np.array_equal(ids[pos], draws)
    return [np.bincount(pos[mir == flag].reshape(-1), minlength=len(ids)) for flag in (False, True)]
def values(s, p):
    n = len(s['ids']); assert len(np.unique(s['ids'])) == n
    for key in ('gate', 'chosen_card', 'expert_cell'): assert len(p[key]) == n
    assert np.isfinite(p['gate']).all() and ((p['gate'] >= 0) & (p['gate'] <= 1)).all()
    assert p['allowed'].dtype == bool and p['allowed'].shape == (n, 4)
    assert ((p['expert_cell'] >= 0) & (p['expert_cell'] < 2304)).all()
    assert not np.isnan(p['card_logits']).any() and not np.isposinf(p['card_logits']).any()
    slot = np.where(p['allowed'], p['card_logits'], -np.inf).argmax(1)
    assert np.array_equal(p['chosen_card'], s['hand_card'][np.arange(n), slot])
    play = s['y_gate'] == 1; has = p['allowed'].any(1); called = (p['gate'] > .35) & has
    card = (p['chosen_card'] == s['y_card']) & has
    xy = np.c_[p['expert_cell'] % 36 / 36, p['expert_cell'] // 36 / 64]
    distance = np.linalg.norm((xy-s['y_xy'])*[18, 32], axis=1); aim = distance <= 1
    success = play & called & card & aim
    return dict(play=play, wait_correct=~play & ~called, called=called, card=play & card,
                aim1=play & aim, play_success=success, action=success | (~play & ~called),
                gate_failure=play & ~called, card_failure=play & called & ~card,
                aim_failure=play & called & card & ~aim, distance=distance)
def summarize(s, p, weights, cv):
    v = values(s, p); present = weights > 0; play = s['y_gate'] == 1
    rocket = play & (s['y_card'] == cv.index('rocket'))
    groups = dict(all=np.ones(len(play), bool), play=play, rocket=rocket, late_rocket=rocket & (s['tick'] >= 4800))
    groups.update({'card/'+cv[int(k)]: play & (s['y_card'] == k) for k in np.unique(s['y_card'][play])})
    result = {}
    for key, m in groups.items():
        mask = m & present; w = np.where(mask, weights, 0)
        counts = {k: int(np.dot(w, val.astype(np.int64))) for k, val in v.items() if k != 'distance'}
        replays = {}
        reps, inverse = np.unique(s['rep'][mask], return_inverse=True)
        columns = dict(views=np.bincount(inverse, minlength=len(reps)),
                       weight=np.bincount(inverse, weights=weights[mask], minlength=len(reps)))
        for k, val in v.items():
            if k != 'distance': columns[k] = np.bincount(inverse, weights=weights[mask]*val[mask], minlength=len(reps))
        for i, rep in enumerate(reps):
            replays[str(int(rep))] = {k: int(val[i]) for k, val in columns.items()}
        result[key] = dict(views=int(mask.sum()), weight=int(w.sum()), replays=len(replays), **counts, by_replay=replays)
    return result
