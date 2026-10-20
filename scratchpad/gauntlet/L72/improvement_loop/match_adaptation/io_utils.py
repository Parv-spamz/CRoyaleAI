"""IO and frozen membership only. No model imports or tactical logic."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
import numpy as np

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'development_iteration_1'
OUT = ROOT / 'icebow/data/bench/match_adaptation_20261005'
DATA = ROOT / 'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz'
ORIGINAL = ROOT / 'icebow/data/pipeline/gen_dataset_v31_public.npz'
INDEX = ROOT / 'icebow/data/bench/development_iteration_1_20261005/indices.npz'
LABELS = ROOT / '.foreman/codex_autopilot/runs/public_labels_full_reconstructed/labels.jsonl'
MANIFEST = LABELS.with_name('manifest.json')
FIELDS = 'rep side tick split y_gate y_card y_xy y_wait_card y_wait_dt y_crowns y_cell y_hand_pos sc'.split()

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def write(p, value):
    Path(p).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')

def take(archive, name, ids):
    with archive.open(name+'.npy') as f:
        ver=np.lib.format.read_magic(f)
        shape,fort,dtype=(np.lib.format.read_array_header_1_0(f) if ver==(1,0) else np.lib.format.read_array_header_2_0(f))
        assert not fort and not dtype.hasobject
        width=int(np.prod(shape[1:]))*dtype.itemsize
        out=np.empty((len(ids),)+shape[1:],dtype)
        step=max(1,(16<<20)//width)
        for lo in range(0,shape[0],step):
            count=min(step,shape[0]-lo);buf=f.read(count*width)
            assert len(buf)==count*width
            a,b=np.searchsorted(ids,[lo,lo+count])
            if b>a:out[a:b]=np.frombuffer(buf,dtype).reshape((count,)+shape[1:])[ids[a:b]-lo]
        return out

def load_rows():
    with np.load(OUT/'rows.npz') as z:
        return {k:z[k] for k in z.files}

def check_binding():
    binding=read(HERE/'prepared.json')
    for name,h in binding['inputs'].items():
        assert sha(ROOT/name)==h, name
    assert sha(OUT/'rows.npz')==binding['rows_sha256']
    return binding
