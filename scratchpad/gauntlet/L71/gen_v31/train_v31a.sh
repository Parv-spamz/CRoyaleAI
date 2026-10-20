#!/bin/bash
# gen_v3.1a training relaunch (lead 2026-10-04 03:4x) after the effects_overflow gate fix (40 of 1,719,918 effects).
cd /c/Users/benpe/ClashBot; G=scratchpad/gauntlet/L71/gen_v31
echo "[v31a] train relaunch $(date '+%F %T')" >> $G/chain.log
icebow/.venv/Scripts/python.exe -u scratchpad/gauntlet/L69/gen_v2/_train_every_epoch.py --data icebow/data/pipeline/gen_dataset_v31_public.npz --seed 0 --epochs 4 --val-sample 30000 --grid lattice --feature-version 4 --amp bf16 --allow-causal-tti-unknowns --inputs-only-arm --out-dir icebow/data/pipeline/gen_v31a_s0 > $G/train_v31a.out 2>&1
echo "[v31a] train exit $? $(date '+%F %T')" >> $G/chain.log
