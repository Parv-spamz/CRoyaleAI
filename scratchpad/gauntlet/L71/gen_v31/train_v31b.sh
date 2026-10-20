#!/bin/bash
# gen_v3.1b (lead 2026-10-04): gen_v3.1a's exact recipe + six-target context weighting 2.0 (Codex C2 artifact).
cd /c/Users/benpe/ClashBot; G=scratchpad/gauntlet/L71/gen_v31
echo "[v31b] train start $(date '+%F %T')" >> $G/chain.log
icebow/.venv/Scripts/python.exe -u scratchpad/gauntlet/L69/gen_v2/_train_every_epoch.py --data icebow/data/pipeline/gen_dataset_v31_public.npz --seed 0 --epochs 4 --val-sample 30000 --grid lattice --feature-version 4 --amp bf16 --allow-causal-tti-unknowns --rocket-context-weight 2.0 --rocket-context-artifact .foreman/codex_autopilot/runs/public_context/artifact.json --out-dir icebow/data/pipeline/gen_v31b_s0 > $G/train_v31b.out 2>&1
echo "[v31b] train exit $? $(date '+%F %T')" >> $G/chain.log
