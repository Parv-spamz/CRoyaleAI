"""Independent raw recount; does not import the producer or original scorer."""
import collections,copy,gzip,hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
def tower_value(frame,side):
    if frame is None:return None
    tw=frame['towers'];keys={(v['side'],v['kind'],v['x'],v['y']) for v in tw};assert len(tw)==6 and len(keys)==6
    for s in (0,1):
        kinds=sorted(v['kind'] for v in tw if v['side']==s);assert kinds==['king','princess','princess']
    if any(v.get('hp') is None for v in tw):return None
    for v in tw:assert v['hp']>=0 and math.isfinite(v['hp'])
    own=[v['hp'] for v in tw if v['side']==side and v['hp']>0];enemy=[v['hp'] for v in tw if v['side']!=side and v['hp']>0]
    if not own or not enemy:return None
    cr=[]
    for s in (1-side,side):
        dead=[v for v in tw if v['side']==s and v['hp']==0]
        cr.append(3 if any(v['kind']=='king' for v in dead) else len(dead))
    return {'margin':min(own)-min(enemy),'own_min':min(own),'enemy_min':min(enemy),'crowns':cr}
def divergence(a,b):
    events=[]
    for d in (a,b):
        events.append(sorted((v['tick'],v['side'],v['card'],v['x'],v['y'],v['ability']) for v in d['accepted_plays']))
    different=None
    for i in range(max(map(len,events))):
        u=events[0][i] if i<len(events[0]) else None;v=events[1][i] if i<len(events[1]) else None
        if u!=v:different=min(x[0] for x in (u,v) if x is not None);break
    if different is None:return {'first_tick':None,'frames_equal_before':None,'commands_v5':[],'commands_v6':[],'different_roles':[]}
    cmds=[[list(x[1:]) for x in es if x[0]==different] for es in events]
    fa=[v for v in a['frames'] if v['tick']<different];fb=[v for v in b['frames'] if v['tick']<different]
    ca,cb=map(lambda vs:collections.Counter(map(tuple,vs)),cmds)
    diff=(ca-cb)+(cb-ca)
    return {'first_tick':different,'frames_equal_before':fa==fb if fa and fb else None,'commands_v5':cmds[0],'commands_v6':cmds[1],
        'different_roles':sorted({'learner' if v[0]==a['match']['learner_side'] else 'opponent' for v in diff})}
def controls():
    f={'towers':[dict(side=s,kind=k,x=x,y=s,hp=h) for s in (0,1) for k,x,h in [('king',9,4000),('princess',3,1000 if s==0 else 700),('princess',14,3000)]]}
    assert tower_value(f,0)['margin']==300 and tower_value(f,1)['margin']==-300
    d=copy.deepcopy(f);d['towers'][1]['hp']=0;assert tower_value(d,0)=={'margin':2300,'own_min':3000,'enemy_min':700,'crowns':[0,1]}
    d=copy.deepcopy(f);d['towers'][0]['hp']=None;assert tower_value(d,0) is None
    bad=[]
    for key,val in [('side',2),('kind','building'),('hp',-1),('hp',float('nan'))]:
        d=copy.deepcopy(f);d['towers'][1][key]=val;bad.append(d)
    d=copy.deepcopy(f);d['towers'][2]=copy.deepcopy(d['towers'][1]);bad.append(d)
    for d in bad:
        try:tower_value(d,0)
        except AssertionError:pass
        else:raise AssertionError('corrupt tower accepted')
    ev=lambda t,c:dict(tick=t,side=0,card=c,x=3,y=4,ability=False,accepted=True)
    a=dict(match={'learner_side':0},frames=[{'tick':9,'v':1},{'tick':11,'v':1}],accepted_plays=[ev(10,'Log'),ev(10,'Knight')]);b=copy.deepcopy(a);b['accepted_plays'].reverse()
    assert divergence(a,b)['first_tick'] is None
    b['accepted_plays'][0]['card']='Tesla';b['frames'][1]['v']=2
    assert divergence(a,b)['first_tick']==10 and divergence(a,b)['frames_equal_before'] is True
    b['frames'][0]['v']=2;assert divergence(a,b)['frames_equal_before'] is False
    return dict(tower_positive=3,tower_corruptions=5,command_positive=2,prior_frame_negative=1)
