"""L68 ranking check: does RoyaleSim order v6lat_s0 / v6aug_s1 the way the real engine does, on the SAME opponents?

    python3 scratchpad/gauntlet/L68/rank/score.py
Win = 1, draw = 0.5, loss = 0. Paired by ghost tag; only tags present in every compared run count.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
L67 = HERE.parents[1] / "L67" / "e1"


def load(dirs):
    out = {}
    for d in dirs:
        for f in Path(d).glob("**/matches.jsonl"):
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    out[r["tag"]] = {"win": 1.0, "draw": 0.5, "loss": 0.0}[r["outcome"]]
    return out


royale = {ck: load(HERE.glob(f"{ck}_sh*")) for ck in ("v6lat_s0", "v6aug_s1")}
real = {"v6lat_s0": load([L67 / "baseline_k0"]), "v6aug_s1": load([L67 / "attrib" / "e2_v6aug_s1_tau027"])}


def rate(d, tags):
    return f"{100 * sum(d[t] for t in tags) / len(tags):.1f}% (n={len(tags)})" if tags else "n=0"


both_royale = sorted(set(royale["v6lat_s0"]) & set(royale["v6aug_s1"]))
print("RoyaleSim, all playable:   v6lat", rate(royale["v6lat_s0"], both_royale), " v6aug", rate(royale["v6aug_s1"], both_royale))
four = [t for t in both_royale if t in real["v6lat_s0"] and t in real["v6aug_s1"]]
print("same tags, both engines:   RoyaleSim v6lat", rate(royale["v6lat_s0"], four), "v6aug", rate(royale["v6aug_s1"], four))
print("                           real      v6lat", rate(real["v6lat_s0"], four), "v6aug", rate(real["v6aug_s1"], four))
for ck in ("v6lat_s0", "v6aug_s1"):
    tags = [t for t in royale[ck] if t in real[ck]]
    agree = sum(royale[ck][t] == real[ck][t] for t in tags)
    print(f"{ck}: per-opponent outcome agreement RoyaleSim vs real {agree}/{len(tags)}"
          f" | real {rate(real[ck], tags)} vs RoyaleSim {rate(royale[ck], tags)}")
d = [royale["v6aug_s1"][t] - royale["v6lat_s0"][t] for t in both_royale]
print(f"RoyaleSim paired v6aug - v6lat: {100 * sum(d) / max(len(d), 1):+.1f} pp; "
      f"v6aug better on {sum(x > 0 for x in d)}, worse on {sum(x < 0 for x in d)}, same {sum(x == 0 for x in d)}")
