"""Independent scalar joins, recurrence and reductions from original saved inputs."""
import copy,math,statistics
from collections import defaultdict
from common import *

def close(a,b):
    if isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:close(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):close(x,y)
    elif isinstance(a,float):assert isinstance(b,(float,int)) and math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
    else:assert a==b
def coefficient(ticks,end):
    assert len(ticks)>0 and all(b>a for a,b in zip(ticks,ticks[1:])) and end>=ticks[-1]
    cs=[0.]*len(ticks);cs[-1]=.99994**(end-ticks[-1])
    for k in range(len(ticks)-2,-1,-1):cs[k]=cs[k+1]*.95*(.99994**(ticks[k+1]-ticks[k]))
    return cs
def commands(plays):
    lookup={}
    for c in plays:
        key=(c['tick'],c['slot'],c['cell']);assert key not in lookup;lookup[key]=c
    return lookup
def take_command(lookup,tick,slot,cell):
    assert (tick,slot,cell) in lookup;return lookup.pop((tick,slot,cell))
def gate_credit(played,gate_sampled,logp,advantage,weight):
    if not gate_sampled:return -1.,0.
    p=math.exp(logp) if played else -math.expm1(logp)
    assert 0<=p<=1 and all(math.isfinite(x) for x in (p,advantage,weight))
    return p,weight*advantage*(int(played)-p)
def controls():
    ticks=[10,40,60];end=100;cs=coefficient(ticks,end)
    close(cs,[.99994**90*.95**2,.99994**60*.95,.99994**40])
    assert coefficient([100],100)==[1.]
    c=dict(tick=1,slot=2,cell=3,accepted=False,reason='match_over_before_landing')
    assert take_command(commands([c]),1,2,3)==c
    close(list(gate_credit(True,True,math.log(.25),2.,.1)),[.25,.15])
    close(list(gate_credit(False,True,math.log(.75),2.,.1)),[.25,-.05])
    rejected=0
    probes=[lambda:coefficient([2,1],3),lambda:coefficient([1,1],3),lambda:coefficient([1,3],2),lambda:commands([c,c]),lambda:take_command(commands([c]),1,1,3),lambda:take_command(commands([]),1,2,3),lambda:close(cs,[v+.1 for v in cs]),lambda:close({'advantage':1.},{'advantage':float('nan')}),lambda:gate_credit(True,True,.1,2.,.1)]
    for f in probes:
        try:f()
        except (AssertionError,ValueError):rejected+=1
        else:raise AssertionError('Corrupted credit control accepted')
    return dict(positive=5,negative=rejected)
def summarize(z,ids):
    data={k:v[ids].tolist() for k,v in z.items()};a=data['advantage'];w=data['weight'];s=data['gate_score'];n=len(ids)
    mean=lambda values:math.fsum(values)/n
    r=dict(n=n,matches=len(set(data['match'])),updates=len(set(data['update'])),positive=sum(v>0 for v in a),negative=sum(v<0 for v in a),zero=sum(v==0 for v in a),advantage_mean=mean(a),abs_advantage_mean=mean([abs(v) for v in a]),return_mean=mean(data['returns']),value_mean=mean(data['value']),weighted_advantage=math.fsum(x*y for x,y in zip(w,a)),weighted_abs_advantage=math.fsum(x*abs(y) for x,y in zip(w,a)),gate_sampled=sum(data['gate_sampled']),gate_score=math.fsum(s),abs_gate_score=math.fsum(abs(x) for x in s),direct_terminal_mean=mean(data['terminal_contribution']))
    for status in ('accepted','refused','unlanded','unknown'):r[status]=data['status'].count(status)
    for key in ('remaining','lag_seconds','terminal_coefficient'):
        v=data[key];r[key]=dict(min=float(min(v)),median=float(statistics.median(v)),max=float(max(v)))
    return r
def group_ids(z):
    totals=defaultdict(list);byupdate=defaultdict(lambda:defaultdict(list));bymatch=defaultdict(lambda:defaultdict(list))
    for i in range(len(z['tick'])):
        u=int(z['update'][i]);m=int(z['match'][i]);card=str(z['card'][i]);acts=['all','PLAY' if z['played'][i] else 'WAIT']
        if card:acts.append('card:'+card)
        if card=='rocket':acts.append('Rocket')
        names=[f'{phase}/{a}/{o}' for phase in ('all','warmup' if u<=5 else 'policy') for a in acts for o in ('all',str(z['outcome'][i]))]
        if u>5 and card=='rocket':
            seconds=float(z['lag_seconds'][i]);b='0-10' if seconds<=10 else '10-30' if seconds<=30 else '30-60' if seconds<=60 else '60+'
            names.append('policy/Rocket/distance:'+b)
        for name in names:totals[name].append(i);byupdate[str(u)][name].append(i);bymatch[str(m)][name].append(i)
    return totals,byupdate,bymatch
