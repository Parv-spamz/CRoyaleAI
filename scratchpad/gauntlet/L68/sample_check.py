"""L68e acceptance 2 (real-engine check): --policy sample at T=1e-4 reproduces the greedy live rule on real
Tornado RoyaleSim, on a handful of held-out entries -- complements pipeline/tests/test_e1_batch.py's synthetic-
tensor unit tests (which are tie-free by construction; here ties are real and possible, so they are reported
per row rather than treated as a failure -- rl_plan.md's sampler spec expects this).

    research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L68/sample_check.py [--n 5] [--device cuda]

Reference = rank_tornado/v6aug_s1/matches.jsonl (real Tornado, no subs, the live rule) -- the same reference
batch_parity2.py uses.
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
ap.add_argument("--n", type=int, default=5, help="held-out entries to check (first n tags of the reference, sorted)")
ap.add_argument("--device", default="cuda")
a = ap.parse_args()
torch.set_num_threads(2)

ref = {}
for line in (REPO / "scratchpad/gauntlet/L68/rank_tornado/v6aug_s1/matches.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(line)
    ref[r["tag"]] = r
tags = sorted(ref)[: a.n]

model, minfo = ep.load_model(REPO / "icebow/data/pipeline/s1_icebow_v6aug_s1.pt", a.device)
cfg = {"policy": "sample", "tau": E.TAU_LIVE, "afford_mask": True, "stall_elixir": E.STALL_ELIXIR_LIVE,
       "stall_seconds": E.STALL_SECONDS_LIVE, "obs": "live", "noise": E.parse_noise_off(""), "p_random": 0.09,
       "random_hand_only": False, "grid": minfo.get("grid", "floor"), "device": a.device,
       "decide_every": E.DECIDE_EVERY, "slot": 0, "port": 0, "T": 1e-4}
entries = select_split(load_pool_v1(), "heldout")
jobs = [(i, e, 0) for i, e in enumerate(entries) if e["tag"] in tags]
out = []
t0 = time.perf_counter()
E.run_batch(lambda: RoyalePoolEnv(), model, load_deck("icebow"), jobs, cfg, max(len(jobs), 1),   # NO subs
            on_result=out.append, skip=(UnsupportedDeck,))
wall = time.perf_counter() - t0

key = (lambda r: [(p["tick"], p["slot"], p["cell"]) for p in r["plays"]])
same = 0
diffs = []
for r in out:
    a_seq, b_seq = key(r), key(ref[r["tag"]])
    if a_seq == b_seq:
        same += 1
        continue
    i = next((j for j in range(min(len(a_seq), len(b_seq))) if a_seq[j] != b_seq[j]), min(len(a_seq), len(b_seq)))
    diffs.append({"tag": r["tag"], "first_diff_index": i, "sample_play": a_seq[i] if i < len(a_seq) else None,
                  "live_play": b_seq[i] if i < len(b_seq) else None,
                  "n_plays_sample": len(a_seq), "n_plays_live": len(b_seq)})
print(json.dumps({"n": len(out), "tags": [r["tag"] for r in out], "identical_play_sequence": f"{same}/{len(out)}",
                  "wall_s": round(wall, 1), "diffs": diffs}, indent=1))
