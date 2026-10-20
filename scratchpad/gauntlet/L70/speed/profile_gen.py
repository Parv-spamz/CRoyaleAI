"""GPU step-time profile of train_gen's exact step on real gen_dataset_v2 rows (owner 10-03: train as fast as
possible). Variants: base (as train_gen: fp32, 7 host syncs/step) | nosync | tf32 | bf16 (autocast) | bf16+tf32.
Same model config as gen_v1 (d 128, layers 4, d_c 64, lattice). Prints ms/step and rows/s per variant.
    icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L70/speed/profile_gen.py [--rows 200000] [--steps 60]"""
import argparse, sys, time
from pathlib import Path
import numpy as np, torch
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from pipeline.dataset import load as load_ds
from pipeline.eval_gen import GenRows
from pipeline.model_gen import GenModel
from pipeline.train_gen import losses

ap = argparse.ArgumentParser(); ap.add_argument("--rows", type=int, default=200000); ap.add_argument("--steps", type=int, default=60)
ap.add_argument("--bs", type=int, default=256); a = ap.parse_args()
arrs, meta = load_ds(Path("icebow/data/pipeline/gen_dataset_v2.npz"))
n = len(arrs["y_gate"]); idx = np.arange(min(a.rows, n))
dev = torch.device("cuda"); rows = GenRows(arrs, idx, dev)
vocab = meta["card_vocab"]; rng = np.random.default_rng(0)

def run(name, sync=True, tf32=False, bf16=False):
    torch.backends.cuda.matmul.allow_tf32 = tf32; torch.backends.cudnn.allow_tf32 = tf32
    torch.manual_seed(0)
    model = GenModel(d=128, layers=4, d_c=64, n_cards=len(vocab)).to(dev); model.train()
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
    perm = rng.permutation(idx); tot = torch.zeros((), device=dev)
    def step(s):
        nonlocal tot
        b = rows.batch(perm[s * a.bs:(s + 1) * a.bs])
        with torch.autocast("cuda", dtype=torch.bfloat16, enabled=bf16):
            loss, parts = losses(model, b, mirror=bool(s % 2), grid="lattice")
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
        if sync:
            float(loss.detach())
        else:
            tot = tot + loss.detach()
    for s in range(5): step(s)                                  # warm-up
    torch.cuda.synchronize(); t = time.time()
    for s in range(5, 5 + a.steps): step(s)
    torch.cuda.synchronize(); dt = (time.time() - t) / a.steps
    print(f"{name:10s} {dt * 1000:7.1f} ms/step  {a.bs / dt:7.0f} rows/s  peak {torch.cuda.max_memory_allocated() / 2**20:.0f} MiB", flush=True)
    torch.cuda.reset_peak_memory_stats()

print(f"rows {len(idx)} bs {a.bs} steps {a.steps}; GPU {torch.cuda.get_device_name(0)}")
run("base")
run("tf32", tf32=True)
run("bf16", bf16=True)
run("bf16+tf32", tf32=True, bf16=True)
