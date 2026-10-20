"""Between-match navigation for live_play.py --matches N: start the next FRIENDLY 1v1 battle against ONE friend.

This module is the optional friend-match navigation route. It taps only the allowlisted targets in TARGETS, each
only after its screen was recognised (template matching
on `adb exec-out screencap` frames against scratchpad/gauntlet/L69/nav/templates/manifest.json), and every input goes
through command_for() -- the one place that builds an `input` command. The main screen's yellow Battle button,
Quickplay and Add Friends are FORBIDDEN rectangles no target may reach (see EXEMPT for the one documented overlap).

Invite protocol ("accept, else invite after delay"): after a match wait --invite-wait (20 s) on the Social tab for the
friend's invite; if none, send ours; if both are up (crossed) cancel ours, accept theirs. Stops (never taps blindly):
unrecognised screen > 20 s, results screen whose opponent is not the friend, > 180 s for the whole transition.

    # watch the screens and log the tap it WOULD make (never taps); the owner navigates by hand:
    icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L68/live_reader/live_play.py \
        --nav-dry-run --friend JinxTheCat
"""
from __future__ import annotations

import json
import random
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parents[1] / "L69" / "nav" / "templates"

# ---- the allowlist: the ONLY inputs this module can produce -------------------------------------------------------
# tap targets: rectangle the tap point must lie in; swipe targets: fixed (x0, y0, x1, y1, ms). 900x1600 frame.
TARGETS = {
    "results_ok": ("tap", (330, 1395, 570, 1505)),
    "main_to_social": ("swipe", (700, 800, 150, 800, 300)),      # swipe LEFT on the main screen -> Social tab
    "social_scroll": ("swipe", (620, 1100, 620, 800, 600)),      # slow drag up inside the list (no fling)
    "social_scroll_top": ("swipe", (620, 800, 620, 1100, 600)),  # slow drag DOWN: content moves down, toward the top
    "friend_row": ("tap", (85, 580, 825, 1149)),
    "popup_friendly_battle": ("tap", (10, 500, 289, 1500)),
    "battle_type_1v1": ("tap", (44, 384, 858, 504)),
    "invite_accept": ("tap", (440, 0, 720, 1149)),
    "invite_cancel_ours": ("tap", (620, 60, 880, 260)),
}
FORBIDDEN = {                                                    # measured on after_ok_131638 / friends_list_130251
    "battle_button": (290, 1150, 625, 1350),                     # yellow Battle (305-605 x 1168-1335) + margin
    "quickplay": (60, 1275, 400, 1380),                          # (69-393 x 1284-1369)
    "add_friends": (405, 1275, 740, 1375),                       # (411-731 x 1284-1368)
}
# friend_entry_130350: the popup's Friendly Battle button (88-299 x 1267-1356) is drawn ON TOP of Quickplay's screen
# area, so that one target may land inside the Quickplay rectangle -- only after the popup was verified (header =
# friend, button at its offset, the popup's white body on both sides of the button, where Quickplay is blue).
EXEMPT = {"popup_friendly_battle": {"quickplay"}}


class NavViolation(RuntimeError):
    pass


def _inside(pt, r) -> bool:
    return r[0] <= pt[0] <= r[2] and r[1] <= pt[1] <= r[3]


def allowed(target: str, pt) -> bool:
    kind, rect = TARGETS[target]
    return kind == "tap" and _inside(pt, rect) and not any(
        _inside(pt, f) for n, f in FORBIDDEN.items() if n not in EXEMPT.get(target, ()))


def command_for(target: str, pt=None) -> str:
    """The ONLY builder of an `input` command in this module (test_friend_nav checks that statically)."""
    if target not in TARGETS:
        raise NavViolation(f"target {target!r} is not allowlisted")
    kind, spec = TARGETS[target]
    if kind == "swipe":
        if pt is not None:
            raise NavViolation(f"{target} is a fixed swipe")
        return "input swipe {} {} {} {} {}".format(*spec)
    x, y = round(pt[0]), round(pt[1])
    if not allowed(target, (x, y)):
        raise NavViolation(f"{target} tap {(x, y)} outside its region or inside a forbidden rectangle")
    return f"input tap {x} {y}"


