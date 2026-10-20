"""Independent raw-label/membership recount, reusing verified control caches."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'development_iteration_7'))
import numpy as np
from experiment import *
from recount_v2 import independently_count,independent_masks
from extra_masks import independently_verify_extra

def main():
    if (HERE/'results_verified_v2.json').exists():raise ValueError('Preserve existing recount')
    checks=c.ROOT/'scratchpad/gauntlet/L71/integration/checks'
    fail=c.read(checks/'l72-development7-independent.json')
    assert fail['exit_code']!=0 and not fail['matched']
    assert 'AssertionError: gate_logit' in (checks/'l72-development7-independent.out').read_text()
    for stage in ('train','eval'):
        receipt=c.read(checks/f'l72-development7-{stage}.json');assert receipt['exit_code']==0 and receipt['matched']
    c.setup();check_active();ids=c.indices('development');s,meta=c.load_subset(c.DATA,ids);cv=meta['card_vocab']
    masks,target,allowed=independent_masks(ids,s,cv)
    with np.load(SECOND_OUT/'schedule.npz') as z:defdev=set(map(int,z['defensive_development']))
    masks['defensive_sequence']=np.array([int(row) in defdev for row in ids])
    masks['defensive_rocket']=np.array([int(row) in defdev and gate==1 and card==cv.index('rocket') for row,gate,card in zip(ids,s['y_gate'],s['y_card'])])
    with np.load(MASKS) as z:
        assert np.array_equal(ids,z['ids']) and np.array_equal(target,z['target'])
        for key,m in masks.items():assert np.array_equal(m,z['mask_'+key])
        extra={key[5:]:z[key] for key in z.files if key.startswith('mask_') and key[5:] not in masks}
    independently_verify_extra(ids,s,cv,extra);masks.update(extra)
    reports={};hashes={};all_predictions={}
    for arm,folder in [('r1e_corrected',c.OUT/'r1e_corrected_eval'),('ordinary_v5',c.OUT/'ordinary_v5_eval_v2'),('ordinary_v6',c.OUT/'ordinary_v6_eval_v2'),(ARM,OUT/(ARM+'_eval'))]:
        original=c.read(folder/'report.json');cache=folder/'predictions.npz'
        assert original['cache_sha256']==c.sha(cache)
        with np.load(cache) as z:
            assert np.array_equal(ids,z['ids']);p={k:z[k] for k in z.files if k!='ids'}
        assert np.array_equal(allowed,p['allowed'])
        all_predictions[arm]=p
        result=independently_count(s,p,cv,masks,target)
        for key,value in original['counts'].items():assert result[key]==value,(arm,key)
        reports[arm]=result;hashes[arm]=dict(cache=c.sha(cache),report=c.sha(folder/'report.json'))
    folder=OUT/ARM;result=c.read(folder/'result.json');run=c.read(folder/'run.json')
    logs=[c.json.loads(line) for line in (folder/'train.jsonl').read_text().splitlines()]
    assert [x['step'] for x in logs]==list(range(1,1001))
    assert all(np.isfinite(x['loss']) and all(np.isfinite(v) for v in x['parts'].values()) for x in logs)
    assert result['finite_updates']==1000 and result['checkpoint_sha256']==c.sha(folder/'candidate.pt')
    assert run['schedule_sha256']==c.sha(SCHEDULE)
    import torch
    parent=torch.load(INIT,map_location='cpu',weights_only=True);candidate=torch.load(folder/'candidate.pt',map_location='cpu',weights_only=True)
    assert all(torch.equal(v,candidate['model'][k]) for k,v in parent['model'].items())
    assert run['initial_checkpoint_sha256']==c.sha(INIT)
    exact=True;differences={}
    for key in ('gate_logit','card_logits'):
        x,y=all_predictions[ARM][key],all_predictions['ordinary_v5'][key];same=np.array_equal(x,y);exact=exact and same
        finite=np.isfinite(x)&np.isfinite(y);diff=np.abs(x[finite]-y[finite])
        differences[key]=dict(exact=same,different_values=int(np.count_nonzero(x!=y)),values=x.size,max_abs=float(diff.max()))
    differences['gate_decision_changes']=int(np.count_nonzero((all_predictions[ARM]['gate']>.35)!=(all_predictions['ordinary_v5']['gate']>.35)))
    differences['chosen_card_changes']=int(np.count_nonzero(all_predictions[ARM]['chosen_card']!=all_predictions['ordinary_v5']['chosen_card']))
    hashes[ARM]['checkpoint']=result['checkpoint_sha256']
    a,b=reports['ordinary_v5'],reports[ARM]
    late='phase_late_overtime_clock';rocket='rocket_late_overtime_clock'
    late_delta=b[late]['action']/b[late]['rows']-a[late]['action']/a[late]['rows']
    rocket_delta=b[rocket]['action']/b[rocket]['rows']-a[rocket]['action']/a[rocket]['rows']
    card_delta=b['all']['card']/b['all']['play']-a['all']['card']/a['all']['play']
    filters=dict(denominators_present=all(a[k]['rows']>0 for k in (late,rocket,'rocket','defensive_sequence','barrel_pro','witch','night_witch','furnace')),
        exact_gate_card_logits=bool(exact),late_action_nonregression=late_delta>=0,late_rocket_action_nonregression=rocket_delta>=0,
        general_card_exact=card_delta==0,barrel_correct_material=(b['barrel_pro']['log_correct']-a['barrel_pro']['log_correct'])/a['barrel_pro']['rows']>=.15,
        barrel_wrong_halved=b['barrel_pro']['log_wrong']<=.5*a['barrel_pro']['log_wrong'],barrel_action_nonregression=b['barrel_pro']['action']>=a['barrel_pro']['action'],
        defensive_action_nonregression=b['defensive_sequence']['action']>=a['defensive_sequence']['action'],
        rocket_aim_nonregression=b['rocket']['aim1']>=a['rocket']['aim1'],rocket_action_nonregression=b['rocket']['action']>=a['rocket']['action'],
        **{key+'_nonregression':b[key]['action']>=a[key]['action'] for key in ('witch','night_witch','furnace')})
    paired={}
    for control in ('r1e_corrected','ordinary_v5','ordinary_v6'):
        paired[control]={}
        for group,value in b.items():
            paired[control][group]={rep:{k:v-reports[control][group]['by_replay'][rep][k] for k,v in counts.items()} for rep,counts in value['by_replay'].items()}
    c.write(OUT/'all_replay_counts.json',reports);c.write(OUT/'paired_replay_counts.json',paired)
    summary={arm:{key:{k:v for k,v in counts.items() if k!='by_replay'} for key,counts in r.items()} for arm,r in reports.items()}
    c.write(HERE/'results_verified_v2.json',dict(complete=True,rows=len(ids),hashes=hashes,counts=summary,
        filters=filters,base_tensors_exact=True,head_differences=differences,preserved_failed_receipt_sha256=c.sha(checks/'l72-development7-independent.json'),completion_source_sha256=c.sha(Path(__file__)),continuation_point_filter_passed=all(filters.values()),late_action_delta=late_delta,late_rocket_action_delta=rocket_delta,card_delta=card_delta,
        replay_counts_sha256=c.sha(OUT/'all_replay_counts.json'),paired_sha256=c.sha(OUT/'paired_replay_counts.json'),
        developmental_only=True,untouched_generalization=False,deployment_accepted=False))
    check_active();print(c.json.dumps(filters));print('FROZEN_PROJECTILE_RECOUNT_V2_COMPLETE')

if __name__=='__main__':main()
