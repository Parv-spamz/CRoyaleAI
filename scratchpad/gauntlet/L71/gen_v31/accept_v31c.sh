#!/bin/bash
# gen_v3.1c acceptance (copy of accept_v31b.sh; pair vs 3.1b decides the R1e base) (lead 2026-10-04): train_gen's pick (gen_s0.pt = epoch 3) on the pinned-299 ghost screen (tau 0.27,
# forms deck, live condition) paired vs LIVE u0155 and vs the gen_v1 evo base; behaviour telemetry on; reactive plain arm
# vs gen_v1 + S1 (24 seeds). READY gate (owner overnight brief): paired-vs-u0155 CI not entirely below 0 + reactive + smoke.
cd /c/Users/benpe/ClashBot
G=scratchpad/gauntlet/L71/gen_v31; LOG=$G/chain.log
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
BASE=scratchpad/gauntlet/L69/rebase_1001_evo/train_tau0.27.jsonl
LIVE=scratchpad/gauntlet/L70/rl/r1_accept/train_rseries_r1_u0155.jsonl
CK=icebow/data/pipeline/gen_v31c_s0/gen_s0.pt
export PYTHONPATH=.
log() { echo "[v31c-acc] $* $(date '+%F %T')" >> $LOG; }
until [ $(grep -c "\[v31c\] train exit" $LOG) -ge 2 ]; do sleep 30; done   # the 1st exit = the refused weight-4.0 launch
grep "\[v31c\] train exit" $LOG | tail -1 | grep -q "train exit 0" || { log "TRAIN FAILED"; exit 1; }
log "screen start"
$PY $RS --ckpt $CK --out $G/train_gen_v31c.jsonl --split train --noise-off all --opp-elixir counter --action-delay 26 \
    --extrapolate 26 --seeds 0 --device cuda --forms-mode deck --tau 0.27 --only-tags-from $OLD --behaviour-telemetry > $G/screen_v31c.out 2>&1 \
    || { log "SCREEN FAILED (screen_v31c.out)"; exit 1; }
$PY $RS --pair $LIVE $G/train_gen_v31c.jsonl > $G/pair_v31c_vs_u0155.out 2>&1
$PY $RS --pair $BASE $G/train_gen_v31c.jsonl > $G/pair_v31c_vs_genv1.out 2>&1
$PY $RS --pair $G/train_gen_v31b.jsonl $G/train_gen_v31c.jsonl > $G/pair_v31c_vs_v31b.out 2>&1
log "vs u0155 $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $G/pair_v31c_vs_u0155.out | tr -d ' \n')"
log "vs v31b $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $G/pair_v31c_vs_v31b.out | tr -d ' 
')"
log "vs gen_v1 $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $G/pair_v31c_vs_genv1.out | tr -d ' \n')"
$PY -m pipeline.search_s0 --out $G/reactive_v31c --seeds 0:24 --opps gen,s1 --arms plain --gen $CK \
    --opp-gen icebow/data/pipeline/gen_v1_s0/gen_s0.pt --forms-mode deck --device cuda --workers 3 --tail-cap 7200 \
    > $G/reactive_v31c.log 2>&1
log "reactive exit $? wins gen $(grep -cE 'plain +gen +seed [0-9]+ win' $G/reactive_v31c.log)/24 s1 $(grep -cE 'plain +s1 +seed [0-9]+ win' $G/reactive_v31c.log)/24"
log "ACCEPT_DONE"
