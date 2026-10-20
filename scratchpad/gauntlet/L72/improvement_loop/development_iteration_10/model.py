"""Isolated dropout-free development loader; production model and runtime are unchanged."""
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
        cfg=state['development_iteration_10'];assert cfg['training_dropout_disabled'] and cfg['arm']=='ordinary_no_dropout_v5'
    for module in model.modules():
        if isinstance(module,torch.nn.Dropout):module.p=0.
        if isinstance(module,torch.nn.MultiheadAttention):module.dropout=0.
    disabled=validate_disabled(model)
    if not initial:assert state['development_iteration_10']['dropout_settings']==disabled
    return model,state
