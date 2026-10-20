"""CPU data only; strict public-tensor byte equality, no model loads."""
import os
from collections import Counter,defaultdict
import torch
from shared import *

def payload(row):
    pieces=[]
    for key in KEYS:
        x=np.ascontiguousarray(row[key])
        assert x.dtype.kind in 'bifu' and np.isfinite(x).all()
        pieces += [json.dumps([key,x.dtype.str,list(x.shape)],separators=(',',':')).encode()+b'\0',x.tobytes()]
    return b''.join(pieces)

def summarize(z,rocket):
    groups=defaultdict(list)
    for i,key in enumerate(z['hashes']):groups[str(key)].append(i)
    d=dict(rows=len(z['ids']),replays=len(np.unique(z['rep'])),unique_inputs=len(groups),
        duplicate_groups=0,duplicate_rows=0,duplicate_replays=0,max_group=max(map(len,groups.values())),
        gate_conflict_groups=0,gate_conflict_rows=0,minimum_gate_errors=0,
        card_conflict_groups=0,card_conflict_rows=0,minimum_card_errors=0,
        aim_condition_groups=0,aim_conflict_groups=0,aim_conflict_rows=0,minimum_cell_errors=0,
        minimum_aim1_errors=0,rocket_aim_condition_groups=0,rocket_aim_conflict_groups=0,
        rocket_minimum_cell_errors=0,rocket_minimum_aim1_errors=0)
    details=[]; reps=set();cells=np.arange(2304); xy=np.c_[cells%36/36,cells//36/64]
    for key,idx in groups.items():
        if len(idx)<2:continue
        d['duplicate_groups']+=1;d['duplicate_rows']+=len(idx);reps.update(z['rep'][idx].tolist())
        play=[i for i in idx if z['gate'][i]==1];nplay=len(play);nw=len(idx)-nplay
        if nplay and nw:d['gate_conflict_groups']+=1;d['gate_conflict_rows']+=len(idx)
        d['minimum_gate_errors']+=min(nplay,nw)
        cards=Counter(int(z['card'][i]) for i in play)
        if len(cards)>1:d['card_conflict_groups']+=1;d['card_conflict_rows']+=nplay
        d['minimum_card_errors']+=nplay-max(cards.values(),default=0)
        condition=defaultdict(list)
        for i in play:condition[(int(z['card'][i]),int(z['form'][i]))].append(i)
        for (card,form),members in condition.items():
            if len(members)<2:continue
            d['aim_condition_groups']+=1;classes=Counter(int(z['cell'][i]) for i in members)
            errors=len(members)-max(classes.values())
            coverage=np.zeros(2304,np.int64)
            for i in members:coverage += (np.linalg.norm((xy-z['xy'][i])*[18,32],axis=1)<=1)
            aim_errors=len(members)-int(coverage.max())
            if len(classes)>1:d['aim_conflict_groups']+=1;d['aim_conflict_rows']+=len(members)
            d['minimum_cell_errors']+=errors;d['minimum_aim1_errors']+=aim_errors
            if card==rocket:
                d['rocket_aim_condition_groups']+=1;d['rocket_aim_conflict_groups']+=int(len(classes)>1)
                d['rocket_minimum_cell_errors']+=errors;d['rocket_minimum_aim1_errors']+=aim_errors
        details.append(dict(hash=key,ids=[int(z['ids'][i]) for i in idx]))
    d['duplicate_replays']=len(reps)
    return dict(summary=d,duplicates=sorted(details,key=lambda x:x['hash']))

def controls():
    f=fixture();s=summarize(f,1)['summary']
    assert (s['duplicate_groups'],s['duplicate_rows'],s['minimum_gate_errors'],s['minimum_card_errors'],
            s['minimum_cell_errors'],s['minimum_aim1_errors'])==(2,6,1,1,2,1)
    sample={k:np.zeros((2,),np.float32) for k in KEYS};base=payload(sample)
    for k in KEYS:
        changed={a:b.copy() for a,b in sample.items()};changed[k][0]=1
        assert payload(changed)!=base
    assert payload(dict(sample,gate=np.array([1]),card=np.array([1]),xy=np.array([.5,.5])))==base
    return dict(label_fixture=1,input_mutations=16,label_exclusion=1)

def main():
    cutoff();assert not (HERE/'started.json').exists();assert read(HERE.parent/'extended_fit_audit/reviewed.json')['complete']
    OUT.mkdir(exist_ok=False);c.setup();write(HERE/'started.json',dict(pid=os.getpid(),sources=sources()))
    proof=controls();ids,sub,meta,rows=c.load_part('train','cpu');assert len(ids)==213995 and meta['grid']=='lattice'
    hashes=[];forms=[];labels=[]
    from pipeline.model_v3 import cell_label
    for lo in range(0,len(ids),128):
        cutoff();b=rows.batch(np.arange(lo,min(lo+128,len(ids))))
        data={k:b[k].numpy() for k in KEYS}
        for i in range(len(b['gate'])):hashes.append(hashlib.sha256(payload({k:x[i] for k,x in data.items()})).hexdigest())
        forms.extend(b['form'].numpy().tolist());labels.extend(cell_label(b['xy'],'lattice').numpy().tolist())
        if lo%12800==0:write(HERE/'progress.json',dict(done=lo,total=len(ids)))
    z=dict(ids=ids,rep=sub['rep'],hashes=np.asarray(hashes),gate=sub['y_gate'],card=sub['y_card'],
           form=np.asarray(forms),xy=sub['y_xy'],cell=np.asarray(labels))
    np.savez_compressed(OUT/'rows.npz',**z);result=summarize(z,meta['card_vocab'].index('rocket'))
    write(OUT/'groups.json',result);check()
    write(HERE/'collected.json',dict(complete=True,controls=proof,summary=result['summary'],
        rows_sha256=sha(OUT/'rows.npz'),groups_sha256=sha(OUT/'groups.json'),started_sha256=sha(HERE/'started.json'),
        rocket=meta['card_vocab'].index('rocket'),input_keys=KEYS,model_inference=0,optimizer_updates=0))
    print('INPUT_COLLISIONS_COLLECTED')
if __name__=='__main__':main()
