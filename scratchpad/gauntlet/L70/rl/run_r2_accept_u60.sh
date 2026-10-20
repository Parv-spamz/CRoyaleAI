#!/bin/bash
# R2 stopped itself after u59 (HARD pro-agreement guard: gate_bal_acc 0.7119 < 0.7669 - 0.05), so night3's u0080/u0155
# acceptance had nothing to test. Matched-update acceptance at u0060 for BOTH runs (same 5 critic-only warm-up updates,
# 55 policy updates each): pinned-299 ghost screen (tau 0.27, forms deck) vs the evo re-baseline, R2 paired vs R1;
# reactive play (plain arm, gen_v1 + S1, 24 seeds). Same commands as run_night3.sh.
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L70/rl; LOG=$O/night3.log
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
BASE=scratchpad/gauntlet/L69/rebase_1001_evo/train_tau0.27.jsonl
CKB=icebow/data/bench/rl_royale
log() { echo "[n3b] $* $(date)" >> $LOG; }
B=$O/r2_accept; mkdir -p $B
for run in rseries_r1 rseries_r2; do
  t=${run}_u0060
  $PY $RS --ckpt $CKB/$run/$t.pt --out $B/train_$t.jsonl --split train --noise-off all --opp-elixir counter --action-delay 26 \
      --extrapolate 26 --seeds 0 --device cuda --forms-mode deck --only-tags-from $OLD > $B/train_$t.out 2>&1
  $PY $RS --pair $BASE $B/train_$t.jsonl > $B/pair_$t.out 2>&1
  log "screen $t vs base $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $B/pair_$t.out | tr -d ' \n')"
done
$PY $RS --pair $B/train_rseries_r1_u0060.jsonl $B/train_rseries_r2_u0060.jsonl > $B/pair_r2_vs_r1_u0060.out 2>&1
log "screen r2_u0060 vs r1_u0060 $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $B/pair_r2_vs_r1_u0060.out | tr -d ' \n')"
for run in rseries_r1 rseries_r2; do
  t=${run}_u0060
  $PY -m pipeline.search_s0 --out $B/reactive_$t --seeds 0:24 --opps gen,s1 --arms plain \
      --gen $CKB/$run/$t.pt --opp-gen icebow/data/pipeline/gen_v1_s0/gen_s0.pt --forms-mode deck --device cuda --workers 3 \
      --tail-cap 7200 > $B/reactive_$t.log 2>&1
  log "reactive $t exit $? wins gen $(grep -cE 'plain +gen +seed [0-9]+ win' $B/reactive_$t.log)/24 s1 $(grep -cE 'plain +s1 +seed [0-9]+ win' $B/reactive_$t.log)/24"
done
log "u0060 acceptance done"