# ---- screen classifier --------------------------------------------------------------------------------------------
class Classifier:
    def __init__(self, tdir: Path = TEMPLATES):
        self.man = json.loads((tdir / "manifest.json").read_text())
        self.t = {n: (cv2.imread(str(tdir / e["file"])), e) for n, e in self.man["templates"].items()}

    def _score(self, img, n, r):
        t, _ = self.t[n]
        x0, y0 = max(0, int(r[0])), max(0, int(r[1]))
        sub = img[y0:int(r[3]), x0:int(r[2])]
        if sub.shape[0] < t.shape[0] or sub.shape[1] < t.shape[1]:
            return -1.0, None
        _, s, _, loc = cv2.minMaxLoc(cv2.matchTemplate(sub, t, cv2.TM_CCOEFF_NORMED))
        return float(s), (x0 + loc[0] + t.shape[1] / 2, y0 + loc[1] + t.shape[0] / 2)

    def classify(self, img: np.ndarray | None) -> dict:
        """-> {"screen": results|main|social|popup|popup_other|battle_type|pending|incoming|cross|unknown, points...,
        "scores": {template: best score}}. Name templates are verified at their anchored offset (local window)."""
        sc: dict = {}
        if img is None or img.shape[:2] != (1600, 900):
            return {"screen": "unknown", "scores": sc, "why": "no 900x1600 frame"}

        def find(n):
            e = self.t[n][1]
            s, c = self._score(img, n, e["region"])
            sc[n] = round(s, 3)
            return c if s >= e["threshold"] else None

        def at(n, c, tol=25):                            # template n centred within tol px of c
            t, e = self.t[n]
            h, w = t.shape[:2]
            s, _ = self._score(img, n, (c[0] - w / 2 - tol, c[1] - h / 2 - tol, c[0] + w / 2 + tol, c[1] + h / 2 + tol))
            sc[n] = round(s, 3)
            return s >= e["threshold"]

        def anchor(n, c):                                # where n's anchor template sits, given n's centre
            dx, dy = self.t[n][1]["anchor"]["dxdy"]
            return c[0] - dx, c[1] - dy

        cancel = find("pend_cancel")
        pend = bool(cancel) and at("pend_name", anchor("pend_cancel", cancel))
        acc = find("inc_accept")
        inc = False
        if acc:
            nm = anchor("inc_accept", acc)
            dx, dy = self.t["inc_1v1"][1]["anchor"]["dxdy"]
            inc = at("inc_name", nm) and at("inc_1v1", (nm[0] + dx, nm[1] + dy))
        if pend and inc:
            return {"screen": "cross", "cancel": cancel, "accept": acc, "scores": sc}
        if pend:
            return {"screen": "pending", "cancel": cancel, "scores": sc}
        if inc:
            return {"screen": "incoming", "accept": acc, "scores": sc}
        one = find("bt_1v1")
        if one and find("bt_name"):
            return {"screen": "battle_type", "one": one, "scores": sc}
        fb = find("popup_fb")
        if fb:
            flanks = all(int(img[round(fb[1]), round(fb[0]) + dx].min()) > 240 for dx in (-150, 150)
                         if 0 <= round(fb[0]) + dx < 900)
            if at("popup_hdr", anchor("popup_fb", fb)) and flanks:
                return {"screen": "popup", "fb": fb, "scores": sc}
            return {"screen": "popup_other", "scores": sc}        # someone else's popup: never act on it
        ok = find("results_ok")
        if ok:
            return {"screen": "results", "ok": ok, "friend": find("results_name") is not None, "scores": sc}
        if find("social_hdr"):
            return {"screen": "social", "row": find("row_name"), "scores": sc,     # sig: list pixels, to see
                    "sig": cv2.resize(cv2.cvtColor(img[580:1245, 85:825], cv2.COLOR_BGR2GRAY), (74, 66),
                                      interpolation=cv2.INTER_AREA)}                  # when a scroll stops moving
        if find("main_tab"):
            return {"screen": "main", "scores": sc}
        return {"screen": "unknown", "scores": sc}


