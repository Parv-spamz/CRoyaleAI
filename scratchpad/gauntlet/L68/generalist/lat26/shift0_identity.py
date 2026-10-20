"""Shift-0 identity proof: dataset_gen.replay_rows with the new build_replay (shift 0) vs the pre-shift builder
(87a7ff5 pipeline/dataset.py), every returned array compared, on N replays per corpus of gen_dataset_v1."""
import json, subprocess, sys, random
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from pipeline import dataset_gen as dg
from pipeline.tests.test_dataset_shift import ref_module, REPO

src = subprocess.run(["git", "-C", str(REPO), "show", "87a7ff5:pipeline/dataset.py"], capture_output=True,
                     text=True, check=True, encoding="utf-8").stdout
ref = ref_module(src)
meta = json.loads((REPO / "icebow/data/pipeline/gen_dataset_v1.json").read_text(encoding="utf-8"))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 50
rng = random.Random(0)
new_br = dg.build_replay
n_files = n_rows = 0
for c in meta["corpora"]:
    files = sorted((REPO / c).glob("replay_*.json"))
    for f in rng.sample(files, min(N, len(files))):
        dg.build_replay = new_br
        a = dg.replay_rows(str(f), 40, 20, 0)
        dg.build_replay = lambda *x, shift_ticks=0, **k: ref.build_replay(*x, **k)   # replay_rows passes shift_ticks=0
        b = dg.replay_rows(str(f), 40, 20)
        assert "error" not in a and "error" not in b, (f, a.get("error"), b.get("error"))
        assert a.keys() == b.keys()
        for k in a:
            if isinstance(a[k], np.ndarray):
                np.testing.assert_array_equal(a[k], b[k], err_msg=f"{f.name} {k}")
            else:
                assert a[k] == b[k], (f.name, k)
        n_files += 1; n_rows += len(a["sc"])
print(f"IDENTICAL: {n_files} replays, {n_rows} rows, all replay_rows arrays/keys/stats equal (shift 0 vs 87a7ff5)")
