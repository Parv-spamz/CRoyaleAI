"""New cached-head decomposition; zero predictions/optimizer updates."""
from data_io import *
def row_values(s,p):
    has=p['allowed'].any(1);play=s['y_gate']==1;fire=(p['gate']>.35)&has
    card=(p['chosen_card']==s['y_card'])&has
    cell=p['expert_cell'];distance=np.linalg.norm((np.c_[cell%36/36,cell//36/64]-s['y_xy'])*[18,32],axis=1)
    aim=distance<=1;state=np.where(play,fire*4+card*2+aim,np.where(fire,9,8)).astype(int)
    action=np.where(play,fire&card&aim,~fire)
    return dict(state=state,distance=distance,fire=fire,card=card,aim=aim,action=action)
def tally(mask,play,values,ps):
    out=dict(rows=int(mask.sum()),play=int((mask&play).sum()),wait=int((mask&~play).sum()),models={},pairs={})
    for arm,v in values.items():
        out['models'][arm]={k:int((mask&f).sum()) for k,f in dict(action=v['action'],called=v['fire'],card=play&v['card'],aim1=play&v['aim'],play_action=play&v['action'],wait_action=~play&v['action']).items()}
    b=values[ARM]
    for arm in (CONTROL,'r1e_corrected'):
        a=values[arm];gain=~a['action']&b['action'];loss=a['action']&~b['action']
        flags=dict(action_gained=gain,action_lost=loss,play_gained=gain&play,play_lost=loss&play,wait_gained=gain&~play,wait_lost=loss&~play,
            fire_changed=a['fire']!=b['fire'],card_changed=ps[arm]['chosen_card']!=ps[ARM]['chosen_card'],cell_changed=ps[arm]['expert_cell']!=ps[ARM]['expert_cell'],aim_gained=play&~a['aim']&b['aim'],aim_lost=play&a['aim']&~b['aim'])
        r={k:int((mask&f).sum()) for k,f in flags.items()}
        r['states']=np.bincount(a['state'][mask]*10+b['state'][mask],minlength=100).reshape(10,10).tolist()
        r['hybrid_actions']=[]
        for bits in range(8):
            f=b['fire'] if bits&4 else a['fire'];c=b['card'] if bits&2 else a['card'];aim=b['aim'] if bits&1 else a['aim']
            r['hybrid_actions'].append(int((mask&np.where(play,f&c&aim,~f)).sum()))
        assert r['action_gained']-r['action_lost']==r['play_gained']-r['play_lost']+r['wait_gained']-r['wait_lost']
        out['pairs'][arm]=r
    return out
def main():
    assert not OUT.exists() and not (HERE/'started.json').exists();binding=identities();OUT.mkdir()
    write(HERE/'started.json',dict(inputs=binding,predictions=0,optimizer_updates=0))
    ids,s,cv,groups,ps=load();play=s['y_gate']==1;values={a:row_values(s,p) for a,p in ps.items()}
    counts={g:tally(m,play,values,ps) for g,m in groups.items()};paired={}
    for g,m in groups.items():paired[g]={str(int(rep)):tally(m&(s['rep']==rep),play,values,ps) for rep in np.unique(s['rep'][m])}
    reference=read(BASE/'development_rl_1/results_verified.json')
    for g in GROUPS:
        for a in ps:
            assert counts[g]['rows']==reference['counts'][a][g]['rows']
            for key in ('action','called','card','aim1'):assert counts[g]['models'][a][key]==reference['counts'][a][g][key],(g,a,key)
    records=[]
    for i in np.flatnonzero(groups['rocket']):
        a,b=values[CONTROL],values[ARM]
        records.append(dict(row=int(ids[i]),rep=int(s['rep'][i]),side=int(s['side'][i]),tick=int(s['tick'][i]),expert_card=int(s['y_card'][i]),expert_xy=s['y_xy'][i].tolist(),hand=s['hand_card'][i].tolist(),allowed=ps[CONTROL]['allowed'][i].tolist(),
            changes=dict(fire=bool(a['fire'][i]!=b['fire'][i]),card=bool(ps[CONTROL]['chosen_card'][i]!=ps[ARM]['chosen_card'][i]),aim=bool(a['aim'][i]!=b['aim'][i]),action=int(b['action'][i])-int(a['action'][i])),
            models={arm:dict(gate=float(p['gate'][i]),card=int(p['chosen_card'][i]),cell=int(p['expert_cell'][i]),distance=float(values[arm]['distance'][i]),state=int(values[arm]['state'][i])) for arm,p in ps.items()}))
    write(OUT/'by_replay.json',paired);write(OUT/'rocket_rows.json',records)
    label_hashes={k:hashlib.sha256(s[k].tobytes()).hexdigest() for k in LABELS}
    write(HERE/'report.json',dict(complete=True,rows=len(ids),replays=len(np.unique(s['rep'])),counts=counts,label_hashes=label_hashes,by_replay_sha256=sha(OUT/'by_replay.json'),rocket_rows_sha256=sha(OUT/'rocket_rows.json'),predictions=0,optimizer_updates=0,accepted=False))
    assert identities()==binding;print('RL_FAILURE_AUDIT_COMPLETE')
if __name__=='__main__':main()
