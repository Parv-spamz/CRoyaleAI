"""New scalar credit decomposition of saved training data. No model imports."""
import datetime,os
from common import *

def summarize(z,ix):
    n=len(ix);assert n
    a=z['advantage'][ix];w=z['weight'][ix];s=z['gate_score'][ix]
    r=dict(n=n,matches=int(len(np.unique(z['match'][ix]))),updates=int(len(np.unique(z['update'][ix]))),positive=int((a>0).sum()),negative=int((a<0).sum()),zero=int((a==0).sum()),advantage_mean=float(a.mean()),abs_advantage_mean=float(np.abs(a).mean()),return_mean=float(z['returns'][ix].mean()),value_mean=float(z['value'][ix].mean()),weighted_advantage=float((w*a).sum()),weighted_abs_advantage=float((w*np.abs(a)).sum()),gate_sampled=int(z['gate_sampled'][ix].sum()),gate_score=float(s.sum()),abs_gate_score=float(np.abs(s).sum()),direct_terminal_mean=float(z['terminal_contribution'][ix].mean()))
    for status in ('accepted','refused','unlanded','unknown'):r[status]=int((z['status'][ix]==status).sum())
    for key in ('remaining','lag_seconds','terminal_coefficient'):
        v=z[key][ix];r[key]=dict(min=float(v.min()),median=float(np.median(v)),max=float(v.max()))
    return r
def groups(z):
    result={};allrows=np.ones(len(z['tick']),bool)
    for phase,pm in [('all',allrows),('warmup',z['update']<=5),('policy',z['update']>5)]:
        actions=[('all',allrows),('PLAY',z['played']),('WAIT',~z['played']),('Rocket',z['card']=='rocket')]+[(f'card:{c}',z['card']==c) for c in sorted(set(z['card'])-{''})]
        for action,am in actions:
            for resultname,om in [('all',allrows)]+[(q,z['outcome']==q) for q in ('win','loss','draw')]:
                ix=np.flatnonzero(pm&am&om)
                if len(ix):result[f'{phase}/{action}/{resultname}']=summarize(z,ix)
    for name,mask in [('0-10',z['lag_seconds']<=10),('10-30',(z['lag_seconds']>10)&(z['lag_seconds']<=30)),('30-60',(z['lag_seconds']>30)&(z['lag_seconds']<=60)),('60+',z['lag_seconds']>60)]:
        ix=np.flatnonzero((z['update']>5)&(z['card']=='rocket')&mask)
        if len(ix):result[f'policy/Rocket/distance:{name}']=summarize(z,ix)
    return result
