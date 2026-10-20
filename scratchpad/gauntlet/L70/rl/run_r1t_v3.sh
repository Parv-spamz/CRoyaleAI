#!/bin/bash
# R1t from gen_v3 (owner 2026-10-03: R1t and R1e start from gen_v3; no R1v3 control -- confounding accepted): R1's
# recipe + gae_terminal_gap=true, init = gen_v3 (train_gen's pick), pro agreement on the v3 dataset. Waits for the gen_v3
# acceptance chain. Then acceptance at u0080 / u0155: ghost screen vs gen_v3 (its init) and vs the gen_v1 evo base,
# reactive play gen_v1 + S1.
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L70/rl; LOG=$O/night3.log; G=scratchpad/gauntlet/L70/gen_v3
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
BASE=scratchpad/gauntlet/L69/rebase_1001_evo/train_tau0.27.jsonl
V3=icebow/data/pipeline/gen_v3_s0/gen_s0.pt; CKB=icebow/data/bench/rl_royale
export PYTHONPATH=.
log() { echo "[r1t_v3] $* $(date)" >> $LOG; }
log "waiting for the gen_v3 acceptance"
until grep -q "acceptance done\|TRAINING CRASHED" $G/chain.log; do sleep 120; done
grep -q "TRAINING CRASHED" $G/chain.log && { log "gen_v3 training crashed -- not starting"; exit 1; }
CFG=scratchpad/gauntlet/L69/rl/r1_rl_royale.yaml
OVR="init=$V3 proagree_data_gen=icebow/data/pipeline/gen_dataset_v3.npz league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 max_updates=155 screen_seeds=[0] league_learner_icebow_share=1.0 forms_mode=deck league_decks=scratchpad/gauntlet/L69/pool/loadable_decks.json advantage=gae gae_gamma_unit=tick critic_warmup_updates=5 gae_terminal_gap=true"
log "R1t_v3 start"
$PY -m pipeline.rl_royale --config $CFG --run rseries_r1t_v3 $OVR > $O/r1t_v3_gpu.out 2> $O/r1t_v3_gpu.out.err
rc=$?
log "R1t_v3 gpu exited $rc -- $(grep -a 'STOP after' $O/r1t_v3_gpu.out | tail -1)"
if [ "$rc" -ne 0 ]; then log "TRAINING FAILED -- acceptance not run"; exit "$rc"; fi
B=$O/r1t_v3_accept; mkdir -p $B
for u in 0080 0155; do
  t=rseries_r1t_v3_u$u; ck=$CKB/rseries_r1t_v3/$t.pt
  [ -f $ck ] || { log "$t missing -- skipped"; continue; }
  $PY $RS --ckpt $ck --out $B/train_$t.jsonl --split train --noise-off all --opp-elixir counter --action-delay 26 \
      --extrapolate 26 --seeds 0 --device cuda --forms-mode deck --tau 0.27 --only-tags-from $OLD > $B/train_$t.out 2>&1
  $PY $RS --pair $BASE $B/train_$t.jsonl > $B/pair_$t.out 2>&1
  log "screen $t vs gen_v1 base $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $B/pair_$t.out | tr -d ' \n')"
  $PY $RS --pair $G/train_gen_v3.jsonl $B/train_$t.jsonl > $B/pair_${t}_vs_v3.out 2>&1
  log "screen $t vs gen_v3 $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $B/pair_${t}_vs_v3.out | tr -d ' \n')"
  $PY -m pipeline.search_s0 --out $B/reactive_$t --seeds 0:24 --opps gen,s1 --arms plain --gen $ck \
      --opp-gen icebow/data/pipeline/gen_v1_s0/gen_s0.pt --forms-mode deck --device cuda --workers 3 --tail-cap 7200 \
      > $B/reactive_$t.log 2>&1
  log "reactive $t exit $? wins gen $(grep -cE 'plain +gen +seed [0-9]+ win' $B/reactive_$t.log)/24 s1 $(grep -cE 'plain +s1 +seed [0-9]+ win' $B/reactive_$t.log)/24"
done
log "all done"
