"""L67: audit two live screen readers -- the per-unit HP-bar fraction reader
(``detect_obs.read_hp_frac``) and per-track unit velocity (``replay_mine.TeamTracker``) --
on a recorded RAW session, with no ground-truth labels.

    python tools/live_reader_audit.py <session dir> <stdout log> --out <dir>

WHY SELF-CONSISTENCY, NOT LABELS
---------------------------------
There is no ground truth painted on the live screen. Every check here is a PROXY built from
facts the game itself guarantees:

  * a card WE just played can only be OUR unit, and it starts undamaged -> its first HP read
    should be ~1.0 (the "at-deploy" check);
  * an alive unit's true HP fraction cannot legitimately climb by a lot without a heal/shield
    (there are none in this deck) -> a big consecutive INCREASE is suspicious (monotonicity);
  * a real HP value should not swing wildly between two reads 0.2s apart on an undamaged-ish
    unit -> jitter measures reader noise, not game truth;
  * every troop's ground speed is a published game constant (config/cards_stats.json,
    ``speed_tiles``, tiles/second) -> comparing the tracker's measured speed to that constant is
    the only speed check available with no ground-truth trajectories.

None of these prove correctness on any single frame; each is a lower/upper bound or a proxy,
spelled out under "limitations" in the report.

MIRRORS live play.py, NOT LiveMatchEnv
---------------------------------------
Like tools/detector_audit.py, this builds the detector + TeamTracker DIRECTLY and stamps every
read with the RECORDING's own capture time (meta.json start_time + frame_times[i]), never the
processing wall clock -- see detector_audit.py's module docstring for why that distinction
matters (a live-thread snapshot or wall-clock stamping silently invalidates every number).

READ-ONLY on icebow/data -- only cv2.VideoCapture(...).read() calls into the session folder.
"""
from __future__ import annotations

import argparse
import datetime
import itertools
import json
import math
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

_ROOT = Path(__file__).resolve().parents[1]          # icebow/
sys.path.insert(0, str(_ROOT / "src"))

from clashrl.config import Config                      # noqa: E402
from clashrl.cards import CardDB                        # noqa: E402
from clashrl import card_threat                         # noqa: E402
from clashrl.actions import ActionSpace                 # noqa: E402
from clashrl.vision import Vision                       # noqa: E402
from clashrl.states import GameState                    # noqa: E402
from clashrl.detect_obs import read_hp_frac             # noqa: E402
from clashrl.replay_mine import load_detector, TeamTracker, own_card_bases  # noqa: E402
from clashrl.hero_ability import TILE_X, TILE_Y          # noqa: E402

PLAY_RE = re.compile(
    r"\[student\] (?:PLAY|STALL-PLAY) (\S+) p=[0-9.]+ cell (\d+) .*?wall=(\d\d):(\d\d):(\d\d)\.(\d{3})")

# ---- audit thresholds (fixed here so the report's numbers are reproducible) ----------------
DEPLOY_WINDOW_S = 1.5          # "appears within ~1.5s near the play" (ticket wording)
DEPLOY_RADIUS = 0.15           # normalized frame distance from the tap point
JITTER_DT_LO, JITTER_DT_HI = 0.15, 0.35     # "~0.2s apart"
MAX_SEG_DT = 1.0               # a bigger gap between consecutive reads of one track is a
                                # detector miss bridging, not a clean two-frame estimate
MOVE_MIN_TILES_S = 0.15        # below this, a "moving" segment is more likely position jitter
STRAIGHT_ANGLE_DEG = 30.0      # consecutive-segment heading change under this = "straight"
MIN_CLASS_SAMPLES = 8          # "enough samples" for a per-class speed number
HP_FOUND_EPS = 0.999           # read_hp_frac returns exactly 1.0 as its "no bar found" sentinel


def _wall_to_video_t(hh, mm, ss, ms, sess_date, start_time, roll_state):
    s = hh * 3600 + mm * 60 + ss + ms / 1000.0
    if roll_state["last"] is not None and s < roll_state["last"] - 6 * 3600:
        roll_state["roll"] += 1
    roll_state["last"] = s
    d = sess_date + datetime.timedelta(days=roll_state["roll"])
    dt = datetime.datetime.combine(d, datetime.time(hh, mm, ss, ms * 1000))
    return dt.timestamp() - start_time


