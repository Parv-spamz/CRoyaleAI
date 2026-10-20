"""Load saved roots only: no engine reset/step, policy or optimizer."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];BASE=HERE.parent/'impact_learnability_2'
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('qualified_v4',HERE.parent/'moving_impact_readiness_v4/collect.py')
v4=importlib.util.module_from_spec(spec);spec.loader.exec_module(v4)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def canonical(x):return json.loads(json.dumps(x,allow_nan=False,separators=(',',':')))
def check(before,after,frame,saved):
    assert before==after and canonical(frame)==saved
def diffs(a,b,path='root'):
    if isinstance(a,dict):
        assert set(a)==set(b)
        return sum((diffs(a[k],b[k],path+'.'+k) for k in a),[])
    if isinstance(a,(list,tuple)):
        assert isinstance(b,list) and len(a)==len(b)
        own=[dict(path=path,native_type=type(a).__name__,json_type=type(b).__name__)] if type(a)!=type(b) else []
        return own+sum((diffs(x,y,path+f'[{i}]') for i,(x,y) in enumerate(zip(a,b,strict=True))),[])
    assert a==b and type(a)==type(b),(path,type(a),type(b))
    return []
def main():
    assert not (HERE/'report.json').exists()
    p=read(BASE/'prepared.json');pv=read(BASE/'preparation_verified.json')
    assert pv['complete'] and pv['prepared_sha256']==sha(BASE/'prepared.json')
    for name,h in p['sources'].items():assert sha(ROOT/name)==h
    receipt=ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-impact-learning2-collect.json'
    r=read(receipt);assert r['exit_code']==1 and not r['matched']
    log=receipt.with_suffix('.out');assert hashlib.sha256(log.read_text(encoding='utf-8').encode()).hexdigest()==r['output_sha256']
    assert 'collect.py", line 26' in log.read_text()
    core=v4.RustEngine();rows=[];first=None
    for rec in p['roots']:
        rootpath=ROOT/rec['root_path'];assert sha(rootpath)==rec['root_sha256']
        before=rootpath.read_bytes();core.load_state(before);after=bytes(core.save_state());frame=v4.frame(core);saved=read(ROOT/rec['meta_path'])['root']
        check(before,after,frame,saved);changes=diffs(frame,saved)
        assert changes and all(q['native_type']=='tuple' and q['json_type']=='list' for q in changes)
        rows.append(dict(root_id=rec['spec']['root_id'],root_sha256=rec['root_sha256'],exact_bytes=True,original_frame_equal=frame==saved,exact_json_equal=True,type_differences=changes))
        if first is None:first=(before,after,frame,saved)
    assert len(rows)==192 and all(not r['original_frame_equal'] for r in rows)
    negatives=0
    for i in range(4):
        a,b,f,s=copy.deepcopy(first)
        if i==0:f['entities'][0]['x']+=1
        if i==1:s['entities'][0]['hp']-=1
        if i==2:s['entities'].pop()
        if i==3:b=b[:-1]+bytes([b[-1]^1])
        try:check(a,b,f,s)
        except AssertionError:negatives+=1
        else:raise AssertionError('unrejected restore corruption')
    assert not any((BASE/n).exists() for n in ('collected.json','training_started.json','trained.json'))
    result=dict(complete=True,roots=rows,controls=dict(positive=192,negative=negatives),native_resets=0,native_steps=0,optimizer_updates=0,original_gate_pass=False,original_receipt_sha256=sha(receipt),original_output_sha256=sha(log),prepared_sha256=sha(BASE/'prepared.json'),preparation_verified_sha256=sha(BASE/'preparation_verified.json'),source_sha256=sha(Path(__file__)))
    (HERE/'report.json').write_text(json.dumps(result,indent=2)+'\n');print('IMPACT_ROOT_RESTORE_DIAGNOSED')
if __name__=='__main__':main()
