"""Calibration v2: timing term + intercept recalibration of the phase-2 press models.

Run:  icebow/.venv/Scripts/python.exe calibration_v2.py [--cv]
Writes ability_models_v2.json and CALIBRATION_V2.md (v1 files are never touched).

Labels (A): native_targets_2326 first-press ticks, joined to the phase-2 frame
sequences by (ability, replay tag, side, play_index). Fallback abilities (hero
Goblins, hero Tombstone: native linkage 388 / 36 of ~2.7k deployments) keep the
phase-1 share target (abilities.json) and use phase-2 context press ticks as the
shape labels. Model (B): v1 standardized features (age column dropped) + piecewise
linear timing term in seconds-since-deploy + intercept. Discrete-time survival MLE:
frame f covers [t_f, t_f+dt_f), p = sigmoid(score) is the v1 1-second probability and
h = 1-(1-p)**dt_f (the v1 cadence convention). The knot values are then moved by a
damped fixed point until the model's first-press mass per age bin equals the pro mass
(share and first-delay distribution together). Shares/delays are computed
analytically from h (no RNG), so held-out numbers carry no simulation noise.
Split: the phase-2 replay split (test 20% = held out, validation 16% for the ridge
choice only). Both sides of a replay stay together because the split is by replay.
Recordings snapshot at the press tick, so a fired frame's delay is that frame's age.
"""
import os
for _n in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_n] = '1'
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from ability_policy import FEATURE_NAMES, sigmoid
from calibration import model_scores

HERE = Path(__file__).resolve().parent
KNOTS = [1, 2, 3, 4, 6, 8, 10, 12, 15, 18, 22, 28, 40]  # seconds since deploy; flat outside
FALLBACK = {'goblins-hero', 'tombstone-hero'}  # native linkage unreliable (report.json limitations)
RIDGES = (.03, .3, 3., 30.)
COOLDOWN_S = 3.0  # boss-bandit proxy cooldown, 60 ticks as in calibration.py


def hat(age, knots=KNOTS):
    """Piecewise-linear basis, columns for knots[1:] (knot 0's value is the intercept)."""
    age = np.clip(age, knots[0], knots[-1])
    return np.stack([np.interp(age, knots, np.eye(len(knots))[k]) for k in range(1, len(knots))], 1)


def softplus(s):
    return np.log1p(np.exp(-np.abs(s))) + np.maximum(s, 0)


def hazard(score, dt):
    return -np.expm1(-dt * softplus(score))  # == 1-(1-sigmoid(s))**dt


