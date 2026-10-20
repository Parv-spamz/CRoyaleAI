"""Only expert Rocket cell contributions change; no tactical inference behavior."""
import torch
import torch.nn.functional as F
from pipeline.train_gen import _ce
from pipeline.model_v3 import cell_label

def components(out,b,grid,rocket_id,weight):
    play=b['gate']>.5;parts={}
    if play.any():
        parts['cell']=F.cross_entropy(out['cell'][play],cell_label(b['xy'][play],grid))
        parts['card']=_ce(out['card'][play],b['slot'][play])
    if (~play).any():parts['wait']=.5*_ce(out['wait'][~play],b['wait'][~play])
    parts['gate']=F.binary_cross_entropy_with_logits(out['gate'],b['gate'])
    parts['value']=.5*F.cross_entropy(out['value'],b['value'])
    rocket=play&(b['card']==rocket_id)
    if weight!=1 and rocket.any():
        parts['rocket_cell_extra']=(weight-1)*F.cross_entropy(out['cell'][rocket],cell_label(b['xy'][rocket],grid),reduction='sum')/play.sum()
    return parts

def losses(model,b,grid,rocket_id,weight=3.):
    out=model(b,card=b['card'],form=b['form'])
    parts=components(out,b,grid,rocket_id,weight)
    return sum(parts.values()),{k:float(v.detach()) for k,v in parts.items()}

def train_step(model,b,opt,grid,rocket_id):
    model.train();loss,parts=losses(model,b,grid,rocket_id)
    if not torch.isfinite(loss):raise ValueError('Nonfinite loss')
    opt.zero_grad(set_to_none=True);loss.backward()
    if not all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters()):raise ValueError('Nonfinite gradient')
    torch.nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step()
    return float(loss.detach()),parts
