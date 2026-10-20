"""R2 pre-flight 1 (reward_plan.md §3.1): on N played IL matches, sum_t gamma^t F_t == -Phi(s_0) to float precision.

    research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L69/rshape/telescope_check.py \
        --out scratchpad/gauntlet/L69/rshape/telescope_100 --matches 100 [--workers 2] [--threads 2] [--smoke]

Checked on the real raw() states for gamma 1 and 0.999 and three weight pairs: the discounted sum identity, the
undiscounted one at gamma 1, the per-term breakdown summing to F, and that every decision's shaping return-to-go is
-Phi(s_t). The same three on training's KEPT rows (gate_sampled | played, gamma per kept row) through rl_royale's
own shaping_rewards / terminal_rewards (``err_kept_*``). Also counts decisions where crowns derived from the towers
disagree with the engine's own crowns, and records kept-row counts per match.
Writes <out>/telescope.json; exit 1 if any check fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np                                   # noqa: E402

import common as C                                   # noqa: E402
from pipeline import reward_shaping as RS            # noqa: E402

TOL = 1e-9
GAMMAS = (1.0, 0.999)
WEIGHTS = ((1.0, 1.0), (1.0, 0.0), (0.3, 0.7))


def reduce(rec: dict) -> dict:
    states, L = rec["_states"], rec["learner_side"]
    err = {"sum_discounted": 0.0, "breakdown": 0.0, "rtg": 0.0}
    for g in GAMMAS:
        for w in WEIGHTS:
            sh = RS.shaping_terms(states, L, g, w)
            phi0 = RS.phi(states[0], L, *w)
            err["sum_discounted"] = max(err["sum_discounted"], abs(sum(g ** t * f for t, f in enumerate(sh["F"])) + phi0))
            err["breakdown"] = max(err["breakdown"], max(abs(a + b - f) for a, b, f in zip(sh["tower"], sh["crown"], sh["F"])))
            err["rtg"] = max(err["rtg"], max(abs(G + RS.phi(s, L, *w)) for G, s in zip(RS.returns_to_go(sh["F"], g), states)))
            k = C.kept_shaping(rec, g, *w)                 # training's rows: Phi per kept row, terminal after the last
            if len(k["F"]):
                Gk = np.array(RS.returns_to_go(k["F"], g))
                err["kept_sum_discounted"] = max(err.get("kept_sum_discounted", 0.0),
                                                 abs(float((g ** np.arange(len(k["F"])) * k["F"]).sum() + k["phi"][0])))
                err["kept_breakdown"] = max(err.get("kept_breakdown", 0.0), float(np.abs(k["tower"] + k["crown"] - k["F"]).max()))
                err["kept_rtg"] = max(err.get("kept_rtg", 0.0), float(np.abs(Gk + k["phi"]).max()))
                err["kept_phi_vs_state"] = max(err.get("kept_phi_vs_state", 0.0), float(np.abs(
                    k["phi"] - np.array([RS.phi(s, L, *w) for s, kp in zip(states, rec["keep"]) if kp])).max()))
    ph = [RS.phi(s, L, 1.0, 1.0) for s in states]
    return {"seed": rec["seed"], "decisions": rec["decisions"], "kept_rows": rec["kept_rows"], "phi0_w11": ph[0],
            "min_phi_w11": min(ph),
            "max_phi_w11": max(ph),
            "crowns_derivation_mismatch": rec["crowns_derivation_mismatch"], **{f"err_{k}": v for k, v in err.items()}}


def main() -> int:
    a = C.cli(__doc__).parse_args()
    rows = C.play_all(a, ["il"], reduce)
    worst = {k: max(r.get(k, 0.0) for r in rows) for k in ("err_sum_discounted", "err_breakdown", "err_rtg",
                                                            "err_kept_sum_discounted", "err_kept_breakdown",
                                                            "err_kept_rtg", "err_kept_phi_vs_state")}
    ok = all(v < TOL for v in worst.values())
    C.write(a.out, "telescope.json", {
        "pass": ok, "tol": TOL, "gammas": GAMMAS, "weights": WEIGHTS, "matches": len(rows),
        "worst": worst, "max_abs_phi0": max(abs(r["phi0_w11"]) for r in rows),
        "kept_rows": [r["kept_rows"] for r in rows], "decisions": [r["decisions"] for r in rows],
        "crowns_derivation_mismatch_total": sum(r["crowns_derivation_mismatch"] for r in rows),
        "per_match": rows})
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
