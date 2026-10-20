"""Independent CPU reductions and original schedule/label checks; no model load."""
import copy
import math
from zipfile import ZipFile
from shared import *

def reduce_vectors(z,shapes):
    g=z['g'];reach=z['reach'];sizes=[math.prod(s) for s in shapes]
    assert g.dtype==np.float32 and g.shape==(6,sum(sizes)) and np.isfinite(g).all()
    assert reach.dtype==bool and reach.shape==(5,len(sizes))
    buckets={'all':[],'shared':[]};errors=[];total=[];maxerr=0.;maxval=0.;off=0
    for j,size in enumerate(sizes):
        a=g[:,off:off+size].astype(np.float64);off+=size
        for k in range(5):
            if not reach[k,j]:assert np.count_nonzero(a[k])==0
        error=(a[0]+a[1]+a[2]+a[3]+a[4])-a[5]
        errors.append(float(np.dot(error,error)));total.append(float(np.dot(a[5],a[5])))
        maxerr=max(maxerr,float(np.abs(error).max()));maxval=max(maxval,float(np.abs(a[5]).max()))
        dots=[[float(np.dot(a[k],a[l])) for l in range(5)] for k in range(5)]
        r=a[1]+a[2]+a[3]+a[4]
        item=(size,dots,float(np.dot(r,r)),float(np.dot(a[0],r)),float(np.dot(a[0],a[5])))
        buckets['all'].append(item)
        if reach[0,j] and any(reach[1:,j]):buckets['shared'].append(item)
    en=math.sqrt(math.fsum(errors));tn=math.sqrt(math.fsum(total))
    assert maxerr<=1e-5+1e-4*maxval and en<=(1e-4*tn if tn else 1e-6)
    result=dict(linearity_max=maxerr,linearity_l2=en,total_norm=tn)
    for name,items in buckets.items():
        dots=[[math.fsum(x[1][k][l] for x in items) for l in range(5)] for k in range(5)]
        norms=[math.sqrt(dots[k][k]) for k in range(5)];rn=math.sqrt(math.fsum(x[2] for x in items))
        cr=math.fsum(x[3] for x in items);ct=math.fsum(x[4] for x in items)
        result[name]=dict(parameters=sum(x[0] for x in items),norms=norms,dots=dots,
            cosines=[[dots[k][l]/(norms[k]*norms[l]) if norms[k] and norms[l] else None for l in range(5)] for k in range(5)],
            rest_norm=rn,cell_rest_dot=cr,cell_rest_cosine=cr/(norms[0]*rn) if norms[0] and rn else None,
            cell_total_dot=ct,opposed=cr<0,total_opposes_cell=ct<0)
    return result

def compare(a,b):
    if isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:compare(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):compare(x,y)
    elif isinstance(a,float):assert isinstance(b,(int,float)) and math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
    else:assert a==b

def identity(r,model,step):
    assert r['model']==model and r['step']==step and r['rows']==128 and r['weights_unchanged']
    assert set(r['losses'])==set(HEADS) and all(math.isfinite(x) for x in r['losses'].values()) and math.isfinite(r['total_loss'])

