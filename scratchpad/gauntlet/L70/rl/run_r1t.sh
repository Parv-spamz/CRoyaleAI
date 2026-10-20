#!/bin/bash
# R1t = R1 with ONE change: gae_terminal_gap=true (the terminal outcome is also discounted over the gap from the last
# kept decision to the actual match end; review point 1, code e87c638). Queued 2026-10-03 while the per-ability
# hero/champion work for R1e is researched (GPU otherwise idle).
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L70/rl; LOG=$O/night3.log
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
BASE=scratchpad/gauntlet/L69/rebase_1001_evo/train_tau0.27.jsonl
CKB=icebow/data/bench/rl_royale
log() { echo "[r1t] $* $(date)" >> $LOG; }
log "waiting for the R1u chain"
until grep -q "\[r1u\] all done" $LOG; do sleep 120; done
CFG=scratchpad/gauntlet/L69/rl/r1_rl_royale.yaml
OVR="init=icebow/data/pipeline/gen_v1_s0/gen_s0.pt league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 max_updates=155 screen_seeds=[0] league_learner_icebow_share=1.0 forms_mode=deck league_decks=scratchpad/gauntlet/L69/pool/loadable_decks.json advantage=gae gae_gamma_unit=tick critic_warmup_updates=5 gae_terminal_gap=true"
log "R1t start"
$PY -m pipeline.rl_royale --config $CFG --run rseries_r1t $OVR > $O/r1t_gpu.out 2> $O/r1t_gpu.out.err
log "R1t gpu exited $? -- $(grep -a 'STOP after' $O/r1t_gpu.out | tail -1)"
if grep -q "out of memory" $O/r1t_gpu.out $O/r1t_gpu.out.err; then
  log "OOM -> resume on CPU"
  $PY -m pipeline.rl_royale --config $CFG --run rseries_r1t --resume $OVR learner_device=cpu actor_device=cpu > $O/r1t_cpu.out 2> $O/r1t_cpu.out.err
  log "R1t cpu exited $?"
fi
B=$O/r1t_accept; mkdir -p $B
for u in 0080 0155; do
  t=rseries_r1t_u$u
  [ -f $CKB/rseries_r1t/$t.pt ] || { log "$t missing -- skipped"; continue; }
  $PY $RS --ckpt $CKB/rseries_r1t/$t.pt --out $B/train_$t.jsonl --split train --noise-off all --opp-elixir counter \
      --action-delay 26 --extrapolate 26 --seeds 0 --device cuda --forms-mode deck --only-tags-from $OLD > $B/train_$t.out 2>&1
  $PY $RS --pair $BASE $B/train_$t.jsonl > $B/pair_$t.out 2>&1
  log "screen $t vs base $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $B/pair_$t.out | tr -d ' \n')"
  $PY $RS --pair $O/r1_accept/train_rseries_r1_u$u.jsonl $B/train_$t.jsonl > $B/pair_${t}_vs_r1.out 2>&1
  log "screen $t vs r1_u$u $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $B/pair_${t}_vs_r1.out | tr -d ' \n')"
  $PY -m pipeline.search_s0 --out $B/reactive_$t --seeds 0:24 --opps gen,s1 --arms plain --gen $CKB/rseries_r1t/$t.pt \
      --opp-gen icebow/data/pipeline/gen_v1_s0/gen_s0.pt --forms-mode deck --device cuda --workers 3 --tail-cap 7200 \
      > $B/reactive_$t.log 2>&1
  log "reactive $t exit $? wins gen $(grep -cE 'plain +gen +seed [0-9]+ win' $B/reactive_$t.log)/24 s1 $(grep -cE 'plain +s1 +seed [0-9]+ win' $B/reactive_$t.log)/24"
done
log "all done"
