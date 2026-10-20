"""Prepare historical expert development rows; no model loading or optimization."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pipeline.expert_context import load_contexts

SOURCE = ROOT / 'icebow/data/pipeline/gen_dataset_v31_public.npz'
DATA = ROOT / 'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz'
CORRECTION = DATA.parent / 'manifest.json'
CONTEXT = ROOT / 'icebow/data/bench/context_teaching_20261005'
INIT = ROOT / 'icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt'
OUT = ROOT / 'icebow/data/bench/development_iteration_1_20261005/indices.npz'
SALT = 'clashbot-l72-development-1-20261005:'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    report = HERE / 'prepared.json'
    if report.exists() or OUT.exists():
        raise ValueError('Fresh preparation required; preserve existing artifacts')
    cohorts, _, _, binding = load_contexts(CONTEXT, DATA, SOURCE, CORRECTION)
    with np.load(DATA, allow_pickle=False) as z:
        split, rep, tags, gates = z['split'], z['rep'], z['tags'].astype(str), z['y_gate']
    ids = np.flatnonzero(cohorts['pool'] & (split == 0))
    assert len(ids) == 268718
    selected_tags = set(tags[rep[ids]])
    reservation_path = HERE.parent / 'replay_reservation.json'
    reservation = json.loads(reservation_path.read_text())
    reserved_path = Path(reservation['reservation_file'])
    assert sha(reserved_path) == reservation['reservation_sha256']
    with reserved_path.open() as stream:
        reserved = {json.loads(line)['tag'].lower() for line in stream}
    assert not {t.lower() for t in selected_tags} & reserved
    bucket = np.array([int.from_bytes(hashlib.sha256((SALT + t).encode()).digest()[:8], 'big') % 5 for t in tags])
    train = ids[bucket[rep[ids]] != 0]
    development = ids[bucket[rep[ids]] == 0]
    assert len(train) and len(development)
    assert not set(rep[train]) & set(rep[development])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT, train=train, development=development)
    counts = {}
    for name, rows in [('training', train), ('development', development)]:
        plays = int((gates[rows] > .5).sum())
        counts[name] = dict(rows=len(rows), replays=len(set(rep[rows])), plays=plays, waits=len(rows)-plays)
    sources = [SOURCE, DATA, CORRECTION, CONTEXT/'manifest.json', CONTEXT/'cohorts.npz',
               INIT, reservation_path, reserved_path, HERE/'PLAN.md', Path(__file__),
               HERE.parent/'DEVELOPMENT_AMENDMENT.md', HERE.parent/'defence_crosswalk_verified.json']
    result = dict(complete=True, training_launched=False, optimizer_updates=0,
                  optimizer_allowed=False, next_gate='D3 trainer/metric manifest and smoke',
                  exposure='Historical split0 expert rows; R1e parent has seen both inner subsets. Not an untouched test.',
                  source_binding=binding, salt=SALT, counts=counts, ordinary_rows=len(ids),
                  excluded_original_pool_validation=int((cohorts['pool'] & (split != 0)).sum()),
                  reserved_groups_checked=len(reserved), reserved_overlap=0,
                  indices=str(OUT.relative_to(ROOT)), indices_sha256=sha(OUT),
                  sources={str(p.relative_to(ROOT)):sha(p) for p in sources},
                  assignment={t:('development' if int.from_bytes(hashlib.sha256((SALT+t).encode()).digest()[:8], 'big')%5==0 else 'training') for t in sorted(selected_tags)})
    report.write_text(json.dumps(result, indent=2))
    print(json.dumps(counts))
    print('DEVELOPMENT_1_DATA_PREPARED')


if __name__ == '__main__':
    main()
