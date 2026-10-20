"""Independent scalar decoding and raw-label aggregation; imports no producer/model."""
import hashlib,json,math,copy
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
OUT=ROOT/'icebow/data/bench/tower_aim_localization_20261005'
BASE=ROOT/'icebow/data/bench/development_iteration_1_20261005'

def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def scalar(x,y,cell):
    assert isinstance(cell,(int,np.integer)) and 0<=cell<2304
    cx=min(35,max(0,round(float(np.float32(x)*np.float32(36)))))
    cy=min(63,max(0,round(float(np.float32(y)*np.float32(64)))))
    px,py=int(cell)%36,int(cell)//36
    dx=(px/36-float(x))*18;dy=(py/64-float(y))*32
    ok=math.sqrt(dx*dx+dy*dy)<=1
    same=(px//4==cx//4 and py//4==cy//4)
    return dict(exact_cell=px==cx and py==cy,same_patch=same,aim1=ok,
        same_patch_ok=same and ok,same_patch_miss=same and not ok,
        other_patch_ok=not same and ok,other_patch_miss=not same and not ok)

def near(x,y,sc):
    for slot,tx in ((4,3.5/18),(5,14.5/18)):
        if sc[64+slot]>.5:
            dx=(float(x)-tx)*18;dy=(float(y)-6.5/32)*32
            if math.sqrt(dx*dx+dy*dy)<=1:return True
    return False

def validate_members(ids,expected,split):
    assert np.array_equal(ids,expected) and len(set(ids))==len(ids) and np.all(split==0)

def controls():
    # Three independent golden cases: exact, same-patch miss, adjacent-patch success.
    assert scalar(0.,0.,0)['exact_cell']
    assert scalar(0.,0.,3*36+3)['same_patch_miss']
    assert scalar(3/36,0.,4)['other_patch_ok']
    sc=np.zeros(70);sc[68]=1
    assert near(3.5/18,6.5/32,sc)
    dead=sc.copy();dead[68]=0;dead[65]=1
    assert not near(3.5/18,6.5/32,dead) and not near(3.5/18,25.5/32,sc)
    ids=np.array([3,6,9]);validate_members(ids,ids,np.zeros(3))
    rejected=0
    for wrong,split in ((ids[::-1],np.zeros(3)),(np.array([3,6,6]),np.zeros(3)),(np.array([3,6,10]),np.zeros(3)),(ids,np.array([0,1,0]))):
        try:validate_members(wrong,ids,split)
        except AssertionError:rejected+=1
        else:raise AssertionError('Membership corruption accepted')
    for cell in (-1,2304,1.5):
        try:scalar(0,0,cell)
        except AssertionError:rejected+=1
        else:raise AssertionError('Invalid cell accepted')
    assert not scalar(0.,0.,3*36+3)['aim1']
    assert not scalar(0.,0.,4)['same_patch']
    rejected+=2
    return dict(positive=4,negative=9,own_dead_tower_excluded=True,lattice_boundary_checked=True)

def main():
    assert not (HERE/'verified.json').exists()
    start=read(HERE/'started.json');report=read(HERE/'report.json')
    for p,h in start['inputs'].items():assert sha(ROOT/p)==h,p
    assert sha(OUT/'counts.json')==report['counts_sha256'] and sha(OUT/'details.npz')==report['details_sha256']
    ctl=controls();original=read(OUT/'counts.json')
    with np.load(BASE/'indices.npz') as z:ids=z['development']
    with np.load(ROOT/'icebow/data/bench/match_adaptation_20261005/rows.npz') as z:
        index={int(x):i for i,x in enumerate(z['ids'])};ix=np.array([index[int(x)] for x in ids]);s={k:z[k][ix] for k in ('rep','tick','split','y_gate','y_card','y_xy','sc')}
    validate_members(ids,ids,s['split']);play=s['y_gate']==1
    cv=read(HERE.parent/'match_adaptation/prepared.json')['card_vocab']
    with np.load(ROOT/'icebow/data/bench/development_iteration_4_20261005/development_masks.npz') as z:
        assert np.array_equal(ids,z['ids']);groups={k[5:]:z[k]&play for k in z.files if k.startswith('mask_')}
    close=np.array([bool(g) and near(x,y,sc) for g,(x,y),sc in zip(play,s['y_xy'],s['sc'])])
    for card in set(s['y_card'][play].tolist()):groups['card/'+cv[card]]=play&(s['y_card']==card)
    groups.update(near_enemy_princess=close,other_target=play&~close)
    phases=('single_clock','double_regulation_clock','early_overtime_clock','late_overtime_clock')
    for p in phases:
        for name,mask in [('near_enemy_princess',close),('other_target',play&~close)]:groups['rocket_target/'+p+'/'+name]=groups['rocket_'+p]&mask
    folders={'r1e_corrected':BASE/'r1e_corrected_eval','ordinary_v6':BASE/'ordinary_v6_eval_v2',
        'tower_spatial_v7':ROOT/'icebow/data/bench/development_iteration_5_20261005/tower_spatial_v7_eval'}
    all_counts={}
    for arm,folder in folders.items():
        with np.load(folder/'predictions.npz') as z:
            assert np.array_equal(z['ids'],ids);cells=z['expert_cell'];chosen=z['chosen_card'];gates=z['gate'];afford=z['allowed'].any(1)
        row_flags=[]
        for i,(x,y) in enumerate(s['y_xy']):
            v=scalar(x,y,cells[i]);active=gates[i]>.35 and afford[i];right=chosen[i]==s['y_card'][i]
            v.update(full_action=bool(active and right and v['aim1']),correct_card=bool(right and afford[i]),fired=bool(active))
            row_flags.append(v)
        flags={k:np.array([v[k] for v in row_flags]) for k in row_flags[0]}
        with np.load(OUT/'details.npz') as z:
            assert np.array_equal(z['ids'],ids) and np.array_equal(z['near_enemy_princess'],close)
            for key,value in flags.items():assert np.array_equal(value,z[arm+'/'+key]),(arm,key)
        assert set(groups)==set(original[arm]);all_counts[arm]={}
        for name,m in groups.items():
            parts={}
            for i in np.flatnonzero(m):
                rep=str(int(s['rep'][i]));r=parts.setdefault(rep,dict(rows=0,**{k:0 for k in flags}))
                r['rows']+=1
                for key,value in flags.items():r[key]+=int(value[i])
            totals={k:sum(v[k] for v in parts.values()) for k in ('rows',*flags)}
            totals.update(replays=len(parts),by_replay=parts)
            assert totals==original[arm][name],(arm,name)
            assert {k:v for k,v in totals.items() if k!='by_replay'}==report['counts'][arm][name]
            assert totals['rows']==sum(totals[k] for k in ('same_patch_ok','same_patch_miss','other_patch_ok','other_patch_miss'))
            all_counts[arm][name]=totals
    assert report['rows']==len(ids)==54723 and report['play']==sum(play)==17192 and report['wait']==sum(~play)
    # Verify original metric totals independently against the completed comparison.
    proof=read(HERE.parent/'development_iteration_5/results_verified.json')
    for arm in all_counts:
        for name in ('rocket','rocket_late_overtime_clock'):
            assert all_counts[arm][name]['aim1']==proof['counts'][arm][name]['aim1']
            assert all_counts[arm][name]['full_action']==proof['counts'][arm][name]['action']
    result=dict(complete=True,report_sha256=sha(HERE/'report.json'),started_sha256=sha(HERE/'started.json'),
        rows=len(ids),models=len(all_counts),groups=len(groups),controls=ctl,predictions=0,optimizer_updates=0)
    (HERE/'verified.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));print('TOWER_LOCALIZATION_INDEPENDENT_COMPLETE')

if __name__=='__main__':main()
