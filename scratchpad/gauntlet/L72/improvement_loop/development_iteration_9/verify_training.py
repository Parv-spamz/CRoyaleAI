"""Independent log/schedule/final optimizer reconciliation; no inference."""
from shared import *


def verify_log(logs,draws,mirrors):
    assert len(logs)==STEPS and [r['step'] for r in logs]==list(range(1,STEPS+1))
    for i,r in enumerate(logs):
        assert np.isfinite(r['loss']) and r['loss']>=0 and r['parts']
        assert all(np.isfinite(v) and v>=0 for v in r['parts'].values())
        assert abs(r['loss']-sum(r['parts'].values()))<1e-4
        assert type(r['mirror']) is bool and r['mirror']==bool(mirrors[i])
        assert r['draw_sha256']==hashlib.sha256(draws[i].tobytes()).hexdigest()
        assert np.isfinite(r['seconds']) and r['seconds']>=0
        if i: assert r['seconds']>=logs[i-1]['seconds']


def main():
    cutoff(); p=check(); assert not (HERE/'training_verified.json').exists()
    t=read(HERE/'trained.json'); assert t['complete'] and t['finite_updates']==STEPS
    for key,name in [('checkpoint','candidate.pt'),('optimizer','optimizer.pt'),('log','train.jsonl'),('run','run.json')]:
        assert t[key+'_sha256']==sha(OUT/name)
    assert t['prepared_sha256']==sha(HERE/'prepared.json')
    schedule=arrays(OUT/'schedule.npz'); draws=schedule['rows']; mir=schedule['mirror']; train=c.indices('train')
    assert draws.shape==(8000,128) and mir.dtype==bool
    rng=np.random.default_rng(SEED)
    for i in range(8000):
        assert np.array_equal(draws[i],train[rng.choice(len(train),128)])
        assert mir[i]==(rng.random()<.5)
    assert not np.intersect1d(draws,c.indices('development')).size
    logs=[json.loads(line) for line in (OUT/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    verify_log(logs,draws,mir); negatives=0
    import copy
    mutations=[('step',0),('loss',float('nan')),('loss',-1),('parts',{'cell':float('inf')}),
        ('parts',{'cell':0}),('mirror',not bool(mir[0])),('draw_sha256','0'*64),('seconds',-1)]
    for key,value in mutations:
        bad=copy.deepcopy(logs); bad[0][key]=value
        try: verify_log(bad,draws,mir)
        except AssertionError: negatives+=1
        else: raise AssertionError('Bad training log accepted')
    parent=torch.load(INIT,map_location='cpu',weights_only=True)
    candidate=torch.load(OUT/'candidate.pt',map_location='cpu',weights_only=True)
    x=parent['model']; y=candidate['model']; assert set(x)==set(y)
    changed=[]
    for k,v in y.items():
        assert v.shape==x[k].shape and v.dtype==x[k].dtype and torch.isfinite(v).all()
        if not torch.equal(v,x[k]): changed.append(k)
    assert changed and candidate['args']==parent['args']
    run=read(OUT/'run.json'); assert candidate['development_iteration_9']==run
    assert run['initial_sha256']==sha(INIT) and run['schedule_sha256']==p['schedule_sha256']
    assert run['steps']==8000 and run['batch']==128 and run['seed']==SEED and run['optimizer']=='fresh AdamW'
    optimizer=torch.load(OUT/'optimizer.pt',map_location='cpu',weights_only=True)
    assert len(optimizer['param_groups'])==1
    group=optimizer['param_groups'][0]; assert group['lr']==1e-5 and group['weight_decay']==.01
    steps=[]
    for item in optimizer['state'].values():
        step=int(item['step'].item()); assert 0<step<=8000; steps.append(step)
        assert torch.isfinite(item['exp_avg']).all() and torch.isfinite(item['exp_avg_sq']).all()
    assert steps and max(steps)==8000
    write(HERE/'training_verified.json',dict(complete=True,finite_updates=8000,draws=int(draws.size),
        controls=dict(positive=1,negative=negatives),changed_tensors=changed,optimizer_parameters=len(steps),
        optimizer_parameter_step_range=[min(steps),max(steps)],
        trained_sha256=sha(HERE/'trained.json'),checkpoint_sha256=sha(OUT/'candidate.pt'),source_sha256=sha(Path(__file__))))
    print('ORDINARY_EXTENDED_TRAINING_VERIFIED')


if __name__=='__main__': main()
