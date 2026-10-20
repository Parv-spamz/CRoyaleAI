"""Expert-only rare-context cohorts; no new targets or live tactical rules."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from pipeline.rocket_teaching import sha
from pipeline.train_rocket_curriculum import take

SOURCE_DATA = ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
ROCKET = ROOT/'icebow/data/bench/rocket_teaching_20261004'
XBOW = ROOT/'scratchpad/gauntlet/L71/xbow_support/audit.json'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise ValueError('Fresh output directory required')
    rocket = json.loads((ROCKET/'manifest.json').read_text())
    assert rocket['dataset_sha256'] == sha(SOURCE_DATA) and rocket['trainable']
    assert rocket['cohorts_sha256'] == sha(ROCKET/'cohorts.npz')
    with np.load(ROCKET/'cohorts.npz') as z:
        cohorts = {k: z[k] for k in z.files}
    with np.load(SOURCE_DATA) as z:
        meta = json.loads(str(z['meta']))
        values = {k: z[k] for k in ('split', 'rep', 'tags', 'tick', 'side', 'y_gate', 'y_card')}
    ids = np.flatnonzero(cohorts['pool'])
    with ZipFile(SOURCE_DATA) as archive:
        projectiles = take(archive, 'projectiles', ids)
    barrel_id = meta['card_vocab'].index('goblin-barrel')
    seen = (projectiles[..., 0] == barrel_id) & (projectiles[..., 1] == 1)
    cohorts['barrel'] = np.zeros(len(cohorts['pool']), bool)
    cohorts['barrel'][ids] = seen.any(1)
    cohorts['barrel_multiple'] = np.zeros(len(cohorts['pool']), bool)
    cohorts['barrel_multiple'][ids] = seen.sum(1) > 1
    cohorts['xbow'] = np.zeros(len(cohorts['pool']), bool)
    cohorts['xbow_no_lifetime_target'] = np.zeros(len(cohorts['pool']), bool)
    reps = {str(tag): i for i, tag in enumerate(values['tags'])}
    audit = json.loads(XBOW.read_text())
    for row in audit['pro_rows']:
        if not row['linked']:
            continue
        mask = (cohorts['pool'] & (values['rep'] == reps[row['tag']]) &
                (values['side'] == row['bow']['side']) & (values['tick'] >= row['birth']) &
                (values['tick'] <= row['last_seen']))
        cohorts['xbow'] |= mask
        if not row['crown_reachable'] and not row['defensive_contact']:
            cohorts['xbow_no_lifetime_target'] |= mask
    counts = {}
    for name, mask in cohorts.items():
        assert len(mask) == len(values['split']) and not (mask & ~cohorts['pool']).any()
        counts[name] = {}
        for split, code in (('train', 0), ('validation', 1)):
            rows = mask & (values['split'] == code)
            play = rows & (values['y_gate'] == 1)
            counts[name][split] = dict(rows=int(rows.sum()), plays=int(play.sum()),
                waits=int((rows & (values['y_gate'] == 0)).sum()),
                cards=dict(Counter(meta['card_vocab'][int(i)] for i in values['y_card'][play])))
    assert counts['barrel']['train']['rows'] > 0 and counts['xbow']['train']['rows'] > 0
    assert not set(values['rep'][cohorts['pool'] & (values['split'] == 0)]) & set(values['rep'][cohorts['pool'] & (values['split'] != 0)])
    args.out.mkdir(parents=True)
    np.savez_compressed(args.out/'cohorts.npz', **cohorts)
    report = dict(schema=1, trainable=True, source_dataset_sha256=sha(SOURCE_DATA),
        rocket_manifest_sha256=sha(ROCKET/'manifest.json'), xbow_audit_sha256=sha(XBOW),
        cohorts_sha256=sha(args.out/'cohorts.npz'), builder_sha256=sha(__file__), counts=counts,
        targets='all original expert targets unchanged', public_only=True, training_split_only=True,
        version5_binding='Requires independent unchanged-member verification before binding to corrected dataset',
        limitations=['X-Bow lifetime and future contact labels are offline cohort annotations, not policy inputs.',
                     'The X-Bow cohort includes useful defence, crown reach and low-value placements.',
                     'The Barrel cohort includes both single and paired flights, WAITs and all expert cards.'])
    (args.out/'manifest.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: counts[k] for k in ('xbow', 'barrel', 'barrel_multiple')}))
    print('EXPERT_CONTEXT_COHORTS_BUILT')


if __name__ == '__main__':
    main()
