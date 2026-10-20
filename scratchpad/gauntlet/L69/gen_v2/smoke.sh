#!/bin/bash
# CPU smoke of train_gen_v2.sh + select.sh code paths (no GPU: CUDA hidden). Builds a tiny npz from 7 replays of
# gen_dataset_v2 by STREAMING the members (the full set is 2.2 GB in RAM; a few MB here), trains 1 epoch on 300 rows,
# runs select_gen_v2.py on it (CPU, 1 reactive seed vs S1), checks ep1 == train_gen's own checkpoint, deletes everything.
set -euo pipefail
cd /c/Users/benpe/ClashBot
G=scratchpad/gauntlet/L69/gen_v2
S=$G/_smoke
mkdir -p $S
# CUDA_VISIBLE_DEVICES must be -1: an EMPTY value did NOT hide the GPU from this torch build (measured 2026-10-01:
# the first smoke trained on cuda, gpu_peak_mb 2139). Abort unless torch sees no device.
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 CUDA_VISIBLE_DEVICES=-1
icebow/.venv/Scripts/python.exe -c "import torch,sys; sys.exit(torch.cuda.is_available())" || { echo "CUDA VISIBLE, abort"; exit 1; }
research/ext/Royale/.venv/Scripts/python.exe -c "import torch,sys; sys.exit(torch.cuda.is_available())" || { echo "CUDA VISIBLE, abort"; exit 1; }
icebow/.venv/Scripts/python.exe - "$S/tiny.npz" <<'EOF'
import sys, zipfile, numpy as np
from numpy.lib import format as F
src = "icebow/data/pipeline/gen_dataset_v2.npz"
z = np.load(src); rep, split, v3 = z["rep"], z["split"], z["v3val"]
reps = list(np.unique(rep[v3 == 1])[:2]) + list(np.unique(rep[(split == 1) & (v3 == 0)])[:2]) + list(np.unique(rep[split == 0])[:3])
sel = np.sort(np.where(np.isin(rep, reps))[0]); off = z["off"]
tsel = np.concatenate([np.arange(off[i], off[i + 1]) for i in sel])
zf = zipfile.ZipFile(src)
def take(name, ids):
    f = zf.open(name); F.read_magic(f); shape, _, dt = F.read_array_header_1_0(f)
    rb = int(np.prod(shape[1:], dtype=np.int64)) * dt.itemsize; ch = max(1, (32 << 20) // rb); out, s, j = [], 0, 0
    while j < len(ids):
        n = min(ch, shape[0] - s); buf = np.frombuffer(f.read(n * rb), dt).reshape((n,) + shape[1:])
        k = np.searchsorted(ids, s + n); out.append(buf[ids[j:k] - s].copy()); j, s = k, s + n
    return np.concatenate(out)
o = {}
for n in z.files:
    if n in ("tags", "meta"): o[n] = z[n]
    elif n == "off": o[n] = np.concatenate([[0], np.cumsum(off[sel + 1] - off[sel])]).astype(off.dtype)
    elif n == "tok": o[n] = take("tok.npy", tsel)
    else: o[n] = take(n + ".npy", sel)
np.savez(sys.argv[1], **o)
print({"rows": len(sel), "tokens": len(tsel), "train": int((o["split"] == 0).sum()), "val": int((o["split"] == 1).sum()),
       "v3val": int(o["v3val"].sum()), "play": int(o["y_gate"].sum())})
EOF
echo "== train smoke"
DATA=$S/tiny.npz OUT=$S/ckpt NO_GPU_WAIT=1 EXTRA="--limit-rows 300 --epochs 1 --val-sample 200" bash $G/train_gen_v2.sh
echo "== refuse check (OUT non-empty)"
DATA=$S/tiny.npz OUT=$S/ckpt NO_GPU_WAIT=1 bash $G/train_gen_v2.sh && exit 1 || true
icebow/.venv/Scripts/python.exe - "$S/ckpt" <<'EOF'
import sys, torch
from pathlib import Path
d = Path(sys.argv[1]); a = torch.load(d / "gen_s0.pt", map_location="cpu"); b = torch.load(d / "gen_s0_ep1.pt", map_location="cpu")
same = all(torch.equal(a["model"][k], b["model"][k]) for k in a["model"])
print({"ep1_weights_equal_train_gen_ckpt": same, "ep1_keys": sorted(b), "ep1_epoch": b["epoch"], "args_data": b["args"]["data"],
       "hist_gpu_peak_mb(None=CPU)": __import__("json").loads((d / "hist_gen_s0.json").read_text())["hist"][0]["gpu_peak_mb"]})
assert __import__("json").loads((d / "hist_gen_s0.json").read_text())["hist"][0]["gpu_peak_mb"] is None, "trained on GPU"
assert same and b["gen"] and b["card_vocab"] == a["card_vocab"]
EOF
echo "== select smoke"
NO_GPU_WAIT=1 bash $G/select.sh --ckpts "$S/ckpt/gen_s0_ep*.pt" --out $S/select --data $S/tiny.npz --device cpu \
  --seeds 0:1 --opps s1 --workers 1 --threads 2
echo "== cleanup"
rm -rf $S
echo "SMOKE OK"
