"""clock_verdict: tick-0 countdown must wait (never stall, never decide); a real stall after the clock ran must stop."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from live_play import clock_verdict  # noqa: E402


def run(frames):
    """frames: (tick, seconds). Mirrors the loop: verdicts per frame; last_tick/last_adv update only on proceed+advance."""
    last_tick, last_adv, out = -1, 0.0, []
    for tick, t in frames:
        v = clock_verdict(tick, last_tick, t - last_adv)
        out.append(v)
        if v == "stall":
            break
        if v == "proceed" and tick > last_tick:
            last_tick, last_adv = tick, t
    return out


def test_tick0_for_10s_waits_forever():
    assert set(run([(0, i * 0.1) for i in range(101)])) == {"wait"}   # 10 s at tick 0: never stall, never proceed


def test_zero_then_clock_starts():
    assert run([(0, 0.0), (0, 0.1), (0, 0.2), (1, 4.0), (2, 4.1)]) == ["wait"] * 3 + ["proceed"] * 2


def test_stall_after_clock_ran():
    v = run([(500, 0.0), (500, 1.0), (500, 3.5)])
    assert v == ["proceed", "proceed", "stall"]


def test_advancing_ticks_proceed():
    assert set(run([(150 + i, i * 0.1) for i in range(100)])) == {"proceed"}


def test_tick0_glitch_after_clock_ran_stalls():
    assert run([(500, 0.0), (0, 1.0), (0, 3.5)]) == ["proceed", "proceed", "stall"]   # mid-match 0: same 3 s rule
    assert clock_verdict(0, 500, 10) == "stall"
