"""CPU-only independent saved-vector reduction and binding checks."""
import math,copy
from common import *
def reduce_vectors(z,names,shapes):
    assert z['pg'].ndim==z['vf'].ndim==z['detached'].ndim==1
    assert len(z['pg'])==len(z['vf'])==len(z['detached'])==sum(math.prod(s) for s in shapes)
    assert len(names)==len(shapes)==len(z['reach']) and len(set(names))==len(names)
    assert all(np.isfinite(z[k]).all() for k in ('pg','vf','detached'))
    parts=[];start=0;ps=[];vs=[];dots=[]
    for j,(name,shape) in enumerate(zip(names,shapes)):
        end=start+math.prod(shape);a=z['pg'][start:end].astype(np.float64);b=z['vf'][start:end].astype(np.float64);d=z['detached'][start:end].astype(np.float64)
        pp=float(np.dot(a,a));vv=float(np.dot(b,b));pv=float(np.dot(a,b));dd=float(np.dot(d,d));shared=bool(z['reach'][j] and not name.startswith('value_head.'))
        if not name.startswith('value_head.'):assert not np.count_nonzero(d)
        else:assert not np.count_nonzero(a)
        if not z['reach'][j]:assert not np.count_nonzero(b)
        parts.append(dict(name=name,shape=shape,size=end-start,critic_reachable=bool(z['reach'][j]),shared=shared,pg_sq=pp,vf_sq=vv,dot=pv,detached_sq=dd))
        if shared:ps.append(pp);vs.append(vv);dots.append(pv)
        start=end
    gp=math.sqrt(math.fsum(ps));gv=math.sqrt(math.fsum(vs));dot=math.fsum(dots)
    return dict(tensors=parts,pg_norm=gp,vf_norm=gv,dot=dot,cosine=dot/(gp*gv) if gp and gv else None,vf_share=gv/(gp+gv) if gp+gv else None,critic_larger=gv>gp,opposed=dot<0)
def compare(a,b):
    if isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:compare(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):compare(x,y)
    elif isinstance(a,float):assert isinstance(b,(int,float)) and math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
    else:assert a==b
def controls():
    z=dict(pg=np.array([3.,4.,0.]),vf=np.array([6.,8.,2.]),detached=np.array([0.,0.,2.]),reach=np.array([True,True]))
    names=['encoder.weight','value_head.weight'];shapes=[[2],[1]];r=reduce_vectors(z,names,shapes)
    assert r['pg_norm']==5 and r['vf_norm']==10 and r['dot']==50 and r['cosine']==1
    q=copy.deepcopy(z);q['vf'][:2]*=-1;assert reduce_vectors(q,names,shapes)['cosine']==-1
    q=copy.deepcopy(z);q['vf'][:2]=0;assert reduce_vectors(q,names,shapes)['cosine'] is None
    corrupt=[]
    for key,index,value in [('detached',0,1),('pg',2,1),('vf',0,float('nan')),('reach',0,False)]:
        q=copy.deepcopy(z);q[key][index]=value;corrupt.append(q)
    q=copy.deepcopy(z);q['pg']=q['pg'][:-1];corrupt.append(q)
    rejected=0
    for q in corrupt:
        try:reduce_vectors(q,names,shapes)
        except (AssertionError,ValueError):rejected+=1
        else:raise AssertionError('Corrupt gradient accepted')
    for key in ('dot','pg_norm','vf_share'):
        q=copy.deepcopy(r);q[key]+=.1
        try:compare(r,q)
        except AssertionError:rejected+=1
        else:raise AssertionError('Corrupt summary accepted')
    return dict(positive=3,negative=rejected)
def main():
    assert not (HERE/'verified.json').exists();report=read(HERE/'report.json');assert report['complete'] and report['source_binding']==sources()
    assert report['optimizer_updates']==report['development_predictions']==0 and not report['new_checkpoint']
    receipt=read(ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-rl-gradient-collection.json');assert receipt['exit_code']==0 and receipt['matched']
    assert [r['update'] for r in report['updates']]==list(range(6,33));fixture=controls();summaries=[]
    for r in report['updates']:
        for p,h in r['inputs'].items():assert sha(ROOT/p)==h
        assert r==read(OUT/f"u{r['update']:03d}.json") and r['weights_unchanged'] and r['optimizer_updates']==0 and r['pre_checkpoint_update']==r['update']-1
        f=ROOT/r['gradient_file'];assert sha(f)==r['gradient_sha256'];z=arrays(f)
        expected=np.arange(0,r['cohort_rows'],max(1,r['cohort_rows']//256))[:256]
        assert np.array_equal(z['indices'],expected) and len(expected)==r['sample_rows']
        independent=reduce_vectors(z,r['names'],r['shapes']);compare(independent,r['metrics'])
        assert math.isfinite(r['loss_policy']) and math.isfinite(r['loss_critic']) and math.isfinite(r['loss_detached']) and r['ratio_maxdev']<1e-4
        summaries.append(dict(update=r['update'],rows=r['sample_rows'],**{k:v for k,v in independent.items() if k!='tensors'}))
    assert sources()==report['source_binding']
    write(HERE/'verified.json',dict(complete=True,updates=27,rows=sum(x['rows'] for x in summaries),controls=fixture,report_sha256=sha(HERE/'report.json'),source_sha256=sha(Path(__file__)),summaries=summaries,optimizer_updates=0,new_checkpoint=False,accepted=False))
    print('RL_GRADIENT_VERIFIED')
if __name__=='__main__':main()
