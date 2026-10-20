#!/bin/bash
# R1e v3 = v2 + a TRUE R8 A/B first (3.1a+R8 vs the saved pre-R8 3.1a screen; the 3.1b "A/B" compared R8 with itself:
# Codex finished R8 at 12:01, 3.1b's screen started 11:59). R1e v2 = run_r1e.sh + n_actors=5 (owner 13:4x: "We're going to use 5 workers for R1e"). R1e (owner 2026-10-04: start RL from the best gen_v3.1 base -- 3.1c if it beat 3.1b, else 3.1b; calibrated ability
# models approved). = R1's recipe (GAE, per-tick discount, 5 critic-warm-up updates, 155 updates, live latency + R8
# look-ahead) with REALISTIC OPPONENTS: evo/hero census decks (pool_forms) + every hero/champion pressing its ability by
# the calibrated v2 model. Pro-agreement guard on the v3.1 dataset. Waits for chain_v31c_r8.sh (R1E_BASE.txt).
# Acceptance at u0080 / u0155: ghost screen vs its base (R8 screen) and vs live u0155; reactive gen_v1 + S1 on the old
# census AND on the evo census with abilities (base measured the same way).
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L71/rl; G=scratchpad/gauntlet/L71/gen_v31; LOG=$O/r1e.log
PY=research/ext/Royale/.venv/Scripts/python.exe; RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl; LIVE=scratchpad/gauntlet/L70/rl/r1_accept/train_rseries_r1_u0155.jsonl
EVO=scratchpad/gauntlet/L70/pool_forms/loadable_decks.json; GEN1=icebow/data/pipeline/gen_v1_s0/gen_s0.pt; CKB=icebow/data/bench/rl_royale
export PYTHONPATH=.
log() { echo "[r1e] $* $(date '+%F %T')" >> $LOG; }
ci() { grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $1 | tr -d ' \n'; }
wins() { echo "gen $(grep -cE 'plain +gen +seed [0-9]+ win' $1)/24 s1 $(grep -cE 'plain +s1 +seed [0-9]+ win' $1)/24"; }
until grep -q "\[v31c-r8\] CHAIN_DONE" $G/chain.log 2>/dev/null; do sleep 60; done
if [ ! -s $G/train_gen_v31a_r8.jsonl ]; then
  log "R8 A/B on 3.1a start"
  $PY $RS --ckpt icebow/data/pipeline/gen_v31a_s0/gen_s0.pt --out $G/train_gen_v31a_r8.jsonl --split train --noise-off all --opp-elixir counter       --action-delay 26 --extrapolate 26 --seeds 0 --device cuda --forms-mode deck --tau 0.27 --only-tags-from $OLD --behaviour-telemetry > $G/screen_v31a_r8.out 2>&1
  $PY $RS --pair $G/train_gen_v31a.jsonl $G/train_gen_v31a_r8.jsonl > $G/pair_r8_on_v31a.out 2>&1
  log "R8 A/B (3.1a+R8 vs 3.1a) $(ci $G/pair_r8_on_v31a.out)"
fi
BASECK=$(cat $G/R1E_BASE.txt); case $BASECK in *v31c*) BSCREEN=$G/train_gen_v31c.jsonl;; *) BSCREEN=$G/train_gen_v31b_r8.jsonl;; esac
log "base $BASECK (screen $BSCREEN)"
CFG=scratchpad/gauntlet/L69/rl/r1_rl_royale.yaml
OVR="init=$BASECK proagree_data_gen=icebow/data/pipeline/gen_dataset_v31_public.npz league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 max_updates=155 screen_seeds=[0] league_learner_icebow_share=1.0 forms_mode=deck league_decks=$EVO advantage=gae gae_gamma_unit=tick critic_warmup_updates=5 hero_abilities=true ability_policy=v2 n_actors=5"
log "R1e start"
$PY -m pipeline.rl_royale --config $CFG --run rseries_r1e31 $OVR > $O/r1e_gpu.out 2> $O/r1e_gpu.out.err
rc=$?; log "R1e exited $rc -- $(grep -a 'STOP after' $O/r1e_gpu.out | tail -1)"
[ "$rc" -ne 0 ] && { log "TRAINING FAILED -- acceptance not run"; exit $rc; }
B=$O/r1e_accept; mkdir -p $B
reactive() { $PY -m pipeline.search_s0 --out $B/reactive_$2 --seeds 0:24 --opps gen,s1 --arms plain --gen $1 --opp-gen $GEN1 \
    --forms-mode deck --device cuda --workers 3 --tail-cap 7200 $3 > $B/reactive_$2.log 2>&1; log "reactive $2 $(wins $B/reactive_$2.log)"; }
reactive $BASECK base_evo "--census $EVO --hero-abilities --ability-policy v2"
for u in 0080 0155; do
  t=rseries_r1e31_u$u; ck=$CKB/rseries_r1e31/$t.pt; [ -f $ck ] || { log "$t missing"; continue; }
  $PY $RS --ckpt $ck --out $B/train_$t.jsonl --split train --noise-off all --opp-elixir counter --action-delay 26 --extrapolate 26 \
      --seeds 0 --device cuda --forms-mode deck --tau 0.27 --only-tags-from $OLD --behaviour-telemetry > $B/train_$t.out 2>&1
  $PY $RS --pair $BSCREEN $B/train_$t.jsonl > $B/pair_${t}_vs_base.out 2>&1
  $PY $RS --pair $LIVE $B/train_$t.jsonl > $B/pair_${t}_vs_u0155.out 2>&1
  log "$t vs base $(ci $B/pair_${t}_vs_base.out) | vs u0155 $(ci $B/pair_${t}_vs_u0155.out)"
  reactive $ck $t ""
  reactive $ck ${t}_evo "--census $EVO --hero-abilities --ability-policy v2"
done
printf '%s\n' "ClashAI R1e done: $(grep -E 'vs base|reactive' $LOG | tail -6 | tr '\n' ' ' | cut -c1-1300)" > $O/_msg.txt
icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L69/discord/post.py $O/_msg.txt >> $LOG 2>&1
log "all done"
