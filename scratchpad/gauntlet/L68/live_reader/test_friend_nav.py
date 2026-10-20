"""friend_nav offline: every L69 capture classifies to its screen, plans are the allowlisted input at the expected
point, the Battle / Quickplay buttons are unreachable, stop rules, cross-invite, and an end-to-end run on a scripted
fake device (fake clock; dry-run sends nothing). No emulator is touched."""
import ast
import random
import sys
import time as _time
import types
from pathlib import Path

import cv2
import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import friend_nav as fn  # noqa: E402

RAW = HERE.parents[1] / "L69" / "nav" / "raw"
# Measured from the captures HERE, independently of friend_nav.FORBIDDEN: editing the module's table (a bypass)
# must not make these tests pass.
BATTLE = (305, 1168, 605, 1335)          # yellow Battle button, after_ok_131638
QUICKPLAY = (69, 1284, 393, 1369)        # friends_list_130251
EXPECT = {                               # capture -> (screen, planned target, tap point)
    "results_131619": ("results", "results_ok", (450, 1451)),
    "after_ok_131638": ("main", "main_to_social", None),
    "test_now_125953": ("main", "main_to_social", None),
    "friends_list_130251": ("social", "social_scroll_top", None),      # row cut off: list search starts at the top
    "friends_list_130915": ("social", "friend_row", (292, 1129)),
    "friend_entry_130350": ("popup", "popup_friendly_battle", (193, 1312)),
    "battle_type_130729": ("battle_type", "battle_type_1v1", (450, 442)),
    "invite_sent_130520": ("pending", None, None),
    "cancel_invite_130818": ("pending", None, None),
    "invite_incoming_131227": ("incoming", "invite_accept", (575, 739)),
}
CLF = fn.Classifier()


def img(name):
    return cv2.imread(str(RAW / f"{name}.png"))


def inside(pt, r):
    return r[0] <= pt[0] <= r[2] and r[1] <= pt[1] <= r[3]


def touched_points(cmd):
    """Every screen point an input command touches (a swipe: 21 samples along its path)."""
    v = [int(t) for t in cmd.split()[2:]]
    if cmd.startswith("input tap"):
        return [tuple(v)]
    x0, y0, x1, y1 = v[:4]
    return [(x0 + (x1 - x0) * i / 20, y0 + (y1 - y0) * i / 20) for i in range(21)]


def check_safe(target, pt):
    """The invariant: no input in the Battle rectangle, none in Quickplay except the verified popup button."""
    for p in touched_points(fn.command_for(target, pt)):
        assert not inside(p, BATTLE), (target, p)
        assert target == "popup_friendly_battle" or not inside(p, QUICKPLAY), (target, p)


def plan_after_wait(scr):
    return fn.Nav(0.0, random.Random(0)).plan(scr, 25.0)       # past the 5-20 s invite wait


def test_every_capture_is_covered():
    assert sorted(p.stem for p in RAW.glob("*.png")) == sorted(EXPECT)


@pytest.mark.parametrize("name", sorted(EXPECT))
def test_capture_classifies_and_plans_allowlisted_input(name):
    screen, target, pt = EXPECT[name]
    scr = CLF.classify(img(name))
    assert scr["screen"] == screen, scr
    p = plan_after_wait(scr)
    if target is None:
        assert p[0] == "wait", p
        return
    assert p[:2] == ("act", target), p
    if pt is None:
        assert p[2] is None
    else:
        assert abs(p[2][0] - pt[0]) <= 3 and abs(p[2][1] - pt[1]) <= 3, p
    check_safe(target, p[2])


def test_results_capture_verifies_the_friend():
    assert CLF.classify(img("results_131619"))["friend"] is True


def test_results_foreign_opponent_stops():
    im = img("results_131619")
    im[428:480, 305:590] = im[455, 290]                         # blank the opponent name with the banner colour
    scr = CLF.classify(im)
    assert scr["screen"] == "results" and scr["friend"] is False
    nav = fn.Nav(0.0, random.Random(0))
    plans = [nav.plan(scr, 1.0 + i) for i in range(3)]
    assert [p[0] for p in plans] == ["wait", "wait", "stop"], plans    # never taps OK for a non-friend


def test_unknown_screen_stops_after_timeout_and_never_acts():
    scr = CLF.classify(np.zeros((1600, 900, 3), np.uint8))
    assert scr["screen"] == "unknown"
    nav = fn.Nav(0.0, random.Random(0))
    plans = [(t, nav.plan(scr, t)) for t in np.arange(1.0, 30.0, 0.5)]
    assert all(p[0] == "wait" for t, p in plans if t - 1.0 <= 20)
    stop_t = next(t for t, p in plans if p[0] == "stop")
    assert 21.0 <= stop_t <= 21.6


def test_transition_timeout_stops_even_on_a_known_screen():
    nav = fn.Nav(0.0, random.Random(0))
    assert nav.plan(CLF.classify(img("invite_sent_130520")), 181.0)[0] == "stop"


def test_popup_for_someone_else_is_not_acted_on():
    im = img("friend_entry_130350")
    im[1006:1038, 110:280] = 255                                # header name blanked
    assert CLF.classify(im)["screen"] == "popup_other"


def test_popup_button_drawn_over_quickplay_without_popup_body_is_rejected():
    """The dangerous misread: a Friendly-Battle button + friend header over the bare Social list, where the tap
    would land on Quickplay. The popup's white body is missing on both sides -> never 'popup'."""
    src, im = img("friend_entry_130350"), img("friends_list_130251")
    im[1272:1352, 95:292] = src[1272:1352, 95:292]
    im[1006:1038, 118:270] = src[1006:1038, 118:270]
    scr = CLF.classify(im)
    assert scr["screen"] != "popup", scr
    nav = fn.Nav(0.0, random.Random(0))
    for t in np.arange(25.0, 50.0, 0.5):
        p = nav.plan(scr, t)
        if p[0] == "act":
            check_safe(p[1], p[2])


