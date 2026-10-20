"""Independent original-label/mask/scalar/per-replay recount of both final arms."""
from shared import *

def validate_prediction(a,ids,available):
    assert np.array_equal(a['ids'],ids) and len(np.unique(a['ids']))==len(ids)
    assert a['allowed'].dtype==bool and np.array_equal(a['allowed'],available)
    for k in ('gate','gate_logit','chosen_card','expert_cell','log_cell'):assert a[k].shape==(len(ids),)
    assert a['card_logits'].shape==(len(ids),4)
    assert np.isfinite(a['gate']).all() and ((a['gate']>=0)&(a['gate']<=1)).all()
    assert np.isfinite(a['gate_logit']).all() and not np.isnan(a['card_logits']).any() and not np.isposinf(a['card_logits']).any()
    for k in ('expert_cell','log_cell'):assert ((a[k]>=0)&(a[k]<2304)).all()

def main():
    check();assert not (HERE/'results_verified.json').exists()
    tv=read(HERE/'training_verified.json');ev=read(HERE/'evaluated.json');assert tv['complete'] and ev['complete']
    assert ev['training_verified_sha256']==sha(HERE/'training_verified.json')
    c.setup();ids=c.indices('development');s,meta=c.load_subset(c.DATA,ids);cv=meta['card_vocab']
    original=arrays(ROOT/'icebow/data/bench/match_adaptation_20261005/rows.npz');positions=np.searchsorted(original['ids'],ids)
    np.testing.assert_array_equal(original['ids'][positions],ids)
    for k in ('rep','side','tick','split','y_gate','y_card','y_xy','y_wait_card','y_crowns','y_cell','y_hand_pos'):
        np.testing.assert_array_equal(s[k],original[k][positions])
    sv=read(HERE.parent/'sequence_data/verified.json');assert sv['original_labels_exact'] and sv['all_windows_exact']
    assert sv['features_sha256']==sha(SEQ/'features.npz') and sv['audit_sha256']==sha(SEQ/'audit.npz')
    ns=prior.independent();controls=ns['controls']();ms,target,available=ns['independent_masks'](ids,s,cv)
    ms['defensive_sequence']=np.isin(ids,arrays(prior.DEFENSE)['defensive_development'])
    ms['defensive_rocket']=ms['defensive_sequence']&(s['y_gate']==1)&(s['y_card']==cv.index('rocket'))
    saved,expected_target=prior.masks(ids);np.testing.assert_array_equal(target,expected_target)
    for k,v in ms.items():np.testing.assert_array_equal(v,saved[k])
    extra={k:v for k,v in saved.items() if k not in ms};prior.extra_independent(ids,s,cv,extra);ms.update(extra)
    new,audit=audit_masks(ids,cv)
    # Independently materialize every descriptor slice, including excluded windows.
    az=arrays(SEQ/'audit.npz');fz=arrays(SEQ/'features.npz');ix={int(v):j for j,v in enumerate(az['ids'])}
    for j,oid in enumerate(ids):
        ai=ix[int(oid)];row=az['descriptors'][ai];q=fz['opp_hand_quality'][ai]
        for status in range(6):assert bool(new[f'retention_status_{status}'][j])==(int(row[0])==status)
        assert new['retention_truncated'][j]==bool(row[8]) and new['retention_complete_window'][j]==(not row[8])
        assert new['retention_enemy_revealed'][j]==bool(row[7])
        for key,col in [('hand_full',1),('hand_issue',2)]:assert new[key][j]==bool(q[col])
        assert new['hand_partial'][j]==(not q[1]) and new['hand_no_issue'][j]==(not q[2])
        for key,m in new.items():
            if key.startswith('retention_response_'):
                assert bool(m[j])==(row[0] in (4,5) and row[2]==cv.index(key[len('retention_response_'):]))
    ms.update(new);reports={};hashes={};breakdown={};spending={};negatives=0
    old=read(LOOP/'development_iteration_10/results_verified.json')
    for name,path in {**CONTROLS,**{a:OUT/a/'predictions.npz' for a in ARMS}}.items():
        a=arrays(path);validate_prediction(a,ids,available)
        if name in ARMS:
            assert sha(path)==ev['arms'][name]['cache_sha256']
            assert ev['arms'][name]['checkpoint_sha256']==tv['arms'][name]['checkpoint_sha256']==sha(OUT/name/'candidate.pt')
        else:assert sha(path)==old['hashes'][name]['cache']
        result=ns['independently_count'](s,a,cv,ms,target)
        if name in ARMS:assert result==ev['arms'][name]['counts']
        else:
            for group in saved:assert {k:v for k,v in result[group].items() if k!='by_replay'}==old['counts'][name][group]
        reports[name]=result;hashes[name]=dict(cache=sha(path))
        play=s['y_gate']==1;called=(a['gate']>.35)&a['allowed'].any(1)
        breakdown[name]={k:dict(correct_wait=int(np.count_nonzero(mask&~play&~called)),
            play_success=result[k]['action']-int(np.count_nonzero(mask&~play&~called))) for k,mask in ms.items()}
        future_spend=called&(a['chosen_card']==audit[:,2])&np.isin(audit[:,0],[4,5])
        spending[name]={k:dict(rows=int(mask.sum()),predicted_response_card_spends=int((future_spend&mask).sum()),
            by_replay={str(int(rep)):int((future_spend&mask&(s['rep']==rep)).sum()) for rep in np.unique(s['rep'][mask])})
            for k,mask in new.items()}
        if name in ARMS:
            fragment={k:v[:8].copy() for k,v in a.items()};fi=ids[:8];fa=available[:8];validate_prediction(fragment,fi,fa)
            for key,value in [('ids',-1),('gate',float('nan')),('gate_logit',float('inf')),('expert_cell',2304),('log_cell',-1)]:
                bad={k:v.copy() for k,v in fragment.items()};bad[key][0]=value
                try:validate_prediction(bad,fi,fa)
                except AssertionError:negatives+=1
                else:raise AssertionError('Bad prediction accepted')
            bad={k:v.copy() for k,v in fragment.items()};bad['allowed'][0,0]=~bad['allowed'][0,0]
            try:validate_prediction(bad,fi,fa)
            except AssertionError:negatives+=1
            else:raise AssertionError('Bad affordability accepted')
    assert controls==dict(positive=1,negative=4) and negatives==12
    candidate=reports['hand_belief_v5'];fs={name:prior.filters(reports[name],candidate) for name in ('ordinary_v5','hand_blind_control_v5')}
    paired={}
    for arm in ARMS:
        paired[arm]={}
        for control in ('r1e_corrected','ordinary_v5','hand_blind_control_v5'):
            if arm==control:continue
            paired[arm][control]={group:{rep:{k:v-reports[control][group]['by_replay'][rep][k] for k,v in val.items()}
                for rep,val in r['by_replay'].items()} for group,r in reports[arm].items()}
    write(OUT/'all_replay_counts.json',reports);write(OUT/'paired_replay_counts.json',paired);write(OUT/'response_spending.json',spending)
    compact={name:{k:{f:v for f,v in r.items() if f!='by_replay'} for k,r in report.items()} for name,report in reports.items()}
    loss={}
    for arm in ARMS:
        logs=[json.loads(x) for x in (OUT/arm/'train.jsonl').read_text().splitlines()]
        loss[arm]={window:dict(loss=float(np.mean([x['loss'] for x in subset])),
            **{k:float(np.mean([x['parts'][k] for x in subset])) for k in logs[0]['parts']})
            for window,subset in [('first256',logs[:256]),('last256',logs[-256:])]}
    write(HERE/'results_verified.json',dict(complete=True,rows=len(ids),counts=compact,hashes=hashes,filters=fs,
        continuation_passed=all(all(v.values()) for v in fs.values()),controls=dict(positive=3,negative=16),
        play_wait=breakdown,loss_means=loss,evaluated_sha256=sha(HERE/'evaluated.json'),
        paired_sha256=sha(OUT/'paired_replay_counts.json'),replay_counts_sha256=sha(OUT/'all_replay_counts.json'),
        response_spending_sha256=sha(OUT/'response_spending.json'),accepted=False,deployed=False))
    check();print(json.dumps(fs));print('HAND_LEARNING_RESULTS_VERIFIED')
if __name__=='__main__':main()
