"""Post-game source/terminal/common-prefix diagnosis; no policy or engine calls."""
import collections,gzip,hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
GAME=HERE.parent/'development_gameplay_1';OUT=ROOT/'icebow/data/bench/development_gameplay_1_20261005'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def load(row):
    p=ROOT/row['path'];assert sha(p)==row['sha256']
    with gzip.open(p,'rt') as f:return json.load(f)
def margin(frame,side):
    if frame is None:return None
    towers=frame['towers'];ids=[(x['side'],x['kind'],x['x'],x['y']) for x in towers]
    assert len(towers)==len(set(ids))==6
    assert collections.Counter((x['side'],x['kind']) for x in towers)=={(0,'king'):1,(1,'king'):1,(0,'princess'):2,(1,'princess'):2}
    if any(x.get('hp') is None for x in towers):return None
    assert all(math.isfinite(x['hp']) and x['hp']>=0 for x in towers)
    mins=[];crowns=[]
    for s in (side,1-side):
        live=[x['hp'] for x in towers if x['side']==s and x['hp']>0]
        if not live:return None
        mins.append(min(live))
        enemy=[x for x in towers if x['side']!=s];crowns.append(3 if any(x['kind']=='king' and x['hp']==0 for x in enemy) else sum(x['kind']=='princess' and x['hp']==0 for x in enemy))
    return dict(margin=mins[0]-mins[1],own_min=mins[0],enemy_min=mins[1],crowns=crowns)
def commands(d):
    c=collections.defaultdict(list)
    for p in d['accepted_plays']:
        assert p['accepted'];c[p['tick']].append((p['side'],p['card'],p['x'],p['y'],p['ability']))
    return {t:sorted(v) for t,v in c.items()}
def pair(a,b):
    x,y=commands(a),commands(b);ticks=sorted(set(x)|set(y))
    t=next((t for t in ticks if x.get(t,[])!=y.get(t,[])),None)
    if t is None:return dict(first_tick=None,frames_equal_before=None,commands_v5=[],commands_v6=[],different_roles=[])
    px=[f for f in a['frames'] if f['tick']<t];py=[f for f in b['frames'] if f['tick']<t]
    assert all(x.get(k,[])==y.get(k,[]) for k in ticks if k<t)
    left=collections.Counter(x.get(t,[]))-collections.Counter(y.get(t,[]));right=collections.Counter(y.get(t,[]))-collections.Counter(x.get(t,[]))
    roles=sorted(set('learner' if p[0]==a['match']['learner_side'] else 'opponent' for p in list(left)+list(right)))
    return dict(first_tick=t,frames_equal_before=(px==py if px and py else None),commands_v5=x.get(t,[]),commands_v6=y.get(t,[]),different_roles=roles)
def main():
    assert not (HERE/'started.json').exists()
    index=[json.loads(x) for x in (OUT/'matches.jsonl').read_text().splitlines()]
    assert len(index)==192
    files=[HERE/'PLAN.md',*HERE.glob('*.py'),GAME/'prepared.json',GAME/'results_verified.json',GAME/'reviewed_results.json',OUT/'matches.jsonl',ROOT/'pipeline/royale_env.py',ROOT/'pipeline/e1_eval.py',ROOT/'research/ext/Royale-20261005/RoyaleSim/crates/royalesim/src/state.rs',ROOT/'research/ext/Royale-20261005/runtime/royalesim/data/calibration.json']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in files}
    write(HERE/'started.json',dict(sources=hashes,index=index,policy_predictions=0,optimizer_updates=0,new_games=0))
    rows=[];lookup={};totals={}
    for row in index:
        d=load(row);a=d['model'];m=d['match'];fr=d['full_result'];lookup[(a,d['tag'])]=row
        reasons=collections.Counter(p['reason'] for p in fr['plays'] if not p['accepted'])
        assert reasons==collections.Counter(fr['refuse_reasons'])
        rejected=[dict(tick=p['tick'],land_tick=p['land_tick'],reason=p['reason'],card=p['card']) for p in fr['plays'] if not p['accepted']]
        go=[p for p in rejected if p['reason']=='game_over']
        assert all(6000<=p['land_tick']<=m['end_tick'] for p in go)
        assert not any(p['tick']>=6000 for p in d['accepted_plays'])
        f={x['tick']:x for x in d['frames']}
        r=dict(model=a,tag=d['tag'],outcome=m['outcome'],end_tick=m['end_tick'],reasons=dict(reasons),rejected=rejected,
            game_over_decided_before=sum(p['tick']<6000 for p in go),game_over_decided_after=sum(p['tick']>=6000 for p in go),
            pre_end=margin(f.get(5999),m['learner_side']),after_clear=margin(f.get(6003),m['learner_side']))
        rows.append(r);s=totals.setdefault(a,collections.Counter());s['games']+=1;s['reached6000']+=m['end_tick']>=6000
        s['game_over_decided_before']+=r['game_over_decided_before'];s['game_over_decided_after']+=r['game_over_decided_after'];s.update(reasons)
        if r['after_clear'] is not None:
            s['after_clear_known']+=1;s['after_clear_'+m['outcome']]+=1
            mar=r['after_clear']['margin'];s['after_clear_ahead' if mar>0 else 'after_clear_behind' if mar<0 else 'after_clear_equal']+=1
            s['after_clear_sign_matches_winner']+=m['outcome']==('win' if mar>0 else 'loss' if mar<0 else 'draw')
    pairs=[];counts=collections.Counter();card_changes=collections.Counter()
    for a,tag in sorted(lookup):
        if a!='ordinary_v5':continue
        x,y=load(lookup[(a,tag)]),load(lookup[('ordinary_v6',tag)])
        q=pair(x,y);q.update(tag=tag,v5_outcome=x['match']['outcome'],v6_outcome=y['match']['outcome']);pairs.append(q)
        counts['pairs']+=1;counts['no_command_difference' if q['first_tick'] is None else 'different']+=1
        if q['first_tick'] is not None:
            counts['equal_prior_frames' if q['frames_equal_before'] is True else 'nonidentical_or_missing_prior_frames']+=1
            counts['first_roles_'+','.join(q['different_roles'])]+=1
            l=x['match']['learner_side'];c0=tuple(c[1] for c in q['commands_v5'] if c[0]==l);c1=tuple(c[1] for c in q['commands_v6'] if c[0]==l)
            card_changes[repr(c0)+' -> '+repr(c1)]+=1
    for p,h in hashes.items():assert sha(ROOT/p)==h
    write(HERE/'report.json',dict(complete=True,started_sha256=sha(HERE/'started.json'),matches=rows,pairs=pairs,totals=totals,pair_counts=counts,first_learner_cards=card_changes,developmental_only=True,deployment_accepted=False))
    print(json.dumps(dict(totals=totals,pair_counts=counts,first_learner_cards=card_changes),indent=2));print('GAMEPLAY_FAILURE_AUDIT_COMPLETE')
if __name__=='__main__':main()