def main():
    assert not (HERE/'verified.json').exists();s=read(HERE/'started.json');r=read(HERE/'report.json')
    assert sha(HERE/'started.json')==r['started_sha256'];assert r['complete']
    for p,h in s['sources'].items():assert sha(ROOT/p)==h
    cs=controls();expected={(v['model'],v['tag']):v for v in r['matches']};assert len(expected)==192
    cache={};totals={}
    for row in s['index']:
        path=ROOT/row['path'];assert sha(path)==row['sha256']
        with gzip.open(path,'rt') as f:d=json.load(f)
        key=(d['model'],d['tag']);q=expected.pop(key);fr=d['full_result'];m=d['match']
        refused=[dict(tick=v['tick'],land_tick=v['land_tick'],reason=v['reason'],card=v['card']) for v in fr['plays'] if v['accepted'] is False]
        reasons=dict(collections.Counter(v['reason'] for v in refused));assert q['rejected']==refused and q['reasons']==reasons==fr['refuse_reasons']
        assert q['end_tick']==m['end_tick'] and q['outcome']==m['outcome']
        before=after=0
        for v in refused:
            if v['reason']=='game_over':
                assert v['land_tick']>=6000 and v['land_tick']<=m['end_tick'];before+=v['tick']<6000;after+=v['tick']>=6000
        assert (before,after)==(q['game_over_decided_before'],q['game_over_decided_after'])
        assert all(v['tick']<6000 for v in d['accepted_plays'])
        for tick,name in [(5999,'pre_end'),(6003,'after_clear')]:
            fs=[v for v in d['frames'] if v['tick']==tick]
            assert not fs or all(v==fs[0] for v in fs)
            assert tower_value(fs[0] if fs else None,m['learner_side'])==q[name]
        if d['model']!='r1e':cache[key]=dict(match={'learner_side':m['learner_side'],'outcome':m['outcome']},accepted_plays=d['accepted_plays'],frames=d['frames'])
        z=totals.setdefault(d['model'],collections.Counter());z['games']+=1;z['reached6000']+=m['end_tick']>=6000;z.update(reasons);z['game_over_decided_before']+=before;z['game_over_decided_after']+=after
        t=q['after_clear']
        if t is not None:
            z['after_clear_known']+=1;z['after_clear_'+m['outcome']]+=1;v=t['margin'];z['after_clear_ahead' if v>0 else 'after_clear_behind' if v<0 else 'after_clear_equal']+=1
            z['after_clear_sign_matches_winner']+=m['outcome']==('win' if v>0 else 'loss' if v<0 else 'draw')
    assert not expected and totals==r['totals'];assert len(r['pairs'])==64
    counts=collections.Counter();cards=collections.Counter();seen=set()
    for q in r['pairs']:
        tag=q['tag'];assert tag not in seen;seen.add(tag);a,b=cache[('ordinary_v5',tag)],cache[('ordinary_v6',tag)]
        out=divergence(a,b);out.update(tag=tag,v5_outcome=a['match']['outcome'],v6_outcome=b['match']['outcome']);assert out==q
        counts['pairs']+=1;counts['no_command_difference' if q['first_tick'] is None else 'different']+=1
        if q['first_tick'] is not None:
            counts['equal_prior_frames' if q['frames_equal_before'] is True else 'nonidentical_or_missing_prior_frames']+=1;counts['first_roles_'+','.join(q['different_roles'])]+=1
            side=a['match']['learner_side'];c0=tuple(v[1] for v in q['commands_v5'] if v[0]==side);c1=tuple(v[1] for v in q['commands_v6'] if v[0]==side);cards[repr(c0)+' -> '+repr(c1)]+=1
    assert counts==r['pair_counts'] and cards==r['first_learner_cards']
    for p,h in s['sources'].items():assert sha(ROOT/p)==h
    (HERE/'verified.json').write_text(json.dumps(dict(complete=True,report_sha256=sha(HERE/'report.json'),started_sha256=sha(HERE/'started.json'),matches=192,pairs=64,controls=cs,policy_predictions=0,optimizer_updates=0,new_games=0),indent=2)+'\n')
    print('GAMEPLAY_FAILURE_INDEPENDENT_COMPLETE')
if __name__=='__main__':main()