def test_main_screen_never_yields_battle_or_quickplay_input():
    for name in ("after_ok_131638", "test_now_125953"):
        scr = CLF.classify(img(name))
        nav = fn.Nav(0.0, random.Random(1))
        for t in np.arange(0.0, 60.0, 0.5):
            p = nav.plan(scr, t)
            assert p[0] == "act" and p[1] == "main_to_social", p
            check_safe(p[1], p[2])


def test_friend_row_low_on_screen_scrolls_instead_of_tapping():
    p = plan_after_wait({"screen": "social", "row": (300, 1200), "scores": {}})   # row at the Battle button's height
    assert p[:2] == ("act", "social_scroll_top")


def test_friend_search_is_bounded_top_then_scan_then_stop():
    nav = fn.Nav(0.0, random.Random(0), friend="JinxTheCat")
    t = 25.0
    for target, n in (("social_scroll_top", 6), ("social_scroll", 8)):   # a list that keeps moving: limits hold
        for i in range(n):
            scr = {"screen": "social", "row": None, "scores": {}, "sig": np.full((66, 74), (t * 37) % 255, np.uint8)}
            p = nav.plan(scr, t)
            assert p[:2] == ("act", target), (i, p)
            nav.acted(target, t)
            t += 1
    p = nav.plan({"screen": "social", "row": None, "scores": {}, "sig": np.zeros((66, 74), np.uint8)}, t)
    assert p == ("stop", "friend JinxTheCat not found in the Social list (offline or not visible)")


def test_waits_for_the_friends_invite_before_sending():
    nav = fn.Nav(0.0, random.Random(0))
    wait = nav.wait_until
    assert 5 <= wait <= 20
    scr = CLF.classify(img("friends_list_130915"))
    assert nav.plan(scr, wait - 0.1)[0] == "wait"
    assert nav.plan(scr, wait + 0.1)[:2] == ("act", "friend_row")


def test_cross_invite_cancels_ours_then_accepts_theirs():
    im = img("invite_incoming_131227")
    im[80:225, 25:875] = img("invite_sent_130520")[80:225, 25:875]     # our pending banner over their invite
    scr = CLF.classify(im)
    assert scr["screen"] == "cross", scr
    nav = fn.Nav(0.0, random.Random(0))
    p = nav.plan(scr, 30.0)
    assert p[:2] == ("act", "invite_cancel_ours") and abs(p[2][0] - 750) <= 3 and abs(p[2][1] - 149) <= 3
    check_safe(*p[1:])
    nav.acted("invite_cancel_ours", 30.0)
    assert nav.wait_until >= 35.0                                     # fresh random delay after a cross
    p = nav.plan(CLF.classify(img("invite_incoming_131227")), 31.5)   # ours gone, theirs still up
    assert p[:2] == ("act", "invite_accept")
    check_safe(*p[1:])
    nav.acted("invite_accept", 31.5)
    black = CLF.classify(np.zeros((1600, 900, 3), np.uint8))           # loading screen
    assert nav.plan(black, 32.0)[0] == "wait"
    assert nav.plan(black, 35.1)[0] == "handoff"


def test_allowlist_is_structural():
    with pytest.raises(fn.NavViolation):
        fn.command_for("battle", (455, 1250))
    with pytest.raises(fn.NavViolation):
        fn.command_for("quickplay", (230, 1325))
    for target, (kind, spec) in fn.TARGETS.items():
        if kind == "swipe":
            check_safe(target, None)
            with pytest.raises(fn.NavViolation):
                fn.command_for(target, (455, 1250))
            continue
        with pytest.raises(fn.NavViolation):
            fn.command_for(target, (455, 1250))                         # the Battle button's centre
        if target != "popup_friendly_battle":
            with pytest.raises(fn.NavViolation):
                fn.command_for(target, (230, 1325))                     # Quickplay's centre
    rng = random.Random(0)                                              # fuzz: whatever command_for accepts is safe
    for _ in range(20000):
        target = rng.choice([t for t, (k, _) in fn.TARGETS.items() if k == "tap"])
        pt = (rng.uniform(0, 900), rng.uniform(0, 1600))
        try:
            check_safe(target, pt)
        except fn.NavViolation:
            pass


def test_only_command_for_builds_input_commands():
    src = (HERE / "friend_nav.py").read_text()
    tree = ast.parse(src)
    fdef = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "command_for")
    lines = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and ("input tap" in n.value or "input swipe" in n.value or "keyevent" in n.value)]
    assert len(lines) == 2 and all(fdef.lineno <= ln <= fdef.end_lineno for ln in lines), lines
    shells = [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and n.value == "shell"]
    assert len(shells) == 1                                              # the one adb shell call: `cmd` from command_for


