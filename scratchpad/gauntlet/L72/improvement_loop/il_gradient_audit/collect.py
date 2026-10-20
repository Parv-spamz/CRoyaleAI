"""Fixed-weight training-only loss gradients. No optimizer or checkpoint writes."""
import os
import torch
import torch.nn.functional as F
from shared import *

def metrics(g,reach,shapes):
    assert g.dtype==np.float32 and g.shape==(6,sum(int(np.prod(s)) for s in shapes))
    assert reach.shape==(5,len(shapes)) and reach.dtype==bool and np.isfinite(g).all()
    expanded=np.repeat(reach,np.array([int(np.prod(s)) for s in shapes]),axis=1)
    assert not np.count_nonzero(g[:5][~expanded])
    full=g.astype(np.float64);delta=full[:5].sum(axis=0)-full[5]
    maxerr=float(np.abs(delta).max());errnorm=float(np.linalg.norm(delta));totalnorm=float(np.linalg.norm(full[5]))
    assert maxerr<=1e-5+1e-4*float(np.abs(full[5]).max())
    assert errnorm<=(1e-4*totalnorm if totalnorm else 1e-6)
    result={'linearity_max':maxerr,'linearity_l2':errnorm,'total_norm':totalnorm}
    for name,mask in [('all',np.ones(g.shape[1],bool)),('shared',expanded[0]&expanded[1:].any(axis=0))]:
        a=full[:5,mask];gram=a@a.T;norm=np.sqrt(np.diag(gram));rest=a[1:].sum(axis=0)
        cr=float(a[0]@rest);rn=float(np.linalg.norm(rest));ct=float(a[0]@full[5,mask])
        cos=[[float(gram[i,j]/(norm[i]*norm[j])) if norm[i] and norm[j] else None for j in range(5)] for i in range(5)]
        result[name]=dict(parameters=int(mask.sum()),norms=norm.tolist(),dots=gram.tolist(),cosines=cos,rest_norm=rn,cell_rest_dot=cr,
            cell_rest_cosine=cr/(float(norm[0])*rn) if norm[0] and rn else None,cell_total_dot=ct,opposed=cr<0,total_opposes_cell=ct<0)
    return result

def fixture():
    g=np.zeros((6,2),np.float32);g[0]=[3,4];g[1]=[6,8];g[5]=g[:5].sum(0)
    reach=np.array([[True],[True],[False],[False],[False]])
    m=metrics(g,reach,[[2]]);assert m['all']['cell_rest_dot']==50 and m['all']['cell_rest_cosine']==1
    g[1]*=-1;g[5]=g[:5].sum(0);m=metrics(g,reach,[[2]]);assert m['all']['cell_rest_cosine']==-1 and m['all']['total_opposes_cell']
    g[:]=0;m=metrics(g,reach,[[2]]);assert m['all']['cell_rest_cosine'] is None
    return {'positive':3}

def differentiable(model,b,grid):
    from pipeline.model_v3 import cell_label
    from pipeline.train_gen import _ce
    o=model(b,card=b['card'],form=b['form']);play=b['gate']>.5
    assert play.any() and (~play).any(),'Both PLAY and WAIT required for this fixed sample'
    return dict(cell=F.cross_entropy(o['cell'][play],cell_label(b['xy'][play],grid)),
        card=_ce(o['card'][play],b['slot'][play]),wait=.5*_ce(o['wait'][~play],b['wait'][~play]),
        gate=F.binary_cross_entropy_with_logits(o['gate'],b['gate']),value=.5*F.cross_entropy(o['value'],b['value']))

