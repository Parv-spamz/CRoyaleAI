"""Independently reproduce context memberships, split counts and provenance."""
from collections import Counter
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import numpy as np

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from pipeline.rocket_teaching import sha
from pipeline.train_rocket_curriculum import take
from pipeline.expert_context import probabilities, MIXTURES


def main():
    folder=ROOT/'icebow/data/bench/context_teaching_20261005'
    source=ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
    rocket=ROOT/'icebow/data/bench/rocket_teaching_20261004'
    audit=ROOT/'scratchpad/gauntlet/L71/xbow_support/audit.json'
    m=json.loads((folder/'manifest.json').read_text())
    assert m['source_dataset_sha256']==sha(source)
    assert m['cohorts_sha256']==sha(folder/'cohorts.npz')
    assert m['rocket_manifest_sha256']==sha(rocket/'manifest.json')
    assert m['xbow_audit_sha256']==sha(audit)
    assert m['trainable'] and m['public_only'] and m['training_split_only']
    with np.load(source) as z:
        a={k:z[k] for k in ('split','rep','tags','tick','side','y_gate','y_card')}
        meta=json.loads(str(z['meta']))
    with np.load(folder/'cohorts.npz') as z:
        c={k:z[k] for k in z.files}
    with np.load(rocket/'cohorts.npz') as z:
        for key in z.files:
            np.testing.assert_array_equal(c[key],z[key])
    ids=np.flatnonzero(c['pool'])
    with ZipFile(source) as z:
        shots=take(z,'projectiles',ids)
    enemy=(shots[:,:,0]==meta['card_vocab'].index('goblin-barrel')) & (shots[:,:,1]==1)
    np.testing.assert_array_equal(c['barrel'][ids],enemy.sum(1)>=1)
    np.testing.assert_array_equal(c['barrel_multiple'][ids],enemy.sum(1)>=2)
    # Rebuild exact (tag, side, interval) membership independently of builder masks.
    events={}
    for row in json.loads(audit.read_text())['pro_rows']:
        if row['linked']:
            events.setdefault((row['tag'],row['bow']['side']),[]).append(row)
    for i in ids:
        rows=events.get((str(a['tags'][a['rep'][i]]),int(a['side'][i])),[])
        current=[r for r in rows if r['birth']<=a['tick'][i]<=r['last_seen']]
        assert c['xbow'][i]==bool(current), int(i)
        assert c['xbow_no_lifetime_target'][i]==any(not r['crown_reachable'] and not r['defensive_contact'] for r in current),int(i)
    assert not set(a['rep'][c['pool'] & (a['split']==0)]) & set(a['rep'][c['pool'] & (a['split']!=0)])
    for key,mask in c.items():
        assert mask.dtype==bool and mask.shape==a['split'].shape and not (mask & ~c['pool']).any()
        for name,split in [('train',0),('validation',1)]:
            selected=mask & (a['split']==split)
            play=selected & (a['y_gate']==1)
            measured=dict(rows=int(selected.sum()),plays=int(play.sum()),waits=int((selected & (a['y_gate']==0)).sum()),
                          cards=dict(Counter(meta['card_vocab'][int(v)] for v in a['y_card'][play])))
            assert m['counts'][key][name]==measured,(key,name)
    for arm in MIXTURES:
        p=probabilities(c,a['split'],arm)
        assert p[a['split']!=0].sum()==0 and abs(p.sum()-1)<1e-12
    print(json.dumps({k:m['counts'][k] for k in ('barrel','xbow')}))
    print('EXPERT_CONTEXT_INDEPENDENT_VERIFY_PASS')


if __name__=='__main__':
    main()