def parse_plays(log_path: Path, sess_date, start_time: float):
    """[(video_t, card, cell), ...] for every [student] PLAY / STALL-PLAY line, sorted by time.
    STALL-PLAY is included -- it is still a real tap the game accepted, same at-deploy contract."""
    out = []
    roll_state = {"last": None, "roll": 0}
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = PLAY_RE.search(line)
        if not m:
            continue
        card, cell, hh, mm, ss, ms = m.groups()
        vt = _wall_to_video_t(int(hh), int(mm), int(ss), int(ms), sess_date, start_time, roll_state)
        out.append((vt, card, int(cell)))
    out.sort(key=lambda p: p[0])
    return out


def _make_crop(frame, d):
    fh, fw = frame.shape[:2]
    top = d.gy - d.h
    y0 = max(0.0, top - 0.06)
    y1 = min(1.0, d.gy + d.h * 0.35)
    x0 = max(0.0, d.cx - d.w * 0.9)
    x1 = min(1.0, d.cx + d.w * 0.9)
    py0, py1 = int(y0 * fh), max(int(y0 * fh) + 4, int(y1 * fh))
    px0, px1 = int(x0 * fw), max(int(x0 * fw) + 8, int(x1 * fw))
    return frame[py0:py1, px0:px1].copy()


def _tile_crops(entries, out_path: Path, cols: int = 6):
    if not entries:
        cv2.imwrite(str(out_path), np.full((60, 200, 3), 30, np.uint8))
        return
    cell_w, cell_h, label_h = 168, 110, 18
    rows = math.ceil(len(entries) / cols)
    canvas = np.full((rows * (cell_h + label_h), cols * cell_w, 3), 30, np.uint8)
    for i, (crop, hp, base, team, found) in enumerate(entries):
        r, c = divmod(i, cols)
        if crop is None or crop.size == 0:
            continue
        ch, cw = crop.shape[:2]
        scale = min((cell_w - 4) / cw, (cell_h - 4) / ch)
        rw, rh = max(1, int(cw * scale)), max(1, int(ch * scale))
        resized = cv2.resize(crop, (rw, rh))
        y0 = r * (cell_h + label_h) + (cell_h - rh) // 2
        x0 = c * cell_w + (cell_w - rw) // 2
        canvas[y0:y0 + rh, x0:x0 + rw] = resized
        label = f"{base[:11]} {team[0]} {'%.2f' % hp if found else 'nobar'}"
        col = (140, 255, 140) if found else (150, 150, 255)
        cv2.putText(canvas, label, (c * cell_w + 3, r * (cell_h + label_h) + cell_h + 13),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, col, 1, cv2.LINE_AA)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), canvas)