# ---- end to end on a scripted fake device ---------------------------------------------------------------------------
class FakeDevice:
    """Screens advance only when the matching allowlisted input arrives -- like the game."""
    NEXT = {"results_131619": ((450, 1451), "after_ok_131638"),
            "after_ok_131638": ("swipe", "friends_list_130915"),
            "friends_list_130915": ((292, 1129), "friend_entry_130350"),
            "friend_entry_130350": ((193, 1312), "battle_type_130729"),
            "battle_type_130729": ((450, 442), "invite_sent_130520")}

    def __init__(self):
        self.screen, self.pending_polls, self.cmds, self.now = "results_131619", 0, [], 0.0
        self.imgs = {n: img(n) for n in EXPECT}

    def grab(self):
        if self.screen == "invite_sent_130520":
            self.pending_polls += 1
            if self.pending_polls > 6:                                  # friend accepted: loading screen
                return np.zeros((1600, 900, 3), np.uint8)
        return self.imgs[self.screen]

    def run(self, args, **kw):
        cmd = args[-1]
        self.cmds.append(cmd)
        want, nxt = self.NEXT.get(self.screen, (None, None))
        v = cmd.split()
        if want == "swipe" and v[1] == "swipe" or (want and v[1] == "tap" and want != "swipe"
                                                   and max(abs(int(v[2]) - want[0]), abs(int(v[3]) - want[1])) <= 3):
            self.screen = nxt
        return types.SimpleNamespace(stdout=b"", returncode=0)


@pytest.mark.parametrize("dry", [False, True])
def test_end_to_end_fake_device(dry, monkeypatch, tmp_path):
    dev = FakeDevice()
    clock = types.SimpleNamespace(time=lambda: dev.now, strftime=_time.strftime,
                                  sleep=lambda s: setattr(dev, "now", dev.now + s))
    monkeypatch.setattr(fn, "time", clock)
    monkeypatch.setattr(fn.subprocess, "run", dev.run)

    class QuickNav(fn.Nav):                                             # shorter clocks: each frame costs a real
        TRANSITION_S = 20.0                                             # full-resolution classification

        def __init__(self, t0, rng=None, **kw):
            super().__init__(t0, rng, **kw)
            self.wait_until = t0 + 5.0
    monkeypatch.setattr(fn, "Nav", QuickNav)
    nav = fn.FriendNav(["adb"], "JinxTheCat", dry_run=dry, log_dir=tmp_path)
    monkeypatch.setattr(nav, "grab", dev.grab)
    ok, why = nav.run()
    if dry:
        assert dev.cmds == [] and not ok and "transition" in why        # nothing sent; stays on results -> 180 s stop
        return
    assert ok, why
    kinds = [c.split()[1] for c in dev.cmds]
    assert kinds == ["tap", "swipe", "tap", "tap", "tap"], dev.cmds
    for c in dev.cmds:
        for p in touched_points(c):
            assert not inside(p, BATTLE)
    in_qp = [c for c in dev.cmds if any(inside(p, QUICKPLAY) for p in touched_points(c))]
    assert len(in_qp) == 1 and dev.cmds.index(in_qp[0]) == 3              # only the verified popup button


def test_wrong_friend_refused():
    with pytest.raises(SystemExit):
        fn.FriendNav(["adb"], "SomeoneElse")


# ---- live_play.play_match safety (repair 2): fake reader / adb / pilot / guard, no device ---------------------------
import argparse  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import threading  # noqa: E402

import live_play as lp  # noqa: E402


def rframe(tick, stale=False):
    me = {"side": 0, "hand_deck_indices": [0, 1, 2, 3], "elixir_raw": 80000, "deck_card_ids": [26000000] * 8,
          "deck_form_flags": [0] * 8}
    opp = dict(me, side=1, hand_deck_indices=[-1] * 4)
    return json.dumps({"battle_active": True, "coherent": True, "game_tick": tick, "sample_monotonic_us": tick * 50000,
                       "players": [me, opp], "entities": [], "stale": stale}) + "\n"


class FakeSampler:
    """adb shell live_sampler: yields its lines slowly, then stays OPEN (a live sampler) until terminate()."""
    def __init__(self, lines, on_line=None):
        self.lines, self.on_line, self.killed = lines, on_line, threading.Event()
        self.stderr = io.StringIO("")
        self.stdout = self._out()

    def _out(self):
        for i, ln in enumerate(self.lines):
            if self.killed.is_set():
                return
            if self.on_line:
                self.on_line(i)
            yield ln
            _time.sleep(0.03)                           # one frame at a time: the loop sees each as the newest
        self.killed.wait(15)

    def terminate(self):
        self.killed.set()

    def wait(self, timeout=None):
        return 0


class FakeGuard:
    """Always sees a battle screen once armed (isolates the reader-side fixes); tests set .menu."""
    inst = None

    def __init__(self, adb, *a, **k):
        self.menu, self.armed, self.ok_ts, self.armed_at = None, False, None, None
        FakeGuard.inst = self

    def arm(self):
        self.armed, self.armed_at, self.ok_ts = True, _time.time(), _time.time()

    def clear(self, now):
        return self.armed and self.menu is None

    def blind_s(self, now):
        return 0.0

    def feed(self, img, t_grab=None):
        pass

    def stop(self):
        pass


class FakePilot:
    def __init__(self):
        self.decided, self.last = [], None
        from pipeline.decision_options import DecisionOptions
        self.decision_options, self.match_seed, self.feature_version = DecisionOptions(), 0, 4

    def observe(self, f):
        return None

    def decide(self, f):
        self.decided.append(f)
        self.last = f
        return {"play": True, "card": 1, "form": 0, "hand_pos": 0, "deck_index": 0, "xy": (0.5, 0.6),
                "name": "Knight", "p_play": 0.9, "public_audit": {}}

    def record_play(self, *a):
        pass


