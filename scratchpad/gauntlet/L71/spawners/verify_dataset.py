"""Independent archive/target/split and changed-column verification."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from pipeline import vocab
from pipeline.rocket_teaching import sha
from body_identity import FAMILIES


def digest(z, name):
    h = hashlib.sha256()
    with z.open(name) as f:
        for block in iter(lambda: f.read(16 << 20), b''):
            h.update(block)
    return h.hexdigest()


def header(f):
    version = np.lib.format.read_magic(f)
    return np.lib.format.read_array_header_1_0(f) if version == (1, 0) else np.lib.format.read_array_header_2_0(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('directory', type=Path)
    ap.add_argument('--allow-smoke', action='store_true')
    args = ap.parse_args()
    manifest = json.loads((args.directory/'manifest.json').read_text())
    assert manifest['trainable'] or args.allow_smoke
    old = ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
    new = args.directory/'gen_dataset_v5_public.npz'
    assert sha(old) == manifest['hashes']['dataset']
    assert sha(new) == manifest['output_sha256']
    changes = []
    with ZipFile(old) as a, ZipFile(new) as b:
        assert set(a.namelist()) == set(b.namelist())
        modified = {'tok.npy', 'unit_form.npy', 'meta.npy'}
        for name in set(a.namelist()) - modified:
            assert digest(a, name) == digest(b, name) == manifest['preserved_members_sha256'][name], name
        with a.open('tok.npy') as af, b.open('tok.npy') as bf:
            ah, bh = header(af), header(bf)
            assert ah == bh
            shape, fortran, dtype = ah
            assert not fortran and shape[1] == 14
            for lo in range(0, shape[0], 50000):
                n = min(50000, shape[0]-lo)
                aa = np.frombuffer(af.read(n*14*dtype.itemsize), dtype).reshape(n, 14)
                bb = np.frombuffer(bf.read(n*14*dtype.itemsize), dtype).reshape(n, 14)
                assert np.array_equal(aa[:, 1:], bb[:, 1:]), lo
                changed = np.flatnonzero(aa[:, 0] != bb[:, 0])
                assert np.isin(aa[changed, 0], [vocab.unit_id(k) for k in FAMILIES]).all()
                changes.extend((changed+lo).tolist())
    with np.load(old) as a, np.load(new) as b:
        old_forms, new_forms = a['unit_form'], b['unit_form']
        class_changes = np.asarray(changes)
        form_changes = np.flatnonzero(old_forms != new_forms)
        assert np.isin(form_changes, class_changes).all()
        assert (new_forms[class_changes] == 0).all()
        assert len(class_changes) == manifest['stats']['changed_tokens']
        assert len(form_changes) == manifest['stats']['changed_forms']
        changed_rows = np.unique(np.searchsorted(a['off'], class_changes, side='right')-1)
        np.testing.assert_array_equal(changed_rows, np.sort(np.load(args.directory/'changed_rows.npy')))
        assert len(changed_rows) == manifest['stats']['changed_rows']
        before, after = json.loads(str(a['meta'])), json.loads(str(b['meta']))
        assert after['feature_version'] == 5 and after['trainable'] == manifest['trainable']
        assert before['card_vocab'] == after['card_vocab'] and before['decks'] == after['decks']
    if manifest['trainable']:
        assert manifest['stats']['reproduced_rows'] == manifest['expected_affected_rows']
    print(json.dumps(dict(changed_rows=len(changed_rows), changed_tokens=len(class_changes),
                          changed_forms=len(form_changes), trainable=manifest['trainable'])))
    print('SPAWNER_DATASET_VERIFY_PASS')


if __name__ == '__main__':
    main()
