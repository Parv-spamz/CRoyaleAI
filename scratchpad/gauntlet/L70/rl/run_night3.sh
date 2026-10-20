#!/bin/bash
# Night 3 (2026-10-02 -> 10-03, owner: "keep running things overnight, continue the RL work"). ONE GPU job at a time,
# chained after the gen_v2 chain (train + select). The live ladder run shares the GPU (owner-approved, light inference).
# (1) R1 acceptance at matched POLICY updates (R1 had 5 critic-only warm-up updates): R1 u0080 ~ R0' u0075, R1 u0155 ~
#     R0' u0150. Ghost screen (pinned 299, tau 0.27, forms deck) paired vs the evo re-baseline AND vs R0' at the matched
#     update; reactive play (plain arm vs frozen gen_v1 and S1, 24 seeds, forms deck).
# (2) R2 = R1 + shaping=tower_crown (w 0.3/0.3, residual critic scale 1.5, critic warm-up 5; pre-flight 3/3 PASS
#     10-01), max_updates 155 = 150 policy updates. The ONE change vs R1 is the shaping (the 10-02 critic monitors are
#     logging only; gae_terminal_gap stays off).
# (3) R2 acceptance, same instruments, paired vs R1 at the same update.
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L70/rl; LOG=$O/night3.log
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
BASE=scratchpad/gauntlet/L69/rebase_1001_evo/train_tau0.27.jsonl
R0A=scratchpad/gauntlet/L69/rl/r0p_accept
CKB=icebow/data/bench/rl_royale
log() { echo "[n3] $* $(date)" >> $LOG; }
screen() {   # $1 run, $2 update, $3 out dir, $4 paired file to compare against (besides BASE)
  local t=$1_u$2
  $PY $RS --ckpt $CKB/$1/$t.pt --out $3/train_$t.jsonl --split train --noise-off all --opp-elixir counter --action-delay 26 \
      --extrapolate 26 --seeds 0 --device cuda --forms-mode deck --only-tags-from $OLD > $3/train_$t.out 2>&1
  $PY $RS --pair $BASE $3/train_$t.jsonl > $3/pair_$t.out 2>&1
  log "screen $t vs base $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $3/pair_$t.out | tr -d ' \n')"
  if [ -n "$4" ] && [ -f "$4" ]; then
    $PY $RS --pair $4 $3/train_$t.jsonl > $3/pair_${t}_vs_prev.out 2>&1
    log "screen $t vs $(basename $4) $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $3/pair_${t}_vs_prev.out | tr -d ' \n')"
  fi
}
reactive() {   # $1 run, $2 update, $3 out dir
  local t=$1_u$2
  $PY -m pipeline.search_s0 --out $3/reactive_$t --seeds 0:24 --opps gen,s1 --arms plain \
      --gen $CKB/$1/$t.pt --opp-gen icebow/data/pipeline/gen_v1_s0/gen_s0.pt --forms-mode deck --device cuda --workers 3 \
      --tail-cap 7200 > $3/reactive_$t.log 2>&1
  log "reactive $t exit $? wins gen $(grep -cE 'plain +gen +seed [0-9]+ win' $3/reactive_$t.log)/24 s1 $(grep -ciE 'plain +s1 +seed [0-9]+ win' $3/reactive_$t.log)/24"
}
log "waiting for the gen_v2 chain (select)"
until grep -q "\[g2\] select exit" scratchpad/gauntlet/L69/gen_v2/chain.log 2>/dev/null; do sleep 120; done
log "gen_v2 chain done: $(tail -1 scratchpad/gauntlet/L69/gen_v2/chain.log)"
A=$O/r1_accept; mkdir -p $A
screen rseries_r1 0080 $A $R0A/train_rseries_r0p_u0075.jsonl
screen rseries_r1 0155 $A $R0A/train_rseries_r0p_u0150.jsonl
reactive rseries_r1 0080 $A
reactive rseries_r1 0155 $A
CFG=scratchpad/gauntlet/L69/rl/r1_rl_royale.yaml
OVR="init=icebow/data/pipeline/gen_v1_s0/gen_s0.pt league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 max_updates=155 screen_seeds=[0] league_learner_icebow_share=1.0 forms_mode=deck league_decks=scratchpad/gauntlet/L69/pool/loadable_decks.json advantage=gae gae_gamma_unit=tick critic_warmup_updates=5 shaping=tower_crown"
log "R2 start"
$PY -m pipeline.rl_royale --config $CFG --run rseries_r2 $OVR > $O/r2_gpu.out 2> $O/r2_gpu.out.err
log "R2 gpu exited $?"
if grep -q "out of memory" $O/r2_gpu.out $O/r2_gpu.out.err; then
  log "OOM -> resume on CPU"
  $PY -m pipeline.rl_royale --config $CFG --run rseries_r2 --resume $OVR learner_device=cpu actor_device=cpu > $O/r2_cpu.out 2> $O/r2_cpu.out.err
  log "R2 cpu exited $?"
fi
B=$O/r2_accept; mkdir -p $B
for u in 0080 0155; do
  [ -f $CKB/rseries_r2/rseries_r2_u$u.pt ] || { log "R2 u$u missing -- skipped"; continue; }
  screen rseries_r2 $u $B $A/train_rseries_r1_u$u.jsonl
  reactive rseries_r2 $u $B
done
log "all done"
