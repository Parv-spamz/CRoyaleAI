"""L68e: does e1_eval.run_batch's now-BATCHED decide (live_decide_batch, one cell_logits call per round for
every playing row -- not one per match) reproduce the sequential run_match? Copy of batch_parity.py, but the
reference is scratchpad/gauntlet/L68/rank_tornado/v6aug_s1 (real Tornado, NO card substitutions) instead of
L68/rank's v6aug_s1_sh* (which were made with Tornado->Arrows): that reference's env must also carry no subs,
or a genuinely different card would make every play sequence differ.

    research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L68/batch_parity2.py [--n 29] [--device cuda]

Acceptance (ticket L68e/1): identical play sequence (tick, slot, cell) 58/58 and same outcome 58/58.
"""
import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
import torch  # noqa: E402

from pipeline import e1_eval as E  # noqa: E402
from pipeline import engine_play as ep  # noqa: E402
from pipeline.e1_pool import load_pool_v1, select_split  # noqa: E402
from pipeline.obs_contract import load_deck  # noqa: E402
from pipeline.royale_env import RoyalePoolEnv, UnsupportedDeck  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=29)
ap.add_argument("--device", default="cuda")
a = ap.parse_args()
torch.set_num_threads(2)

ref = {}
for line in (REPO / "scratchpad/gauntlet/L68/rank_tornado/v6aug_s1/matches.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(line)
    ref[r["tag"]] = r
model, minfo = ep.load_model(REPO / "icebow/data/pipeline/s1_icebow_v6aug_s1.pt", a.device)
cfg = {"policy": "live", "tau": E.TAU_LIVE, "afford_mask": True, "stall_elixir": E.STALL_ELIXIR_LIVE,
       "stall_seconds": E.STALL_SECONDS_LIVE, "obs": "live", "noise": E.parse_noise_off(""), "p_random": 0.09,
       "random_hand_only": False, "grid": minfo.get("grid", "floor"), "device": a.device,
       "decide_every": E.DECIDE_EVERY, "slot": 0, "port": 0}
entries = select_split(load_pool_v1(), "heldout")
jobs = [(i, e, 0) for i, e in enumerate(entries) if e["tag"] in ref]
out = []
t0 = time.perf_counter()
E.run_batch(lambda: RoyalePoolEnv(), model, load_deck("icebow"), jobs, cfg, a.n,          # NO subs -- real Tornado
            on_result=out.append, skip=(UnsupportedDeck,))
wall = time.perf_counter() - t0
same_outcome = sum(r["outcome"] == ref[r["tag"]]["outcome"] for r in out)
key = (lambda r: [(p["tick"], p["slot"], p["cell"]) for p in r["plays"]])
same_plays = sum(key(r) == key(ref[r["tag"]]) for r in out)
mismatches = [r["tag"] for r in out if key(r) != key(ref[r["tag"]])]
print(json.dumps({"matches": len(out), "n_in_flight": a.n, "device": a.device, "wall_s": round(wall, 1),
                  "s_per_match": round(wall / max(len(out), 1), 2),
                  "same_outcome": f"{same_outcome}/{len(out)}", "identical_play_sequence": f"{same_plays}/{len(out)}",
                  "wins_batched": sum(r["outcome"] == "win" for r in out),
                  "wins_reference": sum(ref[r["tag"]]["outcome"] == "win" for r in out),
                  "mismatched_tags": mismatches}))
