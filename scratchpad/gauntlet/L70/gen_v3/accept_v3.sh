#!/bin/bash
# gen_v3 acceptance (sim; runs right after training): train_gen's pick (gen_s0.pt, best all-deck val epoch) on the
# pinned-299 ghost screen (tau 0.27, forms deck, live condition) paired vs the evo re-baseline of gen_v1, and reactive
# play (plain arm, gen_v1 + S1, 24 seeds, forms deck). The sim gives EXACT per-unit forms (status flags), so this is
# gen_v3's best case; live is blocked until the reader can tell evolved units (HANDOFF 12:4x).
cd /c/Users/benpe/ClashBot
G=scratchpad/gauntlet/L70/gen_v3; LOG=$G/chain.log
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
BASE=scratchpad/gauntlet/L69/rebase_1001_evo/train_tau0.27.jsonl
V3=icebow/data/pipeline/gen_v3_s0/gen_s0.pt
export PYTHONPATH=.
log() { echo "[v3] $* $(date)" >> $LOG; }
until grep -q "\[every_epoch\] completed metadata" $G/train.out 2>/dev/null; do
  grep -q "Traceback" $G/train.out && { log "TRAINING CRASHED -- see train.out"; exit 1; }; sleep 60; done
log "train done: $(grep -a '\[every_epoch\] completed' $G/train.out)"
grep -aE '"v3val"|"val"' $G/train.out | tail -4 >> $LOG
$PY $RS --ckpt $V3 --out $G/train_gen_v3.jsonl --split train --noise-off all --opp-elixir counter --action-delay 26 \
    --extrapolate 26 --seeds 0 --device cuda --forms-mode deck --tau 0.27 --only-tags-from $OLD > $G/screen.out 2>&1
$PY $RS --pair $BASE $G/train_gen_v3.jsonl > $G/pair_gen_v3.out 2>&1
log "screen gen_v3 vs gen_v1 base $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $G/pair_gen_v3.out | tr -d ' \n')"
$PY -m pipeline.search_s0 --out $G/reactive_gen_v3 --seeds 0:24 --opps gen,s1 --arms plain --gen $V3 \
    --opp-gen icebow/data/pipeline/gen_v1_s0/gen_s0.pt --forms-mode deck --device cuda --workers 3 --tail-cap 7200 \
    > $G/reactive_gen_v3.log 2>&1
log "reactive gen_v3 exit $? wins gen $(grep -cE 'plain +gen +seed [0-9]+ win' $G/reactive_gen_v3.log)/24 s1 $(grep -cE 'plain +s1 +seed [0-9]+ win' $G/reactive_gen_v3.log)/24"
log "acceptance done"
