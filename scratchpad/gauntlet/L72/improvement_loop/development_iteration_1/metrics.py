"""Frozen development masks and replay-cluster counts; no policy fitting."""
from zipfile import ZipFile
import numpy as np
from common import SOURCE, ROOT
from pipeline import vocab
from pipeline.train_rocket_curriculum import take
from pipeline.opp_elixir_count import card_cost

FAMILIES=('witch','night_witch','furnace')


def allowed(sub,cv):
    costs=np.array([card_cost(k.replace('-','_')) or 0 for k in cv])
    hand=sub['hand_card']
    return (hand>0)&(costs[hand]<=np.floor(sub['sc'][:,3]*10+1e-3)[:,None])


def make_masks(ids,sub,cv):
    with np.load(SOURCE) as z,ZipFile(SOURCE) as archive:
        off=z['off'];gather=np.concatenate([np.arange(off[i],off[i+1]) for i in ids])
        original=take(archive,'tok',gather)
    def present(tok,key):
        yes=(tok[:,0]==vocab.unit_id(key))&(tok[:,2]>.5)
        pref=np.r_[0,np.cumsum(yes)]
        return (pref[sub['off'][1:]]-pref[sub['off'][:-1]])>0
    m={key:present(original,key) for key in FAMILIES}
    for key in FAMILIES:
        parent=present(sub['tok'],key)
        m[key+'_parent']=m[key]&parent
        m[key+'_child_only']=m[key]&~parent
    play=sub['y_gate']==1
    shots=sub['projectiles'];enemy=(shots[:,:,0]==cv.index('goblin-barrel'))&(shots[:,:,1]==1)
    target=shots[np.arange(len(ids)),enemy.argmax(1),4:6]
    known=(enemy.sum(1)==1)&np.isfinite(target).all(1)&(target[:,0]>=0)&(target[:,0]<=1)&(target[:,1]>=.5)&(target[:,1]<=1)&((target[:,0]<.4)|(target[:,0]>.6))
    log=cv.index('the-log');playable=known&((sub['hand_card']==log)&allowed(sub,cv)).any(1)
    pro=playable&play&(sub['y_card']==log)&((sub['y_xy'][:,0]<.5)==(target[:,0]<.5))
    m.update(barrel_pro=pro,barrel_other_play=playable&play&~pro,
             barrel_wait=playable&~play,barrel_multiple=enemy.sum(1)>1,
             barrel_ambiguous=enemy.any(1)&~known,barrel_absent=~enemy.any(1),
             rocket=play&(sub['y_card']==cv.index('rocket')),all=np.ones(len(ids),bool))
    with np.load(ROOT/'icebow/data/bench/context_teaching_20261005/cohorts.npz') as z:
        for key in ('finish','combo','xbow','xbow_no_lifetime_target'):m[key]=z[key][ids]
    return m,target


def row_values(sub,p,cv,target):
    play=sub['y_gate']==1;has=p['allowed'].any(1)
    called=(p['gate']>.35)&has
    card=(p['chosen_card']==sub['y_card'])&has
    xy=np.c_[p['expert_cell']%36/36,p['expert_cell']//36/64]
    distance=np.linalg.norm((xy-sub['y_xy'])*[18,32],axis=1)
    same=(p['log_cell']%36/36<.5)==(target[:,0]<.5)
    fired=called&(p['chosen_card']==cv.index('the-log'))
    return dict(play=play,card=play&card,action=np.where(play,called&card&(distance<=1),~called),
        called=called,aim1=play&(distance<=1),aim2=play&(distance<=2),
        rocket_called=called&(p['chosen_card']==cv.index('rocket')),
        log_correct=fired&same,log_wrong=fired&~same,log_not_fired=~fired,forced_log_same=same)


def summarize(sub,p,cv,masks,target):
    values=row_values(sub,p,cv,target);result={}
    for key,m in masks.items():
        groups={}
        for rep in np.unique(sub['rep'][m]):
            selected=m&(sub['rep']==rep)
            groups[str(int(rep))]=dict(rows=int(selected.sum()),**{k:int((v&selected).sum()) for k,v in values.items()})
        result[key]=dict(rows=int(m.sum()),replays=len(groups),**{k:int((v&m).sum()) for k,v in values.items()},by_replay=groups)
    return result
