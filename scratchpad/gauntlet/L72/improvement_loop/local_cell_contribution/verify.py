import copy
import math
import statistics
from shared import *
import torch.nn.functional as F

def validate(z,expected,raw,cache,mir,weights):
    n=len(expected);d=weights['cell_emb'].shape[1]
    assert np.array_equal(z['ids'],expected) and len(set(expected))==n
    for key,source in [('rep','rep'),('tick','tick'),('card','y_card')]:assert np.array_equal(z[key],raw[source][expected])
    xy=raw['y_xy'][expected].copy()
    if mir:xy[:,0]=1-xy[:,0]
    assert np.array_equal(z['xy'],xy)
    for i,row in enumerate(expected):
        hit=np.where(raw['deck_card'][row]==z['card'][i])[0];assert len(hit)==1
        assert z['form'][i]==raw['deck_form'][row,hit[0]]
    pos=np.searchsorted(cache['ids'],expected);assert np.array_equal(cache['ids'][pos],expected)
    assert np.array_equal(z['anchor'],cache['expert_cell'][pos])
    for key,shape in [('p',(n,144,d)),('g',(n,d)),('q',(n,d)),('base',(n,2304)),('residual',(n,2304)),('full',(n,2304))]:
        assert z[key].shape==shape and z[key].dtype==np.float32 and np.isfinite(z[key]).all(),key
    assert np.array_equal(z['base']+z['residual'],z['full'])
    assert np.array_equal(z['full'].argmax(1),z['anchor'])
    def linear(x,name):return F.linear(x,weights[name+'.weight'],weights[name+'.bias'])
    cids=torch.tensor(z['card'].astype(np.int64));forms=torch.tensor(z['form'].astype(np.int64))
    g=torch.from_numpy(z['g']).double();p=torch.from_numpy(z['p']).double()
    embed=weights['card_id.weight'][cids]+weights['form_id.weight'][forms]
    q=linear(F.gelu(linear(torch.cat([g,embed],-1),'query.0')),'query.2')
    assert np.allclose(q.numpy(),z['q'],atol=5e-4,rtol=2e-5)
    kp=(linear(p,'cell_key')*q[:,None,:]).sum(-1)
    kc=q@linear(weights['cell_emb'],'cell_key').T
    patches=torch.tensor([(i//36//4)*9+(i%36//4) for i in range(2304)])
    offsets=torch.tensor([((i//36)%4)*4+i%4 for i in range(2304)])
    base=(kp[:,patches]+kc)/math.sqrt(d)+weights['cell_bias']
    joined=torch.cat([p,q[:,None,:].expand(-1,144,-1)],-1)
    score=linear(F.gelu(linear(joined,'local_cell.0')),'local_cell.2')
    score-=score.mean(-1,keepdim=True);res=score[:,patches,offsets]
    assert np.allclose(base.numpy(),z['base'],atol=5e-4,rtol=2e-5),'base reconstruction'
    assert np.allclose(res.numpy(),z['residual'],atol=5e-4,rtol=2e-5),'residual reconstruction'
    return dict(base_max_abs=float(np.max(np.abs(base.numpy()-z['base']))),residual_max_abs=float(np.max(np.abs(res.numpy()-z['residual']))))

def recount(z,cv):
    collected={};patch=lambda i:(i//36//4)*9+i%36//4
    for i in range(len(z['ids'])):
        x,y=z['xy'][i];target=min(63,max(0,int(np.float32(y*64))))*36+min(35,max(0,int(np.float32(x*36))))
        pred={k:int(np.argmax(z[col][i])) for k,col in [('on','full'),('off','base')]}
        values={}
        for name,col in [('on','full'),('off','base')]:
            cell=pred[name];dx=(cell%36/36-float(x))*18;dy=(cell//36/64-float(y))*32;distance=math.sqrt(dx*dx+dy*dy)
            hit=distance<=1
            values.update({name+'_aim':int(hit),name+'_exact':int(cell==target),
                name+'_miss_same_patch':int(not hit and patch(cell)==patch(target)),
                name+'_miss_other_patch':int(not hit and patch(cell)!=patch(target))})
            scores=z[col][i].astype(np.float64);maximum=float(max(scores))
            values[name+'_ce']=maximum+math.log(float(np.exp(scores-maximum).sum()))-float(scores[target])
            others=np.r_[scores[:target],scores[target+1:]]
            values[name+'_target_margin']=float(scores[target]-max(others))
        values['choice_changed']=int(pred['on']!=pred['off'])
        values['aim_gain']=int(values['on_aim']>values['off_aim']);values['aim_loss']=int(values['on_aim']<values['off_aim'])
        values['aim_tie']=int(values['on_aim']==values['off_aim'])
        residual=z['residual'][i].astype(np.float64);rp=[residual[j] for j in range(2304) if patch(j)==patch(target)]
        values['residual_expert_patch_span']=float(max(rp)-min(rp))
        values['residual_target_vs_base_winner']=float(residual[target]-residual[pred['off']])
        values['base_winner_vs_target_gap']=float(z['base'][i,pred['off']])-float(z['base'][i,target])
        groups=['all','card/'+cv[int(z['card'][i])]]
        if cv[int(z['card'][i])]=='rocket':
            groups.append('rocket')
            if z['tick'][i]>=4800:groups.append('late_rocket')
        for group in groups:collected.setdefault(group,[]).append((int(z['rep'][i]),values))
    result={}
    for group,rows in collected.items():
        countkeys=[k for k,v in rows[0][1].items() if type(v) is int]
        floats=[k for k in rows[0][1] if k not in countkeys];replays={}
        for rep,values in rows:
            dest=replays.setdefault(str(rep),{k:0 for k in countkeys})
            for k in countkeys:dest[k]+=values[k]
        result[group]=dict(rows=len(rows),replays=len(replays),counts={k:sum(v[k] for _,v in rows) for k in countkeys},
            values={k:dict(mean=sum(v[k] for _,v in rows)/len(rows),median=statistics.median(v[k] for _,v in rows)) for k in floats},by_replay=replays)
    return result

def equivalent(a,b):
    if isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:equivalent(a[k],b[k])
    elif isinstance(a,float):assert math.isfinite(a) and math.isfinite(b) and abs(a-b)<=1e-10,(a,b)
    else:assert a==b

def main():
    cutoff();c.setup();assert not (HERE/'verified.json').exists()
    report=read(HERE/'collected.json');assert report['complete'] and report['sources']==sources()
    for path,h in report['sources'].items():assert sha(ROOT/path)==h,path
    assert report['forward_views']==2048 and report['play_records']==1024 and report['weights_unchanged']
    assert report['backward']==report['optimizer_updates']==0
    assert sha(OUT/'report.json')==report['report_sha256']
    raw,meta=f.raw_labels()
    with np.load(c.DATA,allow_pickle=False) as data:
        for key in ('deck_card','deck_form'):raw[key]=data[key]
    sample=arrays(f.OUT/'schedule.npz')['sample'];ids=sample[raw['y_gate'][sample]==1]
    assert len(ids)==512 and np.isin(ids,c.indices('train')).all()
    with np.load(c.SOURCE,allow_pickle=False) as original:
        for key in ('rep','tick','y_gate','y_card','y_xy','hand_card','split','deck_card','deck_form'):
            assert np.array_equal(raw[key][ids],original[key][ids])
    state=torch.load(CKPT,map_location='cpu',weights_only=True)
    weights={k:v.double() for k,v in state['model'].items()}
    expected=read(OUT/'report.json');got={};errors={};positives=0;test=None;cache0=None
    for mir in (False,True):
        orientation='mirrored' if mir else 'native';filename=orientation+'.npz'
        assert sha(OUT/filename)==report['artifacts'][filename]
        z=arrays(OUT/filename);cache=arrays(f.OUT/('local_cell_final_'+orientation+'.npz'))
        errors[orientation]=validate(z,ids,raw,cache,mir,weights);positives+=1
        got[orientation]=recount(z,meta['card_vocab']);equivalent(got[orientation],expected[orientation])
        old=read(FIT/'results_verified.json')['summaries']['local_cell_final/'+orientation]
        for group,vals in got[orientation].items():
            prior=old['play' if group=='all' else group]
            assert vals['counts']['on_aim']==prior['aim1'] and vals['rows']==prior['views']
        if not mir:test={k:v[:8].copy() for k,v in z.items()};cache0=cache
    validate(test,ids[:8],raw,cache0,False,weights);positives+=1
    cases=[]
    for key,value in [('ids',-1),('rep',-1),('card',0),('form',3),('anchor',2304)]:
        bad=copy.deepcopy(test);bad[key][0]=value;cases.append(bad)
    for key in ('xy','p','q','base','residual','full'):
        bad=copy.deepcopy(test);bad[key].reshape(-1)[0]=np.nan;cases.append(bad)
    bad=copy.deepcopy(test);bad['base'][0,:]+=1;bad['full']=bad['base']+bad['residual'];cases.append(bad)
    bad=copy.deepcopy(test);bad['residual'][0,:]+=1;bad['full']=bad['base']+bad['residual'];cases.append(bad)
    negatives=0
    for bad in cases:
        try:validate(bad,ids[:8],raw,cache0,False,weights)
        except (AssertionError,IndexError):negatives+=1
        else:raise AssertionError('Corrupt diagnostic accepted')
    assert negatives==13
    logs=[json.loads(line) for line in (f.OUT/'train.jsonl').read_text().splitlines()]
    means={key:{part:sum(r['parts'][part] for r in rows)/len(rows) for part in logs[0]['parts']} for key,rows in [('first256',logs[:256]),('last256',logs[-256:])]}
    equivalent(means,report['loss_parts'])
    assert sources()==report['sources']
    write(HERE/'verified.json',dict(complete=True,collected_sha256=sha(HERE/'collected.json'),report_sha256=sha(OUT/'report.json'),
        controls=dict(positive=positives,negative=negatives),reconstruction_errors=errors,loss_parts=means,
        summaries={ori:{key:{k:v for k,v in vals.items() if k!='by_replay'} for key,vals in groups.items()} for ori,groups in got.items()},
        optimizer_updates=0,backward=0,accepted=False,deployed=False,source_sha256=sha(Path(__file__))))
    print('LOCAL_CELL_CONTRIBUTION_VERIFIED')

if __name__=='__main__':main()