def controls():
    g=np.zeros((6,2),np.float32);g[0]=[3,4];g[1]=[6,8];g[5]=g[:5].sum(0)
    z=dict(g=g,reach=np.array([[True],[True],[False],[False],[False]]));shapes=[[2]]
    m=reduce_vectors(z,shapes);assert m['all']['norms'][:2]==[5.,10.] and m['all']['cell_rest_dot']==50
    q=copy.deepcopy(z);q['g'][1]*=-1;q['g'][5]=q['g'][:5].sum(0);assert reduce_vectors(q,shapes)['all']['total_opposes_cell']
    q=copy.deepcopy(z);q['g'][:]=0;assert reduce_vectors(q,shapes)['all']['cell_rest_cosine'] is None
    bads=[]
    q=copy.deepcopy(z);q['g'][0,0]=float('nan');bads.append(lambda q=q:reduce_vectors(q,shapes))
    q=copy.deepcopy(z);q['g']=q['g'][:-1];bads.append(lambda q=q:reduce_vectors(q,shapes))
    q=copy.deepcopy(z);q['reach'][0,0]=False;bads.append(lambda q=q:reduce_vectors(q,shapes))
    q=copy.deepcopy(z);q['g'][5,0]+=1;bads.append(lambda q=q:reduce_vectors(q,shapes))
    q=copy.deepcopy(m);q['all']['norms'][0]+=1;bads.append(lambda q=q:compare(m,q))
    r=dict(model='ordinary_v5',step=0,rows=128,weights_unchanged=True,losses={k:1. for k in HEADS},total_loss=5.)
    identity(r,'ordinary_v5',0)
    q=copy.deepcopy(r);q['step']=500;bads.append(lambda q=q:identity(q,'ordinary_v5',0))
    q=copy.deepcopy(r);q['losses']['cell']=float('nan');bads.append(lambda q=q:identity(q,'ordinary_v5',0))
    for fn in bads:
        try:fn()
        except (AssertionError,ValueError):pass
        else:raise AssertionError('Malformed evidence accepted')
    return dict(positive=3,negative=len(bads))

def main():
    cutoff();assert not (HERE/'verified.json').exists();c.setup();ctrl=controls();started=check();report=read(HERE/'collected.json')
    assert report['complete'] and report['started_sha256']==sha(HERE/'started.json') and report['sample_sha256']==sha(OUT/'sample.npz')
    assert report['controls']==dict(positive=3) and report['optimizer_updates']==report['development_predictions']==0 and not report['new_checkpoint']
    assert len(report['records'])==32
    train=c.indices('train');rng=np.random.default_rng(2026100609);draws=[];mirrors=[]
    for _ in range(8000):draws.append(train[rng.choice(len(train),128)]);mirrors.append(rng.random()<.5)
    draws=np.asarray(draws);mirrors=np.asarray(mirrors);schedule=arrays(TRAIN/'schedule.npz')
    assert np.array_equal(draws,schedule['rows']) and np.array_equal(mirrors,schedule['mirror'])
    sample=arrays(OUT/'sample.npz');assert np.array_equal(sample['select'],np.arange(0,8000,500))
    assert np.array_equal(sample['draws'],draws[SELECT]) and np.array_equal(sample['mirrors'],mirrors[SELECT])
    assert np.array_equal(sample['ids'],np.unique(draws[SELECT])) and np.all(sample['split']==0)
    from pipeline.train_rocket_curriculum import take
    for path in (c.DATA,c.SOURCE):
        with ZipFile(path) as archive:
            for k in LABELS:assert np.array_equal(take(archive,k,sample['ids']),sample[k]),(path,k)
    summaries=[]
    for i,r in enumerate(report['records']):
        cutoff();model=list(MODELS)[i//16];step=int(SELECT[i%16]);identity(r,model,step)
        assert r['mirror']==bool(mirrors[step]) and r['draw_sha256']==hashlib.sha256(draws[step].tobytes()).hexdigest()
        assert r['play']==int((sample['y_gate'][np.searchsorted(sample['ids'],draws[step])]>.5).sum())
        assert len(r['names'])==len(r['shapes']) and len(set(r['names']))==len(r['names'])
        f=OUT/(model+'_'+str(step)+'.npz');assert r['file']==str(f.relative_to(ROOT)) and sha(f)==r['sha256']
        m=reduce_vectors(arrays(f),r['shapes']);compare(m,r['metrics'])
        summaries.append(dict(model=model,step=step,losses=r['losses'],total_loss=r['total_loss'],metrics=m))
    check()
    write(HERE/'verified.json',dict(complete=True,controls=ctrl,collected_sha256=sha(HERE/'collected.json'),sample_sha256=sha(OUT/'sample.npz'),
        summaries=summaries,model_batches=32,model_row_views=4096,unique_sample_rows=len(sample['ids']),optimizer_updates=0,new_checkpoint=False,accepted=False,deployed=False))
    print('IL_GRADIENT_VERIFIED')
if __name__=='__main__':main()
