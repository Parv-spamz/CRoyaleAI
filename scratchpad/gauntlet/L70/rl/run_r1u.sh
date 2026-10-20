#!/bin/bash
# R1u = R1 with ONE change: gae_gamma_tick 1.0 (undiscounted episodic win/loss; outside review 2026-10-02: the per-tick
# discount 0.99994 scales the first row's return to ~0.77 of the last -> win fast / lose slow, which winning does not
# need). Started 2026-10-03 05:1x after R2's guard stop (owner: "continue on with the RL work"). Then acceptance at the
# matched updates u0080 / u0155, paired vs R1 (r1_accept) and the evo re-baseline, reactive play gen_v1 + S1.
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L70/rl; LOG=$O/night3.log
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
BASE=scratchpad/gauntlet/L69/rebase_1001_evo/train_tau0.27.jsonl
CKB=icebow/data/bench/rl_royale
log() { echo "[r1u] $* $(date)" >> $LOG; }
CFG=scratchpad/gauntlet/L69/rl/r1_rl_royale.yaml
OVR="init=icebow/data/pipeline/gen_v1_s0/gen_s0.pt league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 max_updates=155 screen_seeds=[0] league_learner_icebow_share=1.0 forms_mode=deck league_decks=scratchpad/gauntlet/L69/pool/loadable_decks.json advantage=gae gae_gamma_unit=tick critic_warmup_updates=5 gae_gamma_tick=1.0"
log "R1u start"
$PY -m pipeline.rl_royale --config $CFG --run rseries_r1u $OVR > $O/r1u_gpu.out 2> $O/r1u_gpu.out.err
log "R1u gpu exited $? -- $(grep -a 'STOP after' $O/r1u_gpu.out | tail -1)"
if grep -q "out of memory" $O/r1u_gpu.out $O/r1u_gpu.out.err; then
  log "OOM -> resume on CPU"
  $PY -m pipeline.rl_royale --config $CFG --run rseries_r1u --resume $OVR learner_device=cpu actor_device=cpu > $O/r1u_cpu.out 2> $O/r1u_cpu.out.err
  log "R1u cpu exited $?"
fi
B=$O/r1u_accept; mkdir -p $B
for u in 0080 0155; do
  t=rseries_r1u_u$u
  [ -f $CKB/rseries_r1u/$t.pt ] || { log "$t missing -- skipped"; continue; }
  $PY $RS --ckpt $CKB/rseries_r1u/$t.pt --out $B/train_$t.jsonl --split train --noise-off all --opp-elixir counter \
      --action-delay 26 --extrapolate 26 --seeds 0 --device cuda --forms-mode deck --only-tags-from $OLD > $B/train_$t.out 2>&1
  $PY $RS --pair $BASE $B/train_$t.jsonl > $B/pair_$t.out 2>&1
  log "screen $t vs base $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $B/pair_$t.out | tr -d ' \n')"
  $PY $RS --pair $O/r1_accept/train_rseries_r1_u$u.jsonl $B/train_$t.jsonl > $B/pair_${t}_vs_r1.out 2>&1
  log "screen $t vs r1_u$u $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $B/pair_${t}_vs_r1.out | tr -d ' \n')"
  $PY -m pipeline.search_s0 --out $B/reactive_$t --seeds 0:24 --opps gen,s1 --arms plain --gen $CKB/rseries_r1u/$t.pt \
      --opp-gen icebow/data/pipeline/gen_v1_s0/gen_s0.pt --forms-mode deck --device cuda --workers 3 --tail-cap 7200 \
      > $B/reactive_$t.log 2>&1
  log "reactive $t exit $? wins gen $(grep -cE 'plain +gen +seed [0-9]+ win' $B/reactive_$t.log)/24 s1 $(grep -cE 'plain +s1 +seed [0-9]+ win' $B/reactive_$t.log)/24"
done
log "all done"