def run_match(monkeypatch, tmp_path, lines, dry_run, on_line=None, start_timeout=None, guard_cls=None,
              menu_guard=True, adb_timeout=False, tap_timeout_at=None):
    samplers, taps, pilot = [], [], FakePilot()
    guard_cls = guard_cls or FakeGuard
    guard_cls.inst = None

    def popen(args, **kw):
        s = FakeSampler(lines if not samplers else [], on_line)
        samplers.append(s)
        return s

    def adb(*args, **kw):
        if "input tap" in args[-1]:
            g = guard_cls.inst or types.SimpleNamespace(menu=None, ok_ts=None, armed_at=None)
            taps.append((args[-1], bool(pilot.last and pilot.last["stale"]), g.menu, g.ok_ts, g.armed_at,
                         _time.time()))
            if tap_timeout_at is not None and len(taps) >= tap_timeout_at and kw.get("strict"):
                raise lp.subprocess.TimeoutExpired("adb", 5)
        return ""
    monkeypatch.setattr(lp.subprocess, "Popen", popen)
    if adb_timeout:                                     # the REAL adb(): every adb call times out
        def timeout_run(*a, **k):
            raise lp.subprocess.TimeoutExpired("adb", 5)
        monkeypatch.setattr(lp.subprocess, "run", timeout_run)
    else:
        monkeypatch.setattr(lp, "adb", adb)
    monkeypatch.setattr(lp, "MenuGuard", guard_cls)
    monkeypatch.setattr(lp, "HERE", tmp_path)
    a = argparse.Namespace(tau=0.5, leak=9.5, dry_run=dry_run, ckpt="x", extrapolate=0, no_opp_counter=True,
                           no_record=True, no_ability=True, interval_ms=100, max_seconds=400, overlay="both",
                           menu_guard=menu_guard, reader="v2", no_anti_leak=True, public_audit=True,
                           ckpt_source="fixture", ckpt_sha256="fixture")
    why = lp.play_match(a, pilot, lp.Layout(900, 1600), "cpu", None, start_timeout=start_timeout, record=False)
    return why, samplers, taps, pilot


def test_stale_same_tick_frames_never_decide_or_tap(monkeypatch, tmp_path):
    lines = []
    for t in range(150, 400, 2):
        lines += [rframe(t), rframe(t, stale=True), rframe(t, stale=True)]
    for dry in (True, False):
        why, samplers, taps, pilot = run_match(monkeypatch, tmp_path, lines, dry,
                                               on_line=lambda i: None if i < len(lines) - 1 else
                                               setattr(FakeGuard.inst, "menu", "results"))
        assert pilot.decided and not any(f["stale"] for f in pilot.decided), dry
        assert not any(t[1] for t in taps)
        assert (len(taps) > 0) == (not dry)
        assert len(samplers) == 1, "the sampler was restarted after the match's own kill"


def test_menu_during_match_stops_before_any_tap(monkeypatch, tmp_path):
    lines = [rframe(t) for t in range(150, 400, 2)]

    def menu_from_start(i):
        FakeGuard.inst.menu = "main"
    why, samplers, taps, pilot = run_match(monkeypatch, tmp_path, lines, False, on_line=menu_from_start)
    assert why == "menu_screen:main" and taps == [] and len(samplers) == 1

    def menu_midway(i):
        if i == 60:
            FakeGuard.inst.menu = "main"
    why, samplers, taps, pilot = run_match(monkeypatch, tmp_path, lines, False, on_line=menu_midway)
    assert why == "menu_screen:main" and taps and all(t[2] is None for t in taps)
    assert why not in lp.MATCH_OVER and "menu_screen:results" in lp.MATCH_OVER


def test_silent_reader_fires_start_and_stall_timeouts(monkeypatch, tmp_path):
    why, *_ = run_match(monkeypatch, tmp_path, [], True, start_timeout=1.5)          # never a line
    assert why == "no_battle_start"
    monkeypatch.setattr(lp, "READER_SILENT_S", 1.5)
    why, samplers, *_ = run_match(monkeypatch, tmp_path, [rframe(t) for t in range(150, 170, 2)], True)
    assert why == "reader_silent" and len(samplers) == 1


def test_guard_timing_values():
    assert fn.MenuGuard.FRESH_S == 8.0 and lp.GUARD_BLIND_S == 30.0   # 2026-09-30 live stop under adb saturation


def test_menu_guard_arms_only_when_the_clock_runs_and_fails_closed():
    g = fn.MenuGuard(["no-such-adb"], clf=CLF)
    g.stop()
    g.feed(img("after_ok_131638"))
    assert g.menu is None and not g.clear(_time.time())  # started from the menu (Training Camp flow): ignored
    t_before = _time.time()
    g.arm()
    black = np.zeros((1600, 900, 3), np.uint8)
    g.feed(None)                                        # failed grab: NOT a success
    g.feed(np.zeros((1920, 1080, 3), np.uint8))         # wrong size: NOT a success
    g.feed(black, t_grab=t_before - 1)                  # grabbed before arming: NOT a success
    assert g.ok_ts is None and not g.clear(_time.time())
    g.feed(black)
    assert g.clear(_time.time()) and not g.clear(_time.time() + fn.MenuGuard.FRESH_S + 1)   # fresh for FRESH_S
    g.feed(img("after_ok_131638"))
    assert g.menu == "main" and not g.clear(_time.time())