def main():
    assert not (HERE/'verified.json').exists();r=read(HERE/'report.json');assert r['complete'] and r['sources']==sources()
    fixture=controls();receipt=read(ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-rl-credit-producer.json');assert receipt['exit_code']==0 and receipt['matched']
    for p,h in r['inputs'].items():assert sha(ROOT/p)==h
    for p,h in r['outputs'].items():assert sha(OUT/p)==h
    z=arrays(OUT/'rows.npz');assert len(set(len(x) for x in z.values()))==1 and len(z['tick'])==73783
    log=logs();pos=0;ind_matches=[]
    for u,l in enumerate(log):
        raw=read(TRAIN/'rollouts'/f'u{u:03d}.json');saved=arrays(TRAIN/'rollouts'/f'u{u:03d}_contract.npz');local=0
        assert len(raw)==8 and [x['entry_index'] for x in raw]==list(range(8))
        paths=[ROOT/x['trajectory'] for x in raw];trajectories=[arrays(p,KEYS) for p in paths]
        lengths=[sum(bool(a) or bool(b) for a,b in zip(t['played'],t['gate_sampled'])) for t in trajectories];M=sum(x>0 for x in lengths)
        for j,(rec,t,n) in enumerate(zip(raw,trajectories,lengths)):
            keep=[k for k in range(len(t['tick'])) if t['played'][k] or t['gate_sampled'][k]];ticks=[int(t['tick'][k]) for k in keep];cs=coefficient(ticks,rec['end_tick']);lookup=commands(rec['plays']);counts=dict(accepted=0,refused=0,unlanded=0,unknown=0)
            assert len(keep)==n and all(int(x)==j for x in saved['match'][local:local+n])
            for h,k in enumerate(keep):
                i=pos+h;play=bool(t['played'][k]);gs=bool(t['gate_sampled'][k]);tick=int(t['tick'][k]);slot=int(t['slot'][k]);cell=int(t['cell'][k]);status='wait';card=''
                if play:
                    cmd=take_command(lookup,tick,slot,cell);card=cmd['card']
                    status='accepted' if cmd.get('accepted') is True else 'unlanded' if cmd.get('reason')=='match_over_before_landing' else 'refused' if cmd.get('accepted') is False and cmd.get('reason') else 'unknown';counts[status]+=1
                a=float(saved['advantage'][local+h]);weight=1./n/M;R={'win':1,'loss':-1,'draw':0}[rec['outcome']]
                prob,score=gate_credit(play,gs,float(t['lp_gate'][k]),a,weight)
                expect=dict(update=u+1,match=u*8+j,entry_index=j,tag=rec['tag'],side=rec['side'],outcome=rec['outcome'],raw_index=k,tick=tick,end_tick=rec['end_tick'],played=play,gate_sampled=gs,slot=slot,cell=cell,card=card,status=status,advantage=a,returns=float(saved['returns'][local+h]),value=float(saved['v_old'][local+h]),step_reward=float(saved['r_step'][local+h]),gamma=float(saved['gamma_row'][local+h]),weight=weight,probability=prob,gate_score=score,remaining=n-1-h,lag_seconds=(rec['end_tick']-tick)/20.,terminal_coefficient=cs[h],terminal_contribution=cs[h]*R)
                assert set(expect)==set(z)
                for key,val in expect.items():close(val,z[key][i].item())
            assert not lookup
            ind_matches.append(dict(match=u*8+j,update=u+1,index=j,tag=rec['tag'],side=rec['side'],outcome=rec['outcome'],native=rec['native'],raw_decisions=len(t['tick']),contributing=n,commands=len(rec['plays']),**counts))
            pos+=n;local+=n
        assert local==l['rows']==len(saved['match'])
    assert pos==73783;close(ind_matches,read(OUT/'matches.json'))
    total,perupdate,permatch=group_ids(z);close({k:summarize(z,v) for k,v in total.items()},r['groups'])
    for ids,name in [(perupdate,'per_update.json'),(permatch,'per_match.json')]:
        expected=read(OUT/name);assert set(ids)==set(expected)
        for group,indices in ids.items():close({k:summarize(z,v) for k,v in indices.items()},expected[group])
    assert sources()==r['sources']
    write(HERE/'verified.json',dict(complete=True,rows=pos,updates=32,matches=256,groups=len(total),controls=fixture,report_sha256=sha(HERE/'report.json'),source_sha256=sha(Path(__file__)),outputs=r['outputs'],model_inference=0,optimizer_updates=0,accepted=False))
    print('RL_CREDIT_VERIFIED')
if __name__=='__main__':main()
