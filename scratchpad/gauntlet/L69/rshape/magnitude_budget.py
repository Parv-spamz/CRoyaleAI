"""R2 pre-flight 2 (reward_plan.md §3.2 as corrected in §3b): how loud is each shaping term next to the terminal (1)?

    research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L69/rshape/magnitude_budget.py \
        --out scratchpad/gauntlet/L69/rshape/budget_100 --matches 100 [--workers 2] [--threads 2] [--smoke]

PROPOSAL (plan §3b) = the HARD bound, not a measurement: before the terminal |phi_tower| < 1 and |phi_crown| <= 2/3
(3 crowns ends the match), so |Phi| < (5/3) w on every state ANY policy can reach; w_tower = w_crown = 0.5 / (5/3) =
0.3 keeps |Phi| (the shaping part of every return-to-go) <= 0.5 x terminal everywhere. IL matches never reach the
extremes (losing trajectories do: |Phi| ~ 1.65 at w = 1 on never-play), so the IL measurement below is INFORMATION.

Information, on N IL matches (common.py: gen_v1_s0 plain live condition vs frozen gen_v1 on census decks), on
training's KEPT rows (gate_sampled | played; gamma per kept row; Phi = 0 after the last kept row; rl_royale's own
shaping_rewards): per term (tower, crown, both at weight 1) and gamma (1, 0.999), per match |sum_t F_t| (the plan's
original metric: = |Phi(first kept row)| ~ 0 at gamma 1, it cannot bound anything), mean |F_t|, sum |F_t|, mean and
max |Phi(s_t)|; pooled over kept rows: p50/p95/p99/max |Phi|; and the same at the proposal. Writes <out>/budget.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C                                   # noqa: E402

BUDGET = 0.5
BOUND = 5 / 3                                        # max pre-terminal |phi_tower + phi_crown| at weight 1
W_PROPOSAL = BUDGET / BOUND                          # 0.3
TERMS = {"tower": (1.0, 0.0), "crown": (0.0, 1.0), "both": (1.0, 1.0)}
GAMMAS = (1.0, 0.999)


def reduce(rec: dict) -> dict:
    out = {"seed": rec["seed"], "outcome": rec["outcome"], "decisions": rec["decisions"],
           "kept_rows": rec["kept_rows"], "crowns_derivation_mismatch": rec["crowns_derivation_mismatch"], "phi": {}}
    for name, w in TERMS.items():
        for g in GAMMAS:
            k = C.kept_shaping(rec, g, *w)
            F = k["F"]
            out[f"{name}|g{g}"] = {"abs_sum_F": float(abs(F.sum())), "mean_abs_F": float(np.abs(F).mean()),
                                   "sum_abs_F": float(np.abs(F).sum())}
        ph = k["phi"]                                 # Phi per kept row (gamma-independent)
        out["phi"][name] = ph                         # pooled later (not written per match)
        out[f"{name}|phi"] = {"mean_abs_phi": float(np.abs(ph).mean()), "max_abs_phi": float(np.abs(ph).max())}
    return out


def main() -> int:
    a = C.cli(__doc__).parse_args()
    rows = [r for r in C.play_all(a, ["il"], reduce) if r["kept_rows"]]
    per_term = {}
    for name in TERMS:
        pooled = np.abs(np.concatenate([r["phi"][name] for r in rows]))
        d = {"pooled_abs_phi": {q: float(np.percentile(pooled, int(q[1:]))) for q in ("p50", "p95", "p99")}
             | {"max": float(pooled.max())},
             **{k: C.mean(r[f"{name}|phi"][k] for r in rows) for k in ("mean_abs_phi", "max_abs_phi")}}
        for g in GAMMAS:
            d[f"gamma_{g}"] = {k: C.mean(r[f"{name}|g{g}"][k] for r in rows)
                               for k in ("abs_sum_F", "mean_abs_F", "sum_abs_F")}
        per_term[name] = d
    b, s = per_term["both"], W_PROPOSAL               # every magnitude is linear in a common weight
    proposal = {"w_tower": round(W_PROPOSAL, 4), "w_crown": round(W_PROPOSAL, 4),
                "rule": "hard bound: |Phi| < (5/3) w on every pre-terminal state, <= 0.5 x terminal (plan 3b)",
                "bound_abs_phi": BOUND * W_PROPOSAL,
                "il_measured_at_proposal (information)": {
                    **{f"{q}_abs_phi": v * s for q, v in b["pooled_abs_phi"].items()},
                    "mean_abs_phi": b["mean_abs_phi"] * s,
                    "mean_abs_sum_F_g1": b["gamma_1.0"]["abs_sum_F"] * s,
                    "mean_abs_sum_F_g0.999": b["gamma_0.999"]["abs_sum_F"] * s,
                    "mean_sum_abs_F_g0.999": b["gamma_0.999"]["sum_abs_F"] * s,
                    "mean_abs_F_g0.999": b["gamma_0.999"]["mean_abs_F"] * s}}
    info = {"il_only_w_for_p99_budget": min(1.0, BUDGET / b["pooled_abs_phi"]["p99"]) if b["pooled_abs_phi"]["p99"] else 1.0,
            "note": "IL-only percentile rule (looser than the bound: IL matches never reach the extremes); NOT the proposal"}
    for r in rows:
        r.pop("phi")
    C.write(a.out, "budget.json", {
        "matches": len(rows), "terminal_magnitude": 1.0, "budget": BUDGET, "proposal": proposal,
        "wins": sum(r["outcome"] == "win" for r in rows), "losses": sum(r["outcome"] == "loss" for r in rows),
        "decisions_mean": C.mean(r["decisions"] for r in rows), "kept_rows_mean": C.mean(r["kept_rows"] for r in rows),
        "crowns_derivation_mismatch_total": sum(r["crowns_derivation_mismatch"] for r in rows),
        "unweighted_kept_rows (information)": per_term, "il_percentile_rule (information)": info, "per_match": rows})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
