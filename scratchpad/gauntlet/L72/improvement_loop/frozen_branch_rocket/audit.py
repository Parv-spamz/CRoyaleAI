"""Vectorized cached-error diagnosis; no policy forward passes."""
from data_io import *
CAND='frozen_base_projectile_v6';CONTROL='ordinary_v5'
def patch(c):return (c//36//4)*9+c%36//4
def geometry(s):
    obj=s['projectiles'];xy=obj[:,:,4:6]
    valid=(obj[:,:,0]>0)&np.isfinite(xy).all(2)&(xy>=0).all(2)&(xy<=1).all(2)
    cells=np.floor(np.where(valid[:,:,None],xy,0)*np.array([9,16],np.float32)).astype(int);cells=np.clip(cells,[0,0],[8,15])
    support=np.zeros((len(obj),144),bool)
    for row,slot in zip(*np.where(valid)):
        x,y=cells[row,slot]
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                if 0<=x+dx<9 and 0<=y+dy<16:support[row,(y+dy)*9+x+dx]=True
    target=np.clip(np.rint(s['y_xy']*[np.float32(36),np.float32(64)]),[0,0],[35,63]).astype(int)
    target=target[:,1]*36+target[:,0]
    own=(valid&(obj[:,:,1]==0)).any(1);enemy=(valid&(obj[:,:,1]==1)).any(1)
    assert np.all(~valid|np.isin(obj[:,:,1],[0,1]))
    return valid,support,target,own,enemy
def flags(s,p,support,target):
    c=p['expert_cell'];assert c.dtype.kind in 'iu' and np.all((c>=0)&(c<2304))
    distance=np.linalg.norm((np.c_[c%36/36,c//36/64]-s['y_xy'])*[18,32],axis=1)
    called=(p['gate']>.35)&p['allowed'].any(1);right=p['chosen_card']==s['y_card'];play=s['y_gate']==1
    return dict(aim1=play&(distance<=1),action=np.where(play,called&right&(distance<=1),~called),called=called,
        correct_card=play&right&p['allowed'].any(1),expert_in_support=support[np.arange(len(c)),patch(target)],
        predicted_in_support=support[np.arange(len(c)),patch(c)],distance=distance)
def main():
    assert not OUT.exists() and not (HERE/'started.json').exists();OUT.mkdir()
    original=read(HERE.parent/'development_iteration_1/prepared.json')
    assert sha(DATA)==original['source_binding']['dataset_sha256'] and sha(BASE/'indices.npz')==original['indices_sha256']
    assert sha(ROWS)==read(HERE.parent/'match_adaptation/prepared.json')['rows_sha256']
    binding=inputs();write(HERE/'started.json',dict(inputs=binding,predictions=0,optimizer_updates=0))
    ids,s,cv,groups,ps=load();valid,support,target,own,enemy=geometry(s);play=s['y_gate']==1
    masks=dict(groups);contexts={'none':valid.sum(1)==0,'one':valid.sum(1)==1,'multiple':valid.sum(1)>1,
        'own_only':own&~enemy,'enemy_only':enemy&~own,'mixed':own&enemy,
        'invalid_real':((s['projectiles'][:,:,0]>0)&~valid).any(1)}
    for card in np.unique(s['projectiles'][:,:,0][valid]).astype(int):contexts['identity/'+cv[card]]=(valid&(s['projectiles'][:,:,0]==card)).any(1)
    near=np.zeros(len(ids),bool)
    for slot,x in ((4,3.5/18),(5,14.5/18)):
        near|=(s['sc'][:,64+slot]>.5)&(np.linalg.norm((s['y_xy']-[x,6.5/32])*[18,32],axis=1)<=1)
    contexts['near_princess']=near;contexts['other_aim']=~near
    for key,m in contexts.items():
        masks['context/'+key]=m
        masks['rocket_context/'+key]=m&groups['rocket']
    for card in np.unique(s['y_card'][play]):masks['expert_card/'+cv[int(card)]]=play&(s['y_card']==card)
    masks['play']=play;masks['wait']=~play
    allflags={a:flags(s,p,support,target) for a,p in ps.items()};a,b=allflags[CONTROL],allflags[CAND]
    transitions={'aim_gained':~a['aim1']&b['aim1']&play,'aim_lost':a['aim1']&~b['aim1'],
        'both_right':a['aim1']&b['aim1'],'both_wrong':play&~a['aim1']&~b['aim1'],
        'action_gained':~a['action']&b['action'],'action_lost':a['action']&~b['action'],
        'cell_changed':ps[CONTROL]['expert_cell']!=ps[CAND]['expert_cell'],
        'patch_changed':patch(ps[CONTROL]['expert_cell'])!=patch(ps[CAND]['expert_cell']),
        'distance_better':play&(b['distance']<a['distance']),'distance_worse':play&(b['distance']>a['distance']),
        'gate_decision_changed':a['called']!=b['called'],'card_choice_changed':ps[CONTROL]['chosen_card']!=ps[CAND]['chosen_card'],
        'log_cell_changed':ps[CONTROL]['log_cell']!=ps[CAND]['log_cell']}
    for k in ('expert_in_support','predicted_in_support'):
        transitions['control_'+k]=a[k];transitions['candidate_'+k]=b[k]
    counts={};paired={}
    for name,m in masks.items():
        reps={}
        for rep in np.unique(s['rep'][m]):
            sel=m&(s['rep']==rep);r=dict(rows=int(sel.sum()))
            r.update({k:int((f&sel).sum()) for k,f in transitions.items()})
            for arm,f in allflags.items():
                for key in ('aim1','action','called','correct_card'):r[arm+'/'+key]=int((f[key]&sel).sum())
            reps[str(int(rep))]=r
        keys=next(iter(reps.values())).keys() if reps else ['rows',*transitions,*[a+'/'+k for a in ps for k in ('aim1','action','called','correct_card')]]
        counts[name]={k:sum(v[k] for v in reps.values()) for k in keys};counts[name]['replays']=len(reps)
        paired[name]=reps
    proof=read(HERE.parent/'development_iteration_7/results_verified_v2.json')
    for arm in ps:
        for group in groups:
            for key in ('aim1','action','called'):
                assert counts[group][arm+'/'+key]==proof['counts'][arm][group][key],(arm,group,key)
    details={**{k:s[k] for k in FIELDS},'ids':ids,'target':target,'valid':valid,'support':support,
        **{'transition/'+k:f for k,f in transitions.items()},**{arm+'/'+k:p[k] for arm,p in ps.items() for k in ('expert_cell','log_cell','chosen_card','gate')}}
    np.savez_compressed(OUT/'details.npz',**details);write(OUT/'by_replay.json',paired)
    records=[]
    for i in np.flatnonzero(groups['rocket']):
        records.append(dict(row=int(ids[i]),rep=int(s['rep'][i]),side=int(s['side'][i]),tick=int(s['tick'][i]),expert_xy=s['y_xy'][i].tolist(),
            expert_cell=int(target[i]),projectiles=s['projectiles'][i][s['projectiles'][i,:,0]>0].tolist(),
            valid_targets=int(valid[i].sum()),**{k:bool(f[i]) for k,f in transitions.items()},
            models={arm:dict(cell=int(ps[arm]['expert_cell'][i]),distance=float(f['distance'][i]),aim1=bool(f['aim1'][i]),action=bool(f['action'][i])) for arm,f in allflags.items()}))
    write(OUT/'rocket_rows.json',records)
    write(HERE/'report.json',dict(complete=True,rows=len(ids),counts=counts,details_sha256=sha(OUT/'details.npz'),replays_sha256=sha(OUT/'by_replay.json'),rocket_rows_sha256=sha(OUT/'rocket_rows.json'),predictions=0,optimizer_updates=0,accepted=False))
    assert inputs()==binding;print('FROZEN_BRANCH_ROCKET_AUDIT_COMPLETE')
if __name__=='__main__':main()
