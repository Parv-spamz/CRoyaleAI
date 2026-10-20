#!/bin/bash
# (lead 2026-10-04 13:0x) Replaces accept_v31c.sh + swap_v31c.sh: R8 (look-ahead advances projectiles/effects, default-on
# for v4) landed 12:5x, so every NEW screen runs with R8 while the saved 3.1a/3.1b screens ran without it. Order (one GPU
# job at a time): wait 3.1c training -> (1) R8 A/B = 3.1b+R8 screen paired vs saved 3.1b -> (2) 3.1c+R8 screen paired vs
# 3.1b+R8 (fair, decides the R1e base + the live swap; owner 13:0x), vs u0155, vs gen_v1 -> (3) reactive 3.1c ->
# (4) decision: 3.1c wins iff ghost delta vs 3.1b+R8 >= 0 and the reader smoke passes -> live CKPT_OVERRIDE = 3.1c.
# Else, if R8 did not hurt 3.1b (delta >= 0), restart live on 3.1b so R8 reaches live. Discord post at the end.
cd /c/Users/benpe/ClashBot; G=scratchpad/gauntlet/L71/gen_v31; LOG=$G/chain.log
PY=research/ext/Royale/.venv/Scripts/python.exe; RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl; BASE=scratchpad/gauntlet/L69/rebase_1001_evo/train_tau0.27.jsonl
LIVE=scratchpad/gauntlet/L70/rl/r1_accept/train_rseries_r1_u0155.jsonl
B=icebow/data/pipeline/gen_v31b_s0/gen_s0.pt; C=icebow/data/pipeline/gen_v31c_s0/gen_s0.pt
export PYTHONPATH=.
log() { echo "[v31c-r8] $* $(date '+%F %T')" >> $LOG; }
ci() { grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $1 | tr -d ' \n'; }
delta() { python -c "import re;print(re.search(r'\"delta_pp\": *(-?[0-9.e-]+)',open('$1').read()).group(1))"; }
screen() { $PY $RS --ckpt $1 --out $2 --split train --noise-off all --opp-elixir counter --action-delay 26 --extrapolate 26 \
    --seeds 0 --device cuda --forms-mode deck --tau 0.27 --only-tags-from $OLD --behaviour-telemetry > $2.out 2>&1; }
until [ $(grep -c "\[v31c\] train exit" $LOG) -ge 2 ]; do sleep 30; done
grep "\[v31c\] train exit" $LOG | tail -1 | grep -q "train exit 0" || { log "3.1c TRAIN FAILED"; exit 1; }
log "start"
screen $B $G/train_gen_v31b_r8.jsonl || { log "3.1b+R8 SCREEN FAILED"; exit 1; }
$PY $RS --pair $G/train_gen_v31b.jsonl $G/train_gen_v31b_r8.jsonl > $G/pair_r8_on_v31b.out 2>&1
log "R8 A/B (3.1b+R8 vs 3.1b) $(ci $G/pair_r8_on_v31b.out)"
screen $C $G/train_gen_v31c.jsonl || { log "3.1c SCREEN FAILED"; exit 1; }
$PY $RS --pair $G/train_gen_v31b_r8.jsonl $G/train_gen_v31c.jsonl > $G/pair_v31c_vs_v31b_r8.out 2>&1
$PY $RS --pair $LIVE $G/train_gen_v31c.jsonl > $G/pair_v31c_vs_u0155.out 2>&1
$PY $RS --pair $BASE $G/train_gen_v31c.jsonl > $G/pair_v31c_vs_genv1.out 2>&1
log "3.1c vs 3.1b+R8 $(ci $G/pair_v31c_vs_v31b_r8.out) | vs u0155 $(ci $G/pair_v31c_vs_u0155.out) | vs gen_v1 $(ci $G/pair_v31c_vs_genv1.out)"
$PY -m pipeline.search_s0 --out $G/reactive_v31c --seeds 0:24 --opps gen,s1 --arms plain --gen $C \
    --opp-gen icebow/data/pipeline/gen_v1_s0/gen_s0.pt --forms-mode deck --device cuda --workers 3 --tail-cap 7200 > $G/reactive_v31c.log 2>&1
log "reactive 3.1c gen $(grep -cE 'plain +gen +seed [0-9]+ win' $G/reactive_v31c.log)/24 s1 $(grep -cE 'plain +s1 +seed [0-9]+ win' $G/reactive_v31c.log)/24 (3.1b: 15, 16)"
DC=$(delta $G/pair_v31c_vs_v31b_r8.out); DR=$(delta $G/pair_r8_on_v31b.out)
if python -c "import sys; sys.exit(0 if float('$DC') >= 0 else 1)" && icebow/.venv/Scripts/python.exe .foreman/codex_autopilot/reader_v31_smoke.py --ckpt $C --side 1 --out $G/smoke_v31c > $G/smoke_v31c.out 2>&1 && grep -q TRAINED_CHECKPOINT_READER_SMOKE_PASS $G/smoke_v31c.out; then
  echo $C > $G/R1E_BASE.txt
  printf '%s\n' "C:/Users/benpe/ClashBot/$C" > scratchpad/gauntlet/L70/live/CKPT_OVERRIDE
  MSG="ClashAI: gen_v3.1c beat gen_v3.1b ($DC pp, both with the R8 look-ahead fix; R8 alone on 3.1b: $DR pp) -> live switches to 3.1c (with R8) at the next match; R1e starts from 3.1c."
else
  echo $B > $G/R1E_BASE.txt
  if python -c "import sys; sys.exit(0 if float('$DR') >= 0 else 1)"; then
    printf '%s\n' "$B" > scratchpad/gauntlet/L70/live/CKPT_OVERRIDE   # relative path != the absolute one -> live restarts on 3.1b WITH R8
    MSG="ClashAI: gen_v3.1c did not beat 3.1b ($DC pp). R8 look-ahead fix on 3.1b: $DR pp (not worse) -> live restarts on 3.1b WITH R8. R1e starts from 3.1b."
  else
    MSG="ClashAI: gen_v3.1c did not beat 3.1b ($DC pp). R8 look-ahead fix on 3.1b: $DR pp (worse) -> live unchanged (3.1b without R8). R1e base 3.1b. Lead to review R8."
  fi
fi
log "DECISION: $MSG"; printf '%s\n' "$MSG" > $G/_msg.txt
icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L69/discord/post.py $G/_msg.txt >> $LOG 2>&1
log "CHAIN_DONE"
