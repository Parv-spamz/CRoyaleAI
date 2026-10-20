from shared import *
def main():
    assert not OUT.exists() and not (HERE/'prepared.json').exists()
    mv=read(HERE.parent/'model_verified.json');sv=read(HERE.parent/'sequence_data/verified.json')
    hv=read(HERE.parent/'mirror_replays_verified.json');assert hv['complete'] and hv['all_new_tokens_independent']
    for p,h in hv['inputs'].items():assert sha(ROOT/p)==h,p
    assert mv['complete'] and sv['complete'] and mv['sequence_verified_sha256']==sha(HERE.parent/'sequence_data/verified.json')
    for p,h in mv['sources'].items():assert sha(ROOT/p)==h,p
    assert sha(INIT)==mv['parent_sha256']=='c0ba1ab910df50fdcbe1fcf4191aedd584c86fe94c5a6d3248359bda059db419'
    assert sv['features_sha256']==sha(SEQ/'features.npz') and sv['audit_sha256']==sha(SEQ/'audit.npz')
    train=c.indices('train');dev=c.indices('development');assert len(train)==213995 and len(dev)==54723
    assert not np.intersect1d(train,dev).size
    rng=np.random.default_rng(SEED);draws=[];mirrors=[]
    for _ in range(STEPS):draws.append(train[rng.choice(len(train),128)]);mirrors.append(rng.random()<.5)
    OUT.mkdir(parents=True);np.savez_compressed(OUT/'schedule.npz',rows=np.array(draws),mirror=np.array(mirrors,bool))
    feature_hashes={};f=arrays(SEQ/'features.npz')
    for part,ids in [('train',train),('development',dev)]:
        ix=np.searchsorted(f['ids'],ids);assert np.array_equal(f['ids'][ix],ids)
        np.savez_compressed(OUT/(part+'_features.npz'),**{k:v[ix] for k,v in f.items()})
        feature_hashes[part]=sha(OUT/(part+'_features.npz'))
    write(HERE/'prepared.json',dict(complete=True,sources=sources(),schedule_sha256=sha(OUT/'schedule.npz'),
        feature_hashes=feature_hashes,
        seed=SEED,steps=STEPS,batch=128,arms=ARMS,training_rows=len(train),development_rows=len(dev),
        unique_draws=len(np.unique(draws)),mirrored_draws=int(sum(mirrors)*128),
        runtime=dict(torch=str(torch.__version__),python=sys.version,cuda=torch.version.cuda)))
    print('HAND_LEARNING_PREPARED')
if __name__=='__main__':main()
