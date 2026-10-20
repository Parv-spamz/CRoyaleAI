#!/bin/bash
# R1e = R1 with ONE (owner-folded) change: REALISTIC OPPONENTS = league decks from the census WITH evolution / hero forms
# AND opponents pressing their hero abilities (hero_abilities=true; owner 2026-10-03 chose to fold this in, accepting
# that evo vs hero-ability effects cannot be separated)
# (scratchpad/gauntlet/L70/pool_forms/loadable_decks.json: 999/1000 decks carry forms; 99.9% of census deck-sides have an
# evo or hero; 0 form fallbacks). Owner 2026-10-03: "the model doesn't really know how to counter evos in live matches".
# Waits for the R1u chain (one GPU job at a time). Then:
# (1) NEW instrument baselines: reactive play vs gen_v1 playing EVO census decks (search_s0 --census pool_forms, --opps
#     gen) for gen_v1 itself and R1 u0155 (24 seeds) -- the old-census numbers are not comparable to these.
# (2) R1e training, 155 updates (5 critic-only), same OVR as R1 + league_decks=pool_forms.
# (3) R1e acceptance at u0080 / u0155: ghost screen vs R1 at the same update + vs base; reactive old census (vs R1's);
#     reactive evo census (vs step 1).
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L70/rl; LOG=$O/night3.log
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
BASE=scratchpad/gauntlet/L69/rebase_1001_evo/train_tau0.27.jsonl
CKB=icebow/data/bench/rl_royale
EVO=scratchpad/gauntlet/L70/pool_forms/loadable_decks.json
GEN1=icebow/data/pipeline/gen_v1_s0/gen_s0.pt
log() { echo "[r1e] $* $(date)" >> $LOG; }
wins() { echo "gen $(grep -cE 'plain +gen +seed [0-9]+ win' $1)/$(grep -cE 'plain +gen +seed' $1) s1 $(grep -cE 'plain +s1 +seed [0-9]+ win' $1)/$(grep -cE 'plain +s1 +seed' $1)"; }
reactive() {   # $1 ckpt, $2 out name, $3 opps, $4 extra args
  $PY -m pipeline.search_s0 --out $B/reactive_$2 --seeds 0:24 --opps $3 --arms plain --gen $1 --opp-gen $GEN1 \
      --forms-mode deck --device cuda --workers 3 --tail-cap 7200 $4 > $B/reactive_$2.log 2>&1
  log "reactive $2 exit $? $(wins $B/reactive_$2.log)"
}
log "waiting for the R1u chain"
until grep -q "\[r1u\] all done" $LOG; do sleep 120; done
B=$O/r1e_accept; mkdir -p $B
reactive $GEN1 evo_base_gen_v1 gen "--census $EVO --hero-abilities"
reactive $CKB/rseries_r1/rseries_r1_u0155.pt evo_rseries_r1_u0155 gen "--census $EVO --hero-abilities"
CFG=scratchpad/gauntlet/L69/rl/r1_rl_royale.yaml
OVR="init=$GEN1 league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 max_updates=155 screen_seeds=[0] league_learner_icebow_share=1.0 forms_mode=deck league_decks=$EVO advantage=gae gae_gamma_unit=tick critic_warmup_updates=5 hero_abilities=true"
log "R1e start"
$PY -m pipeline.rl_royale --config $CFG --run rseries_r1e $OVR > $O/r1e_gpu.out 2> $O/r1e_gpu.out.err
log "R1e gpu exited $? -- $(grep -a 'STOP after' $O/r1e_gpu.out | tail -1)"
for u in 0080 0155; do
  t=rseries_r1e_u$u; ck=$CKB/rseries_r1e/$t.pt
  [ -f $ck ] || { log "$t missing -- skipped"; continue; }
  $PY $RS --ckpt $ck --out $B/train_$t.jsonl --split train --noise-off all --opp-elixir counter --action-delay 26 \
      --extrapolate 26 --seeds 0 --device cuda --forms-mode deck --only-tags-from $OLD > $B/train_$t.out 2>&1
  $PY $RS --pair $BASE $B/train_$t.jsonl > $B/pair_$t.out 2>&1
  log "screen $t vs base $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $B/pair_$t.out | tr -d ' \n')"
  $PY $RS --pair $O/r1_accept/train_rseries_r1_u$u.jsonl $B/train_$t.jsonl > $B/pair_${t}_vs_r1.out 2>&1
  log "screen $t vs r1_u$u $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $B/pair_${t}_vs_r1.out | tr -d ' \n')"
  reactive $ck $t gen,s1 ""
  reactive $ck evo_$t gen "--census $EVO --hero-abilities"
done
log "all done"
