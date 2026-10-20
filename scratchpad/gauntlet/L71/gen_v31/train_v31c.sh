#!/bin/bash
# gen_v3.1c (lead 2026-10-04, owner: stronger weight): gen_v3.1b recipe with weight 4.0 (Codex C2 artifact).
cd /c/Users/benpe/ClashBot; G=scratchpad/gauntlet/L71/gen_v31
echo "[v31c] train start $(date '+%F %T')" >> $G/chain.log
icebow/.venv/Scripts/python.exe -u scratchpad/gauntlet/L69/gen_v2/_train_every_epoch.py --data icebow/data/pipeline/gen_dataset_v31_public.npz --seed 0 --epochs 4 --val-sample 30000 --grid lattice --feature-version 4 --amp bf16 --allow-causal-tti-unknowns --rocket-context-weight 4.0 --rocket-context-artifact .foreman/codex_autopilot/runs/public_context_w4/artifact.json --out-dir icebow/data/pipeline/gen_v31c_s0 > $G/train_v31c.out 2>&1
echo "[v31c] train exit $? $(date '+%F %T')" >> $G/chain.log
