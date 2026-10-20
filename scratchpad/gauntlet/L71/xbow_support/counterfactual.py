"""Matched SIM support/WAIT diagnostics with the actual opponent kept fixed.

Every branch resumes both policies after one root intervention. Never imported
by live play or training. Root engine truth is an offline simulation limitation.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import sys

import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from pipeline import e1_eval as E, search_s0 as S
from pipeline.decision_options import match_kwargs
from pipeline.dataset_gen import card_key
from pipeline.model_v3 import cell_xy
from pipeline.public_geometry import constants,in_xbow_range
from pipeline.public_outcomes import normalize
from pipeline.rocket_teaching import catalog,sha
from pipeline.body_identity import resolve
from pipeline import vocab


def candidates(raw,side,decision,deck,grid,initial_towers):
    if not decision['play'] or card_key(deck[decision['slot']])=='x-bow':return []
    x,y=cell_xy(decision['cell'],grid)
    x,y=((x*18000,(1-y)*32000) if side==0 else ((1-x)*18000,y*32000))
    public=normalize(raw,'sim')
    raw_ids={e['entity_id']:e for e in raw['entities']}
    for body in public['bodies']:
        e=raw_ids[body['id']]
        identity=resolve(e['name'],e['max_hp'])
        if identity.cls is not None:
            body['card']=vocab.UNIT_VOCAB[identity.cls].replace('_','-')
    current={(t['side'],t['kind'],t['x'],t['y']):t for t in public['towers']}
    towers=[current.get((t['side'],t['kind'],t['x'],t['y']),dict(t,hp=0)) for t in initial_towers]
    result=[]
    for bow in public['bodies']:
        if bow['side']!=side or bow['card']!='x-bow' or bow['hp']<=0:continue
        lane=[t for t in towers if t['side']!=side and t['kind']=='princess' and (t['x']<9000)==(bow['x']<9000)]
        if len(lane)!=1 or lane[0]['hp']>0 or math.hypot(x-bow['x'],y-bow['y'])>5000:continue
        crown=any(t['side']!=side and t['hp']>0 and in_xbow_range(bow,t) for t in towers)
        ground=[e for e in public['bodies'] if e['side']!=side and e['hp']>0 and
            catalog().get(e['card'],{}).get('flying_height',0)==0 and
            math.hypot(e['x']-bow['x'],e['y']-bow['y'])<=constants()['xbow_range']]
        result.append(dict(bow=bow,cast=dict(x=x,y=y,card=card_key(deck[decision['slot']])),
            crown_reachable=crown,ground_targets=len(ground),no_target_now=not crown and not ground))
    return result


def plain_todo(ds):
    todo=[]
    for s in ds:
        p,enc,h,hand=S.forward(s);_,allowed,stalled=s.pre(hand)
        d=E.live_decide_batch(s.model,enc,h,[p],allowed[None],np.array([stalled]),tau=s.cfg['tau'],
                             device=s.cfg['device'],**match_kwargs([s]))[0]
        todo.append((s,p,d))
    return todo


def branch_pair(run,m,ds,todo,out):
    """Return both branches and prove the root engine/public Python state survives."""
    from pipeline.tests.test_search_s0 import env_digest,side_digest,new_st
    original=(env_digest(m.env),side_digest(m.learner),side_digest(m.opp))
    blob=m.env.core.save_state();digest=hashlib.sha256(blob).hexdigest()
    out.mkdir(parents=True);(out/'root.bin').write_bytes(blob)
    root_tick=m.env.tick;cap=min(m.env.tail_cap,root_tick+240);us=m.learner.side
    n0=len(m.learner.plays);scorer=S.make_scorer(m.env,'v2');s0=scorer.snapshot(m.env.core.state(),us)
    reports=[]
    for index,arm in enumerate(('support','wait')):
        f=S.fork_into(m,run._pool(2)[index],blob);f.env.tail_cap=cap
        assert f.opp.model is m.opp.model and f.learner.model is m.learner.model
        for s,p,d in todo:
            target=f.learner if s is m.learner else f.opp
            target.apply(p,S.WAIT if s is m.learner and arm=='wait' else d)
        stats=new_st();rng=random.Random(0)
        while due:=f.due():
            S.Runner.round(run,f,due,'plain',stats,rng)
        st=f.env.core.state();spent=S.fork_spent(f.learner,n0)
        accepted=[r for r in f.learner.plays[n0:] if r['accepted']]
        assert abs(spent-sum(f.learner.costs[r['slot']] for r in accepted))<1e-6
        reports.append(dict(arm=arm,end_tick=f.env.tick,accepted_followup_plays=accepted,all_elixir_spent=spent,
            remaining_elixir=st.players[us].elixir_milli/1000,
            hand=[f.env.names.get(c,str(c)) for c in st.players[us].hand],
            our_tower_hp=S.tower_hp(st,us),enemy_tower_hp=S.tower_hp(st,1-us),
            crowns_for=st.players[us].crowns,crowns_against=st.players[1-us].crowns,
            score_v2=scorer.score(s0,scorer.snapshot(st,us),spent)))
    assert m.env.core.save_state()==blob
    assert original==(env_digest(m.env),side_digest(m.learner),side_digest(m.opp))
    return dict(root_tick=root_tick,root_sha256=digest,horizon_ticks=240,branches=reports,
        support_minus_wait_score=reports[0]['score_v2']-reports[1]['score_v2'],
        support_minus_wait_our_tower_hp=reports[0]['our_tower_hp']-reports[1]['our_tower_hp'],
        support_minus_wait_spending=reports[0]['all_elixir_spent']-reports[1]['all_elixir_spent'])


class AuditRunner(S.Runner):
    def round(self,m,ds,arm,st,rng):
        for s in ds:s.prepare()
        todo=plain_todo(ds)
        for s,p,d in todo:
            if s is not m.learner:continue
            slot_deck=[s.engine_deck[s.deck_index_of_slot[i]] for i in range(8)]
            contexts=candidates(m.env.raw(),s.side,d,slot_deck,s.cfg['grid'],self.initial_towers)
            eligible=[v for v in contexts if (m.spec['tag'],v['bow']['id']) not in self.seen]
            if eligible:
                context=eligible[0];self.seen.add((m.spec['tag'],context['bow']['id']))
                ix=len(self.events)
                result=branch_pair(self,m,ds,todo,self.output/('root_'+str(ix)))
                result.update(context=context,spec=m.spec,opponent_policy='unchanged actual frozen gen',
                    root_decision=d,root_gate=float(p))
                self.events.append(result)
                (self.output/('root_'+str(ix))/'result.json').write_text(json.dumps(result,indent=2))
                print(json.dumps(dict(event='matched_support',root=ix,tick=m.env.tick,
                    no_target=context['no_target_now'],score_delta=result['support_minus_wait_score'])),flush=True)
        for s,p,d in todo:s.apply(p,d)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seeds',type=int,default=24);a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh diagnostic output required')
    args=dict(threads=1,device='cpu',gen='icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt',
        opp_gen=S.GEN_CKPT,opps=['gen'],tail_cap=7200,forms_mode='deck',hero_abilities=True,ability_policy='v2',
        horizon=12,interval=1,topk=4,cells=3,search_min_p=0,rollout_self='policy',scorer='v2',
        census='scratchpad/gauntlet/L70/pool_forms/loadable_decks.json')
    S._init_worker(args);run=S._W['runner'];run.__class__=AuditRunner
    run.output=a.out;run.events=[];run.seen=set();a.out.mkdir(parents=True)
    manifest=dict(args=args,script_sha256=sha(__file__),checkpoints={k:sha(ROOT/args[k]) for k in ('gen','opp_gen')},
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'pipeline').glob('*.py')},
        selection='first support decision per observed dead-lane X-Bow; all gen seeds 0..N-1',
        limitations=['Root simulator truth is used only for offline branches, never policy inputs or training.',
            'Nearby spending is spatial association, not inferred intent.',
            'Twelve-second horizon and v2 board-value approximation cannot prove full-game benefit.'])
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    matches=[]
    for seed in range(a.seeds):
        got=S.setup_job(run,S._W['census'],'gen',seed)
        if got is None:raise ValueError('Missing loadable diagnostic seed')
        m,name=got;run.initial_towers=normalize(m.env.raw(),'sim')['towers']
        result=run.play('plain',m);result['opp_deck_name']=name;matches.append(result)
        print(json.dumps(dict(seed=seed,outcome=result['outcome'],events=len(run.events))),flush=True)
    report=dict(matches=matches,events=run.events,manifest_sha256=sha(a.out/'manifest.json'))
    (a.out/'report.json').write_text(json.dumps(report,indent=2))
    print('XBOW_MATCHED_COUNTERFACTUAL_COMPLETE')


if __name__=='__main__':main()
