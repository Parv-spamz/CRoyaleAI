"""Isolated diagnostic-only generic local-cell residual; production unchanged."""
import torch
from torch import nn
from pipeline.model_gen import GenModel

class LocalCellModel(GenModel):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.local_cell=nn.Sequential(nn.Linear(2*self.d,self.d),nn.GELU(),nn.Linear(self.d,16))
        nn.init.zeros_(self.local_cell[2].weight); nn.init.zeros_(self.local_cell[2].bias)
        cells=torch.arange(2304)
        self.register_buffer('local_cell_offset',(cells//36%4)*4+cells%36%4)

    def local_scores(self,p,q):
        q=q[:,None,:].expand(-1,p.shape[1],-1)
        score=self.local_cell(torch.cat([p,q],dim=-1))
        return score-score.mean(-1,keepdim=True)

    def cell_logits_gen(self,enc,card,form):
        original=super().cell_logits_gen(enc,card,form)
        q=self.query(torch.cat([enc['g'],self.emb(card,form)],dim=-1))
        scores=self.local_scores(enc['p'],q)
        return original+scores[:,self.cell_patch,self.local_cell_offset]

def load_local(path,device,initial=False):
    state=torch.load(path,map_location=device,weights_only=True); a=state['args']
    assert state['gen'] and int(a['feature_version'])==5
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(2026100612)
        model=LocalCellModel(d=int(a['d']),layers=int(a['layers']),d_c=int(state['d_c']),
            n_cards=len(state['card_vocab']),feature_version=5).to(device)
    if initial:
        missing,unexpected=model.load_state_dict(state['model'],strict=False)
        assert set(missing)=={'local_cell_offset','local_cell.0.weight','local_cell.0.bias','local_cell.2.weight','local_cell.2.bias'}
        assert not unexpected
    else:
        assert state['local_cell_fit']['quarantined'] and not state['local_cell_fit']['eligible_policy_parent']
        model.load_state_dict(state['model'],strict=True)
    return model,state
