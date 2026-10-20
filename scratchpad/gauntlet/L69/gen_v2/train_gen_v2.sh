#!/bin/bash
# gen_v2 = gen_v1_s0's exact recipe with ONE change, the dataset (gen_dataset_v1 -> gen_dataset_v2, the 3153fa4
# wait-label fix). gen_v1_s0 command (HANDOFF 2026-09-24 "RUNNING: first full generalist training"):
#   icebow/.venv/Scripts/python.exe -m pipeline.train_gen --data icebow/data/pipeline/gen_dataset_v1.npz --seed 0
#     --epochs 4 --val-sample 30000 --grid lattice --out-dir icebow/data/pipeline/gen_v1_s0
# Every other hyper-parameter is train_gen's default, as stored in gen_v1_s0/gen_s0.pt "args" (bs 256, lr 3e-4,
# d 128, layers 4, d_c 64, mirror on, deck_weighting none, limit_rows 0, select cell_tile_top1, tag ""), and the
# trainer code is unchanged since 748021b (before gen_v1 started). Device: cuda (train_gen picks cuda if available).
# Only addition: _train_every_epoch.py also saves gen_s0_ep<k>.pt after every epoch (selection: select.sh).
#
# Real run (waits for an idle GPU first; ~3.6 h uncontended, ~5.8 h if contended like gen_v1):
#   bash scratchpad/gauntlet/L69/gen_v2/train_gen_v2.sh > scratchpad/gauntlet/L69/gen_v2/train_gen_v2.out 2>&1
# Overrides (smoke only): DATA, OUT, EXTRA (appended train_gen args; argparse keeps the LAST value), NO_GPU_WAIT=1.
set -euo pipefail
cd /c/Users/benpe/ClashBot
G=scratchpad/gauntlet/L69/gen_v2
DATA=${DATA:-icebow/data/pipeline/gen_dataset_v2.npz}
OUT=${OUT:-icebow/data/pipeline/gen_v2_s0}
if [ -e "$OUT" ] && [ -n "$(ls -A "$OUT")" ]; then echo "REFUSING: $OUT exists and is not empty"; exit 1; fi
source $G/gpu_wait.sh
[ "${NO_GPU_WAIT:-0}" = 1 ] || gpu_wait
echo "[train_gen_v2] start $(date) data=$DATA out=$OUT extra=${EXTRA:-}"
icebow/.venv/Scripts/python.exe $G/_train_every_epoch.py --data "$DATA" --seed 0 --epochs 4 --val-sample 30000 \
  --grid lattice --out-dir "$OUT" ${EXTRA:-}
echo "[train_gen_v2] done $(date)"
