"""One sequential GPU chain, waiting for the frozen Q3 chain to complete.

No deployment. Every training/evaluation/game subprocess has an exit-code and
output hash receipt. Source changes invalidate the chain before the next job.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from scratchpad.gauntlet.L71.decision_options.run_q3 import idle_gpu
from pipeline.rocket_teaching import sha

TRAIN_PY=Path('C:/Users/benpe/ClashBot/icebow/.venv/Scripts/python.exe')
SIM_PY=ROOT/'research/ext/Royale/.venv/Scripts/python.exe'
SOURCE='icebow/data/pipeline/gen_dataset_v31_public.npz'
CORRECTED='icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz'
CORRECTION='icebow/data/bench/spawner_identity_20261005/manifest.json'
CONTEXTS='icebow/data/bench/context_teaching_20261005'
INIT='icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt'
BENCH=Path('icebow/data/bench/expert_context_20261005')
ARMS=[('v4_uniform',4,'uniform'),('v4_rocket',4,'rocket'),('v5_uniform',5,'uniform'),
      ('v5_rocket',5,'rocket'),('v5_rocket_xbow',5,'rocket_xbow'),
      ('v5_rocket_barrel',5,'rocket_barrel'),('v6_rocket_barrel',6,'rocket_barrel'),
      ('v6_rocket_both',6,'rocket_both')]
SCREEN='scratchpad/gauntlet/L71/decision_options/run_screen_v2.py'


def source_hashes():
    files=list((ROOT/'pipeline').glob('*.py'))+[Path(__file__),Path(__file__).with_name('PLAN.md'),ROOT/SCREEN,
        ROOT/'scratchpad/gauntlet/L71/decision_options/score_q3.py',
        ROOT/'pipeline/rl_royale.yaml',ROOT/'scratchpad/gauntlet/L70/pool_forms/loadable_decks.json',
        ROOT/'scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl',
        ROOT/'scratchpad/gauntlet/L70/abilities/ability_models_v2.json',
        ROOT/'scratchpad/gauntlet/L70/gen_v31/xbow_reach_public.json',
        ROOT/'research/ext/Royale/RoyaleSim/data/derived/cards.json',
        ROOT/'research/ext/cr-native-sandbox/native_core/data/live_card_catalog.json']
    return {str(p.relative_to(ROOT)):sha(p) for p in files}


def jobs(out):
    result=[]
    for name,version,arm in ARMS:
        data=SOURCE if version==4 else CORRECTED
        destination=BENCH/name
        common=['--data',data,'--source-data',SOURCE,'--contexts',CONTEXTS]
        if version>=5:common+=['--correction-manifest',CORRECTION]
        result.append(dict(name='train_'+name,expected=[str(destination/'candidate.pt'),str(destination/'result.json'),
            str(destination/'run.json'),str(destination/'train.jsonl')],marker='EXPERT_CONTEXT_TRAINING_FINISHED_REQUIRES_ACCEPTANCE',
            command=[str(TRAIN_PY),'-u','-m','pipeline.train_expert_context',*common,'--init-ckpt',INIT,
                '--out',str(destination),'--arm',arm,'--feature-version',str(version),'--device','cuda',
                '--steps','1000','--bs','128','--lr','1e-5','--target-lr','1e-3','--seed','20261004']))
        result.append(dict(name='heldout_'+name,expected=[str(destination/'heldout/report.json'),str(destination/'heldout/predictions.npz')],
            marker='EXPERT_CONTEXT_HELDOUT_COMPLETE',command=[str(TRAIN_PY),'-u','-m','pipeline.eval_expert_context',
                *common,'--ckpt',str(destination/'candidate.pt'),'--out',str(destination/'heldout'),'--device','cuda']))
    for name,ckpt in [('r1e',INIT)]+[(n,str(BENCH/n/'candidate.pt')) for n,_,_ in ARMS]:
        ghost=out/('ghost_'+name+'.jsonl');reactive=out/('reactive_'+name)
        result.append(dict(name='ghost_'+name,expected=[str(ghost)],marker='[screen]',command=[str(SIM_PY),SCREEN,
            '--ckpt',ckpt,'--out',str(ghost),'--split','train','--noise-off','all','--opp-elixir','counter',
            '--action-delay','26','--extrapolate','26','--seeds','0','--device','cuda','--forms-mode','deck',
            '--tau','.27','--behaviour-telemetry','--only-tags-from','scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl']))
        result.append(dict(name='reactive_'+name,expected=[str(reactive/'matches.jsonl'),str(reactive/'summary.json')],
            marker='"per_arm_opp"',command=[str(SIM_PY),'-m','pipeline.search_s0','--out',str(reactive),'--gen',ckpt,
                '--opp-gen','icebow/data/pipeline/gen_v1_s0/gen_s0.pt','--seeds','0:24','--opps','gen,s1','--arms','plain',
                '--forms-mode','deck','--device','cuda','--workers','3','--tail-cap','7200',
                '--census','scratchpad/gauntlet/L70/pool_forms/loadable_decks.json','--hero-abilities',
                '--ability-policy','v2','--behaviour-telemetry']))
    return result


def q3_done(folder):
    plan=json.loads((folder/'plan.json').read_text())
    for job in plan['jobs']:
        path=folder/(job['name']+'.receipt.json')
        if not path.exists():return False
        if json.loads(path.read_text()).get('exit_code')!=0:raise ValueError('Failed prerequisite Q3 job')
    log=folder.parent/'q3_chain.out'
    return 'Q3_JOBS_COMPLETE' in log.read_text()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--wait-q3',type=Path,required=True);ap.add_argument('--dry-run',action='store_true');a=ap.parse_args()
    plan=dict(schema=1,cwd=str(ROOT),jobs=jobs(a.out),sources=source_hashes(),
        inputs={p:sha(ROOT/p) for p in (SOURCE,CORRECTED,CORRECTION,CONTEXTS+'/cohorts.npz',CONTEXTS+'/manifest.json',
            INIT,'icebow/data/pipeline/gen_v1_s0/gen_s0.pt','icebow/data/pipeline/s1_icebow_v6aug_s1.pt')},
        prerequisite=str(a.wait_q3),recipe='PLAN.md; fixed final step; no deployment')
    if a.dry_run:
        print(json.dumps(dict(jobs=len(plan['jobs']),sources=len(plan['sources']),inputs=len(plan['inputs']))));return
    a.out.mkdir(parents=True,exist_ok=True);file=a.out/'plan.json'
    if file.exists():
        if json.loads(file.read_text())!=plan:raise ValueError('Plan/source changed')
    else:file.write_text(json.dumps(plan,indent=2))
    print(datetime.now().isoformat(),'WAIT_FOR_Q3_COMPLETE',flush=True)
    while not q3_done(a.wait_q3):time.sleep(30)
    from scratchpad.gauntlet.L71.decision_options.score_q3 import report as q3_report
    verified=q3_report(a.wait_q3.resolve().parents[4],a.wait_q3)
    (a.out/'q3_verified.json').write_text(json.dumps(verified,indent=2))
    baseline=ROOT/'scratchpad/gauntlet/L71/integration/checks/heldout-r1e.json'
    if not baseline.is_file():raise ValueError('CPU held-out diagnostic has not finished')
    checked=json.loads(baseline.read_text())
    if checked['exit_code'] or not checked['matched']:raise ValueError('CPU held-out diagnostic failed')
    for path,digest in plan['inputs'].items():
        if sha(ROOT/path)!=digest:raise ValueError('Training input changed while waiting: '+path)
    print(datetime.now().isoformat(),'Q3_PREREQUISITE_COMPLETE',flush=True)
    for job in plan['jobs']:
        receipt=a.out/(job['name']+'.receipt.json')
        if receipt.exists():
            old=json.loads(receipt.read_text())
            if old['command']!=job['command'] or old['exit_code'] or not old['marker_matched']:
                raise ValueError('Invalid prior job receipt')
            for path,digest in old['outputs'].items():
                if sha(ROOT/path)!=digest:raise ValueError('Completed job output changed')
            continue
        if source_hashes()!=plan['sources']:raise ValueError('Source changed during experiments')
        idle_gpu()
        print(datetime.now().isoformat(),'START',job['name'],flush=True)
        log=a.out/(job['name']+'.out');start=time.time()
        with log.open('w') as stream:
            p=subprocess.run(job['command'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        matched=job['marker'] in log.read_text()
        r=dict(command=job['command'],cwd=str(ROOT),exit_code=p.returncode,marker=job['marker'],marker_matched=matched,
            output_sha256=sha(log),seconds=time.time()-start,
            outputs={path:sha(ROOT/path) for path in job['expected'] if (ROOT/path).is_file()})
        receipt.write_text(json.dumps(r,indent=2))
        if p.returncode or not matched or set(r['outputs'])!=set(job['expected']):
            raise RuntimeError('Job failed: '+job['name'])
        print(datetime.now().isoformat(),'DONE',job['name'],flush=True)
    print('EXPERT_CONTEXT_ALL_JOBS_COMPLETE_REQUIRES_REVIEW',flush=True)


if __name__=='__main__':main()
