"""All-card original expert cell loss balanced by fixed training target regions."""
import torch
import torch.nn.functional as F
from pipeline.train_gen import _ce
from pipeline.model_v3 import cell_label

def components(out,b,grid,weights):
    play=b['gate']>.5;parts={}
    if play.any():
        w=weights[play];target=cell_label(b['xy'][play],grid)
        assert torch.isfinite(w).all() and (w>0).all()
        parts['cell']=F.cross_entropy(out['cell'][play],target) if (w==1).all() else (w*F.cross_entropy(out['cell'][play],target,reduction='none')).sum()/w.sum()
        parts['card']=_ce(out['card'][play],b['slot'][play])
    if (~play).any():parts['wait']=.5*_ce(out['wait'][~play],b['wait'][~play])
    parts['gate']=F.binary_cross_entropy_with_logits(out['gate'],b['gate'])
    parts['value']=.5*F.cross_entropy(out['value'],b['value'])
    return parts

def losses(model,b,grid,weights):
    out=model(b,card=b['card'],form=b['form']);parts=components(out,b,grid,weights)
    return sum(parts.values()),{k:float(v.detach()) for k,v in parts.items()}

def train_step(model,b,opt,grid,weights):
    model.train();loss,parts=losses(model,b,grid,weights)
    if not torch.isfinite(loss):raise ValueError('Nonfinite spatial loss')
    opt.zero_grad(set_to_none=True);loss.backward()
    if not all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters()):raise ValueError('Nonfinite spatial gradient')
    torch.nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step()
    return float(loss.detach()),parts