# ---- invite state machine (pure: no I/O, time passed in) -----------------------------------------------------------
class Nav:
    UNKNOWN_S, TRANSITION_S, HANDOFF_S, GRACE_S, FOREIGN_N = 20.0, 180.0, 3.0, 10.0, 3
    MAX_TOP, MAX_SCAN, SAME_SIG = 6, 8, 2.0       # list search: swipes to the top, swipes down; "unmoved" diff

    def __init__(self, t0: float, rng: random.Random | None = None, friend: str = "the friend",
                 invite_wait: float = 20.0):
        self.rng, self.friend, self.invite_wait = rng or random.Random(), friend, invite_wait
        self.t0 = t0
        self.wait_until = t0 + invite_wait                # owner: wait 20 s for the friend's invite before ours
        self.unknown_since: float | None = None
        self.commit_t: float | None = None               # last time our invite was pending / theirs accepted
        self.foreign = 0
        self.prev_screen: str | None = None             # last RECOGNISED screen (unknown frames ignored)
        self._reset_search()

    def _reset_search(self) -> None:
        """Friend-list search: scroll to the TOP first (until the list stops moving), then scan down to the bottom.
        Reset whenever Social is (re-)entered, e.g. after an expired invite (verifier 2026-09-30)."""
        self.phase, self.top_n, self.scan_n, self.sig, self.sig_before = "top", 0, 0, None, None

    def plan(self, scr: dict, now: float) -> tuple:
        """-> ("act", target, point) | ("wait", why) | ("handoff", why) | ("stop", why)."""
        if now - self.t0 > self.TRANSITION_S:
            return ("stop", f"transition over {self.TRANSITION_S:.0f} s")
        s = scr["screen"]
        if s in ("unknown", "popup_other"):
            self.unknown_since = self.unknown_since if self.unknown_since is not None else now
            idle = now - self.unknown_since
            if self.commit_t is not None and idle >= self.HANDOFF_S:
                return ("handoff", "menus left after the invite: battle loading")
            if idle > self.UNKNOWN_S:
                return ("stop", f"unrecognised screen ({s}) for {self.UNKNOWN_S:.0f} s")
            return ("wait", s)
        self.unknown_since = None
        if s == "social" and self.prev_screen != "social":
            self._reset_search()
        self.prev_screen = s
        if s == "results":
            if not scr["friend"]:
                self.foreign += 1
                if self.foreign >= self.FOREIGN_N:
                    return ("stop", "results screen: opponent is not the friend")
                return ("wait", "results: opponent name not verified")
            self.foreign = 0
            return ("act", "results_ok", scr["ok"])
        if s == "main":
            return ("act", "main_to_social", None)
        if s == "cross":
            return ("act", "invite_cancel_ours", scr["cancel"])
        if s == "incoming":
            return ("act", "invite_accept", scr["accept"])
        if s == "pending":
            self.commit_t = now
            return ("wait", "our invite is pending")
        if s == "battle_type":
            return ("act", "battle_type_1v1", scr["one"])
        if s == "popup":
            return ("act", "popup_friendly_battle", scr["fb"])
        # social list
        if self.commit_t is not None:
            if now - self.commit_t < self.GRACE_S:
                return ("wait", "invite accepted/pending: waiting for the battle")
            self.commit_t, self.wait_until = None, now + self.invite_wait   # the invite died: start over
        if now < self.wait_until:
            return ("wait", f"waiting {self.wait_until - now:.1f} s more for the friend's invite")
        row = scr.get("row")
        if row and allowed("friend_row", row):           # visible (in any phase): tap it as before
            return ("act", "friend_row", row)
        self.sig = scr.get("sig")
        unmoved = (self.sig is not None and self.sig_before is not None
                   and float(np.abs(self.sig.astype(int) - self.sig_before).mean()) < self.SAME_SIG)
        if self.phase == "top":
            if self.top_n < self.MAX_TOP and not unmoved:
                return ("act", "social_scroll_top", None)
            self.phase, self.sig_before, unmoved = "scan", None, False   # at the top / limit: now scan down
        if self.scan_n < self.MAX_SCAN and not unmoved:
            return ("act", "social_scroll", None)
        return ("stop", f"friend {self.friend} not found in the Social list (offline or not visible)")

    def acted(self, target: str, now: float) -> None:
        if target in ("social_scroll", "social_scroll_top"):
            self.sig_before = self.sig                   # the list as it was before this swipe
            self.top_n += target == "social_scroll_top"
            self.scan_n += target == "social_scroll"
        elif target == "invite_accept":
            self.commit_t = now
        elif target == "invite_cancel_ours":             # crossed: a fresh random delay breaks the mirror symmetry
            self.commit_t, self.wait_until = None, now + self.rng.uniform(5, 20)


