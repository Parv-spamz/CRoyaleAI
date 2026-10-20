"""Independent existing expert-label counts and paired-control verdicts; no inference."""
from shared import *
def filters(a,b):
    f=dict(rocket_aim_material=(b['rocket']['aim1']-a['rocket']['aim1'])/a['rocket']['rows']>=.05,
        rocket_action_material=(b['rocket']['action']-a['rocket']['action'])/a['rocket']['rows']>=.02,
        late_rocket_material=(b['rocket_late_overtime_clock']['action']-a['rocket_late_overtime_clock']['action'])/a['rocket_late_overtime_clock']['rows']>=.02,
        general_card_noninferior=(b['all']['card']-a['all']['card'])/a['all']['play']>=-.005,
        barrel_correct_nonregression=b['barrel_pro']['log_correct']>=a['barrel_pro']['log_correct'],
        barrel_wrong_nonregression=b['barrel_pro']['log_wrong']<=a['barrel_pro']['log_wrong'])
    for key in ('witch','night_witch','furnace','defensive_sequence','phase_late_overtime_clock'):f[key+'_nonregression']=b[key]['action']>=a[key]['action']
    return f
def main():
    cutoff();assert not (HERE/'results_verified.json').exists();p=check();trained=read(HERE/'trained.json');tv=read(HERE/'training_verified.json');ev=read(HERE/'evaluated.json')
    assert tv['complete'] and tv['games']==2048 and tv['optimizer_steps']==512 and tv['controls']==dict(positive=32,negative=17)
    assert tv['trained_sha256']==sha(HERE/'trained.json') and ev['complete']
    ids=c.indices('development');sub,meta=c.load_subset(c.DATA,ids);cv=meta['card_vocab'];ms,target=masks(ids)
    count=independent_counter();reports={};hashes={}
    locs={'r1e_corrected':c.OUT/'r1e_corrected_eval/predictions.npz','ordinary_v5':c.OUT/'ordinary_v5_eval_v2/predictions.npz',**{a:OUT/a/'predictions.npz' for a in ARMS}}
    reference=read(HERE.parent/'development_iteration_7/results_verified_v2.json')
    for arm,path in locs.items():
        a=arrays(path);assert np.array_equal(a.pop('ids'),ids)
        if arm not in ARMS:assert sha(path)==reference['hashes'][arm]['cache']
        else:
            ee=read(HERE/(arm+'_evaluated.json'));assert ev['arms'][arm]==sha(HERE/(arm+'_evaluated.json')) and ee['cache_sha256']==sha(path)
            assert ee['checkpoint_sha256']==trained['arms'][arm]['checkpoint_sha256']
        reports[arm]=count(sub,a,cv,ms,target);hashes[arm]=dict(cache=sha(path))
        if arm in ARMS:assert reports[arm]==ee['counts']
    verdicts={};paired={}
    for arm in ARMS:
        controls=['ordinary_v5']+([ARMS[0]] if arm==ARMS[1] else [])
        fs={control:filters(reports[control],reports[arm]) for control in controls}
        verdicts[arm]=dict(filters=fs,continuation_passed=all(all(x.values()) for x in fs.values()))
        paired[arm]={control:{group:{rep:{key:value-reports[control][group]['by_replay'][rep][key] for key,value in vals.items()}
            for rep,vals in groupvals['by_replay'].items()} for group,groupvals in reports[arm].items()} for control in controls+['r1e_corrected']}
    write(OUT/'all_replay_counts.json',reports);write(OUT/'paired_replay_counts.json',paired)
    summary={arm:{group:{k:v for k,v in val.items() if k!='by_replay'} for group,val in groups.items()} for arm,groups in reports.items()}
    write(HERE/'results_verified.json',dict(complete=True,rows=len(ids),hashes=hashes,counts=summary,verdicts=verdicts,
        training_verified_sha256=sha(HERE/'training_verified.json'),paired_sha256=sha(OUT/'paired_replay_counts.json'),replay_counts_sha256=sha(OUT/'all_replay_counts.json'),
        checkpoints=trained['arms'],developmental_only=True,deployment_accepted=False))
    check();print(json.dumps(verdicts));print('LATE_CURRICULUM_RESULTS_VERIFIED')
if __name__=='__main__':main()
