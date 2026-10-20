"""Receipt-checked fixed Q3 comparisons. Partial reports cannot authorize deployment."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from pipeline.e1_score import cluster_bootstrap


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def keys(rows, reactive=False):
    result=[(r['opp'],int(r['seed'])) if reactive else (r['tag'],int(r['k'])) for r in rows]
    if len(set(result))!=len(result):
        raise ValueError('Duplicate match keys')
    return set(result)


def validate(rows, expected, reactive=False):
    if keys(rows,reactive)!=expected:
        raise ValueError('Incomplete or changed paired match keys')
    for r in rows:
        if r['outcome'] not in ('win','loss','draw') or r['end_tick']<=0:
            raise ValueError('Invalid outcome')
        if reactive:
            if r['wall_truncated'] or r['tail_cap']!=7200 or r['end_tick']>=7200:
                raise ValueError('Truncated reactive game')
            if not r['hero_abilities'] or r['ability_policy']!='v2':
                raise ValueError('Reactive ability contract mismatch')
        elif not r['terminated'] or r['termination_reason']!='game_over' or r['action_delay_ticks']!=26 or r['extrapolate_ticks']!=26:
            raise ValueError('Ghost termination or delay mismatch')
        if r['forms_mode']!='deck':
            raise ValueError('Forms contract mismatch')
        b=r.get('behaviour',{})
        if b.get('schema')!='public_behaviour_v1' or b['accepted_plays']!=r['plays_accepted']:
            raise ValueError('Missing or inconsistent behaviour')
        if (b['rocket_share']['denominator']!=b['accepted_plays'] or
                b['tower_rocket_share']['denominator']+b['unknown_rocket_impacts']!=b['rocket_share']['n']):
            raise ValueError('Inconsistent Rocket denominators')


def summarize(rows):
    counts=Counter(r['outcome'] for r in rows)
    bs=[r['behaviour'] for r in rows]
    plays=sum(b['accepted_plays'] for b in bs)
    rockets=sum(b['rocket_share']['n'] for b in bs)
    return dict(n=len(rows),outcomes=dict(counts),wins=counts['win'],accepted_plays=plays,
        rockets=rockets,rocket_share=rockets/plays if plays else None,
        tower_rockets=sum(b['tower_rocket_share']['n'] for b in bs),
        tower_rockets_hp_confirmed=sum(b['tower_hit_hp_confirmation']['n'] for b in bs),
        **{k:sum(b[k] for b in bs) for k in ('finish_offs','multi_rocket_cycles','defensive_rockets',
            'rocket_then_tornado','tornado_then_rocket','unknown_rocket_impacts')},
        preemptive_log_n=sum(b['preemptive_log']['n'] for b in bs),
        preemptive_log_denominator=sum(b['preemptive_log']['denominator'] for b in bs))


def compare(rows,baseline):
    old={(r['tag'],r['k']):r for r in baseline}
    by_tag={}
    for r in rows:
        d=float(r['outcome']=='win')-float(old[r['tag'],r['k']]['outcome']=='win')
        by_tag.setdefault(r['tag'],[]).append(d)
    ci=cluster_bootstrap(by_tag,10000,0)
    changes=[d for ds in by_tag.values() for d in ds]
    return dict(delta_pp=100*ci['point'],ci95_pp=[100*ci['lo'],100*ci['hi']],
                paired=len(rows),entries=ci['n_entries'],better=sum(d>0 for d in changes),worse=sum(d<0 for d in changes))


def report(root,folder,partial=False):
    root,folder=Path(root),Path(folder)
    plan=json.loads((folder/'plan.json').read_text())
    for path,digest in plan['sources'].items():
        if sha(root/path)!=digest:
            raise ValueError('Frozen source changed: '+path)
    from scratchpad.gauntlet.L71.decision_options.run_q3 import MODELS
    for name,path in MODELS.items():
        if sha(root/path)!=plan['checkpoints'][name]:
            raise ValueError('Checkpoint changed: '+name)
    expected=keys(read(root/'scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl'))
    if len(expected)!=299:
        raise ValueError('Pinned set is not 299')
    reactive_keys={(opp,seed) for opp in ('gen','s1') for seed in range(24)}
    data={};receipts={};pending=[]
    for job in plan['jobs']:
        file=folder/(job['name']+'.receipt.json')
        if not file.exists():
            pending.append(job['name']);continue
        receipt=json.loads(file.read_text())
        if receipt['command']!=job['command'] or receipt['exit_code']!=0 or set(receipt['outputs'])!=set(job['expected']):
            raise ValueError('Invalid receipt '+job['name'])
        if sha(folder/(job['name']+'.out'))!=receipt['output_sha256']:
            raise ValueError('Process output changed')
        for path,digest in receipt['outputs'].items():
            if sha(root/path)!=digest:
                raise ValueError('Result changed: '+path)
        rows=read(root/job['expected'][0])
        reactive=job['name'].startswith('reactive_')
        validate(rows,reactive_keys if reactive else expected,reactive)
        data[job['name']]=rows
        receipts[job['name']]=sha(file)
    if pending and not partial:
        raise ValueError('Incomplete Q3 jobs: '+','.join(pending))
    models={}
    for model in ('r1e','r1'):
        gbase=data.get('ghost_'+model+'_baseline');rbase=data.get('reactive_'+model+'_baseline')
        if gbase is None or rbase is None:
            continue
        gb,rb=summarize(gbase),summarize(rbase)
        arms={}
        for arm in ('filtered_T1','filtered_T07','area','combined'):
            ghost=data.get('ghost_'+model+'_'+arm);reactive=data.get('reactive_'+model+'_'+arm)
            if ghost is None or reactive is None:
                continue
            gs,rs=summarize(ghost),summarize(reactive)
            paired=compare(ghost,gbase)
            gates=dict(ghost_nonnegative=paired['delta_pp']>=0,reactive_within_two=rs['wins']>=rb['wins']-2,
                rocket_share_closer=abs(gs['rocket_share']-.058)<abs(gb['rocket_share']-.058),
                tower_rockets_increase=gs['tower_rockets']>gb['tower_rockets'])
            arms[arm]=dict(ghost=gs,reactive=rs,paired=paired,gates=gates,passes=all(gates.values()))
        models[model]=dict(baseline=dict(ghost=gb,reactive=rb),arms=arms)
    return dict(schema=1,complete=not pending,pending=pending,plan_sha256=sha(folder/'plan.json'),
        receipts=receipts,models=models,acceptance=plan['acceptance'],
        limitations=['Ghost screen uses recorded nonreactive opponents and unchanged SIM anti-stall.',
            'Tower hits are interpolated geometry; HP confirmation is reported separately.',
            'A pass does not establish a statistically significant win improvement or authorize an unchecked checkpoint.'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--directory',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--partial',action='store_true');a=ap.parse_args()
    result=report(a.root,a.directory,a.partial)
    a.out.write_text(json.dumps(result,indent=2))
    print(json.dumps({m:{a:v['passes'] for a,v in r['arms'].items()} for m,r in result['models'].items()}))
    print('Q3_PARTIAL_REPORT' if a.partial else 'Q3_COMPLETE_REPORT_VERIFIED')


if __name__=='__main__':
    main()