def grab(adb: list[str]) -> np.ndarray | None:
    from hero_button import parse_raw_screencap
    try:
        raw = subprocess.run(adb + ["exec-out", "screencap"], capture_output=True, timeout=5).stdout
        return parse_raw_screencap(raw)
    except Exception:                                    # noqa: BLE001 -- a missed grab is an unknown frame
        return None


# ---- in-match menu guard ------------------------------------------------------------------------------------------
MENU_SCREENS = {"results", "main", "social", "popup", "popup_other", "battle_type", "pending", "incoming", "cross"}


class MenuGuard:
    """In-match safety net for live_play: if the SCREEN shows a menu while the reader still says "battle", a card
    tap could land on a menu button (249/1378 past board taps fall inside the main screen's Battle button). A frame
    at least every period_s -- HeroButton's own grabs via feed(), else a screencap here -- is classified; .menu is
    the first menu screen seen (sticky). Armed by live_play once the battle clock runs (the script may be started
    from a menu in the Training Camp flow; no tap can happen before the clock runs anyway). FAILS CLOSED: clear()
    is True only after a successful, non-menu classification of a 900x1600 screenshot GRABBED after arming, at most
    FRESH_S old; a failed grab is not a success. 194 frames sampled from recorded live matches classify 'unknown'."""
    FRESH_S = 8.0     # 5 -> 8 s (2026-09-30 live stop: adb saturated by a concurrent job, tap_ms 4358, backlog 48)

    def __init__(self, adb: list[str], period_s: float = 2.0, clf: Classifier | None = None):
        import threading
        self.adb, self.period, self.clf = adb, period_s, clf or Classifier()
        self.menu: str | None = None
        self.last_ts, self._stop, self.armed = 0.0, False, False
        self.armed_at: float | None = None
        self.ok_ts: float | None = None                  # grab time of the last successful non-menu classification
        threading.Thread(target=self._run, daemon=True).start()

    def arm(self) -> None:
        self.armed_at, self.armed = time.time(), True

    def feed(self, img: np.ndarray | None, t_grab: float | None = None) -> None:
        """img grabbed at t_grab (default: now). Only a grab started after arming counts."""
        t_grab = time.time() if t_grab is None else t_grab
        self.last_ts = time.time()
        if not self.armed or img is None or img.shape[:2] != (1600, 900) or t_grab < self.armed_at:
            return
        s = self.clf.classify(img)["screen"]
        if s in MENU_SCREENS:
            if self.menu is None:
                self.menu = s
        elif self.ok_ts is None or t_grab > self.ok_ts:
            self.ok_ts = t_grab

    def clear(self, now: float) -> bool:
        """Taps allowed: armed, no menu ever seen, and a fresh successful classification."""
        return self.armed and self.menu is None and self.ok_ts is not None and now - self.ok_ts <= self.FRESH_S

    def blind_s(self, now: float) -> float:
        """Seconds without a successful classification since arming (0 before arming)."""
        return 0.0 if not self.armed else now - (self.ok_ts if self.ok_ts is not None else self.armed_at)

    def _run(self) -> None:
        while not self._stop and self.menu is None:
            if self.armed and time.time() - self.last_ts >= self.period:
                t = self.last_ts = time.time()           # claim the slot before the ~0.3 s grab
                try:
                    self.feed(grab(self.adb), t)
                except Exception:                        # noqa: BLE001 -- no success recorded: taps stay blocked
                    pass
            time.sleep(0.2)

    def stop(self) -> None:
        self._stop = True


