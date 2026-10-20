"""Independent artifact recount and exclusion negative controls, without inference."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent


def digest(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def disjoint(rows,exposed):
    tags=set();groups=set()
    for r in rows:
        if r['tag'].lower() in exposed or r['tag'] in tags or r['signature'] in groups:
            raise ValueError('Exposed or duplicate group')
        tags.add(r['tag']);groups.add(r['signature'])
    return tags


def main():
    out=HERE/'discovery_diagnosis_verified.json'
    if out.exists():raise ValueError('Fresh verification output required')
    report=json.loads((HERE/'unused_hf_inventory.json').read_text())
    exposure=HERE/'historical_exposure_tags_v2.json'
    candidates=Path(report['candidates'])
    assert digest(exposure)==report['exposure_sha256']
    assert digest(candidates)==report['candidates_sha256']
    exposed=set(json.loads(exposure.read_text()))
    with candidates.open() as f:rows=[json.loads(line) for line in f]
    ids=disjoint(rows,exposed)
    strata=Counter(k for r in rows for k in r['strata'])
    assert len(ids)==report['unused_unique_command_groups'] and dict(strata)==report['strata']
    for bad in ([dict(rows[0],tag=next(iter(exposed)))],[rows[0],rows[0]]):
        try:disjoint(bad,exposed)
        except ValueError:pass
        else:raise AssertionError('Exclusion negative control did not fail')
    reconstruction=json.loads((HERE/'candidate_reconstruction_inventory.json').read_text())
    exact={r['tag'] for r in rows if 'exact_icebow' in r['strata']}
    assert exact=={r['tag'] for r in reconstruction['candidates']}
    statuses=Counter(r['status'] for r in reconstruction['candidates'])
    assert dict(statuses)==reconstruction['status']
    diagnosis=HERE/'train_spawner_diagnosis.json'
    d=json.loads(diagnosis.read_text())
    cache=HERE/'train_spawner_predictions.npz'
    assert digest(cache)==d['predictions_sha256']
    with np.load(cache) as z:
        assert (z['split']==0).all() and len(z['ids'])==d['rows'] and len(np.unique(z['ids']))==d['rows']
        with np.load(ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz') as source:
            for k in ('split','rep','y_card','y_gate','y_xy'):
                assert np.array_equal(z[k],source[k][z['ids']]),k
        play=z['y_gate']==1;any_legal=z['allowed'].any(1)
        actions={}
        for arm,summaries in d['summaries'].items():
            cell=z[arm+'__expert_cell']
            dist=np.hypot((cell%36/36-z['y_xy'][:,0])*18,(cell//36/64-z['y_xy'][:,1])*32)
            called=(z[arm+'__gate']>.35)&any_legal
            correct=(z[arm+'__chosen_card']==z['y_card'])&any_legal
            action=(play&called&correct&(dist<=1))|(~play&~called)
            assert np.array_equal(action,z[arm+'__action'])
            actions[arm]=action
            for name,s in summaries.items():
                mask=z[name+'__mask'];family=name.rsplit('_',1)[0]
                assert len(np.unique(z['rep'][mask]))==int(mask.sum())==s['rows']
                independent=dict(rows=int(mask.sum()),replays=len(np.unique(z['rep'][mask])),
                    changed_rows=int((mask&z['changed_rows']).sum()),
                    corrected_parent_present=int((mask&z[family+'__parent']).sum()),
                    called=int(called[mask].sum()),card_correct=int(correct[mask&play].sum()),
                    forced_aim_within_one=int(((dist<=1)&mask&play).sum()),action_correct=int(action[mask].sum()))
                assert independent==s,(arm,name)
        for pair,counts in d['paired_action_flips'].items():
            a,b=pair.split('_vs_')
            for name,summary in counts.items():
                m=z[name+'__mask'];aa=actions[a];bb=actions[b]
                assert summary==dict(rows=int(m.sum()),gains=int((m&aa&~bb).sum()),losses=int((m&~aa&bb).sum()))
    result=dict(candidate_groups=len(ids),candidate_strata=dict(strata),
        reconstruction_status=dict(statuses),training_rows=d['rows'],models_recounted=len(d['summaries']),
        exclusion_negative_controls=2,confirmation_qualified=False,
        bound_reports={p.name:digest(p) for p in (HERE/'unused_hf_inventory.json',
            HERE/'candidate_reconstruction_inventory.json',diagnosis)},verifier_sha256=digest(__file__))
    out.write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
    print('DISCOVERY_DIAGNOSIS_INDEPENDENTLY_VERIFIED')


if __name__=='__main__':main()
