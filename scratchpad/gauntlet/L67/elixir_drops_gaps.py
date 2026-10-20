"""Like elixir_drops.py, but also times each drop: pauses between plays per clip (for runs with no stdout log).

usage (from icebow/): python elixir_drops_gaps.py <label> <video.mp4> [more.mp4 ...]
Per clip: in-match seconds, drops, plays/min, median gap, longest gap, gaps > 10 s and > 15 s, share of in-match time
inside > 10 s gaps, seconds at 10 elixir. Then a TOTAL line for the label.
"""
import sys

import cv2

sys.path.insert(0, "src")
from clashrl.config import Config            # noqa: E402
from clashrl.states import GameState          # noqa: E402
from clashrl.vision import Vision             # noqa: E402

HZ = 5.0
label, paths = sys.argv[1], sys.argv[2:]
vision = Vision(Config.load())
T_secs = T_drops = T_g10 = T_g15 = 0
T_long = T_full = 0.0
all_gaps = []
for path in paths:
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, int(round(fps / HZ)))
    samples = []                                   # (seconds since first in-match frame, elixir)
    t0 = None
    for fi in range(0, n, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ok, fr = cap.read()
        if not ok:
            break
        if vision.detect_state(fr) != GameState.IN_MATCH:
            continue
        t = fi / fps
        t0 = t if t0 is None else t0
        try:
            samples.append((t - t0, float(vision.read_elixir(fr))))
        except Exception:                          # noqa: BLE001
            pass
    if len(samples) < 10:
        print(f"{path}: too few in-match samples")
        continue
    drop_t, last = [], samples[0][1]
    i = 0
    while i < len(samples) - 2:
        (ta, a), (tb, b), (_, c) = samples[i], samples[i + 1], samples[i + 2]
        if b <= last - 1 and c <= last - 1:        # a fall that holds for two samples
            drop_t.append(tb)
            last = min(b, c)
            i += 2
            continue
        last = a
        i += 1
    secs = samples[-1][0] - samples[0][0]
    marks = [samples[0][0]] + drop_t + [samples[-1][0]]
    gaps = [marks[k + 1] - marks[k] for k in range(len(marks) - 1)]
    full = sum(1 for _, e in samples if e >= 10) / HZ
    g10, g15 = sum(g > 10 for g in gaps), sum(g > 15 for g in gaps)
    long_t = sum(g for g in gaps if g > 10)
    name = path.replace("\\", "/").split("/")[-1]
    print(f"{name}: {secs:.0f} s, drops {len(drop_t)} = {len(drop_t) / max(1e-9, secs / 60):.1f}/min, median gap "
          f"{sorted(gaps)[len(gaps) // 2]:.1f}s, longest {max(gaps):.0f}s, >10s {g10}, >15s {g15}, "
          f"in >10s gaps {long_t / max(1e-9, secs):.0%}, at 10 elixir {full:.0f}s", flush=True)
    T_secs += secs; T_drops += len(drop_t); T_g10 += g10; T_g15 += g15; T_long += long_t; T_full += full
    all_gaps += gaps
if T_secs:
    m = T_secs / 60
    print(f"TOTAL {label}: {m:.1f} min, {T_drops / m:.1f} plays/min, median gap {sorted(all_gaps)[len(all_gaps) // 2]:.1f}s, "
          f">10s {T_g10 / m:.2f}/min, >15s {T_g15 / m:.2f}/min, in >10s gaps {T_long / T_secs:.0%}, "
          f"at 10 elixir {T_full / T_secs:.0%} of match time")