def main():
    cutoff();assert not OUT.exists() and not (HERE/'started.json').exists();c.setup();controls=fixture()
    assert sha(MODELS['ordinary_v5'])==read(c.HERE/'ordinary_v5_portable.json')['portable_sha256']
    assert sha(MODELS['ordinary_no_dropout_v5'])==read(HERE.parent/'development_iteration_10/trained.json')['checkpoint_sha256']
    assert sha(TRAIN/'schedule.npz')==read(HERE.parent/'development_iteration_10/prepared.json')['schedule_sha256']
    src=sources();OUT.mkdir();write(HERE/'started.json',dict(pid=os.getpid(),sources=src,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    schedule=arrays(TRAIN/'schedule.npz');draws=schedule['rows'][SELECT];mirrors=schedule['mirror'][SELECT]
    ids=np.unique(draws);assert np.isin(ids,c.indices('train')).all()
    sub,meta=c.load_subset(c.DATA,ids);assert np.all(sub['split']==0)
    np.savez_compressed(OUT/'sample.npz',ids=ids,draws=draws,mirrors=mirrors,select=SELECT,**{k:sub[k] for k in LABELS})
    rows=c.GenRows(sub,np.arange(len(ids)),'cuda')
    from pipeline.model_gen import load_model
    from pipeline.train_gen import losses
    records=[]
    for modelname,path in MODELS.items():
        cutoff();model,state=load_model(path,'cuda');model.eval()
        assert state['args']['feature_version']==5 and state['args']['grid']==meta['grid']=='lattice' and state['card_vocab']==meta['card_vocab']
        old={k:v.detach().cpu().clone() for k,v in model.state_dict().items()};params=list(model.parameters())
        names=[n for n,p in model.named_parameters()];shapes=[list(p.shape) for p in params]
        for j,step in enumerate(SELECT):
            cutoff();b=c.augment(rows.batch(np.searchsorted(ids,draws[j])),bool(mirrors[j]))
            terms=differentiable(model,b,meta['grid']);original,oparts=losses(model,b,False,meta['grid'])
            values={k:float(v.detach()) for k,v in terms.items()}
            assert values==oparts and float(sum(terms.values()).detach())==float(original.detach())
            vectors=[];reaches=[]
            for name in HEADS:
                grad=torch.autograd.grad(terms[name],params,retain_graph=True,allow_unused=True) if terms[name].requires_grad else tuple(None for p in params)
                reaches.append([v is not None for v in grad])
                vectors.append(np.concatenate([(v.detach().cpu().numpy().reshape(-1) if v is not None else np.zeros(p.numel(),np.float32)) for p,v in zip(params,grad)]))
            grad=torch.autograd.grad(original,params,allow_unused=True)
            vectors.append(np.concatenate([(v.detach().cpu().numpy().reshape(-1) if v is not None else np.zeros(p.numel(),np.float32)) for p,v in zip(params,grad)]))
            g=np.stack(vectors);reach=np.asarray(reaches,bool);result=metrics(g,reach,shapes)
            assert all(torch.equal(old[k],v.detach().cpu()) for k,v in model.state_dict().items()) and all(p.grad is None for p in params)
            f=OUT/(modelname+'_'+str(int(step))+'.npz');np.savez_compressed(f,g=g,reach=reach)
            rec=dict(model=modelname,step=int(step),mirror=bool(mirrors[j]),draw_sha256=hashlib.sha256(draws[j].tobytes()).hexdigest(),
                rows=128,play=int((b['gate']>.5).sum()),losses=values,total_loss=float(original.detach()),names=names,shapes=shapes,
                file=str(f.relative_to(ROOT)),sha256=sha(f),metrics=result,weights_unchanged=True)
            records.append(rec);write(HERE/'progress.json',dict(completed=len(records),total=32,model=modelname,step=int(step)))
            print('IL_GRADIENT_BATCH',len(records),modelname,int(step),flush=True)
            del terms,original,grad,vectors,g
        del model,params,old
    assert sources()==src
    write(HERE/'collected.json',dict(complete=True,controls=controls,records=records,sample_sha256=sha(OUT/'sample.npz'),started_sha256=sha(HERE/'started.json'),
        optimizer_updates=0,new_checkpoint=False,development_predictions=0,accepted=False,deployed=False))
    print('IL_GRADIENT_COLLECTED')
if __name__=='__main__':main()
