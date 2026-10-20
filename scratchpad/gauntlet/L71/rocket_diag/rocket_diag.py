"""Rocket / dead-lane X-Bow diagnosis on gen_v31a_s0 (L71). CPU only, read-only on pipeline/, no training, no sim.

Rows: gen_dataset_v31_public.npz, VALIDATION split (split==1), icebow-deck pro rows (deck_id 90 = ice-wizard knight rocket
skeletons tesla the-log tornado x-bow, the base-key set of the icebow deck; evo/hero forms share the id).
Teacher-forced exactly like e1_eval.live_decide: P(play)=sigmoid(gate); card = argmax over AFFORDABLE hand slots of the
card logits (afford = int(elixir the row shows) >= card cost); cell = argmax of that card's cell logits.
Never uses opponent hidden state: every model input is the dataset's public v4 feature set (GenRows.batch).

run: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L71/rocket_diag/rocket_diag.py
out: results.json next to this file.
"""
from __future__ import annotations

import ctypes
import json
import sys
import time
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
torch.set_num_threads(4)
try:  # below-normal priority (laptop is shared)
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
except Exception:
    pass

from pipeline.eval_gen import GenRows, load_model                      # noqa: E402  (imported as-is)
from pipeline.opp_elixir_count import card_cost                         # noqa: E402

NPZ = REPO / "icebow/data/pipeline/gen_dataset_v31_public.npz"
CKPT = REPO / "icebow/data/pipeline/gen_v31a_s0/gen_s0.pt"
LABELS = REPO / ".foreman/codex_autopilot/runs/public_labels_full_reconstructed/labels.jsonl"
DECK_ID = 90
TAUS = (0.27, 0.35)
GX, GY = 36, 64
B_BOOT = 1000
RNG = np.random.default_rng(0)
# opp K, L, R princess/king centres in MY frame (me at bottom), tiles; obs_contract.py:28-34. Rocket radius 2.0 tiles.
TOWERS = np.array([[9.0, 3.0], [3.5, 6.5], [14.5, 6.5]])
ROCKET_R = 2.0
CX = np.tile(np.arange(GX), GY)
CY = np.repeat(np.arange(GY), GX)
TX, TY = CX / 2.0, CY / 2.0
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:6.0f}s]", *a, flush=True)