def main():
    assert not OUT.exists() and not (HERE/'started.json').exists()
    source=sources();log=logs();OUT.mkdir();write(HERE/'started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=source))
    chunks={};bindings={};matches=[]
    for u,l in enumerate(log):
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,6,4,tzinfo=datetime.timezone.utc):raise RuntimeError('Tuesday cutoff')
        rawpath=TRAIN/'rollouts'/f'u{u:03d}.json';cp=TRAIN/'rollouts'/f'u{u:03d}_contract.npz'
        assert sha(rawpath)==l['rollouts_sha256'] and sha(cp)==l['contract_sha256']
        for p in (rawpath,cp):bindings[str(p.relative_to(ROOT))]=sha(p)
        raw=read(rawpath);c=arrays(cp);assert len(raw)==8 and [r['entry_index'] for r in raw]==list(range(8))
        ts=[];ns=[]
        for r in raw:
            p=ROOT/r['trajectory'];assert sha(p)==r['trajectory_sha256'];bindings[str(p.relative_to(ROOT))]=sha(p)
            t=arrays(p,KEYS);assert len(set(len(v) for v in t.values()))==1 and np.all(np.diff(t['tick'])>0)
            ts.append(t);ns.append(int((t['played']|t['gate_sampled']).sum()))
        assert sum(ns)==l['rows']==len(c['match']);M=sum(n>0 for n in ns);pos=0
        for j,(r,t,n) in enumerate(zip(raw,ts,ns)):
            keep=np.flatnonzero(t['played']|t['gate_sampled']);assert n and np.all(c['match'][pos:pos+n]==j)
            tick=t['tick'][keep];end=r['end_tick'];assert end==r['native']['tick'] and end>=int(tick[-1])
            assert r['native']['game_over'] and r['native']['terminated']
            played=t['played'][keep];gs=t['gate_sampled'][keep];slot=t['slot'][keep];cell=t['cell'][keep]
            cmd={(int(x['tick']),int(x['slot']),int(x['cell'])):x for x in r['plays']};assert len(cmd)==len(r['plays'])==int(played.sum())
            card=np.full(n,'',dtype='U48');status=np.full(n,'wait',dtype='U16');seen=set()
            for k in np.flatnonzero(played):
                key=(int(tick[k]),int(slot[k]),int(cell[k]));assert key in cmd and key not in seen;seen.add(key)
                card[k]=cmd[key]['card'];status[k]=command_status(cmd[key])
            assert len(seen)==len(cmd)
            lp=t['lp_gate'][keep];prob=np.where(gs,np.where(played,np.exp(lp),-np.expm1(lp)),-1.)
            assert np.all((prob[gs]>=0)&(prob[gs]<=1)) and np.all(lp[~gs]==0)
            a=c['advantage'][pos:pos+n];w=np.full(n,1/(n*M));rem=np.arange(n-1,-1,-1)
            coeff=np.power(.99994,end-tick)*np.power(.95,rem)
            values=dict(update=np.full(n,u+1),match=np.full(n,u*8+j),entry_index=np.full(n,j),tag=np.full(n,r['tag']),side=np.full(n,r['side']),outcome=np.full(n,r['outcome']),raw_index=keep,tick=tick,end_tick=np.full(n,end),played=played,gate_sampled=gs,slot=slot,cell=cell,card=card,status=status,advantage=a,returns=c['returns'][pos:pos+n],value=c['v_old'][pos:pos+n],step_reward=c['r_step'][pos:pos+n],gamma=c['gamma_row'][pos:pos+n],weight=w,probability=prob,gate_score=np.where(gs,w*a*(played.astype(float)-prob),0),remaining=rem,lag_seconds=(end-tick)/20.,terminal_coefficient=coeff,terminal_contribution=coeff*outcome(r))
            for k,v in values.items():chunks.setdefault(k,[]).append(v)
            matches.append(dict(match=u*8+j,update=u+1,index=j,tag=r['tag'],side=r['side'],outcome=r['outcome'],native=r['native'],raw_decisions=len(t['tick']),contributing=n,commands=len(cmd),accepted=int((status=='accepted').sum()),refused=int((status=='refused').sum()),unlanded=int((status=='unlanded').sum()),unknown=int((status=='unknown').sum())))
            assert matches[-1]['accepted']==r['plays_accepted'] and matches[-1]['unlanded']==r['plays_unlanded'];pos+=n
        assert pos==len(c['match']);write(HERE/'progress.json',dict(updates=u+1,total=32));print('CREDIT_UPDATE',u+1,'COMPLETE',flush=True)
    z={k:np.concatenate(v) for k,v in chunks.items()};assert len(z['tick'])==73783
    for v in z.values():
        if v.dtype.kind in 'fi':assert np.isfinite(v).all()
    np.savez_compressed(OUT/'rows.npz',**z);write(OUT/'matches.json',matches)
    perupdate={str(u):groups({k:v[z['update']==u] for k,v in z.items()}) for u in range(1,33)}
    permatch={str(m):groups({k:v[z['match']==m] for k,v in z.items()}) for m in range(256)}
    write(OUT/'per_update.json',perupdate);write(OUT/'per_match.json',permatch)
    assert sources()==source
    write(HERE/'report.json',dict(complete=True,rows=len(z['tick']),matches=256,updates=32,groups=groups(z),sources=source,inputs=bindings,outputs={name:sha(OUT/name) for name in ('rows.npz','matches.json','per_update.json','per_match.json')},model_inference=0,optimizer_updates=0,accepted=False))
    print('RL_CREDIT_AUDIT_COMPLETE')
if __name__=='__main__':main()
