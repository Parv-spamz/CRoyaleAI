#!/bin/bash
# gen_v3.1b acceptance (copy of accept_v31a.sh + a pair vs 3.1a) (lead 2026-10-04): train_gen's pick (gen_s0.pt = epoch 3) on the pinned-299 ghost screen (tau 0.27,
# forms deck, live condition) paired vs LIVE u0155 and vs the gen_v1 evo base; behaviour telemetry on; reactive plain arm
# vs gen_v1 + S1 (24 seeds). READY gate (owner overnight brief): paired-vs-u0155 CI not entirely below 0 + reactive + smoke.
cd /c/Users/benpe/ClashBot
G=scratchpad/gauntlet/L71/gen_v31; LOG=$G/chain.log
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
BASE=scratchpad/gauntlet/L69/rebase_1001_evo/train_tau0.27.jsonl
LIVE=scratchpad/gauntlet/L70/rl/r1_accept/train_rseries_r1_u0155.jsonl
CK=icebow/data/pipeline/gen_v31b_s0/gen_s0.pt
export PYTHONPATH=.
log() { echo "[v31b-acc] $* $(date '+%F %T')" >> $LOG; }
until grep -q "\[v31b\] train exit" $LOG; do sleep 30; done
grep -q "\[v31b\] train exit 0" $LOG || { log "TRAIN FAILED"; exit 1; }
log "screen start"
$PY $RS --ckpt $CK --out $G/train_gen_v31b.jsonl --split train --noise-off all --opp-elixir counter --action-delay 26 \
    --extrapolate 26 --seeds 0 --device cuda --forms-mode deck --tau 0.27 --only-tags-from $OLD --behaviour-telemetry > $G/screen_v31b.out 2>&1 \
    || { log "SCREEN FAILED (screen_v31b.out)"; exit 1; }
$PY $RS --pair $LIVE $G/train_gen_v31b.jsonl > $G/pair_v31b_vs_u0155.out 2>&1
$PY $RS --pair $BASE $G/train_gen_v31b.jsonl > $G/pair_v31b_vs_genv1.out 2>&1
$PY $RS --pair $G/train_gen_v31a.jsonl $G/train_gen_v31b.jsonl > $G/pair_v31b_vs_v31a.out 2>&1
log "vs u0155 $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $G/pair_v31b_vs_u0155.out | tr -d ' \n')"
log "vs v31a $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $G/pair_v31b_vs_v31a.out | tr -d ' 
')"
log "vs gen_v1 $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $G/pair_v31b_vs_genv1.out | tr -d ' \n')"
$PY -m pipeline.search_s0 --out $G/reactive_v31b --seeds 0:24 --opps gen,s1 --arms plain --gen $CK \
    --opp-gen icebow/data/pipeline/gen_v1_s0/gen_s0.pt --forms-mode deck --device cuda --workers 3 --tail-cap 7200 \
    > $G/reactive_v31b.log 2>&1
log "reactive exit $? wins gen $(grep -cE 'plain +gen +seed [0-9]+ win' $G/reactive_v31b.log)/24 s1 $(grep -cE 'plain +s1 +seed [0-9]+ win' $G/reactive_v31b.log)/24"
log "ACCEPT_DONE"
