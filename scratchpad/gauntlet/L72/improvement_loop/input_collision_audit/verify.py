"""Independent scalar padding, raw-label joining and group/geometry counts."""
import copy
import math
from collections import Counter,defaultdict
from shared import *

def scalar_row(sub,i):
    lo=int(sub['off'][i]);count=min(int(sub['off'][i+1])-lo,64)
    tok=np.zeros((64,sub['tok'].shape[1]),dtype=sub['tok'].dtype)
    form=np.zeros(64,dtype=np.int64);mask=np.zeros(64,dtype=bool)
    for j in range(count):tok[j]=sub['tok'][lo+j];form[j]=sub['unit_form'][lo+j];mask[j]=True
    row=dict(tok=tok,mask=mask,unit_form=form)
    for key in KEYS:
        if key in row:continue
        row[key]=np.asarray(sub[key][i])
        if key in ('hand_card','hand_form','deck_card','deck_form','next_card','next_form'):
            row[key]=row[key].astype(np.int16).astype(np.int64)
    return row

def independent_bytes(row):
    out=bytearray()
    for key in KEYS:
        x=np.ascontiguousarray(row[key]);assert np.isfinite(x).all()
        out.extend(json.dumps([key,x.dtype.str,list(x.shape)],separators=(',',':')).encode('utf-8'))
        out.append(0);out.extend(x.tobytes(order='C'))
    return bytes(out)

