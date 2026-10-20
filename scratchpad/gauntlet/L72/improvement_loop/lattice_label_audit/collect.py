from shared import *
import os
def main():
    cutoff();assert not (HERE/'started.json').exists();OUT.mkdir(exist_ok=False)
    binding=sources();write(HERE/'started.json',dict(pid=os.getpid(),sources=binding))
    with np.load(DATA,allow_pickle=False) as z:meta=json.loads(str(z['meta']))
    assert meta['grid']=='lattice';records=[];scores={}
    oldaim=read(ROOT/'icebow/data/bench/small_set_aim_audit_20261006/counts.json')
    oldcontrib=read(CONTRIB/'report.json')
    patch=lambda cell:(cell//36//4)*9+cell%36//4
    for name,p in caches().items():
        z=arrays(p);ids=np.flatnonzero(z['y_gate']==1);xy=z['y_xy'][ids]
        scaled=xy*np.array([36,64],np.float32)
        floor=np.clip(scaled.astype(np.int64),[0,0],[35,63]);lattice=np.clip(np.rint(scaled).astype(np.int64),[0,0],[35,63])
        floor=floor[:,1]*36+floor[:,0];lattice=lattice[:,1]*36+lattice[:,0]
        pred=z['expert_cell'][ids];d=np.linalg.norm((np.c_[pred%36/36,pred//36/64]-xy)*[18,32],axis=1)
        aim=d<=1
        if name in oldaim:assert int(aim.sum())==oldaim[name]['play']['aim']
        else:assert int(aim.sum())==oldcontrib['mirrored' if name.endswith('_mirrored') else 'native']['all']['counts']['on_aim']
        for j,i in enumerate(ids):
            r=dict(cache=name,id=int(z['ids'][i]),rep=int(z['rep'][i]),tick=int(z['tick'][i]),card=int(z['y_card'][i]),card_name=meta['card_vocab'][int(z['y_card'][i])],xy=xy[j].tolist(),pred=int(pred[j]),floor=int(floor[j]),lattice=int(lattice[j]),distance=float(d[j]))
            r.update(rows=1,aim=bool(aim[j]),floor_exact=bool(pred[j]==floor[j]),lattice_exact=bool(pred[j]==lattice[j]),label_changed=bool(floor[j]!=lattice[j]),floor_same_miss=bool(not aim[j] and patch(pred[j])==patch(floor[j])),floor_other_miss=bool(not aim[j] and patch(pred[j])!=patch(floor[j])),lattice_same_miss=bool(not aim[j] and patch(pred[j])==patch(lattice[j])),lattice_other_miss=bool(not aim[j] and patch(pred[j])!=patch(lattice[j])),miss_within_1e5_above_one=bool(1<d[j]<=1.00001))
            records.append(r)
        if name.startswith('local_cell_final'):
            orientation='mirrored' if name.endswith('_mirrored') else 'native';s=arrays(CONTRIB/(orientation+'.npz'));assert np.array_equal(s['ids'],z['ids'][ids]) and np.array_equal(s['xy'],xy)
            ix=np.arange(512);a={}
            for mode,key in [('on','full'),('off','base')]:
                logits=s[key].astype(np.float64);mx=logits.max(1)
                ce=mx+np.log(np.exp(logits-mx[:,None]).sum(1))-logits[ix,lattice]
                other=logits.copy();other[ix,lattice]=-np.inf
                a[mode+'_ce']=ce;a[mode+'_margin']=logits[ix,lattice]-other.max(1)
            off=s['base'].argmax(1);res=s['residual'].astype(np.float64)
            a['residual_target_vs_off_winner']=res[ix,lattice]-res[ix,off]
            a['off_winner_target_gap']=s['base'][ix,off].astype(np.float64)-s['base'][ix,lattice]
            mask=patch(np.arange(2304))[None,:]==patch(lattice)[:,None]
            a['residual_expert_patch_span']=np.where(mask,res,-np.inf).max(1)-np.where(mask,res,np.inf).min(1)
            scorepath=OUT/(orientation+'_scores.npz');np.savez_compressed(scorepath,ids=s['ids'],target=lattice,**a)
            scores[orientation]={}
            for group,m in [('all',np.ones(512,bool)),('rocket',s['card']==meta['card_vocab'].index('rocket')),('late_rocket',(s['card']==meta['card_vocab'].index('rocket'))&(s['tick']>=4800))]+[('card/'+meta['card_vocab'][int(card)],s['card']==card) for card in np.unique(s['card'])]:
                scores[orientation][group]=dict(rows=int(m.sum()),replays=len(np.unique(s['rep'][m])),values={k:dict(mean=float(v[m].mean()),median=float(np.median(v[m]))) for k,v in a.items()})
    assert len(records)==4096 and sources()==binding
    (OUT/'rows.jsonl').write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in records),encoding='utf-8')
    report=dict(counts=aggregate(records),scores=scores)
    write(OUT/'report.json',report)
    write(HERE/'collected.json',dict(complete=True,sources=binding,records=len(records),grid='lattice',artifacts={p.name:sha(p) for p in OUT.iterdir()},inference=0,backward=0,optimizer_updates=0,accepted=False,deployed=False))
    print('LATTICE_LABEL_AUDIT_COLLECTED')
if __name__=='__main__':main()
