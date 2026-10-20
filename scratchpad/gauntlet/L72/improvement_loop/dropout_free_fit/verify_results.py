"""Independent scalar raw-label/cache recount; no inference or optimization."""
import copy
import math
from shared import *

KEYS=('play','wait_correct','called','card','aim1','play_success','action','gate_failure','card_failure','aim_failure')

def validate_predictions(z,ids,raw,mirrored,costs,validate):
    validate(z,ids,raw,np.ones(len(ids),np.int64),mirrored,costs)
    assert np.isfinite(z['gate_logit']).all()
    expected=1/(1+np.exp(-z['gate_logit'].astype(np.float64)))
    assert np.max(np.abs(expected-z['gate']))<1e-7

def main():
    cutoff(); check(); assert not (HERE/'results_verified.json').exists()
    report=read(HERE/'evaluated.json'); assert report['complete'] and report['quarantined']
    assert report['development_inference']==0 and report['total_views']==2048 and report['reused_control_views']==6144
    assert report['training_verified_sha256']==sha(HERE/'training_verified.json')
    assert report['counts_sha256']==sha(OUT/'counts.json')
    for name,path in dict(r1e_corrected=c.INIT,ordinary_v5=INIT,assay_final=FOUT/'candidate.pt',dropout_free_final=OUT/'candidate.pt').items():
        assert report['checkpoints'][name]==sha(path)
    raw,meta=raw_labels(); cv=meta['card_vocab']; assert cv==report['card_vocab']
    ids=arrays(OUT/'schedule.npz')['sample']; assert len(ids)==1024 and np.isin(ids,c.indices('train')).all()
    with np.load(c.SOURCE,allow_pickle=False) as original:
        for k in ('rep','tick','y_gate','y_card','y_xy','hand_card','split'):
            assert np.array_equal(raw[k][ids],original[k][ids])
    from pipeline.opp_elixir_count import card_cost
    costs=[card_cost(k.replace('-','_')) or 0 for k in cv]
    ns=functions(HERE.parent/'training_fit_audit/verify.py',('validate','recount'),dict(np=np,math=math,KEYS=KEYS))
    expected=read(OUT/'counts.json'); got={}; filters={}; positives=0; test=None
    for name in ('r1e_corrected','ordinary_v5','assay_final','dropout_free_final'):
        for mir in (False,True):
            orientation='mirrored' if mir else 'native'; key=name+'/'+orientation; filename=name+'_'+orientation+'.npz'
            directory=OUT if name=='dropout_free_final' else FOUT
            assert sha(directory/filename)==report['artifacts'][filename]
            z=arrays(directory/filename); validate_predictions(z,ids,raw,mir,costs,ns['validate']); positives+=1
            got[key]=ns['recount'](z,np.ones(len(ids),np.int64),cv)
            assert got[key]==expected[key],key
            a=got[key]['all']; p=got[key]['play']; r=got[key]['rocket']
            assert a['views']==1024 and a['play']==p['views']==512 and r['views']==64
            filters[key]=dict(play_fit=10*p['play_success']>=9*512,rocket_card_fit=100*r['card']>=95*64,
                rocket_aim_fit=100*r['aim1']>=95*64,wait_fit=100*a['wait_correct']>=95*512,all_card_preserved=p['card']==512,all_wait_preserved=a['wait_correct']==512)
            if key=='ordinary_v5/native': test={k:val[:5].copy() for k,val in z.items()}
    assert filters==report['filters']
    verdict=all(all(filters['dropout_free_final/'+ori].values()) for ori in ('native','mirrored'))
    assert verdict==report['diagnostic_fit']
    small_ids=ids[:5]; validate_predictions(test,small_ids,raw,False,costs,ns['validate'])
    cases=[]
    for key,value in [('ids',int(small_ids[1])),('rep',-99),('y_gate',9),('y_card',-1),('frequency',2),
        ('gate',float('nan')),('gate_logit',float('nan')),('expert_cell',2304),('chosen_card',-1)]:
        bad=copy.deepcopy(test); bad[key][0]=value; cases.append(bad)
    bad=copy.deepcopy(test); bad['y_xy'][0,0]+=.01; cases.append(bad)
    bad=copy.deepcopy(test); bad['allowed'][0,0]=~bad['allowed'][0,0]; cases.append(bad)
    bad=copy.deepcopy(test); bad['gate_logit'][0]+=1; cases.append(bad)
    negatives=0
    for bad in cases:
        try: validate_predictions(bad,small_ids,raw,False,costs,ns['validate'])
        except AssertionError: negatives+=1
        else: raise AssertionError('Corrupt prediction or label accepted')
    assert negatives==12
    logs=[json.loads(line) for line in (OUT/'train.jsonl').read_text().splitlines()]
    loss_means={name:float(np.mean([x['loss'] for x in rows])) for name,rows in [('first256',logs[:256]),('last256',logs[-256:])]}
    loss_components={name:{k:float(np.mean([x['parts'][k] for x in rows])) for k in logs[0]['parts']} for name,rows in [('first256',logs[:256]),('last256',logs[-256:])]}
    summaries={key:{group:{k:val for k,val in values.items() if k!='by_replay'} for group,values in groups.items()} for key,groups in got.items()}
    check(); write(HERE/'results_verified.json',dict(complete=True,controls=dict(positive=positives+1,negative=negatives),
        evaluated_sha256=sha(HERE/'evaluated.json'),counts_sha256=sha(OUT/'counts.json'),summaries=summaries,
        filters=filters,diagnostic_fit=verdict,loss_means=loss_means,loss_components=loss_components,quarantined=True,eligible_policy_parent=False,
        accepted=False,deployed=False,development_inference=0,source_sha256=sha(Path(__file__))))
    print('DROPOUT_FREE_FIT_RESULTS_VERIFIED')

if __name__=='__main__': main()