# ---- device runner ------------------------------------------------------------------------------------------------
class FriendNav:
    POLL_S, COOLDOWN_S = 0.5, 1.5

    def __init__(self, adb: list[str], friend: str, dry_run: bool = False, log_dir: Path = HERE,
                 invite_wait: float = 20.0):
        self.adb, self.dry_run, self.log_dir, self.friend = adb, dry_run, log_dir, friend
        self.invite_wait = invite_wait
        self.clf = Classifier()
        if friend != self.clf.man["friend"]:
            raise SystemExit(f"refusing: --friend {friend!r} but the nav templates were cropped for "
                             f"{self.clf.man['friend']!r} (re-crop templates for another friend)")

    def grab(self) -> np.ndarray | None:
        return grab(self.adb)

    NAV_SCREENS = {"main", "social", "popup", "battle_type", "pending", "incoming", "cross", "results"}

    def probe(self, seconds: float = 8.0) -> str | None:
        """Before match 1: the first recognised nav screen within `seconds` (-> navigate to start the match), or
        None when only unrecognised screens (a battle / loading already running: just play it)."""
        t_end = time.time() + seconds
        while time.time() < t_end:
            s = self.clf.classify(self.grab())["screen"]
            if s in self.NAV_SCREENS:
                print(f"[nav] launch screen: {s} -- navigating to start match 1", flush=True)
                return s
            time.sleep(self.POLL_S)
        print(f"[nav] no menu screen in {seconds:.0f} s -- assuming a battle is running: playing it", flush=True)
        return None

    def run(self) -> tuple[bool, str]:
        """One transition: results -> ... -> battle loading. -> (True, why) on handoff, (False, why) on stop."""
        stamp = time.strftime("%Y%m%d_%H%M%S")
        log = open(self.log_dir / f"nav_{stamp}.jsonl", "w", encoding="utf-8")

        def W(**k):
            log.write(json.dumps({"t": round(time.time(), 2), **k}, default=str) + "\n")
            log.flush()
        nav, prev, last = Nav(time.time(), friend=self.friend, invite_wait=self.invite_wait), None, None
        W(event="nav_start", dry_run=self.dry_run, wait_s=round(nav.wait_until - nav.t0, 1))
        print(f"[nav] {'DRY-RUN ' if self.dry_run else ''}start (log {log.name}); friend-invite wait "
              f"{nav.wait_until - nav.t0:.1f} s", flush=True)
        try:
            while True:
                img = self.grab()
                scr = self.clf.classify(img)
                p = nav.plan(scr, time.time())
                if (scr["screen"], p[:2]) != last:       # log changes only
                    W(event="screen", screen=scr["screen"], plan=p, scores=scr["scores"])
                    print(f"[nav] {scr['screen']}: {p}", flush=True)
                    last = (scr["screen"], p[:2])
                if p[0] in ("handoff", "stop"):
                    if p[0] == "stop" and img is not None:
                        cv2.imwrite(str(self.log_dir / f"nav_stop_{stamp}.png"), img)
                    W(event=p[0], why=p[1])
                    print(f"[nav] {p[0].upper()}: {p[1]}", flush=True)
                    return p[0] == "handoff", p[1]
                if p[0] == "act":
                    # act only when two consecutive frames planned the same input (no tap on a transient frame)
                    same = prev and prev[1] == p[1] and (p[2] is None or max(abs(prev[2][0] - p[2][0]),
                                                                            abs(prev[2][1] - p[2][1])) <= 8)
                    if same:
                        cmd = command_for(p[1], p[2])
                        W(event="input", target=p[1], cmd=cmd, dry_run=self.dry_run)
                        print(f"[nav] {'WOULD ' if self.dry_run else ''}{p[1]}: {cmd}", flush=True)
                        if not self.dry_run:
                            subprocess.run(self.adb + ["shell", cmd], capture_output=True, timeout=5)
                        nav.acted(p[1], time.time())
                        prev = None
                        time.sleep(self.COOLDOWN_S)
                        continue
                    prev = p
                else:
                    prev = None
                time.sleep(self.POLL_S)
        finally:
            log.close()