def test_recorded_battle_frames_are_not_menus():
    """A recording starts on whatever screen the owner launched from (lp_20260930_150349_0: main menu at 0 s, battle
    from 3 s) and may end on results, so sample 15-90% of a recorded match."""
    vid = HERE.parents[3] / "icebow" / "data" / "overlayed_replays" / "raw" / "lp_20260930_122643_0.mp4"
    if not vid.is_file():
        pytest.skip("recorded live match not on this machine")
    cap, n = cv2.VideoCapture(str(vid)), 0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    for i in range(int(total * 0.15), int(total * 0.9), max(1, total // 40)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, im = cap.read()
        if ok:
            n += 1
            assert CLF.classify(im)["screen"] not in fn.MENU_SCREENS, i
    assert n >= 20


def test_matches_zero_refused(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["live_play.py", "--matches", "0"])
    assert lp.main() == 2 and ">= 1" in capsys.readouterr().out


def test_single_frozen_frame_never_taps(monkeypatch, tmp_path):
    """Repair 3: the FIRST active frame of a match is never 'advanced' -- one frozen frame (stale reader) at a
    tap-able tick, or many copies of it, yields no input even with a clear guard."""
    monkeypatch.setattr(lp, "READER_SILENT_S", 1.5)
    for lines in ([rframe(2000)], [rframe(2000)] * 20):
        why, samplers, taps, pilot = run_match(monkeypatch, tmp_path, lines, False)
        assert taps == [] and why in ("reader_silent", "tick_stalled"), why


class SpyGuard(fn.MenuGuard):
    inst = None

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        SpyGuard.inst = self


def test_taps_wait_for_the_first_successful_post_arming_classification(monkeypatch, tmp_path):
    t_start, black = [], np.zeros((1600, 900, 3), np.uint8)

    def grab(adb):                                      # screenshots fail for the first 3 s after arming
        t_start.append(_time.time()) if not t_start else None
        return None if _time.time() - t_start[0] < 3.0 else black
    monkeypatch.setattr(fn, "grab", grab)
    lines = [rframe(t) for t in range(150, 750, 2)]      # 300 frames, ~9 s
    why, samplers, taps, pilot = run_match(monkeypatch, tmp_path, lines, False, guard_cls=SpyGuard)
    SpyGuard.inst.stop()
    assert taps, why
    for cmd, stale, menu, ok_ts, armed_at, t in taps:
        assert ok_ts is not None and ok_ts >= armed_at and t >= ok_ts and t - t_start[0] >= 3.0


def test_blind_guard_blocks_taps_then_stops(monkeypatch, tmp_path):
    monkeypatch.setattr(fn, "grab", lambda adb: None)   # every screenshot fails
    monkeypatch.setattr(lp, "GUARD_BLIND_S", 3.0)
    lines = [rframe(t) for t in range(150, 750, 2)]
    why, samplers, taps, pilot = run_match(monkeypatch, tmp_path, lines, False, guard_cls=SpyGuard)
    SpyGuard.inst.stop()
    assert taps == [] and why == "guard_blind" and pilot.decided   # it decided, but no input reached the device


def test_non_900x1600_screen_refused_without_flag(monkeypatch, capsys):
    class Loaded(Exception):
        pass

    def no_model(*a, **k):
        raise Loaded
    monkeypatch.setattr(lp, "screen_size", lambda: (1080, 1920))
    monkeypatch.setattr(lp, "GenPilot", no_model)
    monkeypatch.setattr(sys, "argv", ["live_play.py", "--menu-guard"])
    assert lp.main() == 2 and "900x1600" in capsys.readouterr().out     # the opt-in guard needs its template size
    for argv in ([], ["--no-menu-guard"]):   # guard off (default / no-op alias)
        monkeypatch.setattr(sys, "argv", ["live_play.py"] + argv)
        with pytest.raises(Loaded):                     # proceeds to the model load
            lp.main()


# ---- friend-list search + first-match navigation ---------------------------------------------------------------------
def _norow():
    im = img("friends_list_130915")
    im[1100:1160, 195:390] = im[1180, 300]                      # the friend's name painted out: someone else's row
    return im


class ListDevice(FakeDevice):
    """The Social list as a stack of scroll positions; swipes move between them (clamped = list end)."""
    def __init__(self, positions, start):
        super().__init__()
        self.positions, self.pos, self.screen = positions, start, "list"

    def grab(self):
        return self.positions[self.pos] if self.screen == "list" else super().grab()

    def run(self, args, **kw):
        if self.screen != "list":
            return super().run(args, **kw)
        cmd = args[-1]
        self.cmds.append(cmd)
        v = cmd.split()
        if v[1] == "swipe":                                       # drag up = content up = further down the list
            self.pos = max(0, min(len(self.positions) - 1, self.pos + (1 if int(v[5]) < int(v[3]) else -1)))
        elif abs(int(v[2]) - 292) <= 3 and abs(int(v[3]) - 1129) <= 3:
            self.screen = "friend_entry_130350"
        return types.SimpleNamespace(stdout=b"", returncode=0)


_orig_nav_init = fn.Nav.__init__


def _quick_nav_init(self, t0, rng=None, **kw):
    _orig_nav_init(self, t0, rng, **kw)
    self.wait_until = t0 + 5.0


def run_list(monkeypatch, tmp_path, positions, start):
    dev = ListDevice(positions, start)
    clock = types.SimpleNamespace(time=lambda: dev.now, strftime=_time.strftime,
                                  sleep=lambda s: setattr(dev, "now", dev.now + s))
    monkeypatch.setattr(fn, "time", clock)
    monkeypatch.setattr(fn.subprocess, "run", dev.run)
    monkeypatch.setattr(fn.Nav, "__init__", _quick_nav_init)
    nav = fn.FriendNav(["adb"], "JinxTheCat", log_dir=tmp_path)
    monkeypatch.setattr(nav, "grab", dev.grab)
    return nav.run(), dev


def test_list_search_goes_to_top_then_finds_row_below_the_fold(monkeypatch, tmp_path):
    top, row = img("friends_list_130251"), img("friends_list_130915")
    (ok, why), dev = run_list(monkeypatch, tmp_path, [top, row], 0)
    assert ok, why
    assert dev.cmds[:3] == ["input swipe 620 800 620 1100 600",    # to the top: the list did not move -> top
                            "input swipe 620 1100 620 800 600",    # scan down one: the row comes into view
                            "input tap 292 1129"], dev.cmds
    for c in dev.cmds:
        for p in touched_points(c):
            assert not inside(p, BATTLE)


def test_list_search_from_below_scrolls_up_to_the_row(monkeypatch, tmp_path):
    top, row = img("friends_list_130251"), img("friends_list_130915")
    (ok, why), dev = run_list(monkeypatch, tmp_path, [top, row, _norow()], 2)
    assert ok and dev.cmds[:2] == ["input swipe 620 800 620 1100 600", "input tap 292 1129"], dev.cmds


def test_friend_not_in_list_stops_cleanly(monkeypatch, tmp_path):
    (ok, why), dev = run_list(monkeypatch, tmp_path, [img("friends_list_130251"), _norow()], 0)
    assert not ok and why == "friend JinxTheCat not found in the Social list (offline or not visible)"
    assert all(c.startswith("input swipe") for c in dev.cmds) and len(dev.cmds) <= fn.Nav.MAX_TOP + fn.Nav.MAX_SCAN


def test_probe_sees_menu_or_assumes_battle(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(fn, "time", types.SimpleNamespace(
        time=lambda: now[0], sleep=lambda s: now.__setitem__(0, now[0] + s + 0.3)))
    nav = fn.FriendNav(["adb"], "JinxTheCat")
    monkeypatch.setattr(nav, "grab", lambda: img("after_ok_131638"))
    assert nav.probe() == "main"
    now[0] = 0.0
    monkeypatch.setattr(nav, "grab", lambda: np.zeros((1600, 900, 3), np.uint8))   # battle / loading
    assert nav.probe() is None and 8.0 <= now[0] <= 9.0


@pytest.mark.parametrize("launch", ["main", None])
def test_first_match_is_navigated_from_a_menu(monkeypatch, launch):
    calls = []

    class FakeNav:
        def __init__(self, adb, friend, dry_run=False, **kw):
            calls.append(("invite_wait", kw.get("invite_wait")))

        def probe(self):
            calls.append("probe")
            return launch

        def run(self):
            calls.append("nav")
            return True, "handoff"

    class NoModel:
        def __init__(self, *a, **k):
            pass

        def reset_match(self):
            pass

    def fake_play(a, pilot, lay, device, renders, start_timeout=None, **kw):
        calls.append(("match", start_timeout))
        return "battle_inactive"
    monkeypatch.setattr(fn, "FriendNav", FakeNav)
    monkeypatch.setattr(lp, "screen_size", lambda: (900, 1600))
    monkeypatch.setattr(lp, "GenPilot", NoModel)
    monkeypatch.setattr(lp, "play_match", fake_play)
    monkeypatch.setattr(sys, "argv", ["live_play.py", "--matches", "2", "--friend", "JinxTheCat"])
    assert lp.main() == 0
    if launch:                                                  # menu at launch: navigate BEFORE match 1
        assert calls == [("invite_wait", 20.0), "probe", "nav", ("match", 60), "nav", ("match", 60)]
    else:                                                       # battle already running: just play it
        assert calls == [("invite_wait", 20.0), "probe", ("match", None), "nav", ("match", 60)]


# ---- 2026-09-30 fixes: side-0 board mirror; list search re-armed on re-entering Social ------------------------------
SIDE0_LOG = HERE.parent / "live_reader_stable" / "live_play_20260930_183149.jsonl"


def test_side0_spawns_map_back_to_the_tap_that_produced_them():
    """Replay the side-0 match: every confirmed spawn, fed through Layout.board, must give the pixel that was tapped.
    Exact (+-3 px) for single units on a centred tile; within the placement snap for a 2x2 building (half a tile in x)
    and the skeleton group (the logged spawn is one member, <= 1 tile off in y). The old mirrored x was 200-600 px off."""
    if not SIDE0_LOG.is_file():
        pytest.skip("side-0 log not on this machine")
    ev = [json.loads(ln) for ln in SIDE0_LOG.read_text().splitlines() if ln.strip()]
    assert all(e.get("my_side", 0) == 0 for e in ev if e["event"] == "frame")
    lay, n_exact = lp.Layout(900, 1600), 0
    plays = [e for e in ev if e["event"] == "play"]
    for e in (e for e in ev if e["event"] == "confirmed" and e["spawn"]):
        tap = [q for q in plays if q["name"] == e["name"] and q["tick"] < e["tick"]][-1]["tap_board"]
        px = lay.board(e["spawn"][0], 0, even=e["name"] in lp.EVEN_BUILDINGS)
        dx, dy = abs(px[0] - tap[0]), abs(px[1] - tap[1])
        if e["name"] == "Tesla":
            assert dx <= 23 and dy <= 3, (e["name"], px, tap)
        elif e["name"] == "Skeletons":
            assert dx <= 3 and dy <= 30, (e["name"], px, tap)
        else:
            assert dx <= 3 and dy <= 3, (e["name"], px, tap)
            n_exact += 1
    assert n_exact >= 5


def test_board_side1_unchanged_and_tesla_nudge_is_native_plus_x():
    lay = lp.Layout(900, 1600)
    for x, y in ((0.139, 0.609), (0.5, 0.75), (0.861, 0.3)):   # side 1: the formula that was already right
        assert lay.board((x, y), 1) == (round(lay.ax0 + (1 - x) * (lay.ax1 - lay.ax0)),
                                        round(lay.ay0 + y * (lay.ay1 - lay.ay0)))
        assert lay.board((x, y), 1, even=True) == (round(lay.ax0 + (1 - x + 0.25 / 18) * (lay.ax1 - lay.ax0)),
                                                   round(lay.ay0 + (y + 0.25 / 32) * (lay.ay1 - lay.ay0)))
    assert lay.board((0.5, 0.5), 0) == lay.board((0.5, 0.5), 1)            # screen x = 1 - our x on both sides
    assert lay.board((0.5, 0.5), 0, even=True)[0] < lay.board((0.5, 0.5), 0)[0]   # side 0: native +x = screen -x
    assert lay.board((0.5, 0.5), 1, even=True)[0] > lay.board((0.5, 0.5), 1)[0]   # side 1: native +x = screen +x


class ExpireDevice(ListDevice):
    """Like ListDevice, but the FIRST invite expires: back on the Social list at the top (row below the fold)."""
    def __init__(self, positions, start):
        super().__init__(positions, start)
        self.expired = False

    def grab(self):
        if self.screen == "invite_sent_130520" and not self.expired:
            self.pending_polls += 1
            if self.pending_polls > 6:
                self.expired, self.screen, self.pos, self.pending_polls = True, "list", 0, 0
        return super().grab()


def test_list_search_restarts_after_an_expired_invite(monkeypatch, tmp_path):
    dev = ExpireDevice([img("friends_list_130251"), img("friends_list_130915")], 0)
    clock = types.SimpleNamespace(time=lambda: dev.now, strftime=_time.strftime,
                                  sleep=lambda s: setattr(dev, "now", dev.now + s))
    monkeypatch.setattr(fn, "time", clock)
    monkeypatch.setattr(fn.subprocess, "run", dev.run)
    monkeypatch.setattr(fn.Nav, "__init__", _quick_nav_init)
    nav = fn.FriendNav(["adb"], "JinxTheCat", log_dir=tmp_path)
    monkeypatch.setattr(nav, "grab", dev.grab)
    ok, why = nav.run()
    assert ok, why
    assert dev.expired and dev.cmds.count("input tap 292 1129") == 2, dev.cmds   # found the row BOTH times
    second = dev.cmds[dev.cmds.index("input tap 292 1129") + 1:]
    assert "input swipe 620 800 620 1100 600" in second                          # searched again from the top


# ---- 2026-09-30: menu guard OPT-IN (its screencaps saturated adb live); adb() survives timeouts ----------------------
def test_menu_guard_is_opt_in(monkeypatch, tmp_path):
    lines = [rframe(t) for t in range(150, 300, 2)]
    why, samplers, taps, pilot = run_match(monkeypatch, tmp_path, lines, False, menu_guard=False)
    (log,) = tmp_path.glob("live_play_*.jsonl")
    assert FakeGuard.inst is None and taps                       # default: no guard, taps still flow
    assert any(json.loads(ln)["event"] == "menu_guard_off" for ln in log.read_text().splitlines())
    for old in tmp_path.glob("live_play_*.jsonl"):
        old.unlink()
    run_match(monkeypatch, tmp_path, lines, False, menu_guard=True)
    assert FakeGuard.inst is not None                            # --menu-guard: created


@pytest.mark.parametrize("argv,on", [([], False), (["--menu-guard"], True), (["--no-menu-guard"], False)])
def test_menu_guard_flag_default_off(monkeypatch, argv, on):
    seen = []

    class NoModel:
        def __init__(self, *a, **k):
            pass
    monkeypatch.setattr(lp, "screen_size", lambda: (900, 1600))
    monkeypatch.setattr(lp, "GenPilot", NoModel)
    monkeypatch.setattr(lp, "play_match", lambda a, *r, **k: seen.append(a.menu_guard) or "battle_inactive")
    monkeypatch.setattr(sys, "argv", ["live_play.py"] + argv)
    assert lp.main() == 0 and seen == [on]


def test_adb_timeout_returns_empty_and_cleanup_completes(monkeypatch, tmp_path, capsys):
    def boom(*a, **k):
        raise lp.subprocess.TimeoutExpired("adb", 5)
    monkeypatch.setattr(lp.subprocess, "run", boom)
    assert lp.adb("shell", "pkill -f live_sampler") == "" and "adb timed out" in capsys.readouterr().out
    monkeypatch.undo()
    lines = [rframe(t) for t in range(150, 200, 2)]
    end = lambda i: setattr(FakeGuard.inst, "menu", "results") if i == len(lines) - 1 else None
    why, samplers, taps, pilot = run_match(monkeypatch, tmp_path, lines, False, on_line=end, adb_timeout=True)
    ev = [json.loads(ln)["event"] for ln in next(tmp_path.glob("live_play_*.jsonl")).read_text().splitlines()]
    assert why == "tap_timeout" and len(samplers) == 1             # finally ran through (pkill timed out) cleanly
    assert "sampler_kill_failed" in ev                            # F2: 5 s + 15 s retry both timed out -> logged


# ---- 2026-09-30: 5_unconfirmed counts CONSECUTIVE misses (slow taps under load landed late, spread over a match) -------
def rframe_hand(tick, hand):
    f = json.loads(rframe(tick))
    f["players"][0]["hand_deck_indices"] = hand
    return json.dumps(f) + "\n"


def unconfirmed_run(monkeypatch, tmp_path, confirm_between):
    """Each fake tap plays hand slot 0. A miss = 31 frames (62 ticks > CONFIRM_TICKS) without slot 0 rotating; with
    confirm_between the slot rotates once after every miss, so the NEXT tap confirms."""
    lines, t, hand = [], 150, [0, 1, 2, 3]
    for k in range(5):
        lines += [rframe_hand(t + 2 * i, hand) for i in range(34)]         # tap on the 2nd frame, then a miss
        t += 68
        if confirm_between and k < 4:
            lines += [rframe_hand(t + 2 * i, hand) for i in range(3)]      # the next tap is made here ...
            hand = [hand[0] + 4] + hand[1:]                                # ... and its slot rotates: confirmed
            lines += [rframe_hand(t + 6 + 2 * i, hand) for i in range(3)]
            t += 12
    end = lambda i: setattr(FakeGuard.inst, "menu", "results") if FakeGuard.inst and i == len(lines) - 1 else None
    why, samplers, taps, pilot = run_match(monkeypatch, tmp_path, lines, False, on_line=end, menu_guard=True)
    ev = [json.loads(ln) for ln in next(tmp_path.glob("live_play_*.jsonl")).read_text().splitlines()]
    return why, [e["event"] for e in ev]


def test_spread_unconfirmed_do_not_stop_but_five_in_a_row_do(monkeypatch, tmp_path):
    why, ev = unconfirmed_run(monkeypatch, tmp_path, confirm_between=True)
    assert ev.count("unconfirmed") >= 5 and ev.count("confirmed") >= 4 and why != "5_unconfirmed", (why, ev.count(
        "unconfirmed"), ev.count("confirmed"))
    for old in tmp_path.glob("live_play_*.jsonl"):
        old.unlink()
    why, ev = unconfirmed_run(monkeypatch, tmp_path, confirm_between=False)
    assert why == "5_unconfirmed" and ev.count("unconfirmed") == 5 and ev.count("confirmed") == 0


# ---- 2026-09-30 batch: late in-match taps (F1), sampler kill retry (F2), fixed invite wait (T9) ---------------------
@pytest.fixture(autouse=True)
def _fresh_inputs():
    lp.INPUTS.update(in_flight=0, last_t=0.0, timed_out=False)   # module-level in-match input state
    yield
    lp.INPUTS.update(in_flight=0, last_t=0.0, timed_out=False)


def test_timed_out_tap_ends_tapping_for_that_match(monkeypatch, tmp_path):
    lines = [rframe(t) for t in range(150, 500, 2)]
    why, samplers, taps, pilot = run_match(monkeypatch, tmp_path, lines, False, tap_timeout_at=1)
    assert why == "tap_timeout" and len(taps) == 1 and lp.INPUTS["timed_out"]


def test_nav_waits_for_inflight_input_and_the_quiet_period(monkeypatch):
    sent = []
    monkeypatch.setattr(lp, "adb", lambda *a, **k: (sent.append((a[-1], _time.time())), _time.sleep(
        1.0 if "input tap" in a[-1] else 0))[-1] or "")
    th = threading.Thread(target=lp.input_cmd, args=("input tap 1 2",))
    th.start()
    _time.sleep(0.2)
    assert lp.INPUTS["in_flight"] == 1
    t0 = _time.time()
    lp.wait_inputs_quiet(quiet_s=0.5)                   # in flight: waits for it to return, then 0.5 s quiet
    assert not th.is_alive() and _time.time() - t0 >= 0.8 + 0.5 - 0.05
    lp.INPUTS["timed_out"] = True                      # a timed-out tap -> pkill "input tap" + the quiet again
    t1 = _time.time()
    lp.wait_inputs_quiet(quiet_s=0.5)
    assert any(c == 'pkill -f "input tap"' for c, _ in sent) and _time.time() - t1 >= 0.5 - 0.05


def test_main_starts_nav_only_after_the_quiet_period(monkeypatch):
    events = []
    monkeypatch.setattr(lp, "NAV_QUIET_S", 1.0)
    monkeypatch.setattr(lp, "adb", lambda *a, **k: "")

    class FakeNav:
        def __init__(self, *a, **k):
            pass

        def probe(self):
            return None                                 # a battle is running at launch: play it

        def run(self):
            events.append(("nav", _time.time()))
            return True, "handoff"

    class NoModel:
        def __init__(self, *a, **k):
            pass

        def reset_match(self):
            pass

    def fake_play(a, *r, **k):
        lp.input_cmd("input tap 1 2")                   # the match's last input
        events.append(("tap", _time.time()))
        return "battle_inactive"
    monkeypatch.setattr(fn, "FriendNav", FakeNav)
    monkeypatch.setattr(lp, "screen_size", lambda: (900, 1600))
    monkeypatch.setattr(lp, "GenPilot", NoModel)
    monkeypatch.setattr(lp, "play_match", fake_play)
    monkeypatch.setattr(sys, "argv", ["live_play.py", "--matches", "2", "--friend", "JinxTheCat"])
    assert lp.main() == 0
    (k1, t_tap), (k2, t_nav) = events[0], events[1]
    assert (k1, k2) == ("tap", "nav") and t_nav - t_tap >= 1.0 - 0.05


def test_invite_wait_fixed_20s_and_random_only_after_a_cross():
    nav = fn.Nav(0.0, random.Random(0))
    social = CLF.classify(img("friends_list_130915"))
    assert nav.plan(social, 19.9)[0] == "wait"                               # no invite of ours before 20 s
    assert nav.plan(social, 20.1)[:2] == ("act", "friend_row")
    nav = fn.Nav(0.0, random.Random(0))
    assert nav.plan(CLF.classify(img("invite_incoming_131227")), 15.0)[:2] == ("act", "invite_accept")
    delays = set()
    for seed in range(5):                                                      # crossed: random 5-20 s re-delay
        nav = fn.Nav(0.0, random.Random(seed))
        nav.acted("invite_cancel_ours", 30.0)
        assert 35.0 <= nav.wait_until <= 50.0
        delays.add(round(nav.wait_until, 3))
    assert len(delays) == 5
    assert fn.Nav(0.0, random.Random(0), invite_wait=7.5).wait_until == 7.5  # --invite-wait
