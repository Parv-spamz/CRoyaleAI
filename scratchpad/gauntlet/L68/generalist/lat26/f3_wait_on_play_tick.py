"""F3 (pre-existing, count only): WAIT rows whose frame tick == an accepted play tick of the SAME side. Frames are
snapshotted before the tick's plays act, but the wait path treats that play as done (``<= t``) and its window
(t, ...] excludes it: such a row labels gate 0 on the exact state the side played from, with the post-play hand."""
import json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
REPO = Path(__file__).resolve().parents[5]
D = REPO / "icebow" / "data" / "pipeline"
for name in sys.argv[1:] or ["gen_dataset_v1"]:
    meta = json.loads((D / f"{name}.json").read_text(encoding="utf-8"))
    path = {}
    for c in meta["corpora"]:
        for f in sorted((REPO / c).glob("replay_*.json")):
            path.setdefault(f.name, f)
    z = np.load(D / f"{name}.npz", allow_pickle=False)
    tags, rep, side, tick, gate, v3 = z["tags"], z["rep"], z["side"], z["tick"], z["y_gate"], z["v3val"]
    w = np.where(gate == 0)[0]
    by_rep = defaultdict(list)
    for i in w:
        by_rep[int(rep[i])].append(i)
    hit = hit_v3 = 0
    for r, idx in by_rep.items():
        rec = json.loads(path[f"replay_{tags[r]}.json"].read_text(encoding="utf-8"))
        acc = {(int(e["side"]), int(e["tick"])) for e in rec["log"] if e.get("accepted") and "tick" in e}
        for i in idx:
            if (int(side[i]), int(tick[i])) in acc:
                hit += 1; hit_v3 += int(v3[i])
    print(f"{name}: wait rows {len(w):,d}; on an own accepted play tick {hit:,d} ({hit / len(w) * 100:.2f}%); "
          f"of them v3val {hit_v3:,d} (v3val wait rows {int(((gate == 0) & (v3 == 1)).sum()):,d})")
