"""Turn the live outcome ledger into the project's first live winrate, with a CI.

Usage:  python scratchpad/gauntlet/L67/score_live_baseline.py [ledger.jsonl] [stdout.log]
        (with no arguments it picks the newest of each)

Reads  icebow/data/live_matches_<session>.jsonl   (written by play.py's L67cb ledger hook)
and    scratchpad/gauntlet/L67/live_baseline_*.log (the run's stdout)

Reports winrate with a WILSON 95% interval -- not a normal approximation, which misbehaves at
small n and near 0/1 -- plus the behaviour counters that speak to the owner's four complaints.

INTEGRITY CHECK, and it matters: the ledger row count must equal the number of IN_MATCH
transitions in the stdout log. If they disagree, matches were dropped and the DENOMINATOR IS
WRONG -- a silently wrong denominator is how a bad winrate looks like a good one.
"""
import json, math, pathlib, re, sys
from collections import Counter

REPO = pathlib.Path(r"C:\Users\benpe\ClashBot")


def newest(pattern_dir, pattern):
    hits = sorted(pattern_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def wilson(k, n, z=1.96):
    """Wilson score interval -- correct at small n, unlike the normal approximation."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, centre - half), min(1.0, centre + half)


def main():
    # POOL EVERY LEDGER FILE. A run that is interrupted and relaunched writes a NEW file, so
    # scoring "the newest" would silently drop the earlier matches. A wrong denominator is exactly
    # the failure the integrity check below exists to catch -- do not reintroduce it here.
    if len(sys.argv) > 1:
        ledgers = [pathlib.Path(sys.argv[1])]
    else:
        ledgers = sorted((REPO / "icebow" / "data").glob("live_matches_*.jsonl"), key=lambda p: p.stat().st_mtime)
    ledgers = [p for p in ledgers if p.exists()]
    if not ledgers:
        print("NO LEDGER FOUND -- the run produced no match rows.")
        return 1

    rows, per_file = [], []
    for p in ledgers:
        rs = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        per_file.append((p.name, len(rs)))
        rows.extend(rs)

    # Pool only rows sharing the SAME (ckpt, tau). Mixing configurations would be two different
    # experiments reported as one number.
    cfgs = Counter((r.get("ckpt"), r.get("tau")) for r in rows)
    if len(cfgs) > 1:
        keep = cfgs.most_common(1)[0][0]
        print(f"*** {len(cfgs)} CONFIGURATIONS PRESENT -- scoring only ckpt={keep[0]} tau={keep[1]} ***")
        for cfg_key, cnt in cfgs.items():
            print(f"      {cfg_key}  n={cnt}{'   <-- scored' if cfg_key == keep else '   <-- EXCLUDED'}")
        rows = [r for r in rows if (r.get("ckpt"), r.get("tau")) == keep]

    logfiles = ([pathlib.Path(sys.argv[2])] if len(sys.argv) > 2
                else sorted((REPO / "scratchpad" / "gauntlet" / "L67").glob("live_baseline_*.log")))
    logfiles = [p for p in logfiles if p.exists()]
    n = len(rows)
    c = Counter(r["outcome"] for r in rows)
    w, ll, d = c.get("win", 0), c.get("loss", 0), c.get("draw", 0)
    p, lo, hi = wilson(w, n)

    print(f"LEDGER  {len(per_file)} file(s), matches={n}")
    for fname, cnt in per_file:
        print(f"    {fname}  {cnt}")
    print(f"  W {w}   L {ll}   D {d}")
    print(f"  WINRATE {p:.1%}   Wilson 95% CI [{lo:.1%}, {hi:.1%}]   (+-{(hi - lo) / 2:.1%})")

    # KNOWN INSTRUMENT LIMIT -- report it, do not hide it behind one number.
    # The ledger reads CROWNS from the tower-destruction latch. It cannot see a 0-0 timeout, which
    # Clash Royale decides on TOWER DAMAGE, so those land here as "draw". Draws sit in the
    # denominator, so a pile of 0-0 finishes biases the headline winrate DOWNWARD. `outcome.py`
    # (read_scoreboard, validated 11/11 offline) reads the real results screen and would resolve
    # them; it is not wired into play.py. Until it is, report both numbers.
    zero = [r for r in rows if r["crowns_for"] == 0 and r["crowns_against"] == 0]
    decided = [r for r in rows if not (r["crowns_for"] == 0 and r["crowns_against"] == 0)]
    if decided:
        dw = sum(1 for r in decided if r["outcome"] == "win")
        dp, dlo, dhi = wilson(dw, len(decided))
        print(f"  crowns-DECIDED only (n={len(decided)}): {dp:.1%}  CI [{dlo:.1%}, {dhi:.1%}]")
    print(f"  0-0 finishes (outcome UNRESOLVABLE by this instrument): {len(zero)}"
          f"{'  <-- the true winrate lies between the two figures above' if zero else ''}")
    if n:
        secs = [r["seconds"] for r in rows if r.get("seconds")]
        if secs:
            print(f"  match length: median {sorted(secs)[len(secs) // 2]:.0f}s   total {sum(secs) / 3600:.2f} h")
        print(f"  crowns for/against: {sum(r['crowns_for'] for r in rows)} / {sum(r['crowns_against'] for r in rows)}")
        print(f"  3-crown finishes recovered by king_trending: "
              f"{sum(1 for r in rows if any(r.get('king_trending', [])) and not any(r.get('king_latched', [])))}")
        print(f"  overtime: {sum(1 for r in rows if r.get('overtime_hint'))}")
        print(f"  ckpt {rows[0].get('ckpt')}  tau {rows[0].get('tau')}")

    if not logfiles:
        print("\n(no stdout log -- skipping the integrity check and behaviour counters)")
        return 0

    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in logfiles)
    starts = len(re.findall(r"state: IN_MATCH", text))
    print(f"\nINTEGRITY  ledger rows {n}  vs  IN_MATCH transitions {starts}", end="  ")
    print("OK" if abs(starts - n) <= 1 else f"*** MISMATCH -- {abs(starts - n)} matches unaccounted for; DENOMINATOR SUSPECT ***")

    taps = re.findall(r"\[student\] TAP .*?wall=(\d+):(\d+):([\d.]+)", text)
    ts = [int(h) * 3600 + int(m) * 60 + float(s) for h, m, s in taps]
    ts = [t for t in ts]
    gaps = [b - a for a, b in zip(ts, ts[1:]) if 0 < b - a < 600]
    print("\nBEHAVIOUR (the owner's complaints, from the same log)")
    print(f"  taps {len(taps)}")
    if gaps:
        sg = sorted(gaps)
        print(f"  median gap between plays {sg[len(sg) // 2]:.2f}s   p90 {sg[int(len(sg) * 0.9)]:.2f}s")
        print(f"  share of time in >10s pauses {sum(g for g in gaps if g > 10) / sum(gaps):.1%}")
    print(f"  [assist] XBOW dead-lane firings {len(re.findall(r'XBOW dead-lane', text))}")
    print(f"  [assist] XBOW pocket firings    {len(re.findall(r'XBOW pocket', text))}")
    for card in ("rocket", "the_log", "tornado", "x_bow", "tesla"):
        print(f"  taps {card:9s} {len(re.findall(r'\[student\] TAP .*? ' + card + ' ', text))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