def recount(z,rocket):
    order=sorted(range(len(z['ids'])),key=lambda i:str(z['hashes'][i])); groups=[]
    for i in order:
        if not groups or z['hashes'][groups[-1][0]]!=z['hashes'][i]:groups.append([])
        groups[-1].append(i)
    s=dict(rows=len(order),replays=len(set(map(int,z['rep']))),unique_inputs=len(groups),
        duplicate_groups=0,duplicate_rows=0,duplicate_replays=0,max_group=max(map(len,groups)),
        gate_conflict_groups=0,gate_conflict_rows=0,minimum_gate_errors=0,
        card_conflict_groups=0,card_conflict_rows=0,minimum_card_errors=0,
        aim_condition_groups=0,aim_conflict_groups=0,aim_conflict_rows=0,minimum_cell_errors=0,
        minimum_aim1_errors=0,rocket_aim_condition_groups=0,rocket_aim_conflict_groups=0,
        rocket_minimum_cell_errors=0,rocket_minimum_aim1_errors=0)
    details=[]; reps=set()
    for indexes in groups:
        if len(indexes)==1:continue
        s['duplicate_groups']+=1;s['duplicate_rows']+=len(indexes)
        reps.update(int(z['rep'][i]) for i in indexes)
        p=[i for i in indexes if int(z['gate'][i])==1];w=len(indexes)-len(p)
        if p and w:s['gate_conflict_groups']+=1;s['gate_conflict_rows']+=len(indexes)
        s['minimum_gate_errors']+=min(len(p),w)
        cards=[int(z['card'][i]) for i in p]
        if len(set(cards))>1:s['card_conflict_groups']+=1;s['card_conflict_rows']+=len(p)
        s['minimum_card_errors']+=len(p)-max((cards.count(v) for v in set(cards)),default=0)
        for card,form in sorted(set((int(z['card'][i]),int(z['form'][i])) for i in p)):
            members=[i for i in p if int(z['card'][i])==card and int(z['form'][i])==form]
            if len(members)<2:continue
            s['aim_condition_groups']+=1
            classes=[int(z['cell'][i]) for i in members];ne=len(members)-max(classes.count(v) for v in set(classes))
            best=0
            for cell in range(2304):
                n=0
                for i in members:
                    x,y=map(float,z['xy'][i]);dx=(cell%36/36-x)*18;dy=(cell//36/64-y)*32
                    n+=int(math.sqrt(dx*dx+dy*dy)<=1)
                best=max(best,n)
            nae=len(members)-best
            if len(set(classes))>1:s['aim_conflict_groups']+=1;s['aim_conflict_rows']+=len(members)
            s['minimum_cell_errors']+=ne;s['minimum_aim1_errors']+=nae
            if card==rocket:
                s['rocket_aim_condition_groups']+=1;s['rocket_aim_conflict_groups']+=int(len(set(classes))>1)
                s['rocket_minimum_cell_errors']+=ne;s['rocket_minimum_aim1_errors']+=nae
        details.append(dict(hash=str(z['hashes'][indexes[0]]),ids=[int(z['ids'][i]) for i in indexes]))
    s['duplicate_replays']=len(reps);return dict(summary=s,duplicates=details)

def validate(z,expected,groups,rocket):
    assert set(z)==set(expected)
    for key in expected:assert np.array_equal(z[key],expected[key]),key
    assert recount(z,rocket)==groups

def main():
    cutoff();check();assert not (HERE/'verified.json').exists();c.setup()
    r=read(HERE/'collected.json');assert r['complete'] and r['rows_sha256']==sha(OUT/'rows.npz') and r['groups_sha256']==sha(OUT/'groups.json')
    ids=c.indices('train');sub,meta=c.load_subset(c.DATA,ids);assert len(ids)==213995
    # Source-label join reads original archive directly, without constructing model batches.
    from zipfile import ZipFile
    from pipeline.train_rocket_curriculum import take
    with ZipFile(c.SOURCE) as original:
        for k in ('rep','y_gate','y_card','y_xy','hand_card','deck_card','deck_form','split'):
            assert np.array_equal(sub[k],take(original,k,ids)),k
    hashes=[];forms=[]
    for i in range(len(ids)):
        if i%12800==0:cutoff();write(HERE/'verification_progress.json',dict(done=i,total=len(ids)))
        hashes.append(hashlib.sha256(independent_bytes(scalar_row(sub,i))).hexdigest())
        card=int(sub['y_card'][i]);hits=np.flatnonzero(sub['deck_card'][i]==card)
        forms.append(int(sub['deck_form'][i,hits[0]]) if len(hits) else 3)
    xy=sub['y_xy'];cx=np.rint(xy[:,0]*np.float32(36)).astype(np.int64).clip(0,35)
    cy=np.rint(xy[:,1]*np.float32(64)).astype(np.int64).clip(0,63)
    expected=dict(ids=ids,rep=sub['rep'],hashes=np.array(hashes),gate=sub['y_gate'],card=sub['y_card'],
        form=np.array(forms),xy=xy,cell=cy*36+cx)
    z=arrays(OUT/'rows.npz');groups=read(OUT/'groups.json');validate(z,expected,groups,r['rocket'])
    positions={int(v):i for i,v in enumerate(ids)}
    for group in groups['duplicates']:
        first=independent_bytes(scalar_row(sub,positions[group['ids'][0]]))
        assert all(independent_bytes(scalar_row(sub,positions[x]))==first for x in group['ids'])
    f=fixture();fg=recount(f,1);s=fg['summary']
    assert (s['duplicate_groups'],s['duplicate_rows'],s['minimum_gate_errors'],s['minimum_card_errors'],s['minimum_cell_errors'],s['minimum_aim1_errors'])==(2,6,1,1,2,1)
    validate(f,f,fg,1);bad=0
    for key,value in [('ids',99),('hashes','c'*64),('gate',0),('card',99),('form',2),('xy',.25)]:
        x=copy.deepcopy(f);x[key][0]=value
        try:validate(x,f,fg,1)
        except AssertionError:bad+=1
        else:raise AssertionError('corruption accepted')
    wrong=copy.deepcopy(fg);wrong['summary']['duplicate_rows']+=1
    try:validate(f,f,wrong,1)
    except AssertionError:bad+=1
    else:raise AssertionError('wrong summary accepted')
    assert bad==7;check()
    write(HERE/'verified.json',dict(complete=True,controls=dict(positive=2,negative=7),summary=groups['summary'],
        collected_sha256=sha(HERE/'collected.json'),rows_sha256=sha(OUT/'rows.npz'),groups_sha256=sha(OUT/'groups.json'),
        model_inference=0,optimizer_updates=0,accepted=False,deployed=False))
    print('INPUT_COLLISIONS_VERIFIED')
if __name__=='__main__':main()
