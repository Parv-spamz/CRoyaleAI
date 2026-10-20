#!/bin/bash
# Overnight 2026-09-29 (owner): (1) re-measure gen_v1_s0 on the updated RoyaleSim + tau sweep, (2) league1 rerun on
# the new engine -- ONE change vs league1 (the engine; same config, same entries.json 299/58, same deck census),
# capped at 200 updates so acceptance can run before the owner wakes (league1's screen plateaued from ~u150).
cd /c/Users/benpe/ClashBot
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
O=scratchpad/gauntlet/L68/overnight0929
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl   # gen_v1_s0, live condition, tau 0.27, OLD engine
CK=icebow/data/pipeline/gen_v1_s0/gen_s0.pt
echo "[drv] start $(date)"
for T in 0.27 0.5 0.15 0.2 0.35 0.65; do
  $PY $RS --ckpt $CK --out $O/train_tau$T.jsonl --split train --noise-off all --opp-elixir counter --action-delay 26 \
      --extrapolate 26 --seeds 0 --device cuda --tau $T --only-tags-from $OLD --resume > $O/train_tau$T.out 2>&1
  echo "[drv] tau $T done $(date): $(tail -1 $O/train_tau$T.out)"
done
$PY $RS --pair $OLD $O/train_tau0.27.jsonl > $O/pair_engine_old_vs_new.out 2>&1
for T in 0.5 0.15 0.2 0.35 0.65; do $PY $RS --pair $O/train_tau0.27.jsonl $O/train_tau$T.jsonl > $O/pair_tau0.27_vs_$T.out 2>&1; done
echo "[drv] pairs done $(date)"
$PY -m pipeline.rl_royale --config pipeline/rl_royale.yaml --run league1b init=icebow/data/pipeline/gen_v1_s0/gen_s0.pt \
    league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 max_updates=200 \
    'screen_seeds=[0]' > $O/league1b_launch.out 2> $O/league1b_launch.out.err
echo "[drv] league1b exited $? $(date): $(tail -2 $O/league1b_launch.out)"
