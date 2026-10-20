#!/bin/bash
# gen_v2 selection = GPU wait + select_gen_v2.py (joint gate+card+cell metric on the v2 val/v3val rows for gen_v1 and every
# gen_v2 epoch; then reactive play, plain arm, 24 seeds, forms deck, for the top 2 epochs and gen_v1). ~1 h on the GPU.
#   bash scratchpad/gauntlet/L69/gen_v2/select.sh > scratchpad/gauntlet/L69/gen_v2/select.out 2>&1
# Extra args go to select_gen_v2.py (e.g. --rank-key joint_top1, --skip-reactive); NO_GPU_WAIT=1 skips the wait (smoke).
set -euo pipefail
cd /c/Users/benpe/ClashBot
G=scratchpad/gauntlet/L69/gen_v2
source $G/gpu_wait.sh
[ "${NO_GPU_WAIT:-0}" = 1 ] || gpu_wait
research/ext/Royale/.venv/Scripts/python.exe $G/select_gen_v2.py --ckpts "icebow/data/pipeline/gen_v2_s0/gen_s0_ep*.pt" \
  --out $G/select "$@"
