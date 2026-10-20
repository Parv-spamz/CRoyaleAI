"""Independent raw-label/mask recount and existing-control comparisons."""
from shared import *


def validate_prediction(a,ids,available):
    assert np.array_equal(a['ids'],ids) and len(np.unique(a['ids']))==len(ids)
    assert a['allowed'].dtype==bool and np.array_equal(a['allowed'],available)
    for k in ('gate','gate_logit','chosen_card','expert_cell','log_cell'): assert a[k].shape==(len(ids),)
    assert a['card_logits'].shape==(len(ids),4)
    assert np.isfinite(a['gate']).all() and ((a['gate']>=0)&(a['gate']<=1)).all()
    assert np.isfinite(a['gate_logit']).all() and not np.isnan(a['card_logits']).any() and not np.isposinf(a['card_logits']).any()
    for k in ('expert_cell','log_cell'): assert ((a[k]>=0)&(a[k]<2304)).all()


def main():
    cutoff(); check(); assert not (HERE/'results_verified.json').exists()
    t=read(HERE/'trained.json'); tv=read(HERE/'training_verified.json'); ev=read(HERE/'evaluated.json')
    assert tv['complete'] and tv['finite_updates']==8000 and tv['controls']==dict(positive=1,negative=9)
    assert tv['trained_sha256']==sha(HERE/'trained.json') and ev['training_verified_sha256']==sha(HERE/'training_verified.json')
    assert ev['complete'] and ev['checkpoint_sha256']==sha(OUT/'candidate.pt')==t['checkpoint_sha256']
    c.setup(); ids=c.indices('development'); s,meta=c.load_subset(c.DATA,ids); cv=meta['card_vocab']
    ns=independent(); controls=ns['controls'](); ms,target,available=ns['independent_masks'](ids,s,cv)
    defense=arrays(DEFENSE)['defensive_development']; ms['defensive_sequence']=np.isin(ids,defense)
    ms['defensive_rocket']=ms['defensive_sequence']&(s['y_gate']==1)&(s['y_card']==cv.index('rocket'))
    saved,expected_target=masks(ids); assert np.array_equal(target,expected_target)
    for key,value in ms.items(): assert np.array_equal(value,saved[key]),key
    extra={k:v for k,v in saved.items() if k not in ms}; extra_independent(ids,s,cv,extra); ms.update(extra)
    count=ns['independently_count']; ref=read(PRIOR/'results_verified.json')
    reports={}; hashes={}; breakdown={}; candidate_predictions=None
    for name,path in {**CONTROLS,ARM:OUT/'predictions.npz'}.items():
        a=arrays(path); validate_prediction(a,ids,available)
        if name in CONTROLS: assert sha(path)==ref['hashes'][name]['cache']
        else: assert sha(path)==ev['cache_sha256']; candidate_predictions=a
        result=count(s,a,cv,ms,target)
        if name==ARM: assert result==ev['counts']
        else:
            compact={k:{f:v for f,v in vals.items() if f!='by_replay'} for k,vals in result.items()}
            assert compact==ref['counts'][name]
        reports[name]=result; hashes[name]=dict(cache=sha(path))
        # Preserve actual PLAY successes separately from the legitimate correct WAIT component.
        play=s['y_gate']==1; called=(a['gate']>.35)&a['allowed'].any(1)
        breakdown[name]={k:dict(correct_wait=int(np.count_nonzero(mask&~play&~called)),
            play_success=result[k]['action']-int(np.count_nonzero(mask&~play&~called))) for k,mask in ms.items()}
    # Known independent scorer controls above:1positive4negative. New real-fragment cache controls:1positive6negative.
    fragment={k:v[:8].copy() for k,v in candidate_predictions.items()}; fi=ids[:8]; fa=available[:8]
    validate_prediction(fragment,fi,fa); negatives=0
    mutations=[('ids',-1),('gate',float('nan')),('gate_logit',float('inf')),('expert_cell',2304),('log_cell',-1)]
    for key,value in mutations:
        bad={k:v.copy() for k,v in fragment.items()}; bad[key][0]=value
        try: validate_prediction(bad,fi,fa)
        except AssertionError: negatives+=1
        else: raise AssertionError('Malformed prediction accepted')
    bad={k:v.copy() for k,v in fragment.items()}; bad['allowed'][0,0]=~bad['allowed'][0,0]
    try: validate_prediction(bad,fi,fa)
    except AssertionError: negatives+=1
    else: raise AssertionError('Incorrect affordability accepted')
    assert controls==dict(positive=1,negative=4) and negatives==6
    fs={control:filters(reports[control],reports[ARM]) for control in ('ordinary_v5','ordinary_extended_v5')}; paired={}
    for control in CONTROLS:
        paired[control]={group:{rep:{k:v-reports[control][group]['by_replay'][rep][k] for k,v in values.items()}
            for rep,values in val['by_replay'].items()} for group,val in reports[ARM].items()}
    write(OUT/'all_replay_counts.json',reports); write(OUT/'paired_replay_counts.json',paired)
    summary={name:{group:{k:v for k,v in val.items() if k!='by_replay'} for group,val in r.items()} for name,r in reports.items()}
    logs=[json.loads(line) for line in (OUT/'train.jsonl').read_text().splitlines()]
    loss_means={name:float(np.mean([x['loss'] for x in rows])) for name,rows in [('first256',logs[:256]),('last256',logs[-256:])]}
    loss_components={name:{k:float(np.mean([x['parts'][k] for x in rows])) for k in logs[0]['parts']} for name,rows in [('first256',logs[:256]),('last256',logs[-256:])]}
    write(HERE/'results_verified.json',dict(loss_means=loss_means,loss_components=loss_components,complete=True,rows=len(ids),counts=summary,hashes=hashes,filters=fs,
        continuation_passed=all(all(v.values()) for v in fs.values()),controls=dict(positive=2,negative=10),play_wait=breakdown,
        paired_sha256=sha(OUT/'paired_replay_counts.json'),replay_counts_sha256=sha(OUT/'all_replay_counts.json'),
        evaluated_sha256=sha(HERE/'evaluated.json'),checkpoint_sha256=t['checkpoint_sha256'],accepted=False,deployed=False))
    check(); print(json.dumps(fs)); print('ORDINARY_NO_DROPOUT_RESULTS_VERIFIED')


if __name__=='__main__': main()
