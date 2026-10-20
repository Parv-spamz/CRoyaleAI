"""Bound read-only IO. No model imports or diagnostic metric functions."""
import hashlib,json
from pathlib import Path
from zipfile import ZipFile
import numpy as np
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=HERE.parents[4]
OUT=ROOT/'icebow/data/bench/rl_failure_audit_20261005'
D1=ROOT/'icebow/data/bench/development_iteration_1_20261005'
DATA=ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz'
MASKS=ROOT/'icebow/data/bench/development_iteration_4_20261005/development_masks.npz'
ARM='outcome_rl_v5';CONTROL='ordinary_v5'
CACHE={'r1e_corrected':D1/'r1e_corrected_eval/predictions.npz',CONTROL:D1/'ordinary_v5_eval_v2/predictions.npz',ARM:ROOT/'icebow/data/bench/development_rl_1_20261005/predictions.npz'}
LABELS='y_gate y_card y_hand_pos y_xy y_wait_card y_wait_dt y_crowns y_cell'.split()
FIELDS=LABELS+['rep','side','tick','split','hand_card']
GROUPS='all rocket rocket_late_overtime_clock barrel_pro witch night_witch furnace defensive_sequence phase_late_overtime_clock'.split()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def take(z,key,ids):
    with z.open(key+'.npy') as f:
        version=np.lib.format.read_magic(f)
        shape,order,dtype=(np.lib.format.read_array_header_1_0(f) if version==(1,0) else np.lib.format.read_array_header_2_0(f))
        assert not order and not dtype.hasobject
        width=int(np.prod(shape[1:]))*dtype.itemsize;step=max(1,(16<<20)//width)
        result=np.empty((len(ids),)+shape[1:],dtype)
        for lo in range(0,shape[0],step):
            count=min(step,shape[0]-lo);raw=f.read(count*width);assert len(raw)==count*width
            a,b=np.searchsorted(ids,[lo,lo+count])
            if b>a:result[a:b]=np.frombuffer(raw,dtype).reshape((count,)+shape[1:])[ids[a:b]-lo]
        return result
def identities():
    paths=[DATA,MASKS,D1/'indices.npz',BASE/'development_iteration_1/prepared.json',BASE/'development_iteration_4/prelaunch.json',BASE/'match_adaptation/prepared.json',BASE/'development_rl_1/results_verified.json',BASE/'development_rl_1/reviewed_results.json']+list(CACHE.values())+list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE/'METRICS.md']
    b={str(p.relative_to(ROOT)):sha(p) for p in paths}
    p=read(BASE/'development_iteration_1/prepared.json');r=read(BASE/'development_rl_1/results_verified.json')
    assert b[str(DATA.relative_to(ROOT))]==p['source_binding']['dataset_sha256']
    assert b[str((D1/'indices.npz').relative_to(ROOT))]==p['indices_sha256']
    assert b[str(MASKS.relative_to(ROOT))]==read(BASE/'development_iteration_4/prelaunch.json')['masks_sha256']
    for a,c in CACHE.items():assert b[str(c.relative_to(ROOT))]==r['hashes'][a]['cache']
    assert r['complete'] and not r['continuation_passed'] and not r['original_probability_summary_exact']
    return b
def load():
    index=arrays(D1/'indices.npz');ids=index['development']
    assert len(ids)==54723 and np.all(np.diff(ids)>0) and not np.intersect1d(ids,index['train']).size
    with ZipFile(DATA) as z:s={k:take(z,k,ids) for k in FIELDS}
    assert np.all(s['split']==0) and len(np.unique(s['rep']))==405
    cv=read(BASE/'match_adaptation/prepared.json')['card_vocab'];m=arrays(MASKS)
    assert np.array_equal(m['ids'],ids)
    groups={g:m['mask_'+g] for g in GROUPS}
    play=s['y_gate']==1;groups.update(play=play,wait=~play)
    for card in np.unique(s['y_card'][play]):groups['expert_card/'+cv[int(card)]]=play&(s['y_card']==card)
    assert np.array_equal(groups['rocket'],play&(s['y_card']==cv.index('rocket')))
    ps={}
    for arm,path in CACHE.items():
        p=arrays(path);assert np.array_equal(p.pop('ids'),ids);ps[arm]=p
    return ids,s,cv,groups,ps
