"""R2 pre-flight 3 (reward_plan.md §3.3): per-decision shaped returns of scripted policies. No degenerate policy may
have a higher mean than the IL policy.

    research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L69/rshape/scripted_audit.py \
        --out scratchpad/gauntlet/L69/rshape/audit_M --matches M [--w-tower 0.3 --w-crown 0.3] [--gamma 0.999] \
        [--lams 1.0,0.95] [--policies il,never,...] [--workers 2] [--threads 2] [--smoke]

Every policy (common.POLICIES) plays the same seeds (same opponent deck, side, deal). Rows = training's KEPT rows
(gate_sampled | played, rl_royale.collate), discounted per kept row; rewards = rl_royale.terminal_rewards (z on the
last kept row) + rl_royale.shaping_rewards (Phi per kept row, Phi = 0 after the last). Per kept row t of a match with
T kept rows and outcome z (+1 / -1 / 0): r_t = F_t + [t == T-1] z, G_t = sum_k (gamma lam)^(k-t) r_k: the lambda-return
with NO critic (V = 0); lam 1 = the plain return-to-go the plan specifies. Split G_t = terminal part
z (gamma lam)^(T-1-t) + shaping part (at lam 1 exactly -Phi(s_t), reward_shaping docstring). "Advantage" = G_t minus
ONE baseline, the mean G over every policy's matches (a constant, so the ranking is the ranking of mean G). Means
weight every MATCH equally, as rl_royale.match_weights does in training (each match's rows sum to 1/M); row-pooled
means (which favour long matches) are kept as information. Rankings reported for G (R1+R2), the terminal part alone (R1) and the shaping part alone. Per lam, two flag
lists: degenerate policies whose match-weighted mean beats il's under the COMBINED return, and under the TERMINAL-ONLY
(R1) return. VERDICT (plan 3b, at the first lam, default 1): STOP only for a policy flagged in BOTH lists (a
combined-only flag is the -Phi(s_t) bias below, not a shaping exploit). Writes <out>/audit.json; exit 2 only on STOP.

CAVEAT (read before trusting the verdict): the shaping part of G_t is -Phi(s_t) -- it is HIGHER when we are behind.
A policy that sits behind all match gets a shaping bonus on every decision without any action having earned it; in
expectation it is a state-only baseline (no policy-gradient bias), but it moves this audit's MEAN. Read the
terminal-only and shaping-only rankings next to the combined one. lam < 1 (V = 0) is the action-dependent view: its
shaping part is ~ the potential GAINED over the next ~1/(1 - gamma lam) decisions (lam 0.95: ~20 decisions = 10 s),
i.e. what a short-horizon GAE would credit the shaping for; there the terminal part reaches only the last decisions.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C                                   # noqa: E402
from pipeline import reward_shaping as RS            # noqa: E402


def main() -> int:
    ap = C.cli(__doc__)
    ap.add_argument("--w-tower", type=float, default=0.3, help="plan 3b hard bound (magnitude_budget's proposal)")
    ap.add_argument("--w-crown", type=float, default=0.3)
    ap.add_argument("--gamma", type=float, default=0.999, help="per KEPT row (rl_royale gae_gamma)")
    ap.add_argument("--lams", default="1.0,0.95", help="lambda-returns with V = 0; the first is the verdict's")
    ap.add_argument("--policies", default=",".join(C.POLICIES))
    a = ap.parse_args()
    pols = [p for p in a.policies.split(",") if p]
    if "il" not in pols or any(p not in C.POLICIES for p in pols):
        raise SystemExit(f"--policies must include il and be drawn from {C.POLICIES}")
    g, w, lams = a.gamma, (a.w_tower, a.w_crown), [float(x) for x in a.lams.split(",") if x]

    def reduce(rec: dict) -> dict:
        sh = C.kept_shaping(rec, g, *w)
        T, r = len(sh["F"]), sh["r"]
        keep = ("policy", "seed", "outcome", "z", "crowns_for", "crowns_against", "decisions", "kept_rows",
                "plays_attempted", "plays_accepted", "crowns_derivation_mismatch", "wall_s")
        out = {**{k: rec[k] for k in keep}, "F": np.asarray(sh["F"]), "lam": {}}
        for lam in lams:
            G = np.array(RS.returns_to_go(r, g * lam))
            term = rec["z"] * (g * lam) ** np.arange(T - 1, -1, -1, dtype=np.float64)
            out["lam"][lam] = {"G": G, "term": term, "shape": G - term}
        return out

    played = C.play_all(a, pols, reduce)
    rows = [r for r in played if r["kept_rows"]]       # a match with no kept row adds nothing to training
    per = {}
    for p in pols:
        rs = [r for r in rows if r["policy"] == p]
        if not rs:
            continue
        per[p] = {"matches": len(rs), "decisions": int(sum(r["decisions"] for r in rs)),
                  "kept_rows": int(sum(r["kept_rows"] for r in rs)),
                  "matches_without_kept_rows": sum(r["policy"] == p and not r["kept_rows"] for r in played),
                  "win": sum(r["outcome"] == "win" for r in rs), "loss": sum(r["outcome"] == "loss" for r in rs),
                  "draw": sum(r["outcome"] == "draw" for r in rs), "z_mean": C.mean(r["z"] for r in rs),
                  "F_mean": float(np.concatenate([r["F"] for r in rs]).mean()),
                  "plays_accepted_mean": C.mean(r["plays_accepted"] for r in rs),
                  "plays_attempted_mean": C.mean(r["plays_attempted"] for r in rs),
                  "crowns_diff_mean": C.mean(r["crowns_for"] - r["crowns_against"] for r in rs)}
    il = {r["seed"]: r for r in rows if r["policy"] == "il"}
    by_lam = {}
    for lam in lams:
        base = C.mean(r["lam"][lam]["G"].mean() for r in rows)
        st = {}
        for p in per:
            rs = [r for r in rows if r["policy"] == p]
            G, term, shape = (np.concatenate([r["lam"][lam][k] for r in rs]) for k in ("G", "term", "shape"))
            mm = (lambda k: C.mean(r["lam"][lam][k].mean() for r in rs))   # training's weight: each match 1/M
            d = np.array([r["lam"][lam]["G"].mean() - il[r["seed"]]["lam"][lam]["G"].mean() for r in rs
                          if r["seed"] in il])
            sd = float(d.std(ddof=1)) if d.size > 1 else 0.0
            st[p] = {"adv_mean": mm("G") - base, "adv_std": float(G.std()), "G_mean": mm("G"),
                     "terminal_part_mean": mm("term"), "shaping_part_mean": mm("shape"),
                     "row_pooled (information)": {"G_mean": float(G.mean()), "terminal_part_mean": float(term.mean()),
                                                  "shaping_part_mean": float(shape.mean())},
                     "paired_vs_il": {"n": int(d.size), "mean": float(d.mean()) if d.size else math.nan,
                                      "t": float(d.mean() / (sd / math.sqrt(d.size))) if sd > 0 else None}}

        def rank(key):
            return sorted(st, key=lambda p: -st[p][key])

        def above_il(key):
            return [p for p in st if p != "il" and st[p][key] > st["il"][key]]

        by_lam[str(lam)] = {"baseline_G": base, "rank_G_R1R2": rank("G_mean"),
                            "rank_terminal_R1": rank("terminal_part_mean"), "rank_shaping_only": rank("shaping_part_mean"),
                            "flags_combined": above_il("G_mean"), "flags_terminal_only": above_il("terminal_part_mean"),
                            "per_policy": st}
        v = by_lam[str(lam)]
        print(f"[audit] lam {lam}: combined (R1+R2) {' > '.join(v['rank_G_R1R2'])} | flags {v['flags_combined']}",
              flush=True)
        print(f"[audit] lam {lam}: terminal-only (R1) {' > '.join(v['rank_terminal_R1'])} | flags "
              f"{v['flags_terminal_only']}", flush=True)
    v = by_lam[str(lams[0])]
    stop = [p for p in v["flags_combined"] if p in v["flags_terminal_only"]]
    if stop:
        reason = f"{stop} beat il under BOTH the combined and the terminal-only return (lam {lams[0]})"
    elif v["flags_combined"]:
        reason = (f"{v['flags_combined']} beat il only under the combined return: the -Phi(s_t) state-only bias "
                  f"(plan 3b), not a STOP")
    else:
        reason = "no degenerate policy beats il under the combined return"
    print(f"[audit] verdict {'STOP: redesign' if stop else 'pass'}: {reason}", flush=True)
    C.write(a.out, "audit.json", {
        "gamma": g, "weights": {"w_tower": w[0], "w_crown": w[1]}, "verdict_lam": lams[0],
        "verdict": "STOP: redesign" if stop else "pass", "verdict_reason": reason, "stop_policies": stop,
        "flags_combined": v["flags_combined"], "flags_terminal_only": v["flags_terminal_only"],
        "per_policy": per, "by_lam": by_lam,
        "per_match": [{k: x for k, x in r.items() if k != "lam" and not isinstance(x, np.ndarray)} for r in played]})
    return 2 if stop else 0


if __name__ == "__main__":
    raise SystemExit(main())
