"""Read existing ghost-screen telemetry; never substitute absent behaviour data.

Paired replay-cluster bootstrap uses identical resamples for each model. This
instrument is the pinned ghost screen, not reactive play or live ladder evidence.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
SOURCES = {
    'gen_v1': 'scratchpad/gauntlet/L69/rebase_1001_evo/train_tau0.27.jsonl',
    'u0155': 'scratchpad/gauntlet/L70/rl/r1_accept/train_rseries_r1_u0155.jsonl',
    'gen_v3': 'scratchpad/gauntlet/L70/gen_v3/train_gen_v3.jsonl',
}
MISSING = {
    'rocket_on_tower_in_pro_contexts': 'Needs fitted public pro-context classifier and tower targets at each decision.',
    'multi_rocket_sequences_same_tower': 'Saved plays have cell IDs but no contemporaneous tower state or hit attribution.',
    'tiebreak_tower_hp_margin': 'Ghost-screen records omit final tower HP and explicit tiebreak outcome.',
    'one_rocket_finish_conversion': 'No per-decision tower HP opportunity denominator in these logs.',
    'preemptive_log_per_opponent_barrel': 'No opponent flight/landing timeline in these logs.',
    'xbow_dead_lane_after_princess_down': 'No contemporaneous princess HP/lane state for each X-Bow in saved ghost logs.',
    'late_game_defensive_xbow_share': 'Exact placement rows can be described, but strategic defensive/bridge labels are not validated.',
    'xbow_to_tower_rocket_cycle_sequences': 'No verified tower-target context; raw card order alone does not establish tower Rocket cycling.',
    'defensive_rocket_rate': 'No contemporaneous troop/hit attribution; a non-tower aim is not automatically defensive.',
    'rocket_then_tornado_synergy_rate': 'Cast order/proximity can be measured, but saved ghost telemetry omits flight/pull/impact evidence.',
    'tornado_then_rocket_synergy_rate': 'Cast order/proximity does not establish a Rocket landing on a pulled group within 2.5s.',
}


def load(path):
    rows = [json.loads(s) for s in path.read_text().splitlines() if s.strip()]
    table = {(r['tag'], r['k'], r['side']): r for r in rows}
    if len(table) != len(rows):
        raise ValueError('Duplicate paired match')
    for r in rows:
        accepted = [p for p in r['plays'] if p.get('accepted')]
        if len(accepted) != r['plays_accepted']:
            raise ValueError('Accepted play count disagrees with telemetry')
    return table


def vectors(rows):
    return np.asarray([[sum(p.get('accepted') and p['card']=='rocket' for p in r['plays']),
                        r['plays_accepted'], r['end_tick']/1200] for r in rows], float)


def metrics(v):
    total = v.sum(axis=-2)
    return np.stack([100*total[..., 0]/total[..., 1], total[..., 1]/total[..., 2]], axis=-1)


def report(root=ROOT):
    data = {name:load(root/path) for name,path in SOURCES.items()}
    keys = sorted(data['gen_v1'])
    if any(set(keys) != set(t) for t in data.values()):
        raise ValueError('Unpaired baseline sets')
    configs = ('tau','afford_mask','stall_elixir','p_random','obs_seed','action_delay_ticks',
               'extrapolate_ticks','forms_mode','obs','policy','side')
    for key in keys:
        base = data['gen_v1'][key]
        for table in data.values():
            if any(base.get(c) != table[key].get(c) for c in configs):
                raise ValueError('Paired condition mismatch')
    # Bounded batches of resamples avoid unnecessary memory / CPU contention.
    rng = np.random.default_rng(20261003)
    ix = rng.integers(len(keys), size=(10000,len(keys)))
    samples = {}; models = {}; inputs = {}
    for name, table in data.items():
        rows = [table[k] for k in keys]; v = vectors(rows)
        samples[name] = metrics(v[ix])
        point = metrics(v); ci = np.quantile(samples[name],[.025,.975],axis=0)
        elixir = [p.get('elixir_exact',p['elixir']) for r in rows for p in r['plays']
                  if p.get('accepted') and p['card']=='rocket']
        models[name] = dict(matches=len(rows), rocket_plays=int(v[:,0].sum()), accepted_plays=int(v[:,1].sum()),
            rocket_share_pct=dict(value=float(point[0]),ci95=ci[:,0].tolist()),
            accepted_plays_per_min=dict(value=float(point[1]),ci95=ci[:,1].tolist()),
            rocket_elixir=dict(n=len(elixir),median=float(np.median(elixir)) if elixir else None),
            unavailable={k:dict(value=None,status='UNMEASURED',reason=why) for k,why in MISSING.items()})
        path=root/SOURCES[name]
        inputs[SOURCES[name]]=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
    paired={}
    for name in ('u0155','gen_v3'):
        d=samples[name]-samples['gen_v1'];ci=np.quantile(d,[.025,.975],axis=0)
        point=metrics(vectors([data[name][k] for k in keys]))-metrics(vectors([data['gen_v1'][k] for k in keys]))
        paired[name]=dict(rocket_share_delta_pp=dict(value=float(point[0]),ci95=ci[:,0].tolist()),
                         plays_per_min_delta=dict(value=float(point[1]),ci95=ci[:,1].tolist()))
    return dict(status='MEASURED_PARTIAL',instrument='paired pinned ghost screen',models=models,
        paired_vs_gen_v1=paired,inputs=inputs,bootstrap=dict(repeats=10000,seed=20261003,unit='paired replay'),
        limitations=['Offline ghost-screen conditions; not live or reactive metrics.',
                     'CI conditions on pinned matches and historical run conditions; no causal attribution.',
                     'Unavailable metrics are null, never zero. No behaviour acceptance threshold is invented.'])


if __name__=='__main__':
    r=report();out=Path(__file__).with_name('behavior_baselines.json')
    out.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(dict(models=r['models'],paired=r['paired_vs_gen_v1']),indent=2))
