"""Remeasure native accepted ability shares/delays with stable controller IDs.

Only unambiguous command-to-controller links become calibration targets. Missing
or multiply linked deployments are reported, never silently labelled no-press.
No model fitting or changes to live/SIM ability policies.
"""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parent/'gen_v31'))
from phase2_build import ability_for_deck,ABILITIES,controller_entities
from audit_runtime import lower_own_priority

def extract(rec,controller_ids):
    decks={s:{a.removesuffix('-hero'):a for c in rec['final_decks'][str(s)] if (a:=ability_for_deck(c))} for s in (0,1)}
    deps=[];bykey=defaultdict(list);presses=[];counts=Counter()
    for p in rec['log']:
        if not p.get('accepted'):continue
        if p.get('ability'):
            presses.append(p);continue
        side=int(p['side']);a=decks[side].get(p.get('card'))
        if a is None:continue
        d=dict(ability=a,tag=rec['tag'],side=side,play_index=p['play_index'],
            tick=int(p.get('engine_tick') or (p['tick']+p.get('delay_ticks',0))),
            entities=[],press_ticks=[],status='NO_OBSERVED_CONTROLLER')
        deps.append(d);bykey[side,a].append(d)
    for ds in bykey.values():ds.sort(key=lambda d:d['tick'])
    seen={};entity_dep={}
    for f in sorted(rec.get('frames',[])+rec.get('play_frames',[]),key=lambda f:f['tick']):
        for e in f['entities']:
            if len(e)!=9 or e[4]<=0:continue
            side,cid,eid=int(e[0]),int(e[-2]),int(e[-1]);ident=(side,eid)
            if ident in seen:continue
            for a in decks[side].values():
                if cid not in controller_ids.get(a,set()):continue
                if not controller_entities(a,[e],int(rec.get('level',11))):continue
                seen[ident]=True
                candidates=[d for d in bykey[side,a] if 0<=f['tick']-d['tick']<=100]
                # Full five-second lookback covers travel/deploy delay; if it
                # contains multiple casts, attribution stays unresolved.
                if len(candidates)==1:
                    d=candidates[0];d['entities'].append(eid);entity_dep[ident]=d
                else:
                    counts['controller_without_unique_deployment']+=1
                    for d in candidates:d['status']='AMBIGUOUS_CONTROLLER_LINK'
    for d in deps:
        if d['status']=='AMBIGUOUS_CONTROLLER_LINK':continue
        if len(d['entities'])==1:d['status']='LINKED'
        elif len(d['entities'])>1:d['status']='MULTIPLE_POSSIBLE_CONTROLLERS'
    for p in presses:
        ident=int(p['side']),int(p['entity_id']);d=entity_dep.get(ident)
        if d is None or d['status']!='LINKED':
            counts['accepted_press_without_unique_deployment']+=1
            a=decks[ident[0]].get(p.get('card'))
            for candidate in bykey.get((ident[0],a),[]):
                if candidate['status']=='LINKED':candidate['status']='UNLINKED_ACCEPTED_PRESS_IN_REPLAY'
            continue
        expected=decks[ident[0]].get(p.get('card'))
        if expected!=d['ability']:raise ValueError('Native controller ability attribution mismatch')
        tick=int(p.get('engine_tick') or p['tick'])
        if tick<d['tick']:raise ValueError('Press before deployment')
        d['press_ticks'].append(tick)
    for d in deps:
        d['press_ticks']=sorted(d['press_ticks'])
        d['delay_s']=(d['press_ticks'][0]-d['tick'])*.05 if d['press_ticks'] else None
    return deps,dict(counts)

def describe(ds):
    linked=[d for d in ds if d['status']=='LINKED'];delay=[d['delay_s'] for d in linked if d['delay_s'] is not None]
    return dict(accepted_deployments=len(ds),linked_deployments=len(linked),status_counts=dict(Counter(d['status'] for d in ds)),
        pressed_linked_deployments=len(delay),pressed_share=len(delay)/len(linked) if linked else None,
        median_first_delay_s=float(np.median(delay)) if delay else None,
        p10_first_delay_s=float(np.quantile(delay,.1)) if delay else None,
        p90_first_delay_s=float(np.quantile(delay,.9)) if delay else None,
        repeated_press_share=sum(len(d['press_ticks'])>1 for d in linked)/len(linked) if linked else None)