# ---------------------------------------------------------------- data
def load_ability(ab, inv, deps, native, phase1=None):
    reps = inv['replays']
    test = set(inv['test_replay_ids']); val = set(inv['validation_replay_ids'])
    z = np.load(HERE / f'phase2_data_{ab}.npz')
    order = np.lexsort((z['tick'], z['deployment']))
    X, dep, tick = (z[k][order] for k in ('X', 'deployment', 'tick'))
    X = X.astype(float)
    D = {d['id']: d for d in deps[ab]}
    ids, first, counts = np.unique(dep, return_index=True, return_counts=True)
    keep, press1, press2, start, drep = [], [], [], [], []
    for di, f0, c in zip(ids, first, counts):
        d = D[int(di)]
        if d['censored']:
            continue
        if ab in FALLBACK:
            pt = d['context_press_ticks']
        else:
            n = native.get((ab, reps[d['replay']], d['side'], d['play_index']))
            if n is None or n['status'] != 'LINKED':
                continue
            pt = n['press_ticks']
        keep.append((f0, c)); start.append(d['tick']); drep.append(d['replay'])
        press1.append(pt[0] if pt else -1); press2.append(pt[1] if len(pt) > 1 else -1)
    rows = np.concatenate([np.arange(f0, f0 + c) for f0, c in keep])
    g = np.repeat(np.arange(len(keep)), [c for _, c in keep])
    X, tick = X[rows], tick[rows]
    nxt = np.r_[tick[1:], 0]
    last = np.r_[g[1:] != g[:-1], True]
    dt = np.where(last, 1., np.clip((nxt - tick) / 20., .05, 1.))
    start = np.asarray(start); press1 = np.asarray(press1); press2 = np.asarray(press2); drep = np.asarray(drep)
    # fire frame: last frame with tick <= press (first frame if the press precedes all frames)
    first_row = np.r_[0, np.flatnonzero(last)[:-1] + 1]
    last_row = np.flatnonzero(last)
    fire_row = np.full(len(keep), -1)
    for i in np.flatnonzero(press1 >= 0):
        r = np.arange(first_row[i], last_row[i] + 1)
        ok = r[tick[r] <= press1[i]]
        fire_row[i] = ok[-1] if len(ok) else r[0]
    # Presses later than the last recorded frame's 1 s window are right-censored: the phase-2 board
    # recordings end (unit dead without ability effects) before the native press, so no frame policy can
    # reproduce them. They stay in 'pressed_all' (pro share) but not in the fit/evaluation target.
    pressed_all = press1 >= 0
    unreach = pressed_all & (press1 > tick[last_row] + 20)
    pressed = pressed_all & ~unreach
    atrisk = ~pressed[g] | (np.arange(len(tick)) <= fire_row[g])
    y = np.zeros(len(tick)); y[fire_row[pressed]] = 1
    # 1-second horizon label for AUC: first press within [tick, tick+20] (at-risk frames only)
    y1 = ((press1[g] >= tick) & (press1[g] <= tick + 20)).astype(float)
    age = X[:, 0]
    delay = np.where(pressed, (press1 - start) / 20., np.nan)
    fire_age = np.where(pressed, (tick[np.maximum(fire_row, 0)] - start) / 20., np.nan)  # what a frame policy can reproduce
    return dict(ab=ab, X=X, g=g, tick=tick, dt=dt, y=y, y1=y1, atrisk=atrisk, age=age,
                pressed=pressed, pressed_all=pressed_all, delay=delay, fire_age=fire_age, start=start,
                rep=drep[g], drep=drep, press1=press1, press2=press2,
                is_test=np.isin(drep, list(test)), is_val=np.isin(drep, list(val)), n=len(keep), last=last)


def subset(d, dmask):
    """Restrict to deployments where dmask is True (re-index)."""
    rm = dmask[d['g']]
    out = dict(d)
    remap = np.cumsum(dmask) - 1
    for k in ('X', 'tick', 'dt', 'y', 'y1', 'atrisk', 'age', 'rep', 'last'):
        out[k] = d[k][rm]
    out['g'] = remap[d['g'][rm]]
    for k in ('pressed', 'pressed_all', 'delay', 'fire_age', 'start', 'drep', 'press1', 'press2', 'is_test', 'is_val'):
        out[k] = d[k][dmask]
    out['n'] = int(dmask.sum())
    return out


# ---------------------------------------------------------------- model scores
def v2_scores(model, X):
    if model['type'] == 'gbt_timing':  # frozen v1 trees (scaled) + timing + intercept
        s = model['intercept'] + model['trees_scale'] * model_scores(dict(model, type='gradient_boosted_trees', intercept=0.), X)
    else:
        z = (X - np.asarray(model['mean'])) / np.asarray(model['scale'])
        s = model['intercept'] + z @ np.asarray(model['coefficients'])
    t = model.get('timing')
    if t:
        s = s + np.interp(X[:, 0], t['knots'], t['values'])
    return s


# ---------------------------------------------------------------- analytic outcomes
def _spans(g):
    b = np.r_[0, np.flatnonzero(g[1:] != g[:-1]) + 1, len(g)]
    return zip(b[:-1], b[1:])


def outcomes(d, score, second_offset=None):
    """Analytic share, first-delay mixture and (optionally) repeat share."""
    h = hazard(score, d['dt'])
    lg = np.log1p(-np.minimum(h, 1 - 1e-12))
    g = d['g']
    cum = np.cumsum(lg); base = np.r_[0., cum][np.r_[0, np.flatnonzero(g[1:] != g[:-1]) + 1]]
    cs = cum - base[g]                       # log survival through frame (inclusive)
    mass = np.exp(cs - lg) * h               # P(first fires in this frame)
    share_i = np.bincount(g, mass, minlength=d['n'])
    res = dict(share=float(share_i.mean()), share_i=share_i)
    # Recordings snapshot at the press tick, so a fired frame's delay is that frame's age (point mass).
    res['delay_cdf'] = ((d['tick'] - d['start'][g]) / 20., mass)
    if second_offset is not None:
        h2 = hazard(score + second_offset, d['dt'])
        lg2 = np.log1p(-np.minimum(h2, 1 - 1e-12))
        rep_i = np.zeros(d['n'])
        for i, (lo, hi) in enumerate(_spans(g)):
            t = d['tick'][lo:hi]; m = mass[lo:hi]
            c2 = np.r_[0., np.cumsum(lg2[lo:hi])]
            j = np.searchsorted(t, t + 20 * COOLDOWN_S)  # first frame allowed for a 2nd press
            rep_i[i] = np.sum(m * (-np.expm1(c2[-1] - c2[j])))
        res['repeat_share'] = float(rep_i.mean())
    return res


