"""gen_dataset_v1 vs gen_dataset_v1_lat26: row counts, drops (overall + icebow deck-sides), offset distribution."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from pipeline.obs_contract import load_deck
from pipeline import vocab as V

D = Path(__file__).resolve().parents[5] / "icebow" / "data" / "pipeline"
ice = sorted(V.base_key(c).replace("_", "-") for c in load_deck("icebow").cards)
out = {}
for name in ("gen_dataset_v1", "gen_dataset_v1_lat26"):
    z = np.load(D / f"{name}.npz", allow_pickle=False)
    meta = json.loads(str(z["meta"]))
    vocab = meta["card_vocab"]
    ice_ids = np.asarray(sorted(vocab.index(c) for c in ice))
    g, sp, v3, dc = z["y_gate"], z["split"], z["v3val"], z["deck_card"]
    isice = (np.sort(dc, 1) == ice_ids).all(1)
    p = g == 1
    out[name] = {"rows": int(len(g)), "play": int(p.sum()), "wait": int((~p).sum()), "val": int((sp == 1).sum()),
                 "val_play": int((p & (sp == 1)).sum()), "v3val": int(v3.sum()), "v3val_play": int((p & (v3 == 1)).sum()),
                 "icebow_play": int((p & isice).sum()), "icebow_wait": int((~p & isice).sum()),
                 "replays": meta["replays"], "decks": len(meta["decks"]), "card_vocab": len(vocab) - 1,
                 "vocab_equal_check": vocab}
    out[name]["stats"] = {k: v for k, v in meta["stats"].items() if k != "unmapped"}
a, b = out["gen_dataset_v1"], out["gen_dataset_v1_lat26"]
print("vocab identical:", a.pop("vocab_equal_check") == b.pop("vocab_equal_check"))
for k in ("rows", "play", "wait", "val", "val_play", "v3val", "v3val_play", "icebow_play", "icebow_wait", "replays", "decks", "card_vocab"):
    print(f"{k:12s} v1 {a[k]:>10,d}  lat26 {b[k]:>10,d}  delta {b[k] - a[k]:>+10,d} ({(b[k] - a[k]) / max(1, a[k]) * 100:+.2f}%)")
st = b["stats"]
drops = {k: v for k, v in st.items() if k in ("shift_no_frame", "shift_no_hand", "shift_drop_combo")}
cand = st["play_rows"] + sum(drops.values())
print("drops:", drops, f"of {cand:,d} candidate play rows -> {sum(drops.values()) / cand * 100:.2f}%",
      f"(combo {drops.get('shift_drop_combo', 0) / cand * 100:.2f}%)")
print(f"icebow deck-sides: play rows {a['icebow_play']:,d} -> {b['icebow_play']:,d}, dropped "
      f"{(a['icebow_play'] - b['icebow_play']) / a['icebow_play'] * 100:.2f}%")
off = {int(k.split(":")[1]): v for k, v in st.items() if k.startswith("shift_off:")}
n = sum(off.values())
vals = np.repeat(list(off), list(off.values()))
print(f"offset (ticks) n={n:,d} min {vals.min()} max {vals.max()} mean {vals.mean():.2f} median {np.median(vals):.0f}")
print("offset histogram:", dict(sorted(off.items())))
print("other stat deltas:", {k: (a['stats'].get(k), st.get(k)) for k in sorted(set(a['stats']) | set(st))
                              if not k.startswith("shift_") and a['stats'].get(k) != st.get(k)})
