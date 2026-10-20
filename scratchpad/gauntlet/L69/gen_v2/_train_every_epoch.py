"""Run ``pipeline.train_gen`` UNCHANGED, plus a copy of the weights after EVERY epoch (train_gen keeps only the best).

    python _train_every_epoch.py <train_gen args...>

Hook (no pipeline/ edit): train_gen calls ``evaluate`` twice per epoch -- the all-deck val sample, then v3val -- and
once more after training (train subset, best weights reloaded). After each epoch's 2nd call the weights are saved to
``<out-dir>/gen_<tag>_ep<k>.pt`` (train_gen's own ``gen_<tag>.pt`` naming); the odd 2E+1-th call is never saved. The
wrapper returns evaluate's result untouched, so training, its RNG stream and train_gen's own selection are identical.
After ``main`` returns, each epoch file gets ``gen_<tag>.pt``'s metadata (args, gen, card_vocab, d_c, n_params, deck)
so ``eval_gen.load_model`` / ``e1_eval.load_policy`` / search_s0 load it like any train_gen checkpoint.
"""
import argparse
import sys
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from pipeline import train_gen as tg  # noqa: E402

argv = sys.argv[1:]
ap = argparse.ArgumentParser(add_help=False)
ap.add_argument("--out-dir", type=Path, required=True)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--tag", default="")
k, _ = ap.parse_known_args(argv)
tag = f"{k.tag}_s{k.seed}" if k.tag else f"s{k.seed}"          # = train_gen's naming
_evaluate, calls, last = tg.evaluate, [0], {}


def evaluate(model, rows, *a, **kw):
    r = _evaluate(model, rows, *a, **kw)
    calls[0] += 1
    if calls[0] % 2:
        last["val"] = r
    else:
        ep = calls[0] // 2
        torch.save({"model": model.state_dict(), "epoch": ep, "val": dict(last["val"], epoch=ep, v3val=r)},
                   k.out_dir / f"gen_{tag}_ep{ep}.pt")
        print(f"[every_epoch] saved gen_{tag}_ep{ep}.pt", flush=True)
    return r


tg.evaluate = evaluate
rc = tg.main(argv)
best = torch.load(k.out_dir / f"gen_{tag}.pt", map_location="cpu")
for p in sorted(k.out_dir.glob(f"gen_{tag}_ep*.pt")):
    torch.save({**best, **torch.load(p, map_location="cpu")}, p)
print(f"[every_epoch] completed metadata of {calls[0] // 2} epoch files (train_gen's pick: epoch {best['epoch']})")
raise SystemExit(rc)
