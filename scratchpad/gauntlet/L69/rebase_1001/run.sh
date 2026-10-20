#!/bin/bash
# Re-baseline gen_v1_s0 on the 2026-10-01 engine (RoyaleSim 369fe33): pinned 299 ghost screen at tau 0.27 and 0.35,
# then the reactive-play baseline (S0 harness plain arm vs frozen gen_v1 and S1, 24 seeds).
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L69/rebase_1001
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
for T in 0.27 0.35; do
  $PY $RS --ckpt icebow/data/pipeline/gen_v1_s0/gen_s0.pt --out $O/train_tau$T.jsonl --split train --noise-off all --opp-elixir counter \
      --action-delay 26 --extrapolate 26 --seeds 0 --device cuda --tau $T --only-tags-from $OLD > $O/train_tau$T.out 2>&1
done
$PY $RS --pair scratchpad/gauntlet/L68/overnight0929/train_tau0.27.jsonl $O/train_tau0.27.jsonl > $O/pair_engine_0929_vs_1001.out 2>&1
$PY -m pipeline.search_s0 --out $O/reactive_genv1 --seeds 0:24 --opps gen,s1 --arms plain --device cuda --threads 1 --workers 3 > $O/reactive_genv1.log 2>&1
echo "[rebase] done $(date)" >> $O/driver.log
