"""Reconcile fixed experiment receipts and diagnostics before any deployment.

The result is a reviewable verdict, never a deployment hook. Partial reports
cannot nominate a model. Thresholds follow PLAN.md and are not tuned on results.
"""
import argparse
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from pipeline.rocket_teaching import sha
from scratchpad.gauntlet.L71.decision_options.score_q3 import read,keys,validate,summarize,compare
from scratchpad.gauntlet.L71.context_teaching.run_experiments import ARMS,BENCH,source_hashes
from pipeline.expert_context import MIXTURES

CONTROL=dict(v4_uniform='r1e',v4_rocket='v4_uniform',v5_uniform='v4_uniform',
    v5_rocket='v5_uniform',v5_rocket_xbow='v5_rocket',v5_rocket_barrel='v5_rocket',
    v6_rocket_barrel='v5_rocket_barrel',v6_rocket_both='v6_rocket_barrel')


def nominate(verdicts, games, complete):
    if not complete:
        return None
    # Ordinary continuation is a control, not evidence for any requested fix.
    passing=[n for n,v in verdicts.items() if n!='v4_uniform' and v['passes']]
    def rank(n):
        # The spatial residual implements Barrel aiming; it is not another
        # user outcome. Prefer the simpler version only after outcome coverage
        # and both game scores tie, as specified in PLAN.md.
        parts=int(int(n[1])>=5)+int('rocket' in n)+int('xbow' in n or 'both' in n)+int('barrel' in n or 'both' in n)
        return parts,games[n]['ghost']['wins'],games[n]['reactive']['wins'],-int(n[1])
    return max(passing,key=rank) if passing else None


def val(report,key):
    return report[key]['rate']


def context(report,key):
    return report['contexts'][key]['action_agreement']['rate']


