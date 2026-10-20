#!/bin/bash
# Owner 2026-10-04: test n_actors 3 vs 5 before R1e uses 5. Same R1e config, tiny (E=6, G=2, 3 updates, 1 critic
# warm-up), CPU only (3.1c owns the GPU), no screens / pro-agreement. PASS = identical per-update stats + identical
# final weights.
cd /c/Users/benpe/ClashBot; O=scratchpad/gauntlet/L71/rl/actors_test
PY=research/ext/Royale/.venv/Scripts/python.exe; export PYTHONPATH=.
CFG=scratchpad/gauntlet/L69/rl/r1_rl_royale.yaml
OVR="init=icebow/data/pipeline/gen_v31b_s0/gen_s0.pt proagree_data_gen=icebow/data/pipeline/gen_dataset_v31_public.npz league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 screen_seeds=[0] league_learner_icebow_share=1.0 forms_mode=deck league_decks=scratchpad/gauntlet/L70/pool_forms/loadable_decks.json advantage=gae gae_gamma_unit=tick hero_abilities=true ability_policy=v2 E=6 G=2 max_updates=3 critic_warmup_updates=1 actor_device=cpu learner_device=cpu screen_every=1000 proagree_every=1000 save_every=1"
for n in 3 5; do
  echo "== n_actors $n start $(date +%T)" >> $O/log.txt
  $PY -m pipeline.rl_royale --config $CFG --run test_actors$n $OVR n_actors=$n > $O/out_$n.txt 2> $O/err_$n.txt
  echo "== n_actors $n exit $? $(date +%T)" >> $O/log.txt
done
$PY - >> $O/log.txt 2>&1 <<'PYEOF'
import torch, re, glob
def stats(n):
    return [re.sub(r'wall roll \S+ upd \S+','',l.strip()) for l in open(f'scratchpad/gauntlet/L71/rl/actors_test/out_{n}.txt') if l.startswith('[rl] u0')]
a, b = stats(3), stats(5)
print('per-update stat lines equal:', a == b, len(a), len(b))
for x, y in zip(a, b):
    if x != y: print(' 3:', x[:300]); print(' 5:', y[:300])
def sd(n):
    f = sorted(glob.glob(f'icebow/data/bench/rl_royale/test_actors{n}/test_actors{n}_u0003.pt'))[0]
    c = torch.load(f, map_location='cpu', weights_only=False); return c.get('model', c.get('state_dict', c))
s3, s5 = sd(3), sd(5)
same = all(torch.equal(s3[k], s5[k]) for k in s3 if torch.is_tensor(s3[k]))
print('final weights identical:', same, 'max abs diff', max(float((s3[k].float()-s5[k].float()).abs().max()) for k in s3 if torch.is_tensor(s3[k])))
PYEOF
echo "== DONE $(date +%T)" >> $O/log.txt
