"""Isolated diagnostic loader; production model and runtime are unchanged."""
import torch
from pipeline.model_gen import load_model
def dropout_settings(model):
    settings={}
    for name,module in model.named_modules():
        if isinstance(module,torch.nn.Dropout):settings[name+'.p']=float(module.p)
        if isinstance(module,torch.nn.MultiheadAttention):settings[name+'.dropout']=float(module.dropout)
    return settings
def validate_disabled(model):
    values=dropout_settings(model)
    assert values and all(v==0 for v in values.values())
    return values
def load_dropout(path,device,initial=False):
    model,state=load_model(path,device)
    assert state['args']['feature_version']==5 and state['args']['grid']=='lattice'
    original=dropout_settings(model);assert original and all(v==.1 for v in original.values())
    if not initial:
        cfg=state['dropout_free_fit'];assert cfg['quarantined'] and not cfg['eligible_policy_parent']
    for module in model.modules():
        if isinstance(module,torch.nn.Dropout):module.p=0.
        if isinstance(module,torch.nn.MultiheadAttention):module.dropout=0.
    disabled=validate_disabled(model)
    if not initial:assert state['dropout_free_fit']['dropout_settings']==disabled
    return model,state
