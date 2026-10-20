"""Repair only this run's TorchVersion metadata; all original weights retained."""
import argparse
import io
from collections.abc import Mapping
import torch
from torch.torch_version import TorchVersion
import common as c
from pipeline.model_gen import load_model


def normalize(v):
    if isinstance(v,TorchVersion):return str(v),1
    if isinstance(v,Mapping):
        out={};count=0
        for key,value in v.items():out[key],n=normalize(value);count+=n
        return out,count
    if isinstance(v,(list,tuple)):
        parts=[normalize(x) for x in v]
        return type(v)(x for x,n in parts),sum(n for x,n in parts)
    return v,0


def equivalent(a,b):
    if isinstance(a,torch.Tensor):
        assert isinstance(b,torch.Tensor) and a.dtype==b.dtype and a.shape==b.shape and torch.equal(a,b)
    elif isinstance(a,Mapping):
        assert set(a)==set(b)
        for key in a:equivalent(a[key],b[key])
    elif isinstance(a,(tuple,list)):
        assert type(a)==type(b) and len(a)==len(b)
        for x,y in zip(a,b):equivalent(x,y)
    elif isinstance(a,TorchVersion):assert type(b) is str and str(a)==b
    else:assert type(a)==type(b) and a==b


def controls():
    original={'model':{'w':torch.tensor([1.,2.])},'meta':{'torch':TorchVersion('2.11.0+cu128')}}
    data=io.BytesIO();torch.save(original,data);data.seek(0)
    try:torch.load(data,weights_only=True)
    except Exception as error:
        assert 'TorchVersion' in str(error)
    else:raise AssertionError('Original serialization failure not reproduced')
    clean,n=normalize(original);assert n==1;equivalent(original,clean)
    data=io.BytesIO();torch.save(clean,data);data.seek(0);roundtrip=torch.load(data,weights_only=True)
    equivalent(original,roundtrip)
    for mutation in ('weight','metadata','dtype'):
        bad,_=normalize(original);bad['model']=dict(bad['model']);bad['meta']=dict(bad['meta'])
        if mutation=='weight':bad['model']['w']=bad['model']['w']+1
        elif mutation=='dtype':bad['model']['w']=bad['model']['w'].double()
        else:bad['meta']['torch']='wrong'
        try:equivalent(original,bad)
        except AssertionError:pass
        else:raise AssertionError('Mutation passed')
    return dict(positive=1,negative=3,original_error_reproduced=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--arm',choices=('ordinary_v5','ordinary_v6'),required=True)
    a=ap.parse_args();c.setup();c.check_prepared();c.check_frozen();tested=controls()
    folder=c.OUT/a.arm;source=folder/'candidate.pt';dest=folder/'candidate_portable.pt'
    receipt=c.HERE/(a.arm+'_portable.json')
    if dest.exists() or receipt.exists():raise ValueError('Preserve existing conversion')
    result=c.read(folder/'result.json');assert result['finite_updates']==1000 and result['checkpoint_sha256']==c.sha(source)
    # Exact own-produced source hash checked above. Only this known string class is allowed.
    with torch.serialization.safe_globals([TorchVersion]):
        state=torch.load(source,map_location='cpu',weights_only=True)
    clean,count=normalize(state);assert count==1
    equivalent(state,clean);torch.save(clean,dest)
    plain=torch.load(dest,map_location='cpu',weights_only=True);equivalent(state,plain)
    model,loaded=load_model(dest,'cpu');equivalent(plain,loaded)
    tensors={k:c.hashlib.sha256(v.detach().cpu().contiguous().numpy().tobytes()).hexdigest() for k,v in state['model'].items()}
    c.write(receipt,dict(complete=True,arm=a.arm,controls=tested,source_sha256=c.sha(source),portable_sha256=c.sha(dest),
        metadata_strings_converted=count,model_tensors=len(tensors),tensor_hashes=tensors,
        all_other_metadata_unchanged=True,standard_loader_passed=True,new_optimizer_updates=0,
        source_script_sha256=c.sha(__file__),deployment_accepted=False))
    print('DEVELOPMENT_1_PORTABLE_CHECKPOINT_VERIFIED')


if __name__=='__main__':main()