# ===================================================================================== streaming npz reader
def take(zf: zipfile.ZipFile, name: str, idx: np.ndarray) -> np.ndarray:
    """rows ``idx`` (sorted unique) of ``name.npy`` inside the compressed npz, streamed (never holds the full array)."""
    idx = np.asarray(idx)
    with zf.open(name + ".npy") as f:
        ver = np.lib.format.read_magic(f)
        shape, _, dt = (np.lib.format.read_array_header_1_0(f) if ver == (1, 0) else np.lib.format.read_array_header_2_0(f))
        rb = int(np.prod(shape[1:], dtype=np.int64)) * dt.itemsize
        out = np.empty((len(idx),) + tuple(shape[1:]), dt)
        step = max(1, (96 << 20) // max(rb, 1))
        o = 0
        for lo in range(0, shape[0], step):
            n = min(step, shape[0] - lo)
            buf = bytearray()
            while len(buf) < n * rb:
                c = f.read(n * rb - len(buf))
                if not c:
                    raise EOFError(name)
                buf += c
            a, b = np.searchsorted(idx, [lo, lo + n])
            if b > a:
                out[o:o + b - a] = np.frombuffer(buf, dt).reshape((n,) + tuple(shape[1:]))[idx[a:b] - lo]
                o += b - a
    assert o == len(idx), (name, o, len(idx))
    return out


def boot(v, rep, B=B_BOOT):
    """mean + replay-cluster bootstrap 95% CI -> [mean, lo, hi]."""
    v = np.asarray(v, float)
    if len(v) == 0:
        return [None, None, None]
    u, inv = np.unique(rep, return_inverse=True)
    s, c = np.bincount(inv, v, len(u)), np.bincount(inv, minlength=len(u)).astype(float)
    ix = RNG.integers(0, len(u), (B, len(u)))
    m = s[ix].sum(1) / np.maximum(c[ix].sum(1), 1)
    return [float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def auc(y, s):
    u, inv, cnt = np.unique(s, return_inverse=True, return_counts=True)
    cs = np.cumsum(cnt)
    r = ((cs - cnt + 1 + cs) / 2.0)[inv]
    n1 = int(y.sum()); n0 = len(y) - n1
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else float("nan")


# ===================================================================================== load rows
zf = zipfile.ZipFile(NPZ)
z = np.load(NPZ, allow_pickle=False)
meta = json.loads(str(z["meta"]))
CV = meta["card_vocab"]
RK, XB = CV.index("rocket"), CV.index("x-bow")
deck_id, split, y_gate, y_card = z["deck_id"], z["split"], z["y_gate"], z["y_card"]
sel = np.flatnonzero((deck_id == DECK_ID) & (split == 1))
n = len(sel)
log("val icebow-deck rows", n, "plays", int((y_gate[sel] == 1).sum()))
COST = np.zeros(len(CV))
for i, c in enumerate(CV):
    if i:
        COST[i] = card_cost(c.replace("-", "_")) or 0.0
keys = ["sc", "hand_card", "hand_form", "next_card", "next_form", "deck_card", "deck_form", "past", "y_gate", "y_card",
        "y_hand_pos", "y_xy", "y_wait_card", "y_crowns", "tick", "side", "rep", "split", "deck_id", "opp_past", "opp_cycle",
        "projectiles", "effects", "own_ability", "y_cell"]
sub = {}
for k in keys:
    sub[k] = take(zf, k, sel)
    log("loaded", k, sub[k].shape)
off = z["off"]
lens = off[sel + 1] - off[sel]
gather = np.concatenate([np.arange(off[i], off[i + 1]) for i in sel])
sub["tok"] = take(zf, "tok", gather)
sub["unit_form"] = take(zf, "unit_form", gather)
sub["off"] = np.concatenate([[0], np.cumsum(lens)]).astype(np.int64)
tags = z["tags"]
# pro X-Bow rows, ALL splits of the icebow deck (pro-rate stats only, no model): sc, cell, rep
xb_all = np.flatnonzero((deck_id == DECK_ID) & (y_gate == 1) & (y_card == XB))
xb_all_sc = take(zf, "sc", xb_all)
xb_all_cell, xb_all_rep, xb_all_split = z["y_cell"][xb_all].astype(int), z["rep"][xb_all], split[xb_all]
log("pro xbow all splits", len(xb_all))

# ===================================================================================== model forward
model, st = load_model(CKPT, torch.device("cpu"))
model.eval()
FV = int(st["args"].get("feature_version", 1))
rows = GenRows(sub, np.arange(n), torch.device("cpu"))
gate_logit = np.zeros(n, np.float32)
card_logit = np.zeros((n, 4), np.float32)
need_cell = np.flatnonzero((sub["y_gate"] == 1) & np.isin(sub["y_card"], [RK, XB]))
cell_row = {int(r): j for j, r in enumerate(need_cell)}
cell_p = np.zeros((len(need_cell), GX * GY), np.float32)
with torch.no_grad():
    for s in range(0, n, 256):
        ids = np.arange(s, min(s + 256, n))
        b = rows.batch(ids)
        enc = model.encode_gen(b)
        h = model.heads_gen(enc, b)
        gate_logit[ids] = h["gate"].float().numpy()
        card_logit[ids] = h["card"].float().numpy()
        loc = [i for i, r in enumerate(ids) if int(r) in cell_row]
        if loc:
            li = torch.tensor(loc)
            c = model.cell_logits_gen({k: v[li] for k, v in enc.items()}, b["card"][li], b["form"][li])
            cell_p[[cell_row[int(ids[i])] for i in loc]] = torch.softmax(c.float(), -1).numpy()
        if (s // 256) % 20 == 0:
            log("forward", s, "/", n)
log("forward done; ckpt feature_version", FV)

# ===================================================================================== per-row decision quantities
sc, hand, ycard, ygate, rep, tick, side = sub["sc"], sub["hand_card"].astype(int), sub["y_card"].astype(int), sub["y_gate"], sub["rep"], sub["tick"], sub["side"]
p_play = 1 / (1 + np.exp(-gate_logit.astype(np.float64)))
el_int = np.floor(sc[:, 3] * 10 + 1e-3)
inhand = hand > 0
afford = inhand & (COST[hand] <= el_int[:, None] + 1e-6)
any_aff = afford.any(1)
lg = card_logit.astype(np.float64)
lg_aff = np.where(afford, lg, -np.inf)


def softmax_rows(a):
    m = np.where(np.isfinite(a).any(1, keepdims=True), a.max(1, keepdims=True), 0.0)
    e = np.exp(np.where(np.isfinite(a), a - m, -np.inf))
    return e / np.maximum(e.sum(1, keepdims=True), 1e-300)


P_hand = softmax_rows(np.where(inhand, lg, -np.inf))        # over all hand cards
P_aff = softmax_rows(lg_aff)                                 # over affordable hand cards (what live_decide sees)
isR = hand == RK
r_in_hand = isR.any(1)
r_aff = (isR & afford).any(1)
PR_hand = (P_hand * isR).sum(1)
PR_aff = (P_aff * isR).sum(1)
am_aff = lg_aff.argmax(1)
arg_is_R = any_aff & isR[np.arange(n), am_aff]


def rank_among(mask_cols, target):
    """1-based rank of the Rocket slot among ``mask_cols`` slots by card logit (0 if Rocket not in the set)."""
    L = np.where(mask_cols, lg, -np.inf)
    rl = np.where(isR, L, -np.inf).max(1)
    rank = 1 + (L > rl[:, None]).sum(1)
    return np.where((isR & mask_cols).any(1), rank, 0)


rank_hand = rank_among(inhand, None)
rank_aff = rank_among(afford, None)

# ---- public context from sc (the model's own view): time, crowns, tower HP
t_sec = sc[:, 0] * 300.0
overtime = sc[:, 2] > 0.5
late = overtime | (t_sec >= 120.0)                                   # overtime or last 60 s of regulation
alive = sc[:, 64:70] > 0.5                                           # my K,L,R then opp K,L,R
my_cr = (~alive[:, 4]).astype(int) + (~alive[:, 5]).astype(int)      # opp princesses down
op_cr = (~alive[:, 1]).astype(int) + (~alive[:, 2]).astype(int)
hp_my, hp_op = sc[:, 52:55].sum(1), sc[:, 55:58].sum(1)
level = my_cr == op_cr
behind_cr = op_cr > my_cr
ahead_cr = my_cr > op_cr
hp_deficit = hp_my < hp_op - 0.05
deficit_any = behind_cr | (level & hp_deficit)                       # behind on crowns, or level with a tower-HP deficit

# ---- join to Rocket labels
lab = {}
for line in LABELS.open():
    r = json.loads(line)
    lab[(r["tag"], r["side"], r["tick"], r["card"])] = r
ridx = np.flatnonzero((ygate == 1) & (ycard == RK))
L = [lab.get((str(tags[rep[i]]), int(side[i]), int(tick[i]), "rocket")) for i in ridx]
log("rocket rows", len(ridx), "joined", sum(x is not None for x in L))
assert all(x is not None for x in L)
g = lambda key: np.array([bool(x[key]) if x.get(key) is not None else False for x in L])        # noqa: E731
known = np.array([x.get("tower_rocket") is not None for x in L])
tower_r, def_r = g("tower_rocket"), g("defensive_rocket")
rtt, ttr = g("rocket_then_tornado"), g("tornado_then_rocket")
tbc = g("tiebreak_cycle_context")
prior = np.array([max([h.get("prior_rockets", 0) for h in x.get("tower_hits", [])] + [0]) for x in L])
lab_late = np.array([x["phase"] == "overtime" or x["seconds_left"] <= 60 for x in L])
lab_cr = np.array([x["crowns_before"] for x in L])
agree = {"late_sc_vs_label": float((late[ridx] == lab_late).mean()),
         "crowns_sc_vs_label(mine,theirs)": float((np.c_[my_cr, op_cr][ridx] == lab_cr).all(1).mean())}
log("sc-vs-label agreement", agree)

# ===================================================================================== Rocket tables
rrep = rep[ridx]


def funnel(m, rows_idx=ridx, tag=""):
    """stats over pro Rocket plays rows_idx[m]."""
    i = rows_idx[m]
    r = rep[i]
    out = {"n": int(len(i)), "n_replays": int(len(set(r.tolist())))}
    if not len(i):
        return out
    out["P(play)_mean"] = boot(p_play[i], r)
    for t in TAUS:
        out[f"gate_pass_tau{t}"] = boot(p_play[i] > t, r)
    out["affordable_share"] = boot(r_aff[i], r)
    out["P(Rocket)_over_hand_mean"] = boot(PR_hand[i], r)
    out["P(Rocket)_over_affordable_mean(0 if unaffordable)"] = boot(np.where(r_aff[i], PR_aff[i], 0.0), r)
    out["P(Rocket)_over_affordable_mean|affordable"] = boot(PR_aff[i][r_aff[i]], r[r_aff[i]]) if r_aff[i].any() else None
    out["P(Rocket)_over_hand_median"] = float(np.median(PR_hand[i]))
    out["rank_in_hand_dist(1..4)"] = {k: float((rank_hand[i] == k).mean()) for k in (1, 2, 3, 4)}
    out["rank_among_affordable_dist"] = {**{str(k): float((rank_aff[i] == k).mean()) for k in (1, 2, 3, 4)}, "unaffordable": float((~r_aff[i]).mean())}
    out["argmax_is_Rocket_share(all rows)"] = boot(arg_is_R[i], r)
    out["argmax_is_Rocket|affordable"] = boot(arg_is_R[i][r_aff[i]], r[r_aff[i]]) if r_aff[i].any() else None
    out["rank2_lost_to_argmax_share(affordable, rank 2)"] = float((rank_aff[i] == 2).mean())
    for t in TAUS:
        fire = arg_is_R[i] & (p_play[i] > t)
        out[f"WOULD_FIRE_Rocket_tau{t}(gate&argmax)"] = boot(fire, r)
        # bottleneck decomposition among rows that do NOT fire
        nf = ~fire
        out[f"nofire_cause_tau{t}"] = {"unaffordable": float((nf & ~r_aff[i]).sum() / max(len(i), 1)),
                                       "affordable_but_gate_blocked_only": float((nf & r_aff[i] & ~(p_play[i] > t) & arg_is_R[i]).sum() / max(len(i), 1)),
                                       "affordable_but_argmax_other_only": float((nf & r_aff[i] & (p_play[i] > t) & ~arg_is_R[i]).sum() / max(len(i), 1)),
                                       "both_gate_and_argmax": float((nf & r_aff[i] & ~(p_play[i] > t) & ~arg_is_R[i]).sum() / max(len(i), 1))}
    # P(Rocket) given Rocket is affordable AND we pretend the gate passes
    return out


# tower-Rocket cell analysis
def cell_stats(m):
    i = ridx[m]
    out = {"n": int(len(i))}
    if not len(i):
        return out
    cp = np.stack([cell_p[cell_row[int(k)]] for k in i])
    pc = sub["y_cell"][i].astype(int)
    px, py = (pc % GX) / 2.0, (pc // GX) / 2.0
    d_pro = np.hypot(TX[None, :] - px[:, None], TY[None, :] - py[:, None])
    # enemy towers alive (opp K,L,R) -> cells whose centre is within the Rocket radius of an alive enemy tower
    al = alive[i][:, 3:6]
    hit = np.zeros_like(cp, bool)
    for t in range(3):
        d = np.hypot(TX - TOWERS[t, 0], TY - TOWERS[t, 1]) <= ROCKET_R
        hit |= al[:, t:t + 1] & d[None, :]
    am = cp.argmax(1)
    r = rep[i]
    out["P(pro cell)"] = boot(cp[np.arange(len(i)), pc], r)
    out["P(within 1 tile of pro)"] = boot((cp * (d_pro <= 1.0)).sum(1), r)
    out["P(within 2 tiles of pro)"] = boot((cp * (d_pro <= 2.0)).sum(1), r)
    out["P(any tower-hitting cell, alive tower within 2.0 tiles)"] = boot((cp * hit).sum(1), r)
    out["argmax_cell_exact_pro"] = boot(am == pc, r)
    out["argmax_cell_within_1_tile"] = boot(np.hypot(TX[am] - px, TY[am] - py) <= 1.0, r)
    out["argmax_cell_within_2_tiles"] = boot(np.hypot(TX[am] - px, TY[am] - py) <= 2.0, r)
    out["argmax_cell_hits_alive_tower"] = boot(hit[np.arange(len(i)), am], r)
    out["pro_cell_hits_alive_tower(sanity)"] = boot(hit[np.arange(len(i)), pc], r)
    out["median_dist_argmax_to_pro_tiles"] = float(np.median(np.hypot(TX[am] - px, TY[am] - py)))
    out["entropy_nats_mean"] = float((-(cp * np.log(np.clip(cp, 1e-12, None))).sum(1)).mean())
    return out


Rk = len(ridx)
ctx = {  # masks over the Rocket-play rows (ridx)
    "ALL Rockets": np.ones(Rk, bool),
    "label unknown (8 rows, excluded below)": ~known,
    "TOWER Rocket (hit an enemy tower)": tower_r,
    "  tower, NOT also troop-hit": tower_r & ~def_r,
    "  tower, late (overtime or last 60s), any score": tower_r & late[ridx],
    "  tower, late, level crowns": tower_r & late[ridx] & level[ridx],
    "  tower, late, level crowns + tower-HP deficit": tower_r & late[ridx] & level[ridx] & hp_deficit[ridx],
    "  tower, late, behind on crowns": tower_r & late[ridx] & behind_cr[ridx],
    "  tower, late, behind (crowns, or level w/ HP deficit)": tower_r & late[ridx] & deficit_any[ridx],
    "  tower, late, ahead on crowns (contrast)": tower_r & late[ridx] & ahead_cr[ridx],
    "  tower, OVERTIME only, behind (crowns or HP)": tower_r & overtime[ridx] & deficit_any[ridx],
    "  tower, repeat on same tower (prior_rockets>=1)": tower_r & (prior >= 1),
    "DEFENSIVE Rocket (hit troops)": def_r,
    "  defensive, NOT tower": def_r & ~tower_r,
    "ROCKET -> TORNADO (first cast)": rtt,
    "TORNADO -> ROCKET": ttr,
    "tiebreak_cycle_context (level crowns, >=150 s)": tbc,
    "neither tower nor troop hit (other)": known & ~tower_r & ~def_r,
}
R = {"data": {"npz": str(NPZ.relative_to(REPO)), "ckpt": str(CKPT.relative_to(REPO)), "feature_version": FV, "deck_id": DECK_ID,
              "split": "val", "n_rows": int(n), "n_play_rows": int((ygate == 1).sum()), "n_replays": int(len(set(rep.tolist()))),
              "n_pro_rocket_plays": int(Rk), "n_pro_rocket_replays": int(len(set(rrep.tolist()))),
              "pro_rocket_share_of_plays": float(Rk / (ygate == 1).sum()), "costs": {CV[c]: float(COST[c]) for c in (RK, XB)},
              "label_join": agree, "taus": list(TAUS), "late_def": "sc: overtime flag or t>=120 s (last 60 s of regulation)",
              "deficit_def": "behind on crowns (princesses down) OR level crowns and sum(my 3 tower hp frac) < sum(opp 3) - 0.05",
              "anti_stall": "not modelled (live stall override ignored)"}}
R["rocket_contexts"] = {k: funnel(m & (known | (k.startswith("label unknown")))) for k, m in ctx.items()}
R["tower_rocket_cell_head"] = {k: cell_stats(m & known) for k, m in ctx.items()
                               if k.startswith(("TOWER", "  tower")) and (m & known).sum() > 0}
R["defensive_rocket_cell_head"] = {k: cell_stats(m & known) for k, m in ctx.items() if k.startswith(("DEFENSIVE", "ROCKET ->")) and (m & known).sum() > 0}
log("rocket tables done")

# ===================================================================================== contrast: non-Rocket plays with Rocket in hand & affordable
play = ygate == 1
Pm = play & (ycard == RK)                                   # pro Rocket plays (all)
Pm_aff = Pm & r_aff                                         # ... with Rocket affordable
Qm = play & (ycard != RK) & r_aff                           # pro played something else, Rocket in hand and affordable


def contrast(m, name):
    i = np.flatnonzero(m)
    r = rep[i]
    o = {"n": int(len(i)), "n_replays": int(len(set(r.tolist())))}
    if not len(i):
        return o
    o["P(play)_mean"] = boot(p_play[i], r)
    for t in TAUS:
        o[f"gate_pass_tau{t}"] = boot(p_play[i] > t, r)
    o["P(Rocket)_over_affordable_mean"] = boot(PR_aff[i], r)
    o["rank_among_affordable_dist"] = {str(k): float((rank_aff[i] == k).mean()) for k in (1, 2, 3, 4)}
    o["argmax_is_Rocket_share"] = boot(arg_is_R[i], r)
    for t in TAUS:
        o[f"WOULD_FIRE_Rocket_tau{t}"] = boot(arg_is_R[i] & (p_play[i] > t), r)
    return o


def sit_table(name, base):
    """Among play rows where Rocket is in hand+affordable and ``base`` holds: what the pro did vs what the model's argmax does."""
    i = np.flatnonzero(play & r_aff & base)
    r = rep[i]
    o = {"n_play_rows_rocket_affordable": int(len(i)), "n_replays": int(len(set(r.tolist())))}
    if not len(i):
        return o
    o["pro_plays_Rocket_share"] = boot(ycard[i] == RK, r)
    o["model_argmax_is_Rocket_share"] = boot(arg_is_R[i], r)
    o["mean_P(Rocket)_over_affordable"] = boot(PR_aff[i], r)
    for t in TAUS:
        o[f"model_would_fire_Rocket_tau{t}"] = boot(arg_is_R[i] & (p_play[i] > t), r)
    pos = ycard[i] == RK
    o["pro_Rocket_rows_argmax_Rocket"] = boot(arg_is_R[i][pos], r[pos]) if pos.any() else None
    o["AUC_P(Rocket)_separates_pro_Rocket_vs_other"] = auc(pos.astype(int), PR_aff[i])
    return o


R["contrast"] = {
    "pro_Rocket_plays_Rocket_affordable": contrast(Pm_aff, "P"),
    "pro_OTHER_plays_Rocket_in_hand_and_affordable": contrast(Qm, "Q"),
}
R["situations_play_rows_rocket_affordable"] = {
    "all": sit_table("all", np.ones(n, bool)),
    "late": sit_table("late", late),
    "late & level crowns": sit_table("", late & level),
    "late & behind (crowns or level+HP deficit)": sit_table("", late & deficit_any),
    "late & behind on crowns": sit_table("", late & behind_cr),
    "overtime & behind (crowns or HP)": sit_table("", overtime & deficit_any),
    "late & ahead on crowns": sit_table("", late & ahead_cr),
    "not late": sit_table("", ~late),
}

# logit-bias / sampling sweep: Rocket-affordable play rows; recall on pro Rocket rows vs false-fire on other pro plays
i_all = np.flatnonzero(play & r_aff)
isP = ycard[i_all] == RK
rr = rep[i_all]
sweep = {}
for d in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0):
    L2 = lg_aff[i_all].copy()
    Rc = isR[i_all] & afford[i_all]
    L2 = np.where(Rc, L2 + d, L2)
    fire = (L2.argmax(1) == np.argmax(isR[i_all], 1)) & (p_play[i_all] > TAUS[1])
    arg = L2.argmax(1) == np.argmax(isR[i_all], 1)
    sweep[f"bias+{d}"] = {"argmax_R_recall_on_pro_Rocket": boot(arg[isP], rr[isP]), "argmax_R_false_rate_on_other_plays": boot(arg[~isP], rr[~isP]),
                          "fire_tau0.35_recall": boot(fire[isP], rr[isP]), "fire_tau0.35_false_rate": boot(fire[~isP], rr[~isP]),
                          "precision_argmax(pro Rocket share among argmax-R rows)": float(isP[arg].mean()) if arg.any() else None}
samp = {}
for T in (1.0, 0.7):
    Pt = softmax_rows(lg_aff[i_all] / T)
    pr = (Pt * (isR[i_all] & afford[i_all])).sum(1)
    samp[f"sample_T{T}"] = {"E[pick Rocket] on pro Rocket rows": boot(pr[isP], rr[isP]), "E[pick Rocket] on other pro plays": boot(pr[~isP], rr[~isP])}
R["sweeps"] = {"rows": "play rows with Rocket affordable", "n_pro_Rocket": int(isP.sum()), "n_other": int((~isP).sum()),
               "AUC_P(Rocket|affordable)_pro_Rocket_vs_other": auc(isP.astype(int), PR_aff[i_all]),
               "logit_bias": sweep, "sampling": samp,
               "pro_Rocket_share_in_these_rows": float(isP.mean())}
# decision-rule replay: Rocket share of decided plays over all val icebow rows
dec = {}
for t in TAUS:
    for nm, mk in (("play_rows", play), ("wait_rows", ~play), ("all_rows", np.ones(n, bool))):
        d = mk & any_aff & (p_play > t)
        dec[f"tau{t}_{nm}"] = {"n_decisions": int(d.sum()), "rocket_share": float(arg_is_R[d].mean()) if d.any() else None,
                               "decision_rate": float(d.sum() / max(mk.sum(), 1))}
R["decision_rule_replay"] = dec
R["pro_card_share_play_rows"] = {CV[c]: float(((ycard == c) & play).sum() / play.sum()) for c in np.unique(ycard[play])}
am_card = np.where(any_aff, hand[np.arange(n), am_aff], 0)
R["model_argmax_card_share_play_rows_tau0.35"] = {CV[c]: float(((am_card == c) & play & (p_play > 0.35)).sum() / max((play & (p_play > 0.35) & any_aff).sum(), 1)) for c in np.unique(am_card) if c}
log("contrast/sweeps done")

# ===================================================================================== dead-lane X-Bow
xb_sc, xb_cell = None, None


def lane_of_x(tx):
    return np.where(tx <= 7.0, "left", np.where(tx >= 11.0, "right", "center"))


def deadlane_block(scm, cellm, repm, splitm=None):
    """pro X-Bow plays with EXACTLY ONE enemy princess destroyed (alive flag opp L/R)."""
    al = scm[:, 64 + 4:64 + 6] > 0.5                      # opp L, R princess alive flags
    one = al.sum(1) == 1
    dead_left = ~al[:, 0]
    tx = (cellm % GX) / 2.0
    ln = lane_of_x(tx)
    dead_lane = np.where(dead_left, "left", "right")
    alive_lane = np.where(dead_left, "right", "left")
    return one, ln, dead_lane, alive_lane


o = {}
one, ln, dl, alv = deadlane_block(xb_all_sc, xb_all_cell, xb_all_rep)
for nm, m in (("pro_all_splits_icebow_deck", np.ones(len(xb_all), bool)), ("pro_val_only", xb_all_split == 1), ("pro_train_only", xb_all_split == 0)):
    mm = m & one
    r = xb_all_rep[mm]
    o[nm] = {"n_xbow_plays": int(m.sum()), "n_one_princess_down": int(mm.sum()), "n_replays": int(len(set(r.tolist()))),
             "own_half_share": float(((xb_all_cell[mm] // GX) > GY // 2).mean()) if mm.any() else None,
             "in_dead_lane": boot(ln[mm] == dl[mm], r), "in_alive_lane": boot(ln[mm] == alv[mm], r), "center(7<x<11)": boot(ln[mm] == "center", r),
             "dead_lane_AND_enemy_half(pocket, cy<=32)": boot((ln[mm] == dl[mm]) & (xb_all_cell[mm] // GX <= GY // 2), r),
             "dead_lane_AND_own_half": boot((ln[mm] == dl[mm]) & (xb_all_cell[mm] // GX > GY // 2), r),
             "alive_lane_AND_enemy_half": boot((ln[mm] == alv[mm]) & (xb_all_cell[mm] // GX <= GY // 2), r),
             "dead_lane_share_of_lane_placements(excl center)": boot((ln[mm] == dl[mm])[ln[mm] != "center"], r[ln[mm] != "center"]) if (ln[mm] != "center").any() else None}
R["dead_lane_xbow_pro"] = o

# model on VAL X-Bow plays (teacher-forced on the card, like the cell head in live)
vx = np.flatnonzero(play & (ycard == XB))
vsc = sc[vx]
vcell = sub["y_cell"][vx].astype(int)
one, ln, dl, alv = deadlane_block(vsc, vcell, rep[vx])
cp = np.stack([cell_p[cell_row[int(k)]] for k in vx])
am = cp.argmax(1)
lane_am = lane_of_x((am % GX) / 2.0)
txall = TX
mass = {}
for nm, mk in (("dead_lane", None), ("alive_lane", None)):
    pass
mm = one
idx1 = np.flatnonzero(mm)
r1 = rep[vx][mm]
tgt_dead = np.where((~(vsc[:, 64 + 4] > 0.5))[mm], "left", "right")
tgt_alive = np.where(tgt_dead == "left", "right", "left")
lane_cells = {"left": txall <= 7.0, "right": txall >= 11.0, "center": (txall > 7.0) & (txall < 11.0)}
mass_dead = np.array([cp[i][lane_cells[tgt_dead[j]]].sum() for j, i in enumerate(idx1)])
mass_alive = np.array([cp[i][lane_cells[tgt_alive[j]]].sum() for j, i in enumerate(idx1)])
mass_cent = np.array([cp[i][lane_cells["center"]].sum() for i in idx1])
am_lane1 = lane_am[mm]
pro_lane1 = ln[mm]
hs = vx[mm]
R["dead_lane_xbow_model_val"] = {
    "n_xbow_plays": int(len(vx)), "n_one_princess_down": int(mm.sum()), "n_replays": int(len(set(r1.tolist()))),
    "pro_lane": {"dead": boot(pro_lane1 == tgt_dead, r1), "alive": boot(pro_lane1 == tgt_alive, r1), "center": boot(pro_lane1 == "center", r1)},
    "model_argmax_lane": {"dead": boot(am_lane1 == tgt_dead, r1), "alive": boot(am_lane1 == tgt_alive, r1), "center": boot(am_lane1 == "center", r1)},
    "model_cell_mass": {"dead": boot(mass_dead, r1), "alive": boot(mass_alive, r1), "center": boot(mass_cent, r1)},
    "argmax_lane_equals_pro_lane": boot(am_lane1 == pro_lane1, r1),
    "pro_dead_lane_enemy_half(pocket)": boot((pro_lane1 == tgt_dead) & (vcell[mm] // GX <= GY // 2), r1),
    "pro_dead_lane_own_half": boot((pro_lane1 == tgt_dead) & (vcell[mm] // GX > GY // 2), r1),
    "model_argmax_dead_lane_enemy_half(pocket)": boot((am_lane1 == tgt_dead) & (am[mm] // GX <= GY // 2), r1),
    "model_argmax_dead_lane_own_half": boot((am_lane1 == tgt_dead) & (am[mm] // GX > GY // 2), r1),
    "model_mass_dead_lane_enemy_half": boot(np.array([cp[i][lane_cells[tgt_dead[j]] & (CY <= GY // 2)].sum() for j, i in enumerate(idx1)]), r1),
    "model_mass_dead_lane_own_half": boot(np.array([cp[i][lane_cells[tgt_dead[j]] & (CY > GY // 2)].sum() for j, i in enumerate(idx1)]), r1),
    "argmax_lane_in_pro_lane_given_both_non_center": boot((am_lane1 == pro_lane1)[(am_lane1 != "center") & (pro_lane1 != "center")], r1[(am_lane1 != "center") & (pro_lane1 != "center")]),
    "model_argmax_card_is_XBow(affordable,at pro rows)": boot(((am_card[hs]) == XB), r1),
    "P(X-Bow)_over_affordable_mean": boot(np.array([(P_aff[i] * (hand[i] == XB)).sum() for i in hs]), r1)}
# also: all X-Bows split by number of enemy princesses down (0/1/2) for the argmax lane: how the model's lane tracks alive/dead flags
R["dead_lane_xbow_model_val"]["by_alive_flags"] = dict(Counter(int((vsc[k, 64 + 4:64 + 6] > 0.5).sum()) for k in range(len(vx))))
# label cross-check for X-Bow lane_state (labels' target-tower rule)
xl = []
for k in vx[mm]:
    xl.append(lab.get((str(tags[rep[k]]), int(side[k]), int(tick[k]), "x-bow")))
R["dead_lane_xbow_model_val"]["label_join"] = int(sum(x is not None for x in xl))
if all(x is not None for x in xl):
    ls = np.array([x["lane_state"] for x in xl]); off_l = np.array([bool(x["offensive_xbow"]) for x in xl])
    R["dead_lane_xbow_model_val"]["label_lane_state_dead_share"] = boot(ls == "dead", r1)
    R["dead_lane_xbow_model_val"]["label_offensive_lock_share"] = boot(off_l, r1)
    R["dead_lane_xbow_model_val"]["label_lane_state_vs_sc_dead_lane_agree"] = float(((ls == "dead") == (pro_lane1 == tgt_dead))[pro_lane1 != "center"].mean())
log("dead-lane done")

json.dump(R, open(OUT / "results.json", "w"), indent=1, default=float)
print("done", OUT / "results.json")
