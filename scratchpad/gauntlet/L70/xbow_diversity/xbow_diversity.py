"""X-Bow placement diversity diagnosis (L70). CPU only, read-only on pipeline/*.py, no training.

H1 argmax collapse (model's own cell distribution is spread over pro-like lock-on cells, argmax picks 1-2)
H2 model concentrated (low entropy / mass on 1-2 cells)
H3 pro placement depends on PUBLIC context (enemy defensive buildings, tower HP, lane, phase) -> not random

run: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L70/xbow_diversity/xbow_diversity.py
out: results.json next to this file (REPORT.md is written by hand from it).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
torch.set_num_threads(4)

from pipeline import vocab                                    # noqa: E402
from pipeline.eval_gen import GenRows, load_model             # noqa: E402  (imported as-is)

NPZ = REPO / "icebow/data/pipeline/gen_dataset_v3.npz"
CKPTS = {"gen_v3_s0": REPO / "icebow/data/pipeline/gen_v3_s0/gen_s0.pt",
         "live_u0155": REPO / "icebow/data/bench/rl_royale/rseries_r1/rseries_r1_u0155.pt"}
GX, GY = 36, 64
RNG = np.random.default_rng(0)
B_BOOT = 1000

# ---- geometry (tiles; obs_contract.py:28-34, cards.json: Xbow range 11.5, PrincessTower r 1.0, KingTower r 1.4) ----
TOWERS = np.array([[9.0, 3.0, 1.4], [3.5, 6.5, 1.0], [14.5, 6.5, 1.0]])   # opp K, L, R in MY frame (me at bottom)
XBOW_RANGE = 11.5
LAX = 1.0        # tap -> building slack, see report: strict rule admits only a few % of the pro cells
DEF_IDS = {vocab.UNIT_VOCAB.index(n) for n in ("tesla", "tesla_evo", "cannon", "cannon_evo", "inferno_tower", "bomb_tower")}
BUILD_IDS = {i for i, n in enumerate(vocab.UNIT_VOCAB) if n in vocab.BUILDING_CLASSES}

CX = np.tile(np.arange(GX), GY)
CY = np.repeat(np.arange(GY), GX)
CELL_TX, CELL_TY = CX / 2.0, CY / 2.0            # lattice: cell (cx, cy) -> tile (cx/2, cy/2)


def in_range_mask(alive, slack):
    """alive bool[n,3] (opp K,L,R) -> bool[n, 2304]: cell centre within range(+slack) of an alive enemy tower, own half."""
    d = np.hypot(CELL_TX[None, :, None] - TOWERS[None, None, :, 0], CELL_TY[None, :, None] - TOWERS[None, None, :, 1])
    ok = (d - TOWERS[None, None, :, 2] <= XBOW_RANGE + slack) & alive[:, None, :]
    return ok.any(-1) & (CY[None, :] > GY // 2)


def boot_mean(v, rep, B=B_BOOT):
    """mean + replay-cluster bootstrap 95% CI."""
    v = np.asarray(v, float)
    u, inv = np.unique(rep, return_inverse=True)
    s, c = np.bincount(inv, v, len(u)), np.bincount(inv, minlength=len(u)).astype(float)
    ix = RNG.integers(0, len(u), (B, len(u)))
    m = s[ix].sum(1) / c[ix].sum(1)
    return [float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


# ======================================================================================= load
z = np.load(NPZ, allow_pickle=False)
meta = json.loads(str(z["meta"]))
XB = meta["card_vocab"].index("x-bow")
sel = np.where((z["y_gate"][:] == 1) & (z["y_card"][:] == XB))[0]
off = z["off"]
per_row_keys = ["sc", "hand_card", "hand_form", "next_card", "next_form", "deck_card", "deck_form", "past", "y_gate", "y_card",
                "y_hand_pos", "y_xy", "y_wait_card", "y_wait_dt", "y_crowns", "tick", "side", "rep", "split", "deck_id", "v3val",
                "opp_past", "y_cell"]
sub = {k: z[k][sel] for k in per_row_keys}
tok_all, uf_all = z["tok"], z["unit_form"]
lens = off[sel + 1] - off[sel]
off_sub = np.concatenate([[0], np.cumsum(lens)])
gather = np.concatenate([np.arange(off[i], off[i + 1]) for i in sel])
sub["tok"], sub["unit_form"], sub["off"] = tok_all[gather], uf_all[gather], off_sub
n_all = len(sel)
del tok_all, uf_all

xy, sc, cell, split, rep = sub["y_xy"], sub["sc"], sub["y_cell"].astype(int), sub["split"], sub["rep"]
cx_p, cy_p = cell % GX, cell // GX
tile_p = np.stack([cx_p / 2.0, cy_p / 2.0], 1)
hp = np.where(sc[:, 52 + 3:52 + 6] > 0, sc[:, 52 + 3:52 + 6], 0.0)               # opp K, L, R hp frac
alive_known = sc[:, 64 + 3:64 + 6] > 0.5
alive = alive_known & (hp > 0)
alive_unk = alive_known                                                        # for reporting only
dist_edge = np.hypot(tile_p[:, 0, None] - TOWERS[None, :, 0], tile_p[:, 1, None] - TOWERS[None, :, 1]) - TOWERS[None, :, 2]
in_strict = ((dist_edge <= XBOW_RANGE) & alive).any(1)
in_lax = ((dist_edge <= XBOW_RANGE + LAX) & alive).any(1)
own_half = cy_p > GY // 2
off_strict, off_lax = in_strict & own_half, in_lax & own_half
R = {"data": {"npz": str(NPZ.relative_to(REPO)), "n_xbow_plays_all": int(n_all), "replays_all": int(len(set(rep))),
              "n_val": int((split == 1).sum()), "replays_val": int(len(set(rep[split == 1]))),
              "n_train": int((split == 0).sum()), "replays_train": int(len(set(rep[split == 0])))}}
R["rule"] = {"text": ("offensive = pro tap cell on own half (y>0.5) AND an ALIVE enemy tower (hp>0 and alive flag in sc) with "
                      "hypot(cell centre - tower centre) - tower radius <= 11.5 (X-Bow range) + slack. strict: slack 0 "
                      "(lead ruling R1, engine in_range_edge). lax: slack 1.0 tile (tap->building / lattice rounding). "
                      "Tower centres tiles K(9,3) L(3.5,6.5) R(14.5,6.5), radii K1.4 P1.0, tiles = cell/2."),
             "n_strict": int(off_strict.sum()), "n_lax": int(off_lax.sum()), "n_own_half": int(own_half.sum()),
             "n_enemy_half": int((~own_half).sum()),
             "share_strict": float(off_strict.mean()), "share_lax": float(off_lax.mean()),
             "val_n_strict": int(off_strict[split == 1].sum()), "val_n_lax": int(off_lax[split == 1].sum())}
rows_all = Counter(cy_p.tolist()); rows_off = Counter(cy_p[off_lax].tolist())
R["pro_rows"] = {"all_distinct_rows": len(rows_all), "lax_offensive_distinct_rows": len(rows_off),
                 "lax_row_hist(cy half-tile row -> n)": dict(sorted(rows_off.items())),
                 "all_row_hist": dict(sorted(rows_all.items())),
                 "lax_distinct_cells": len(set(cell[off_lax].tolist())),
                 "lax_distinct_cells_val": len(set(cell[off_lax & (split == 1)].tolist())),
                 "lax_distinct_rows_val": len(set(cy_p[off_lax & (split == 1)].tolist())),
                 "lax_modal_row_share": float(max(rows_off.values()) / off_lax.sum())}
tr = off_lax & (split == 0)
cc = Counter(cell[tr].tolist())
P_CELLS = np.array(sorted(c for c, k in cc.items() if k >= 10))
R["pro_rows"]["P_cells_rule"] = "cells with >=10 lax-offensive pro plays in the TRAIN split"
R["pro_rows"]["P_cells_n"] = int(len(P_CELLS))
R["pro_rows"]["P_cells_share_of_train_lax"] = float(np.isin(cell[tr], P_CELLS).mean())
P_MASK = np.zeros(GX * GY, bool); P_MASK[P_CELLS] = True
P_ROWS = sorted({int(c) // GX for c in P_CELLS})
R["pro_rows"]["P_rows"] = P_ROWS

# ======================================================================================= model analysis
FEAS = in_range_mask(alive, LAX)                       # [n_all, 2304] cells from which an alive enemy tower is in range
FEAS0 = in_range_mask(alive, 0.0)
R["feasible_set"] = {"mean_cells_lax_per_row(own half, alive towers)": float(FEAS.sum(1).mean()), "mean_cells_strict_per_row": float(FEAS0.sum(1).mean()),
                     "feasible_lax_rows_cy": [int(v) for v in np.unique(CY[FEAS.any(0)])], "feasible_strict_rows_cy": [int(v) for v in np.unique(CY[FEAS0.any(0)])],
                     "feasible_lax_cells_with_odd_lattice_per_row": float((FEAS & ((CX % 2 == 1) & (CY % 2 == 1))[None, :]).sum(1).mean()),
                     "feasible_strict_cells_with_odd_lattice_per_row": float((FEAS0 & ((CX % 2 == 1) & (CY % 2 == 1))[None, :]).sum(1).mean())}
ODD = (CX % 2 == 1) & (CY % 2 == 1)                    # pro lattice (all pro cells are odd,odd)
R["pro_lattice_check"] = {"share_pro_cells_odd_odd": float(((cx_p % 2 == 1) & (cy_p % 2 == 1)).mean())}
rows = GenRows(sub, np.arange(n_all), torch.device("cpu"))


@torch.no_grad()
def cell_probs(model):
    model.eval(); out = []
    for s in range(0, n_all, 256):
        b = rows.batch(np.arange(s, min(s + 256, n_all)))
        out.append(torch.softmax(model(b, card=b["card"], form=b["form"])["cell"].float(), -1))
    return torch.cat(out)


def nucleus(p, top_p):
    sp, si = p.sort(-1, descending=True)
    keep = (sp.cumsum(-1) - sp) < top_p
    sp = sp * keep
    q = torch.zeros_like(p).scatter_(-1, si, sp)
    return q / q.sum(-1, keepdim=True)


def summarize(p, m, label):
    """p [n,2304] probs; m bool[n] row subset."""
    P = p[torch.from_numpy(m)]
    n = int(m.sum()); r = rep[m]; pc = cell[m]
    ent = -(P * P.clamp_min(1e-12).log()).sum(-1).numpy()
    top1p, am = P.max(-1); top1p, am = top1p.numpy(), am.numpy()
    pro = P[torch.arange(n), torch.from_numpy(pc)].numpy()
    dx = (CX[None, :] - cx_p[m][:, None]) / 2.0; dy = (CY[None, :] - cy_p[m][:, None]) / 2.0
    w1 = torch.from_numpy(np.hypot(dx, dy) <= 1.0)
    mass_w1 = (P * w1).sum(-1).numpy()
    mass_P = (P * torch.from_numpy(P_MASK)[None, :]).sum(-1).numpy()
    mass_feas = (P * torch.from_numpy(FEAS[m])).sum(-1).numpy()
    mass_odd = (P * torch.from_numpy(ODD)[None, :]).sum(-1).numpy()
    mass_own = (P * torch.from_numpy(CY > GY // 2)[None, :]).sum(-1).numpy()
    n5 = (P > 0.05).sum(-1).numpy()
    n5P = ((P > 0.05) & torch.from_numpy(P_MASK)[None, :]).sum(-1).numpy()
    # mass on the argmax cell's own row vs other rows
    am_row = am // GX
    out = {"n_rows": n, "n_replays": int(len(set(r))),
           "entropy_nats": boot_mean(ent, r), "eff_cells_exp_H": boot_mean(np.exp(ent), r),
           "top1_prob": boot_mean(top1p, r), "p_pro_exact": boot_mean(pro, r), "p_within_1_tile_of_pro": boot_mean(mass_w1, r),
           "mass_on_P_cells": boot_mean(mass_P, r), "mass_on_feasible_lax": boot_mean(mass_feas, r),
           "mass_on_lattice_oddodd": boot_mean(mass_odd, r), "mass_own_half": boot_mean(mass_own, r),
           "n_cells_over_5pct": boot_mean(n5, r), "n_P_cells_over_5pct": boot_mean(n5P, r),
           "argmax_exact_pro": boot_mean(am == pc, r),
           "argmax_within_1_tile": boot_mean(np.hypot((am % GX - cx_p[m]) / 2.0, (am // GX - cy_p[m]) / 2.0) <= 1.0, r),
           "argmax_in_P": float(P_MASK[am].mean()), "argmax_feasible": float(FEAS[m][np.arange(n), am].mean()),
           "distinct_argmax_cells": int(len(set(am.tolist()))), "distinct_argmax_rows": int(len(set((am // GX).tolist()))),
           "argmax_cell_hist": {int(k): int(v) for k, v in Counter(am.tolist()).most_common(6)},
           "argmax_row_hist": {int(k): int(v) for k, v in sorted(Counter(am_row.tolist()).items())},
           "pro_distinct_cells_same_rows": int(len(set(pc.tolist()))), "pro_distinct_rows_same_rows": int(len(set((pc // GX).tolist()))),
           "pro_row_hist": {int(k): int(v) for k, v in sorted(Counter((pc // GX).tolist()).items())},
           "model_mean_row_mass": {int(k): float(v) for k, v in zip(range(GY), P.view(n, GY, GX).sum(-1).mean(0).numpy()) if v > 0.005}}
    top2 = np.array([c for c, _ in cc.most_common(2)])               # two most common TRAIN lax-offensive pro cells
    out["pro_top2_cells"] = top2.tolist()
    out["pro_top2_share_in_subset"] = float(np.isin(pc, top2).mean())
    out["model_mean_mass_on_pro_top2"] = float(P[:, torch.from_numpy(top2)].sum(-1).mean())
    out["argmax_top2_share"] = float(np.isin(am, top2).mean())
    bins = [0, .3, .45, .6, 1.01]
    out["top1_calibration"] = {f"[{bins[i]},{bins[i+1]})": {"n": int(((top1p >= bins[i]) & (top1p < bins[i + 1])).sum()),
                                                            "mean_top1_prob": float(top1p[(top1p >= bins[i]) & (top1p < bins[i + 1])].mean()) if ((top1p >= bins[i]) & (top1p < bins[i + 1])).any() else None,
                                                            "argmax_eq_pro": float((am == pc)[(top1p >= bins[i]) & (top1p < bins[i + 1])].mean()) if ((top1p >= bins[i]) & (top1p < bins[i + 1])).any() else None}
                               for i in range(4)}
    lm = (np.abs(tile_p[m, 0] - 9.0) >= 2.0)                          # pro lane-cell rows (|x-9|>=2 tiles)
    pl = tile_p[m, 0] < 9.0; al = (am % GX) / 2.0 < 9.0
    wk = (hp[m, 2] - hp[m, 1]) > 0.02; wk_eq = np.abs(hp[m, 2] - hp[m, 1]) <= 0.02
    out["lane_agree"] = {"n_lane_rows": int(lm.sum()), "argmax_lane==pro_lane": float((al == pl)[lm].mean()),
                         "weaker_tower_rule==pro_lane (|dHP|>0.02)": float((wk == pl)[lm & ~wk_eq].mean()), "n_rule_rows": int((lm & ~wk_eq).sum()),
                         "argmax_lane==pro_lane on the same rule rows": float((al == pl)[lm & ~wk_eq].mean()),
                         "pro_left_share": float(pl[lm].mean()), "argmax_left_share": float(al[lm].mean())}
    # sampling schemes: one draw per row, 200 repeats
    samp = {}
    for name, q in (("argmax", None), ("T1.0", P), ("top_p0.9", nucleus(P, 0.9)),
                    ("T0.7", torch.softmax(P.clamp_min(1e-30).log() / 0.7, -1)), ("T0.5", torch.softmax(P.clamp_min(1e-30).log() / 0.5, -1))):
        if q is None:
            d = am[:, None]
        else:
            d = torch.multinomial(q, 200, replacement=True).numpy()
        d = np.asarray(d)
        reps = d.shape[1]
        distinct = [len(set(d[:, j].tolist())) for j in range(reps)]
        distinct_rows = [len(set((d[:, j] // GX).tolist())) for j in range(reps)]
        samp[name] = {"distinct_cells_per_draw_of_n": float(np.mean(distinct)), "distinct_rows_per_draw_of_n": float(np.mean(distinct_rows)),
                      "agree_exact_pro": float((d == pc[:, None]).mean()),
                      "agree_within_1_tile": float((np.hypot((d % GX - cx_p[m][:, None]) / 2.0, (d // GX - cy_p[m][:, None]) / 2.0) <= 1.0).mean()),
                      "in_P_cells": float(P_MASK[d].mean()), "in_feasible_lax": float(FEAS[m][np.arange(n)[:, None], d].mean()),
                      "on_lattice_oddodd": float(ODD[d].mean()), "own_half": float((d // GX > GY // 2).mean()),
                      "modal_row_share": float(max(Counter((d // GX).ravel().tolist()).values()) / d.size)}
    out["sampling"] = samp
    return out


R["models"] = {}
for name, path in CKPTS.items():
    model, st = load_model(path, torch.device("cpu"))
    p = cell_probs(model)
    res = {"ckpt": str(path.relative_to(REPO)), "feature_version": int(st["args"].get("feature_version", 1)), "grid": st["args"]["grid"]}
    for lab, m in (("val_offensive_lax", (split == 1) & off_lax), ("val_all_xbow", split == 1), ("val_offensive_strict", (split == 1) & off_strict),
                   ("train_offensive_lax", (split == 0) & off_lax)):
        res[lab] = summarize(p, m, lab)
    R["models"][name] = res
    del model, p

# pro baselines on the same val rows: what a context-free sampler of pro cells (marginal) would score
mv = (split == 1) & off_lax
tr_cells = cell[(split == 0) & off_lax]
marg = np.bincount(tr_cells, minlength=GX * GY) / len(tr_cells)
d = RNG.choice(GX * GY, size=(int(mv.sum()), 200), p=marg)
R["context_free_pro_marginal_sampler_val"] = {"agree_exact_pro": float((d == cell[mv][:, None]).mean()),
                                               "argmax_of_marginal_agree": float((marg.argmax() == cell[mv]).mean()),
                                               "distinct_cells_per_draw": float(np.mean([len(set(d[:, j].tolist())) for j in range(200)]))}

# ======================================================================================= H3: pro placement vs public context
tokv, offs = sub["tok"], sub["off"]
n_def = np.zeros((n_all, 2)); n_bld = np.zeros((n_all, 2)); n_troop = np.zeros((n_all, 2)); n_def_tot = np.zeros(n_all)
near_def_d = np.full(n_all, np.nan)
for i in range(n_all):
    t = tokv[offs[i]:offs[i + 1]]
    if not len(t):
        continue
    opp = (t[:, 2] == 1) & (t[:, 13] == 0)
    cls = t[:, 0].astype(int); x, y = t[:, 4], t[:, 5]
    isdef = np.isin(cls, list(DEF_IDS)); isb = np.isin(cls, list(BUILD_IDS))
    for lane, side_ok in enumerate((x < 0.4, x > 0.6)):                      # 0 = left lane (x small), 1 = right
        n_def[i, lane] = (opp & isdef & side_ok & (y < 0.5)).sum()
        n_bld[i, lane] = (opp & isb & side_ok & (y < 0.5)).sum()
        n_troop[i, lane] = (opp & ~isb & side_ok & (y > 0.3) & (y < 0.7)).sum()   # enemy troops near/over the bridge
    n_def_tot[i] = (opp & isdef).sum()
    dm = opp & isdef
    if dm.any():
        near_def_d[i] = np.hypot((x[dm] * 18 - tile_p[i, 0]), (y[dm] * 32 - tile_p[i, 1])).min()

xt = tile_p[:, 0]
lane_ok = off_lax & ((xt <= 7.0) | (xt >= 11.0))
is_left = (xt <= 7.0).astype(float)
dHP = hp[:, 2] - hp[:, 1]                          # right-tower hp minus left (>0: left tower weaker)
dDef = n_def[:, 1] - n_def[:, 0]                   # right defenders minus left (>0: right is more defended)
dTr = n_troop[:, 1] - n_troop[:, 0]


def logit_fit(X, y, l2=1e-2, it=30):
    X1 = np.c_[np.ones(len(X)), X]; b = np.zeros(X1.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-np.clip(X1 @ b, -30, 30))); W = p * (1 - p) + 1e-9
        H = X1.T @ (X1 * W[:, None]) + l2 * np.eye(len(b)); g = X1.T @ (y - p) - l2 * b
        step = np.linalg.solve(H, g); b += step
        if np.abs(step).max() < 1e-7:
            break
    return b


def auc(y, s):
    u, inv, cnt = np.unique(s, return_inverse=True, return_counts=True)
    cs = np.cumsum(cnt); r = ((cs - cnt + 1 + cs) / 2.0)[inv]
    n1 = y.sum(); n0 = len(y) - n1
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else float("nan")


def grouped_cv_auc(X, y, g, k=5):
    ug = np.unique(g); fold = dict(zip(ug, RNG.permutation(len(ug)) % k)); f = np.array([fold[v] for v in g])
    s = np.zeros(len(y)); ll = 0.0; ll0 = 0.0
    for j in range(k):
        te = f == j; b = logit_fit(X[~te], y[~te]); p = 1 / (1 + np.exp(-(np.c_[np.ones(te.sum()), X[te]] @ b))); s[te] = p
        p = np.clip(p, 1e-6, 1 - 1e-6); q = np.clip(y[~te].mean(), 1e-6, 1 - 1e-6)
        ll += -(y[te] * np.log(p) + (1 - y[te]) * np.log(1 - p)).sum(); ll0 += -(y[te] * np.log(q) + (1 - y[te]) * np.log(1 - q)).sum()
    return auc(y, s), float(1 - ll / ll0)           # AUC, McFadden-style CV pseudo-R2 (1 - logloss/logloss_const)


def boot_or(X, y, g, names, B=400):
    """standardised (per +1 SD) log-odds coefficients with replay-cluster bootstrap CI."""
    mu, sd = X.mean(0), X.std(0) + 1e-9; Xs = (X - mu) / sd
    b0 = logit_fit(Xs, y)[1:]
    u, inv = np.unique(g, return_inverse=True); members = [np.where(inv == k)[0] for k in range(len(u))]
    bs = []
    for _ in range(B):
        ix = np.concatenate([members[k] for k in RNG.integers(0, len(u), len(u))]); bs.append(logit_fit(Xs[ix], y[ix])[1:])
    bs = np.array(bs)
    return {nm: {"OR_per_SD": float(np.exp(b0[j])), "ci95": [float(np.exp(np.percentile(bs[:, j], 2.5))), float(np.exp(np.percentile(bs[:, j], 97.5)))]}
            for j, nm in enumerate(names)}


def rate_ci(flag, g):
    return boot_mean(flag.astype(float), g)


H3 = {}
# --- T1 lane (left vs right), non-central offensive placements
m = lane_ok
g = rep[m]
t1 = {"n": int(m.sum()), "replays": int(len(set(g))), "base_rate_left": rate_ci(is_left[m], g)}
sub_w = m & (np.abs(dHP) > 0.02)
t1["plays_in_lane_of_weaker_enemy_tower(|dHP|>0.02)"] = {"n": int(sub_w.sum()), "rate_ci": rate_ci(np.where(dHP[sub_w] > 0, is_left[sub_w] == 1, is_left[sub_w] == 0), rep[sub_w]),
                                                         "null": 0.5}
sub_d = m & (dDef != 0)
t1["plays_in_lane_with_FEWER_enemy_def_buildings(when unequal)"] = {"n": int(sub_d.sum()), "rate_ci": rate_ci(np.where(dDef[sub_d] > 0, is_left[sub_d] == 1, is_left[sub_d] == 0), rep[sub_d]), "null": 0.5}
# NOT conditioned on the offensive rule (that rule needs an alive tower, so it would exclude the dead lane by construction)
lane_any = own_half & ((xt <= 7.0) | (xt >= 11.0)) & (alive_known[:, 1] != alive_known[:, 2]) | (own_half & ((xt <= 7.0) | (xt >= 11.0)) & ((hp[:, 1] > 0) != (hp[:, 2] > 0)))
dead_l = ~((hp[:, 1] > 0) & alive_known[:, 1]); dead_r = ~((hp[:, 2] > 0) & alive_known[:, 2])
sub_x = own_half & ((xt <= 7.0) | (xt >= 11.0)) & (dead_l != dead_r)
t1["plays_in_lane_of_DEAD_princess(exactly one dead; all own-half lane X-Bows)"] = {"n": int(sub_x.sum()), "rate_ci": rate_ci(np.where(dead_l[sub_x], is_left[sub_x] == 1, is_left[sub_x] == 0), rep[sub_x]), "null": 0.5}
X1 = np.c_[dHP, dDef, dTr][m]; nm1 = ["hpR-hpL", "defBldR-defBldL", "enemyTroopsR-L"]
t1["logit_left"] = boot_or(X1, is_left[m], g, nm1)
t1["cv_auc_and_pseudoR2"] = grouped_cv_auc(X1, is_left[m], g)
H3["T1_lane"] = t1
# --- T2 row: P(non-modal row) in offensive lane placements
modal = rows_off.most_common(1)[0][0]
nonmodal = (cy_p != modal).astype(float)
m = off_lax; g = rep[m]
lane_def = np.where(xt < 9.0, n_def[:, 0], n_def[:, 1]); lane_hp = np.where(xt < 9.0, hp[:, 1], hp[:, 2]); lane_troop = np.where(xt < 9.0, n_troop[:, 0], n_troop[:, 1])
X2 = np.c_[sc[:, 0], sc[:, 3], lane_def, lane_hp, lane_troop, n_def_tot][m]
nm2 = ["t_300(match progress)", "my_elixir/10", "enemy_def_bldgs_in_chosen_lane", "enemy_tower_hp_chosen_lane", "enemy_troops_chosen_lane", "enemy_def_bldgs_total"]
H3["T2_row_nonmodal"] = {"modal_cy": int(modal), "n": int(m.sum()), "base_rate_nonmodal": rate_ci(nonmodal[m], g),
                        "logit": boot_or(X2, nonmodal[m], g, nm2), "cv_auc_and_pseudoR2": grouped_cv_auc(X2, nonmodal[m], g),
                        "nonmodal_rate_by_def_bldg_in_lane": {str(int(k)): [int((lane_def[m] == k).sum()), float(nonmodal[m][lane_def[m] == k].mean())] for k in np.unique(lane_def[m])[:4]}}
# --- T3 central pocket vs lane (own-half, any rule): cells 7<x<11 tiles
m = own_half & (cy_p >= 37); g = rep[m]
central = ((xt > 7.0) & (xt < 11.0)).astype(float)
X3 = np.c_[sc[:, 0], sc[:, 3], n_def_tot, np.minimum(hp[:, 1], hp[:, 2]), np.maximum(n_troop[:, 0], n_troop[:, 1])][m]
nm3 = ["t_300", "my_elixir/10", "enemy_def_bldgs_total", "min_enemy_princess_hp", "enemy_troops_max_lane"]
H3["T3_central_vs_lane"] = {"n": int(m.sum()), "base_rate_central": rate_ci(central[m], g), "logit": boot_or(X3, central[m], g, nm3),
                            "cv_auc_and_pseudoR2": grouped_cv_auc(X3, central[m], g)}
# --- T4: does the chosen cell keep its distance from enemy defensive buildings? (cell-level, vs the mirror lane cell)
m = off_lax & ~np.isnan(near_def_d)
mir_x = 18.0 - tile_p[:, 0]
d_mir = np.full(n_all, np.nan)
for i in np.where(m)[0]:
    t = tokv[offs[i]:offs[i + 1]]; cls = t[:, 0].astype(int); dm = (t[:, 2] == 1) & (t[:, 13] == 0) & np.isin(cls, list(DEF_IDS))
    d_mir[i] = np.hypot(t[dm, 4] * 18 - mir_x[i], t[dm, 5] * 32 - tile_p[i, 1]).min()
dd = (near_def_d - d_mir)[m]
H3["T4_distance_to_enemy_def_bldg"] = {"n": int(m.sum()), "mean_dist_chosen_minus_mirror_cell_tiles": boot_mean(dd, rep[m]),
                                      "share_chosen_farther_than_mirror": boot_mean(dd > 0, rep[m]),
                                      "note": "mirror cell = same row, x reflected; >0 means pros place farther from the nearest enemy Tesla/Cannon/Inferno/Bomb than the mirrored cell would be"}
R["H3"] = H3
R["H3"]["context_cohort"] = {"opp_def_bldg_present_share": float((n_def_tot[off_lax] > 0).mean()), "dead_princess_share": float(((~alive[:, 1]) | (~alive[:, 2]))[off_lax].mean())}

json.dump(R, open(OUT / "results.json", "w"), indent=1, default=float)
print("done", OUT / "results.json")
