"""Original development labels plus fixed caches only; no model imports."""
import hashlib,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
OUT=ROOT/'icebow/data/bench/tower_aim_localization_20261005'
BASE=ROOT/'icebow/data/bench/development_iteration_1_20261005'
FIFTH=ROOT/'icebow/data/bench/development_iteration_5_20261005'
ROWS=ROOT/'icebow/data/bench/match_adaptation_20261005/rows.npz'
MASKS=ROOT/'icebow/data/bench/development_iteration_4_20261005/development_masks.npz'
PHASES=('single_clock','double_regulation_clock','early_overtime_clock','late_overtime_clock')

def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def patch(cell):return ((cell//36)//4)*9+(cell%36)//4
def nearby(xy,alive):
    anchors=np.array([[3.5/18,6.5/32],[14.5/18,6.5/32]])
    distance=np.sqrt(np.sum(((xy.astype(np.float64)[:,None]-anchors)*[18,32])**2,axis=-1))
    return np.any((distance<=1)&alive[:,4:6],axis=1)

def main():
    assert not (HERE/'report.json').exists() and not OUT.exists()
    OUT.mkdir();proof=read(HERE.parent/'development_iteration_5/results_verified.json')
    assert proof['complete'] and read(HERE.parent/'development_iteration_5/chain_complete.json')['complete']
    prepared=read(HERE.parent/'match_adaptation/prepared.json')
    assert sha(ROWS)==prepared['rows_sha256']
    folders={'r1e_corrected':BASE/'r1e_corrected_eval','ordinary_v6':BASE/'ordinary_v6_eval_v2','tower_spatial_v7':FIFTH/'tower_spatial_v7_eval'}
    inputs=[ROWS,MASKS,BASE/'indices.npz',HERE.parent/'match_adaptation/prepared.json',HERE.parent/'development_iteration_5/results_verified.json']
    inputs += [d/'predictions.npz' for d in folders.values()]
    inputs += list(HERE.glob('*.py'))+[HERE/'PLAN.md']
    binding={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    write(HERE/'started.json',dict(inputs=binding,predictions=0,optimizer_updates=0))
    with np.load(BASE/'indices.npz') as z:ids=z['development']
    with np.load(ROWS) as z:
        take=np.searchsorted(z['ids'],ids);assert np.array_equal(z['ids'][take],ids)
        s={k:z[k][take] for k in ('rep','side','tick','split','y_gate','y_card','y_xy','sc')}
    assert len(ids)==54723 and np.all(s['split']==0)
    play=s['y_gate']==1;assert play.sum()==17192
    xy=s['y_xy'];cellxy=np.rint(xy*np.array([36,64],dtype=np.float32)).astype(np.int64)
    cellxy=np.maximum(0,np.minimum(cellxy,[35,63]));target=cellxy[:,1]*36+cellxy[:,0]
    target_patch=patch(target);near=nearby(xy,s['sc'][:,64:70]>.5)&play
    with np.load(MASKS) as z:
        assert np.array_equal(ids,z['ids']);masks={k[5:]:z[k]&play for k in z.files if k.startswith('mask_')}
    cv=prepared['card_vocab']
    for i,card in enumerate(cv):
        m=play&(s['y_card']==i)
        if m.any():masks['card/'+card]=m
    masks['near_enemy_princess']=near;masks['other_target']=play&~near
    for phase in PHASES:
        for name,m in [('near_enemy_princess',near),('other_target',play&~near)]:
            masks['rocket_target/'+phase+'/'+name]=masks['rocket_'+phase]&m
    models={};details=dict(ids=ids,rep=s['rep'],target=target,target_patch=target_patch,near_enemy_princess=near,play=play)
    for arm,folder in folders.items():
        assert sha(folder/'predictions.npz')==proof['hashes'][arm]['cache']
        with np.load(folder/'predictions.npz') as z:
            assert np.array_equal(ids,z['ids']);pred=z['expert_cell'];chosen=z['chosen_card'];gate=z['gate'];allowed=z['allowed']
        assert pred.dtype.kind in 'iu' and np.all((pred>=0)&(pred<2304))
        pos=np.column_stack(((pred%36)/36,(pred//36)/64))
        distance=np.linalg.norm((pos-xy.astype(np.float64))*[18,32],axis=1)
        same=patch(pred)==target_patch;ok=distance<=1;active=(gate>.35)&allowed.any(1);right=chosen==s['y_card']
        flags=dict(exact_cell=pred==target,same_patch=same,aim1=ok,
            same_patch_ok=same&ok,same_patch_miss=same&~ok,other_patch_ok=~same&ok,other_patch_miss=~same&~ok,
            full_action=active&right&ok,correct_card=right&allowed.any(1),fired=active)
        models[arm]={}
        for key,mask in masks.items():
            reps={}
            for rep in np.unique(s['rep'][mask]):
                m=mask&(s['rep']==rep);reps[str(int(rep))]=dict(rows=int(m.sum()),**{k:int((m&f).sum()) for k,f in flags.items()})
            models[arm][key]=dict(rows=int(mask.sum()),replays=len(reps),**{k:int((mask&f).sum()) for k,f in flags.items()},by_replay=reps)
        for k,f in flags.items():details[arm+'/'+k]=f
    for key in ('rocket','rocket_late_overtime_clock'):
        for arm in models:
            assert models[arm][key]['aim1']==proof['counts'][arm][key]['aim1']
            assert models[arm][key]['full_action']==proof['counts'][arm][key]['action']
    np.savez_compressed(OUT/'details.npz',**details)
    write(OUT/'counts.json',models)
    report=dict(complete=True,rows=len(ids),play=int(play.sum()),wait=int((~play).sum()),
        counts_sha256=sha(OUT/'counts.json'),details_sha256=sha(OUT/'details.npz'),
        counts={a:{k:{i:v for i,v in r.items() if i!='by_replay'} for k,r in groups.items()} for a,groups in models.items()},
        predictions=0,optimizer_updates=0,developmental_only=True,physical_impact_claim=False)
    assert {str(p.relative_to(ROOT)):sha(p) for p in inputs}==binding
    write(HERE/'report.json',report);print('TOWER_LOCALIZATION_AUDIT_COMPLETE')

if __name__=='__main__':main()
