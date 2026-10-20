"""Validate the live outcome ledger BEFORE spending live matches on it.

The specific risk: crown_counts() returns (blue, red, ...) and I read its docstring as
blue = enemy towers I felled. If that is inverted, 110 matches get recorded with every
win logged as a loss. Reading a docstring is not verification -- this constructs tower
states and checks the mapping, plus the 3-crown recovery via king_trending_down().
"""
import sys, pathlib
sys.path.insert(0, r"C:\Users\benpe\ClashBot\icebow\src")

from clashrl.config import Config          # noqa: E402
from clashrl.reward import TowerTracker    # noqa: E402

cfg = Config.load()
tt = TowerTracker(cfg)
print(f"anchors: mine={len(tt.mine_a)} enemy={len(tt.enemy_a)}  confirm={tt.confirm}")


def outcome(tracker):
    """EXACT copy of the logic in play.py's ledger hook."""
    blue, red, ek, mk = tracker.crown_counts()
    tek, tmk = tracker.king_trending_down()
    if ek or tek:
        blue = 3
    if mk or tmk:
        red = 3
    res = "win" if blue > red else ("loss" if red > blue else "draw")
    return res, blue, red


def setup(enemy_alive, mine_alive, enemy_low=None, mine_low=None):
    tt.reset()
    tt.enemy_alive = list(enemy_alive)
    tt.mine_alive = list(mine_alive)
    if enemy_low:
        tt._enemy_low = list(enemy_low)
    if mine_low:
        tt._mine_low = list(mine_low)
    return tt


A = [True, True, True]          # [princess_l, princess_r, king]
CASES = [
    # (name, enemy_alive, mine_alive, enemy_low, mine_low, expected_outcome, exp_blue, exp_red)
    ("fresh board",                 A, A, None, None, "draw", 0, 0),
    ("I felled one princess",       [False, True, True], A, None, None, "win", 1, 0),
    ("I lost one princess",         A, [False, True, True], None, None, "loss", 0, 1),
    ("one each = draw",             [False, True, True], [True, False, True], None, None, "draw", 1, 1),
    ("I felled two",                [False, False, True], A, None, None, "win", 2, 0),
    ("two down vs one = win",       [False, False, True], [False, True, True], None, None, "win", 2, 1),
    ("enemy KING down = 3 crowns",  [False, False, False], A, None, None, "win", 3, 0),
    ("my KING down = 3 against",    A, [False, False, False], None, None, "loss", 0, 3),
    # the case king_trending_down exists for: king NOT latched, but one 'gone' read landed
    ("enemy king TRENDING (3-crown recovered)", [False, True, True], A, [0, 0, 1], None, "win", 3, 0),
    ("my king TRENDING (3-crown against)",      A, [False, True, True], None, [0, 0, 1], "loss", 0, 3),
]

fails = 0
for name, ea, ma, el, ml, exp_res, exp_b, exp_r in CASES:
    t = setup(ea, ma, el, ml)
    res, blue, red = outcome(t)
    ok = (res == exp_res and blue == exp_b and red == exp_r)
    fails += (not ok)
    print(f"  [{'OK ' if ok else 'FAIL'}] {name:42s} -> {res:5s} {blue}-{red}"
          f"{'' if ok else f'   EXPECTED {exp_res} {exp_b}-{exp_r}'}")

# ledger filename derivation, exactly as play.py builds it
log_path = pathlib.Path(r"C:\Users\benpe\ClashBot\icebow\data\play_20260918_012345.log")
ledger = log_path.with_name(log_path.name.replace("play_", "live_matches_")).with_suffix(".jsonl")
want = "live_matches_20260918_012345.jsonl"
ok = ledger.name == want
fails += (not ok)
print(f"\n  [{'OK ' if ok else 'FAIL'}] ledger path -> {ledger.name}{'' if ok else f'  EXPECTED {want}'}")

print("\nRESULT:", "ALL PASS - instrument is safe to run" if not fails else f"{fails} FAILURES - DO NOT RUN")
sys.exit(1 if fails else 0)