def model_quantiles(res, qs=(.1, .25, .5, .75, .9)):
    """Smallest delay whose cumulative first-press mass reaches q (same convention as pro_quantiles)."""
    a, m = res['delay_cdf']
    o = np.argsort(a, kind='stable')
    cdf = np.cumsum(m[o]) / m.sum()
    return [float(a[o][min(np.searchsorted(cdf, q - 1e-12), len(cdf) - 1)]) for q in qs]


def pro_quantiles(delays, qs=(.1, .25, .5, .75, .9)):
    v = delays[np.isfinite(delays)]
    return [float(np.quantile(v, q, method='inverted_cdf')) for q in qs] if len(v) else [None] * len(qs)


def auc(score, y):
    pos = y == 1
    n1, n0 = pos.sum(), (~pos).sum()
    if n1 == 0 or n0 == 0:
        return None
    _, inv, cnt = np.unique(score, return_inverse=True, return_counts=True)
    rank = (np.cumsum(cnt) - (cnt - 1) / 2.)[inv]
    return float((rank[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


# ---------------------------------------------------------------- fitting
def design(X, v1):
    if v1['type'] == 'gradient_boosted_trees':  # trees stay frozen; only their scale is refit
        base = model_scores(v1, X) - v1['intercept']
        return np.column_stack([np.ones(len(X)), base, hat(X[:, 0])])
    z = (X - np.asarray(v1['mean'])) / np.asarray(v1['scale'])
    return np.column_stack([np.ones(len(X)), z[:, 1:], hat(X[:, 0])])  # age handled by timing term


def nll_grad_hess(theta, D, dt, y, P):
    s = D @ theta
    p = sigmoid(s); u = np.maximum(dt * softplus(s), 1e-12)
    dp = dt * p
    l = np.where(y == 1, -np.log(-np.expm1(-u)), u)
    lu = np.where(y == 1, -1. / np.expm1(u), 1.)
    luu = np.where(y == 1, np.exp(np.minimum(u, 50)) / np.expm1(u) ** 2, 0.)
    g1 = lu * dp
    h1 = np.maximum(luu * dp ** 2 + np.where(y == 1, 0., dt * p * (1 - p)), 1e-9)  # Gauss-Newton curvature
    f = l.sum() + .5 * theta @ (P @ theta)
    return f, D.T @ g1 + P @ theta, (D * h1[:, None]).T @ D + P


def penalty(ridge, nfeat, K):
    """Unpenalized intercept; ridge on feature weights; 2nd-difference smoothing on timing."""
    n = 1 + nfeat + K
    P = np.zeros((n, n))
    P[1:1 + nfeat, 1:1 + nfeat] = np.eye(nfeat) * ridge
    Dm = np.diff(np.eye(K + 1), 2, axis=0)[:, 1:]  # knot-1 value is fixed at 0
    P[1 + nfeat:, 1 + nfeat:] = ridge * 3. * Dm.T @ Dm + 1e-6 * np.eye(K)
    return P


def fit_logistic_timing(D, dt, y, ridge, nfeat, iters=60):
    K = D.shape[1] - 1 - nfeat
    P = penalty(ridge, nfeat, K)
    theta = np.zeros(D.shape[1])
    theta[0] = np.log(max(y.sum(), 1) / max(dt.sum(), 1))  # rough hazard-rate start
    f, grad, hess = nll_grad_hess(theta, D, dt, y, P)
    for _ in range(iters):
        step = np.linalg.solve(hess + 1e-8 * np.eye(len(theta)), grad)
        t = 1.
        while t > 1e-6:
            f2, g2, h2 = nll_grad_hess(theta - t * step, D, dt, y, P)
            if f2 < f - 1e-12 * abs(f):
                break
            t /= 2
        else:
            break
        theta, dec = theta - t * step, f - f2
        f, grad, hess = f2, g2, h2
        if dec < 1e-9 * abs(f):
            break
    return theta, f


def to_model(v1, theta):
    gbt = v1['type'] == 'gradient_boosted_trees'
    nfeat = 1 if gbt else len(FEATURE_NAMES) - 1
    vals = np.r_[0., theta[1 + nfeat:]]
    timing = dict(knots=KNOTS, values=[float(v) for v in vals])
    if gbt:
        return dict(v1, type='gbt_timing', intercept=float(theta[0]), trees_scale=float(theta[1]), timing=timing)
    return dict(type='logistic_timing', mean=v1['mean'], scale=v1['scale'], intercept=float(theta[0]),
                coefficients=[0.] + [float(c) for c in theta[1:1 + nfeat]], timing=timing)


def bisect_offset(fn, target, lo=-8., hi=8.):
    for _ in range(50):
        mid = (lo + hi) / 2
        if fn(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def match_marginal(model, d, share_scale=1., iters=60, eta=.8):
    """Timing recalibration: move the knot values (knot 1 = intercept) until the model's first-press
    mass per hat-bin of age equals the observed first-press mass per bin on the fit replays (so both the
    pressed share and the first-delay distribution are reproduced). Fixed point on log-ratios, damped,
    with a half-count pseudo-count so empty bins stay finite. share_scale rescales the observed mass
    (used only by the phase-1 fallback abilities: shape from labels, level from phase-1 share)."""
    K = len(KNOTS)
    full = lambda a: np.stack([np.interp(np.clip(a, KNOTS[0], KNOTS[-1]), KNOTS, np.eye(K)[k]) for k in range(K)], 1)
    obs = full(d['fire_age'][d['pressed']]).sum(0) * share_scale
    W = full((d['tick'] - d['start'][d['g']]) / 20.)
    model = dict(model, timing=dict(model['timing']))
    for _ in range(iters):
        m = outcomes(d, v2_scores(model, d['X']))['delay_cdf'][1] @ W
        step = np.clip(np.log((obs + .5) / (m + .5)), -.7, .7)
        if np.abs(step[obs > 5]).max() < .01:
            break
        p = model['intercept'] + np.asarray(model['timing']['values']) + eta * step
        model['intercept'] = float(p[0])
        model['timing']['values'] = [float(v) for v in p - p[0]]
    return model


def calibrate_ability(ab, data, v1, phase1_share=None):
    train = subset(data, ~data['is_test'])
    inner_tr = subset(data, ~data['is_test'] & ~data['is_val'])
    val = subset(data, data['is_val'])
    nfeat = 1 if v1['type'] == 'gradient_boosted_trees' else len(FEATURE_NAMES) - 1

    def dsn(d):
        m = d['atrisk']
        return design(d['X'][m], v1), d['dt'][m], d['y'][m]

    # ridge choice on validation replays (frame NLL of at-risk frames)
    Dtr, dttr, ytr = dsn(inner_tr); Dv, dtv, yv = dsn(val)
    best = None
    for r in RIDGES:
        th, _ = fit_logistic_timing(Dtr, dttr, ytr, r, nfeat)
        f, *_ = nll_grad_hess(th, Dv, dtv, yv, np.zeros((len(th), len(th))))
        if best is None or f < best[0]:
            best = (f, r)
    ridge = best[1]
    Dt, dtt, yt = dsn(train)
    theta, _ = fit_logistic_timing(Dt, dtt, yt, ridge, nfeat)
    model = to_model(v1, theta)
    reach = float(train['pressed'].mean() / max(train['pressed_all'].mean(), 1e-9))
    target = phase1_share * reach if ab in FALLBACK else float(train['pressed'].mean())
    raw_share = outcomes(train, v2_scores(model, train['X']))['share']
    off = bisect_offset(lambda o: outcomes(train, v2_scores(model, train['X']) + o)['share'], target)
    model['intercept'] += off
    model = match_marginal(model, train, target / max(train['pressed'].mean(), 1e-9))
    model['ridge'] = ridge
    if ab == 'boss-bandit':  # second charge: offset on top of the same policy, matched to train repeat share
        tgt2 = float((train['press2'] >= 0).mean())
        sc = v2_scores(model, train['X'])
        model['second_charge_offset'] = bisect_offset(lambda o: outcomes(train, sc, o)['repeat_share'], tgt2, -10, 10)
    return model, dict(ridge=ridge, train_pro_share=float(train['pressed'].mean()),
                       train_pro_share_all=float(train['pressed_all'].mean()), mle_share_before_offset=raw_share,
                       offset=off, target_train_share=target, n_train=train['n'])


# ---------------------------------------------------------------- evaluation
def boot(d, reps=300):
    """Replay-cluster bootstrap SE of the pro share and pro median delay."""
    rng = np.random.default_rng(20261004)
    cl = [np.flatnonzero(d['drep'] == r) for r in np.unique(d['drep'])]
    sh, md = [], []
    for _ in range(reps):
        ix = np.concatenate([cl[i] for i in rng.integers(len(cl), size=len(cl))])
        sh.append(d['pressed'][ix].mean())
        v = d['delay'][ix]; v = v[np.isfinite(v)]
        if len(v):
            md.append(np.median(v))
    return float(np.std(sh)), float(np.std(md)) if md else None


def evaluate(ab, data, v1, v2, test=True):
    hold = subset(data, data['is_test'] if test else ~data['is_test'])
    s1, s2 = model_scores(v1, hold['X']), v2_scores(v2, hold['X'])
    o1, o2 = outcomes(hold, s1), outcomes(hold, s2, v2.get('second_charge_offset'))
    q_pro, q1, q2 = pro_quantiles(hold['delay']), model_quantiles(o1), model_quantiles(o2)
    m = hold['atrisk']
    se_share, se_med = boot(hold)
    res = dict(n_deployments=hold['n'], n_pressed=int(hold['pressed'].sum()),
               pro_share=float(hold['pressed'].mean()), pro_share_all=float(hold['pressed_all'].mean()),
               pro_share_se=se_share, pro_median_se=se_med, v1_share=o1['share'], v2_share=o2['share'],
               pro_q=q_pro, v1_q=q1, v2_q=q2,
               auc_v1=auc(s1[m], hold['y1'][m]), auc_v2=auc(s2[m], hold['y1'][m]),
               n_frames=int(m.sum()), n_pos_frames=int(hold['y1'][m].sum()))
    if ab == 'boss-bandit':
        res['pro_repeat_share'] = float((hold['press2'] >= 0).mean()); res['v2_repeat_share'] = o2['repeat_share']
    return res


def cross_val(ab, data, v1, share1, folds=5):
    """Secondary: 5-fold replay-cluster CV over ALL replays (every deployment is scored by a model
    that never saw its replay); per-fold share errors are the same size as the 20% held-out split."""
    fold = np.array([int.from_bytes(hashlib.sha256(f'cv:{r}'.encode()).digest()[:4], 'little') % folds
                     for r in range(int(data['drep'].max()) + 1)])[data['drep']]
    shares = np.zeros(data['n']); err = []
    for k in range(folds):
        d = dict(data, is_test=fold == k, is_val=data['is_val'] & (fold != k))
        model, _ = calibrate_ability(ab, d, v1, share1)
        te = subset(d, d['is_test'])
        shares[d['is_test']] = outcomes(te, v2_scores(model, te['X']))['share_i']
        err.append(100 * (shares[d['is_test']].mean() - te['pressed'].mean()))
    return dict(cv_share=float(shares.mean()), cv_pro_share=float(data['pressed'].mean()),
                cv_fold_err_pp=[float(e) for e in err], cv_n=int(data['n']))


def write_md(out):
    cal = out['calibration']
    rel = [a for a, c in cal.items() if c['reliable']]
    err = {a: 100 * (c['heldout']['v2_share'] - c['heldout']['pro_share']) for a, c in cal.items()}
    over = {a: round(err[a], 1) for a in rel if abs(err[a]) > 3}
    z_over = {a: round(abs(err[a]) / (100 * cal[a]['heldout']['pro_share_se']), 1) for a in over}
    med_ok = [a for a in rel if abs(cal[a]['heldout']['v2_q'][2] - cal[a]['heldout']['pro_q'][2]) <= max(cal[a]['heldout']['pro_median_se'], .25)]
    auc_drop = {a: round(cal[a]['heldout']['auc_v2'] - cal[a]['heldout']['auc_v1'], 3) for a in cal
                if cal[a]['heldout']['auc_v2'] - cal[a]['heldout']['auc_v1'] < -.01}
    fit_err = max(abs(cal[a]['fit']['v2_share'] - cal[a]['fit']['pro_share']) for a in rel) * 100
    fit_med = max(abs(cal[a]['fit']['v2_q'][2] - cal[a]['fit']['pro_q'][2]) for a in rel)
    fit_off = {a: round(100 * (cal[a]['fit']['v2_share'] - cal[a]['fit']['pro_share']), 1) for a in rel if abs(cal[a]['fit']['v2_share'] - cal[a]['fit']['pro_share']) > .005}
    v1_err = [100 * (cal[a]['heldout']['v1_share'] - cal[a]['heldout']['pro_share']) for a in rel]
    rows = []
    for ab, c in cal.items():
        h = c['heldout']; q, m, q1 = h['pro_q'], h['v2_q'], h['v1_q']
        cv = c.get('cv')
        rms = f"{np.sqrt(np.mean(np.square(cv['cv_fold_err_pp']))):.1f}" if cv else 'n/a'
        rows.append(f"| {ab}{'' if c['reliable'] else ' (fallback)'} | {h['n_deployments']} | {100*h['pro_share_all']:.1f} / {100*h['pro_share']:.1f} | "
                    f"{100*h['v1_share']:.1f} | {100*h['v2_share']:.1f} | {err[ab]:+.1f} | "
                    f"{m[2]-q[2]:+.2f} (se {h['pro_median_se']:.2f}; v1 {q1[2]-q[2]:+.2f}) | {(m[3]-m[1])-(q[3]-q[1]):+.1f} | "
                    f"{h['auc_v1']:.3f} -> {h['auc_v2']:.3f} | {rms} |")
    bb = cal['boss-bandit']['heldout']
    md = f"""# Ability press policy v2: timing term + calibration

`ability_models_v2.json` (v1 untouched; `predict(ab, x, version='v2')`). Fit script `calibration_v2.py`. Labels = native_targets_2326 first presses joined to the phase-2 frame sequences by tag/side/play_index; 80% of replays fit, 20% held out by replay (the phase-2 split).
Model: v1 standardized features + piecewise-linear timing term in seconds-since-deploy (13 knots, 1-40 s) + intercept, discrete-time survival MLE; then the knot values are moved by fixed point until the model's first-press mass per age bin equals the pro mass on the fit replays, so share and first-delay distribution match together. The two GBT abilities keep their v1 trees (one scale + timing + intercept). Boss Bandit's second charge adds `second_charge_offset`: held-out repeat share model {100*bb['v2_repeat_share']:.1f}% vs pro {100*bb['pro_repeat_share']:.1f}% (n={bb['n_deployments']}). Shares and delays are analytic over the recorded frames (no RNG).

Held-out (20% of replays), shares in %. "pro all / reach": native linked share / share whose press falls inside the recorded frames (1-4% of presses come after the phase-2 recording ends and no frame policy can reproduce them; they are censored in the fit and the error is against "reach"). Delay errors are model minus pro in seconds (se = replay-cluster bootstrap SE of the pro median); IQR error = model IQR width minus pro. 5-fold RMS = RMS of the share error over 5 replay folds (pp).

| Ability | n | pro all / reach | v1 | v2 | err pp | median err s | IQR err s | AUC v1 -> v2 | 5-fold RMS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
""" + "\n".join(rows) + f"""

Fallback (hero Goblins 388/2,842 linked, hero Tombstone 36/2,641): shape from phase-2 context presses, level set to the phase-1 share (26.5% / 20.1%, abilities.md); their "pro" column is the phase-2 context share, not their target, so Tombstone's {err['tombstone-hero']:+.1f} pp is the phase-1 vs phase-2 disagreement (20.1% vs 10.2%), not a fit error.

Findings
- v1 over-presses the held-out frames by {min(v1_err):.0f} to {max(v1_err):.0f} pp; v2 fit-set share error is at most {fit_err:.1f} pp and fit-set median delay error at most {fit_med:.2f} s (reliable abilities). Fit-set share not matched to within 0.5 pp: {fit_off} (archer-queen's late presses fall where few recorded frames survive, so the late age bins cannot be filled).
- Held-out share error is within 3 pp for {len(rel)-len(over)} of {len(rel)} reliable abilities. Above 3 pp: {over}. Their error in held-out share standard errors (replay-cluster bootstrap) is {z_over}: small samples, listed rather than hidden.
- Held-out median delay is within max(1 SE, 0.25 s) for {len(med_ok)} of {len(rel)}.
- AUC (native 1 s press label) fell by more than 0.01 for {auc_drop}: matching the delay marginal costs some ranking inside the unit's life.
- Native acceptances are re-drive timing, not human timing; board frames omit ability effects (NATIVE_TARGETS_REPORT.md).
"""
    (HERE / 'CALIBRATION_V2.md').write_text(md, encoding='utf8')


def main(cv=False):
    inv = json.loads((HERE / 'phase2_inventory.json').read_text())
    deps = json.loads((HERE / 'phase2_deployments.json').read_text())
    bundle = json.loads((HERE / 'ability_models.json').read_text())
    p1 = json.loads((HERE / 'abilities.json').read_text())['abilities']
    nrep = json.loads((HERE / 'native_targets_2326/report.json').read_text())['abilities']
    native = {}
    for line in (HERE / 'native_targets_2326/deployments.jsonl').open():
        r = json.loads(line)
        native[r['ability'], r['tag'], r['side'], r['play_index']] = r
    out = dict(schema='ability_press_policy_v2', feature_names=FEATURE_NAMES, horizon_seconds=1.0, tick_rate=20,
               distance_units=bundle['distance_units'],
               availability=bundle['availability'] + '; boss-bandit second charge adds second_charge_offset to the score',
               training_target='native_targets_2326 first-press ticks (fallback abilities: phase-2 context presses, phase-1 share)',
               split='phase-2 replay split: 20% test replays held out, 16% validation (ridge choice only)',
               timing='score += interp(seconds_since_deploy, timing.knots, timing.values); coefficients[0] is 0',
               models={}, calibration={})
    for ab in bundle['models']:
        v1 = bundle['models'][ab]
        data = load_ability(ab, inv, deps, native)
        dist = p1[ab]['deployment_press_distribution']
        share1 = 1 - dist['counts']['0'] / dist['n']
        model, info = calibrate_ability(ab, data, v1, share1)
        ev = dict(heldout=evaluate(ab, data, v1, model), fit=evaluate(ab, data, v1, model, test=False))
        reliable = ab not in FALLBACK
        model.update(reliable_native_targets=reliable, fallback='phase1_share_delay' if not reliable else None)
        ev.update(info, reliable=reliable, report_share=nrep[ab]['pressed_share'] if reliable else None,
                  report_linked=nrep[ab]['linked_deployments'], phase1_share=share1,
                  phase1_q=[p1[ab]['first_press_delay_seconds'].get(k) for k in ('p10', 'p25', 'p50', 'p75', 'p90')])
        if cv and reliable:
            ev['cv'] = cross_val(ab, data, v1, share1)
        out['models'][ab] = model; out['calibration'][ab] = ev
        h, f = ev['heldout'], ev['fit']
        print(f"{ab:22s} n={h['n_deployments']:5d} pro={h['pro_share']:.3f}+-{h['pro_share_se']:.3f} v1={h['v1_share']:.3f} v2={h['v2_share']:.3f} "
              f"(fit {f['pro_share']:.3f}/{f['v2_share']:.3f}) med pro/v2 {h['pro_q'][2]}/{h['v2_q'][2]:.2f} "
              f"auc {h['auc_v1']:.3f}->{h['auc_v2']:.3f} ridge={info['ridge']}", flush=True)
    (HERE / 'ability_models_v2.json').write_text(json.dumps(out, indent=1, allow_nan=False) + '\n', encoding='utf8')
    write_md(out)
    print('V2_WRITTEN', len(out['models']))


if __name__ == '__main__':
    if '--md' in sys.argv:  # regenerate CALIBRATION_V2.md from the stored json
        o = json.loads((HERE / 'ability_models_v2.json').read_text(encoding='utf8')); write_md(o)
    else:
        main(cv='--cv' in sys.argv)