def intervals(ds):
    groups=defaultdict(list)
    for d in ds:groups[d['tag']].append(d)
    groups=list(groups.values());rng=np.random.default_rng(20261003);shares=[];delays=[]
    if not groups:return dict(share_ci95=None,median_delay_ci95_s=None)
    # Deployment counts and per-replay delay vectors keep cluster resampling
    # efficient without reconstructing dictionaries a thousand times.
    ns=np.array([sum(d['status']=='LINKED' for d in g) for g in groups]);ps=np.array([sum(d['status']=='LINKED' and d['delay_s'] is not None for d in g) for g in groups])
    xs=[np.array([d['delay_s'] for d in g if d['status']=='LINKED' and d['delay_s'] is not None]) for g in groups]
    for _ in range(1000):
        ix=rng.integers(len(groups),size=len(groups));n=ns[ix].sum()
        if n:shares.append(float(ps[ix].sum()/n))
        values=np.concatenate([xs[i] for i in ix])
        if len(values):delays.append(float(np.median(values)))
    return dict(share_ci95=np.quantile(shares,[.025,.975]).tolist() if shares else None,
        median_delay_ci95_s=np.quantile(delays,[.025,.975]).tolist() if delays else None)

def main(out,repair_from=None):
    out.mkdir(exist_ok=False)
    manifest_path=HERE.parent/'gen_v31/native_mining_1552/manifest.json';manifest_raw=manifest_path.read_bytes()
    evidence=json.loads((HERE/'native_evidence_1903/report.json').read_text())
    controllers={a:{int(c) for c in evidence['abilities'].get(a.removesuffix('-hero'),{}).get('native_controller_ids',{})} for a in ABILITIES}
    all_ds=[];counts=Counter();selected_tags=None
    if repair_from is not None:
        prior=json.loads((repair_from/'report.json').read_text())
        if prior['source_manifest_sha256']!=hashlib.sha256(manifest_raw).hexdigest():raise ValueError('Repair source manifest changed')
        old=[json.loads(line) for line in (repair_from/'deployments.jsonl').read_text().splitlines()]
        selected_tags={d['tag'] for d in old if d['ability'] in ('goblinstein','goblins-hero','tombstone-hero')}
        all_ds=[d for d in old if d['tag'] not in selected_tags]
    for i,row in enumerate(json.loads(manifest_raw)):
        if selected_tags is not None and row['tag'] not in selected_tags:continue
        raw=(ROOT/row['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Native source hash mismatch')
        rec=json.loads(raw)
        ds,cs=extract(rec,controllers);all_ds.extend(ds);counts.update(cs)
        time.sleep(.05)
        if (i+1)%500==0:print('NATIVE_TARGETS',i+1,flush=True)
    report=dict(status='MEASURED_NATIVE_TARGETS_UNAMBIGUOUS_SUBSET_NOT_CALIBRATED_POLICY',
        source_manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),controller_ids={a:sorted(v) for a,v in controllers.items()},
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),counts=dict(counts),abilities={},
        bootstrap='1000 replay-cluster resamples; seed20261003',
        limitations=['Five-second unique deployment-to-controller attribution window; ambiguous/missing links excluded and counted.',
            'Goblinstein doctor, hero Goblins flag and hero Tombstone controller are distinguished by the existing public max-HP contract; card ID alone aliases their siblings.',
            'Survival/readiness eligibility is not observed continuously in historical recordings; targets are deployment shares, not ready-button hazards.',
            'Native re-drive acceptances are not the original human input timing.',
            'These targets do not authorize a calibrated policy or satisfy per-ability delay-error acceptance.'])
    if repair_from is not None:
        report['repair']=dict(prior=str(repair_from),prior_report_sha256=hashlib.sha256((repair_from/'report.json').read_bytes()).hexdigest(),
            prior_deployments_sha256=hashlib.sha256((repair_from/'deployments.jsonl').read_bytes()).hexdigest(),
            reread_replays=len(selected_tags),counts_scope='Repair replay subset only; other deployment records reused exactly.')
    for a in ABILITIES:
        ds=[d for d in all_ds if d['ability']==a]
        report['abilities'][a]=dict(describe(ds),**intervals(ds))
    (out/'deployments.jsonl').write_text(''.join(json.dumps(d)+'\n' for d in all_ds))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('NATIVE_TARGETS_COMPLETE',len(all_ds),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--repair-from',type=Path);args=p.parse_args()
    lower_own_priority();main(args.out,args.repair_from)