def _median(xs):
    return float(np.median(xs)) if xs else None


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("session_dir")
    ap.add_argument("log")
    ap.add_argument("--out", required=True)
    ap.add_argument("--hz", type=float, default=5.0, help="max processing rate (default 5 Hz)")
    ap.add_argument("--max-minutes", type=float, default=20.0, help="wall-clock processing budget")
    ap.add_argument("--crops", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)

    session_dir = Path(a.session_dir)
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed)

    meta = json.loads((session_dir / "meta.json").read_text(encoding="utf-8"))
    fps = float(meta["fps"])
    start_time = float(meta["start_time"])
    frame_times = meta["frame_times"]
    sess_date = datetime.datetime.fromtimestamp(start_time).date()

    plays = parse_plays(Path(a.log), sess_date, start_time)
    print(f"[audit] parsed {len(plays)} PLAY/STALL-PLAY events; session date {sess_date}")

    cfg = Config.load()
    db = CardDB(cfg)
    own = own_card_bases(db)
    actions = ActionSpace(cfg)
    gw = int(actions.gw)
    vision = Vision(cfg)
    detector_conf = float(cfg.get("observation", "detector_conf", default=0.75))

    det = load_detector(cfg)
    if not det.available:
        print("ERROR: no detector weights available -- nothing to audit")
        return 2

    tracker = TeamTracker(
        own_cards=own,
        is_building=lambda b, _db=db: _db.kind(b) == "building",
        is_spell=lambda b, _db=db: _db.kind(card_threat.base_key(str(b))) == "spell",
        spawn_radius=float(cfg.get("observation", "team_spawn_radius", default=0.10)),
        spawn_window_s=float(cfg.get("observation", "team_spawn_window_s", default=2.5)),
        enemy_window_s=float(cfg.get("observation", "team_enemy_window_s", default=4.0)),
        track_radius=float(cfg.get("observation", "team_track_radius", default=0.12)),
        forget_s=float(cfg.get("observation", "team_forget_s", default=4.5)),
        motion_min=float(cfg.get("observation", "team_motion_min", default=0.05)),
        deep_mine_y=float(cfg.get("observation", "team_deep_mine_y", default=0.62)),
        deep_enemy_y=float(cfg.get("observation", "team_deep_enemy_y", default=0.38)),
        min_hits=int(cfg.get("observation", "team_track_min_hits", default=2)),
        phantom_stale_s=float(cfg.get("observation", "team_phantom_stale_s", default=6.0)),
    )
    # No live tower-HP reader is run offline (out of scope for this audit) -- towers are assumed
    # alive throughout, same simplification tools/detector_audit.py documents ("no pocket gating
    # offline"). This can only ever WEAKEN the deep-half side prior near a fallen tower; it cannot
    # affect the own-play anchor (rank 1) that the at-deploy check relies on.
    tracker.set_towers([True, True], [True, True])
    min_hits = tracker.min_hits

    video_path = session_dir / "video.mp4"
    cap = cv2.VideoCapture(str(video_path))
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or int(meta["n_frames"])
    stride = max(1, math.ceil(fps / a.hz))
    print(f"[audit] video: {n_frames} frames @ {fps:.2f} fps; stride {stride} "
          f"(~{fps / stride:.2f} Hz); budget {a.max_minutes:g} min")

    t0 = time.time()
    budget_s = a.max_minutes * 60.0
    stop_reason = "completed the session"

    play_ptr = 0
    n_state_checked = n_in_match = n_frames_processed = n_dets = 0
    last_video_t = 0.0

    read_by_team = defaultdict(lambda: [0, 0])      # team -> [n_found, n_total]
    read_by_class = defaultdict(lambda: [0, 0])
    track_hist = defaultdict(list)                  # aid -> [{"t","x","y","team","base","hp"}]
    aid_of = {}                                     # id(trk dict) -> aid, since trk dicts persist
    aid_counter = itertools.count(1)
    all_dets_log = []                               # (t, base, cx, gy, hp, team) -- for the at-deploy check
    crop_pool_found, crop_pool_unfound = [], []
    CROP_POOL_CAP = 600

    idx = 0
    while idx < n_frames:
        ok = cap.grab()
        if not ok:
            stop_reason = f"video read ended at frame {idx}"
            break
        idx_cur = idx
        idx += 1
        if idx_cur % stride != 0:
            continue
        if time.time() - t0 > budget_s:
            stop_reason = f"time budget ({a.max_minutes:g} min) reached at frame {idx_cur}"
            break
        ok, frame = cap.retrieve()
        if not ok or frame is None:
            continue
        video_t = frame_times[idx_cur] if idx_cur < len(frame_times) else idx_cur / fps
        last_video_t = video_t
        n_state_checked += 1
        if vision.detect_state(frame) != GameState.IN_MATCH:
            continue
        n_in_match += 1

        while play_ptr < len(plays) and plays[play_ptr][0] <= video_t:
            pvt, card, cell = plays[play_ptr]
            base = card_threat.base_key(card)
            gx, gy = cell % gw, cell // gw
            cx, cy = actions.cell_center(gx, gy)
            tracker.record_play(cx, cy, pvt, base=base)
            play_ptr += 1

        try:
            dets = det.detect(frame, conf=detector_conf)
        except Exception as e:  # noqa: BLE001
            print(f"[audit] detector call failed at t={video_t:.1f}s: {type(e).__name__}: {e}")
            continue
        tracker.tag(dets, video_t)
        n_frames_processed += 1

        for d in dets:
            n_dets += 1
            hp = read_hp_frac(frame, d)
            found = hp < HP_FOUND_EPS
            read_by_team[d.team][1] += 1
            read_by_team[d.team][0] += int(found)
            read_by_class[d.base][1] += 1
            read_by_class[d.base][0] += int(found)
            all_dets_log.append((video_t, d.base, d.cx, d.gy, hp, d.team))

            aid = None
            for trk in tracker._tracks:                              # noqa: SLF001 (offline audit, read-only use)
                if trk.get("t") == video_t and trk.get("base") == d.base \
                        and trk.get("x") == d.cx and trk.get("y") == d.gy:
                    aid = aid_of.get(id(trk))
                    if aid is None:
                        aid = next(aid_counter)
                        aid_of[id(trk)] = aid
                    break
            if aid is None:
                aid = next(aid_counter)
            track_hist[aid].append({"t": video_t, "x": d.cx, "y": d.gy, "team": d.team,
                                     "base": d.base, "hp": hp})

            pool = crop_pool_found if found else crop_pool_unfound
            entry = (_make_crop(frame, d), hp, d.base, d.team, found)
            if len(pool) < CROP_POOL_CAP:
                pool.append(entry)
            else:
                j = rng.randint(0, len(pool) - 1)
                if rng.random() < CROP_POOL_CAP / max(1, n_dets):
                    pool[j] = entry
    cap.release()
    elapsed_s = time.time() - t0
    print(f"[audit] {stop_reason}; processed {n_frames_processed} in-match frames "
          f"({n_in_match}/{n_state_checked} state-checked frames were IN_MATCH) in {elapsed_s:.1f}s, "
          f"{n_dets} detections")

    # ---- HP read-rate -----------------------------------------------------------------------
    def _rate(pair):
        found, total = pair
        return (found / total if total else None), total

    read_rate_overall = _rate((sum(v[0] for v in read_by_team.values()),
                                sum(v[1] for v in read_by_team.values())))
    read_rate_by_team = {t: _rate(v) for t, v in sorted(read_by_team.items(), key=lambda kv: -kv[1][1])}
    top_classes = sorted(read_by_class.items(), key=lambda kv: -kv[1][1])[:10]
    read_rate_by_class = {c: _rate(v) for c, v in top_classes}

    qualifying_tracks = {aid: hist for aid, hist in track_hist.items() if len(hist) >= min_hits}
    track_found_ever = [any(s["hp"] < HP_FOUND_EPS for s in hist) for hist in qualifying_tracks.values()]
    track_read_rate = (sum(track_found_ever) / len(track_found_ever)) if track_found_ever else None
    track_read_by_team = defaultdict(lambda: [0, 0])
    for hist in qualifying_tracks.values():
        team = hist[-1]["team"]
        track_read_by_team[team][1] += 1
        track_read_by_team[team][0] += int(any(s["hp"] < HP_FOUND_EPS for s in hist))
    track_read_rate_by_team = {t: _rate(v) for t, v in track_read_by_team.items()}

    # ---- at-deploy check ----------------------------------------------------------------------
    deploy_hits, deploy_misses = [], 0
    deploy_considered = 0
    for pvt, card, cell in plays:
        if pvt > last_video_t:
            continue                                          # play happened after our processed window
        deploy_considered += 1
        base = card_threat.base_key(card)
        gx, gy = cell % gw, cell // gw
        cx, cy = actions.cell_center(gx, gy)
        cand = [(t, hp) for (t, b, x, y, hp, _team) in all_dets_log
                if b == base and pvt - 0.1 <= t <= pvt + DEPLOY_WINDOW_S
                and math.hypot(x - cx, y - cy) <= DEPLOY_RADIUS]
        if not cand:
            deploy_misses += 1
            continue
        cand.sort(key=lambda c: c[0])
        deploy_hits.append(cand[0][1])
    deploy_median = _median(deploy_hits)
    deploy_share_ge_09 = (sum(h >= 0.9 for h in deploy_hits) / len(deploy_hits)) if deploy_hits else None
    deploy_share_lt_07 = (sum(h < 0.7 for h in deploy_hits) / len(deploy_hits)) if deploy_hits else None

    # ---- monotonicity + jitter (found reads only, per qualifying track) -----------------------
    mono_inc, mono_total = 0, 0
    jitter_diffs = []
    for hist in qualifying_tracks.values():
        found_seq = sorted([(s["t"], s["hp"]) for s in hist if s["hp"] < HP_FOUND_EPS])
        for (t0_, h0), (t1_, h1) in zip(found_seq, found_seq[1:]):
            mono_total += 1
            if h1 - h0 > 0.10:
                mono_inc += 1
            dt = t1_ - t0_
            if JITTER_DT_LO <= dt <= JITTER_DT_HI:
                jitter_diffs.append(abs(h1 - h0))
    mono_share = (mono_inc / mono_total) if mono_total else None
    jitter_median = _median(jitter_diffs)

    # ---- velocity ------------------------------------------------------------------------------
    age_qualify = [ (max(s["t"] for s in hist) - min(s["t"] for s in hist)) >= 0.5
                   for hist in qualifying_tracks.values() ]
    velocity_share = (sum(age_qualify) / len(age_qualify)) if age_qualify else None

    seg_by_class = defaultdict(list)                # base -> [(speed_tiles_s, team)]
    angle_changes_deg = []
    for hist in qualifying_tracks.values():
        seq = sorted(hist, key=lambda s: s["t"])
        segs = []
        for s0, s1 in zip(seq, seq[1:]):
            dt = s1["t"] - s0["t"]
            if dt <= 0 or dt > MAX_SEG_DT:
                continue
            dxt = (s1["x"] - s0["x"]) / TILE_X
            dyt = (s1["y"] - s0["y"]) / TILE_Y
            dist = math.hypot(dxt, dyt)
            speed = dist / dt
            ang = math.degrees(math.atan2(dyt, dxt)) if dist > 1e-9 else None
            segs.append({"speed": speed, "ang": ang, "base": s0["base"], "team": s0["team"]})
        for i in range(1, len(segs)):
            a0, a1 = segs[i - 1]["ang"], segs[i]["ang"]
            if a0 is None or a1 is None:
                continue
            d = abs(a1 - a0) % 360.0
            d = 360.0 - d if d > 180.0 else d
            # Only count this pair toward direction STABILITY when both segments already cleared
            # the "moving" speed floor. A near-stationary segment's displacement is dominated by
            # detection-box jitter, not a real heading -- its "angle" is close to noise, and
            # including it would inflate the instability number for a reason that has nothing to
            # do with direction tracking (see Limitations).
            if segs[i - 1]["speed"] >= MOVE_MIN_TILES_S and segs[i]["speed"] >= MOVE_MIN_TILES_S:
                angle_changes_deg.append(d)
            if segs[i]["speed"] >= MOVE_MIN_TILES_S and d < STRAIGHT_ANGLE_DEG:
                seg_by_class[segs[i]["base"]].append(segs[i]["speed"])

    direction_stability_deg = _median(angle_changes_deg)
    speed_by_class = {}
    for base, speeds in sorted(seg_by_class.items(), key=lambda kv: -len(kv[1])):
        if len(speeds) < MIN_CLASS_SAMPLES:
            continue
        stat = db.get(base) or {}
        card_speed = stat.get("speed_tiles")
        med = _median(speeds)
        p25, p75 = float(np.percentile(speeds, 25)), float(np.percentile(speeds, 75))
        speed_by_class[base] = {
            "n": len(speeds), "median_tiles_s": med, "p25": p25, "p75": p75,
            "card_speed_tiles_s": card_speed,
            "ratio_measured_over_card": (med / card_speed) if card_speed else None,
        }

    # ---- crops --------------------------------------------------------------------------------
    n_found_want = min(len(crop_pool_found), max(0, int(round(a.crops * 0.6))))
    n_unfound_want = min(len(crop_pool_unfound), a.crops - n_found_want)
    n_found_want = min(len(crop_pool_found), a.crops - n_unfound_want)
    chosen = rng.sample(crop_pool_found, n_found_want) if n_found_want else []
    chosen += rng.sample(crop_pool_unfound, n_unfound_want) if n_unfound_want else []
    rng.shuffle(chosen)
    _tile_crops(chosen, out_dir / "hp_crops.png")

    # ---- assemble report ------------------------------------------------------------------------
    report = {
        "command": "python tools/live_reader_audit.py " + " ".join(argv),
        "session_dir": str(session_dir), "log": str(a.log),
        "processing": {
            "video_fps": fps, "video_frames": n_frames, "stride_frames": stride,
            "effective_hz": round(fps / stride, 3), "state_checked_frames": n_state_checked,
            "in_match_frames": n_in_match, "frames_with_detections_pass": n_frames_processed,
            "detections_total": n_dets, "elapsed_s": round(elapsed_s, 1),
            "stop_reason": stop_reason, "min_hits_for_a_track": min_hits,
        },
        "hp_reader": {
            "read_rate_overall": {"share": read_rate_overall[0], "n": read_rate_overall[1]},
            "read_rate_by_team": {t: {"share": s, "n": n} for t, (s, n) in read_rate_by_team.items()},
            "read_rate_by_class_top10": {c: {"share": s, "n": n} for c, (s, n) in read_rate_by_class.items()},
            "track_read_rate_overall": {"share": track_read_rate, "n_tracks": len(track_found_ever)},
            "track_read_rate_by_team": {t: {"share": s, "n_tracks": n} for t, (s, n) in track_read_rate_by_team.items()},
            "at_deploy": {
                "plays_in_window": deploy_considered, "matched": len(deploy_hits),
                "unmatched_no_own_unit_seen": deploy_misses,
                "median_first_read": deploy_median,
                "share_ge_0_90": deploy_share_ge_09, "share_lt_0_70": deploy_share_lt_07,
                "window_s": DEPLOY_WINDOW_S, "radius_norm": DEPLOY_RADIUS,
            },
            "monotonicity": {"share_increase_gt_0_10": mono_share, "n_consecutive_pairs": mono_total},
            "jitter": {"median_abs_diff": jitter_median, "n_pairs_dt_0.15_0.35s": len(jitter_diffs)},
        },
        "velocity": {
            "share_tracks_old_enough": {"share": velocity_share, "n_tracks": len(age_qualify),
                                        "age_threshold_s": 0.5},
            "direction_stability_median_abs_angle_change_deg": direction_stability_deg,
            "n_segment_pairs_for_direction": len(angle_changes_deg),
            "by_class": speed_by_class,
            "thresholds": {"move_min_tiles_s": MOVE_MIN_TILES_S, "straight_angle_deg": STRAIGHT_ANGLE_DEG,
                          "max_segment_dt_s": MAX_SEG_DT, "min_class_samples": MIN_CLASS_SAMPLES,
                          "tile_x_frame_units": TILE_X, "tile_y_frame_units": TILE_Y,
                          "speed_field": "cards_stats.json 'speed_tiles' (tiles per second -- "
                                         "verified against known tiers: giant 0.75 [Slow], "
                                         "ice_wizard 1.0 [Medium], skeletons 1.5 [Fast], "
                                         "hog_rider/ice_spirit 2.0 [Very Fast])"},
        },
    }
    (out_dir / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    _write_md(report, out_dir / "report.md")
    print(f"[audit] wrote {out_dir / 'report.json'}, {out_dir / 'report.md'}, {out_dir / 'hp_crops.png'}")
    return 0


def _pct(x):
    return "n/a" if x is None else f"{100.0 * x:.1f}%"


def _num(x, fmt="%.3f"):
    return "n/a" if x is None else (fmt % x)


def _write_md(r, path: Path) -> None:
    p = r["processing"]
    hp = r["hp_reader"]
    v = r["velocity"]
    lines = []
    lines.append("# Live reader audit -- HP bars + velocity")
    lines.append("")
    lines.append(f"Command: `{r['command']}`")
    lines.append("")
    lines.append(f"Processed {p['frames_with_detections_pass']} in-match frames "
                f"({p['in_match_frames']}/{p['state_checked_frames']} state-checked frames were "
                f"`vision.detect_state == IN_MATCH`) at {p['effective_hz']:.2f} Hz "
                f"({p['detections_total']} detections) in {p['elapsed_s']:.0f}s. Stop reason: {p['stop_reason']}.")
    lines.append("")
    lines.append("## HP-bar fraction reader (`detect_obs.read_hp_frac`)")
    lines.append("")
    lines.append("A read counts as \"found\" when the function returns anything other than its own "
                "1.0 no-bar-found sentinel (see Limitations -- this conflates a genuinely full-health "
                "bar with no bar at all, which is rare because the game itself draws no bar on an "
                "undamaged unit).")
    lines.append("")
    o = hp["read_rate_overall"]
    lines.append(f"- **Read rate, all detections:** {_pct(o['share'])} (n={o['n']})")
    lines.append("- **By team:**")
    for t, d in hp["read_rate_by_team"].items():
        lines.append(f"    - {t}: {_pct(d['share'])} (n={d['n']})")
    lines.append("- **By class (top 10 by detection count):**")
    for c, d in hp["read_rate_by_class_top10"].items():
        lines.append(f"    - {c}: {_pct(d['share'])} (n={d['n']})")
    tr = hp["track_read_rate_overall"]
    lines.append(f"- **Read rate, by TRACK (>=1 found read over the track's life):** {_pct(tr['share'])} "
                f"(n_tracks={tr['n_tracks']}, min_hits={p['min_hits_for_a_track']})")
    for t, d in hp["track_read_rate_by_team"].items():
        lines.append(f"    - {t}: {_pct(d['share'])} (n_tracks={d['n_tracks']})")
    lines.append("")
    dep = hp["at_deploy"]
    lines.append(f"- **At-deploy check** (our own PLAY -> matching own unit within "
                f"{dep['window_s']}s / {dep['radius_norm']} normalized-frame radius of the tap point):")
    lines.append(f"    - plays in the processed window: {dep['plays_in_window']}, matched: {dep['matched']}, "
                f"no own unit seen: {dep['unmatched_no_own_unit_seen']}")
    lines.append(f"    - first HP read -- median: {_num(dep['median_first_read'])}, "
                f"share >= 0.90: {_pct(dep['share_ge_0_90'])}, share < 0.70: {_pct(dep['share_lt_0_70'])}")
    mo = hp["monotonicity"]
    lines.append(f"- **Monotonicity** (consecutive found-reads on the same track, share that INCREASE "
                f"by more than 0.10): {_pct(mo['share_increase_gt_0_10'])} (n_pairs={mo['n_consecutive_pairs']})")
    ji = hp["jitter"]
    lines.append(f"- **Jitter** (median |diff| between consecutive found-reads ~0.2s apart): "
                f"{_num(ji['median_abs_diff'])} (n_pairs={ji['n_pairs_dt_0.15_0.35s']})")
    lines.append("")
    lines.append("## Velocity reader (`TeamTracker` per-track positions)")
    lines.append("")
    sv = v["share_tracks_old_enough"]
    lines.append(f"- **Share of tracks old enough to report a velocity** (age >= {sv['age_threshold_s']}s): "
                f"{_pct(sv['share'])} (n_tracks={sv['n_tracks']})")
    lines.append(f"- **Direction stability** (median |angle change| between consecutive ALREADY-MOVING "
                f">= {v['thresholds']['move_min_tiles_s']} tiles/s velocity estimates on the same track): "
                f"{_num(v['direction_stability_median_abs_angle_change_deg'], '%.1f')}"
                f" deg (n_segment_pairs={v['n_segment_pairs_for_direction']})")
    lines.append("")
    lines.append(f"- **Per-class measured speed vs `cards_stats.json.speed_tiles`** "
                f"(straight [<{v['thresholds']['straight_angle_deg']:.0f} deg heading change] and moving "
                f"[>={v['thresholds']['move_min_tiles_s']} tiles/s] segments only, "
                f"n >= {v['thresholds']['min_class_samples']}):")
    if v["by_class"]:
        lines.append("")
        lines.append("| class | n | median tiles/s | p25-p75 | card speed_tiles (tiles/s) | ratio |")
        lines.append("|---|---|---|---|---|---|")
        for base, d in v["by_class"].items():
            lines.append(f"| {base} | {d['n']} | {d['median_tiles_s']:.2f} | "
                        f"{d['p25']:.2f}-{d['p75']:.2f} | {d['card_speed_tiles_s']} | "
                        f"{_num(d['ratio_measured_over_card'])} |")
    else:
        lines.append("(no class reached the minimum sample count in the processed window)")
    lines.append("")
    lines.append("## Limitations -- what each check is a proxy for, and what it cannot see")
    lines.append("")
    lines.append("- **No ground truth exists on the live screen.** Every number above is a "
                "self-consistency check against a game rule (own-play identity, no-heal "
                "monotonicity, a published speed constant), not a comparison to a labelled frame. "
                "A reader that is wrong in a way consistent with these rules would pass undetected.")
    lines.append("- **HP \"found\" is a proxy.** `read_hp_frac` returns exactly `1.0` both when no bar "
                "exists (undamaged unit -- the common, correct case) and, in principle, when a bar is "
                "found completely full. The read-rate numbers here treat every `1.0` as \"not found\"; "
                "since the game itself draws no bar on a full-health unit, this should be a small "
                "underestimate of the true found-rate, not a large one, but it is not exact.")
    lines.append("- **The at-deploy check needs the detector to see the unit at all.** A play with no "
                "own-unit match in the window is counted as `unmatched_no_own_unit_seen`, which mixes "
                "two different failures -- the detector missing a real, correctly-undamaged unit, and "
                "the placement/track-matching radius being too tight/wide -- into one number.")
    lines.append("- **Monotonicity and jitter only run on tracks the detector re-acquires**, i.e. "
                "units that survive long enough with a HIT-count >= the tracker's own `min_hits` "
                "and get re-detected close enough in time (jitter needs a ~0.2s-spaced pair, dropped "
                "reads widen that gap and the pair is simply excluded, not counted as noise). A reader "
                "that is stably WRONG (a constant offset) is invisible to both checks.")
    lines.append("- **Velocity uses the SAME anisotropic TILE_X/TILE_Y linear approximation "
                "`hero_ability.py` already uses** (a flat tiles-per-normalized-frame-unit scale); it "
                "ignores the perspective warp `actions.BoardWarp` corrects for taps, so speeds near the "
                "top/bottom of the arena (foreshortened by the camera) are somewhat over/under-stated "
                "versus the middle. This audit does not attempt the warp correction, so the same bias "
                "sits in every number here.")
    lines.append("- **The \"straight, moving\" filter is a heuristic** (thresholds listed above), tuned "
                "by inspection, not measured against a labelled trajectory; a card whose typical play "
                "pattern is mostly turning (kiting, pathing around a building) will under-sample here, "
                "not because the reader is wrong but because few of its segments qualify as \"straight\".")
    lines.append("- **No live tower-HP reader is run offline.** `TeamTracker.set_towers` is fed "
                "\"all towers alive\" for the whole session (matching `tools/detector_audit.py`'s own "
                "documented simplification), so the deploy-pocket side-prior (evidence rank 4) is "
                "slightly more permissive here than in a real match with a fallen tower. This cannot "
                "affect the at-deploy check, which relies only on the rank-1 own-play anchor.")
    lines.append("- **The detector's own recall/precision is a separate, unmeasured variable here.** "
                "A unit the detector never boxes contributes zero evidence to every check above; none "
                "of these numbers say anything about units the detector missed entirely.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