def heldout_gates(name,reports):
    current=reports[name];base=reports['r1e'];control=reports[CONTROL[name]]
    gates=dict(global_vs_source=val(current,'global_card_agreement')>=val(base,'global_card_agreement')-.01,
        global_vs_control=val(current,'global_card_agreement')>=val(control,'global_card_agreement')-.01)
    version=int(name[1]);has_rocket='rocket' in name
    if version>=5:
        prior=reports['v4_rocket' if has_rocket else 'v4_uniform']
        gates.update(spawner_action_improves=context(current,'spawners')>context(prior,'spawners'),
            night_witch_within_two_pp=context(current,'night_witch')>=context(prior,'night_witch')-.02)
    if has_rocket:
        prior=reports['v4_uniform' if version==4 else 'v5_uniform']
        gates.update(rocket_recall_improves=val(current,'rocket_recall')>val(prior,'rocket_recall'),
            finishing_rocket_observed=current['rocket_finish']['n']>=1,
            combo_rocket_improves=val(current,'combo_rocket')>val(prior,'combo_rocket'),
            combo_tornado_improves=val(current,'combo_tornado')>val(prior,'combo_tornado'))
    if 'xbow' in name or 'both' in name:
        gates.update(xbow_action_improves=context(current,'xbow')>context(control,'xbow'),
            useful_xbow_within_two_pp=context(current,'xbow_useful')>=context(control,'xbow_useful')-.02)
    if 'barrel' in name or 'both' in name:
        prior=reports['v5_rocket_barrel' if version==6 else 'v5_rocket']['barrel']
        cb=current['barrel']
        if cb['pro_same_lane_rows']!=39 or prior['pro_same_lane_rows']!=39:
            raise ValueError('Barrel diagnostic denominator changed')
        gates.update(barrel_correct_fires_improve=cb['gated_correct_lane']['n']>prior['gated_correct_lane']['n'],
            barrel_wrong_fires_nonincreasing=cb['gated_wrong_lane']['n']<=prior['gated_wrong_lane']['n'])
    return gates


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--partial',action='store_true');a=ap.parse_args()
    plan=json.loads((a.directory/'plan.json').read_text())
    if source_hashes()!=plan['sources']:raise ValueError('Experiment sources changed')
    for path,digest in plan['inputs'].items():
        if sha(ROOT/path)!=digest:raise ValueError('Bound experiment input changed: '+path)
    pending=[];receipts={}
    for job in plan['jobs']:
        path=a.directory/(job['name']+'.receipt.json')
        if not path.exists():pending.append(job['name']);continue
        r=json.loads(path.read_text())
        if r['exit_code'] or not r['marker_matched'] or r['command']!=job['command'] or r['cwd']!=plan['cwd'] or set(r['outputs'])!=set(job['expected']):
            raise ValueError('Failed/inconsistent process: '+job['name'])
        if sha(a.directory/(job['name']+'.out'))!=r['output_sha256']:raise ValueError('Changed process log')
        for output,digest in r['outputs'].items():
            if sha(ROOT/output)!=digest:raise ValueError('Changed output '+output)
        receipts[job['name']]=sha(path)
    if pending and not a.partial:raise ValueError('Incomplete experiments: '+','.join(pending))
    base_dir=ROOT/BENCH/'r1e_heldout'
    base=json.loads((base_dir/'report.json').read_text())
    if sha(base_dir/'predictions.npz')!=base['predictions_sha256']:raise ValueError('Baseline predictions changed')
    reports=dict(r1e=base);training={}
    for name,version,arm in ARMS:
        if 'heldout_'+name not in receipts:continue
        folder=ROOT/BENCH/name
        h=json.loads((folder/'heldout/report.json').read_text());t=json.loads((folder/'result.json').read_text())
        run=json.loads((folder/'run.json').read_text());updates=read(folder/'train.jsonl')
        if len(updates)!=1000 or [r['step'] for r in updates]!=list(range(1,1001)):
            raise ValueError('Incomplete fixed training recipe '+name)
        if t['sampled_cohorts']['pool']!=128000 or run['args']['arm']!=arm or run['args']['feature_version']!=version:
            raise ValueError('Changed training arm '+name)
        recipe=dict(steps=1000,bs=128,lr=1e-5,target_lr=1e-3,seed=20261004,device='cuda',smoke_one_batch=False)
        if any(run['args'].get(k)!=v for k,v in recipe.items()) or run['mixture']!=MIXTURES[arm]:
            raise ValueError('Changed training recipe '+name)
        if any(not math.isfinite(r['loss']) for r in updates):
            raise ValueError('Nonfinite training loss '+name)
        if run['init_checkpoint_sha256']!=base['checkpoint_sha256'] or run['heldout_used_for_sampling']:
            raise ValueError('Changed initialization or held-out exposure '+name)
        if h['checkpoint_sha256']!=t['checkpoint_sha256'] or h['feature_version']!=version:
            raise ValueError('Training/held-out checkpoint mismatch '+name)
        if sha(folder/'heldout/predictions.npz')!=h['predictions_sha256']:
            raise ValueError('Changed candidate predictions '+name)
        for key in ('global_card_agreement','global_action_agreement','rocket_recall','rocket_finish','combo_rocket','combo_tornado'):
            if h[key]['denominator']!=base[key]['denominator']:raise ValueError('Changed held-out cohort '+key)
        if h['contexts'].keys()!=base['contexts'].keys():raise ValueError('Changed context keys')
        for key in h['contexts']:
            if h['contexts'][key]['rows']!=base['contexts'][key]['rows']:raise ValueError('Changed context denominator '+key)
        reports[name]=h;training[name]=dict(final_loss=updates[-1]['loss'],sampled=t['sampled_cohorts'],checkpoint_sha256=t['checkpoint_sha256'])
    expected=keys(read(ROOT/'scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl'))
    if len(expected)!=299:raise ValueError('Changed ghost pins')
    reactive_keys={(op,seed) for op in ('gen','s1') for seed in range(24)}
    games={}
    for name in ['r1e']+[n for n,_,_ in ARMS]:
        if 'ghost_'+name not in receipts or 'reactive_'+name not in receipts:continue
        ghost=read(a.directory/('ghost_'+name+'.jsonl'))
        reactive=read(a.directory/('reactive_'+name)/'matches.jsonl')
        validate(ghost,expected);validate(reactive,reactive_keys,True)
        games[name]=dict(ghost_rows=ghost,ghost=summarize(ghost),reactive=summarize(reactive))
    verdicts={}
    for name,version,arm in ARMS:
        controls={CONTROL[name],'r1e'}
        # Input correction in the Rocket recipe has its own like-for-like ablation.
        if name=='v5_rocket':controls.add('v4_rocket')
        needed=controls | {'v4_uniform','v5_uniform','v4_rocket'} if version>=5 else controls
        if name.startswith('v6'):needed.add('v5_rocket_barrel')
        if name not in reports or any(k not in reports for k in needed):continue
        hg=heldout_gates(name,reports)
        pairings={};gg={}
        if name in games and all(k in games for k in controls):
            for prior in sorted(controls):
                pairings[prior]=compare(games[name]['ghost_rows'],games[prior]['ghost_rows'])
                gg['ghost_vs_'+prior]=pairings[prior]['delta_pp']>=0
                gg['reactive_vs_'+prior]=games[name]['reactive']['wins']>=games[prior]['reactive']['wins']-2
            if 'rocket' in name:
                prior='v4_uniform' if version==4 else 'v5_uniform'
                if prior in games:
                    current,old=games[name]['ghost'],games[prior]['ghost']
                    gg.update(rocket_share_closer=abs(current['rocket_share']-.058)<abs(old['rocket_share']-.058),
                        tower_rockets_increase=current['tower_rockets']>old['tower_rockets'])
                else:gg['rocket_control_unavailable']=False
        else:gg['gameplay_pending']=False
        verdicts[name]=dict(primary_control=CONTROL[name],heldout_gates=hg,gameplay_gates=gg,paired=pairings,
            passes=all(hg.values()) and all(gg.values()),
            ghost=games.get(name,{}).get('ghost'),reactive=games.get(name,{}).get('reactive'))
    complete=not pending
    if complete and len(verdicts)!=len(ARMS):
        raise ValueError('Complete receipts but missing candidate comparisons')
    selected=nominate(verdicts,games,complete)
    result=dict(schema=1,complete=complete,pending=pending,plan_sha256=sha(a.directory/'plan.json'),receipts=receipts,
        training=training,verdicts=verdicts,provisional_selection=selected,review_required=True,deployed=False,
        limitations=['Imitation and simulator outcomes remain distinct from live outcomes.',
            'Full review must retain the one-factor component comparisons and reject unsupported claims.',
            'Rocket area aiming requires its separately declared same-checkpoint comparison.'])
    a.out.write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(dict(complete=complete,passes={n:v['passes'] for n,v in verdicts.items()},provisional_selection=selected)))
    print('EXPERT_EXPERIMENTS_PARTIAL' if a.partial else 'EXPERT_EXPERIMENTS_RECONCILED_REQUIRES_REVIEW')


if __name__=='__main__':main()
