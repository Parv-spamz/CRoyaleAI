"""Overlaid replay for live_play.py: the device's own screenrecord + the memory reader's entities burned in.

    icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L68/live_reader/overlay_replay.py LIVE_PLAY_LOG.jsonl [--offset S]

play.py's OverlayReplayRecorder draws the YOLO detector's boxes on host screen grabs; here the "detector" is the
memory reader (what GenPilot perceives), and the frames are `screenrecord` on the device, so every entity is placed
with the SAME pixel mapping the taps use (live_play.Layout) -- no window chrome to calibrate. Video and reader share
the device clock: each segment logs /proc/uptime just before screenrecord starts, each reader frame logs
sample_monotonic_us. ``--offset`` (seconds, + = boxes later) absorbs screenrecord's encoder start-up delay (not
measured yet; the calibration knob).
Drawn: every entity (mine blue, enemy red; towers big) with name + HP%, the model's plays (tap ring for 1.5 s +
card / p_play / forced), tick and elixir. Output: icebow/data/overlayed_replays/live_<stamp>.mp4 (gitignored).
"""
from __future__ import annotations

import argparse
import bisect
import json
import sys
from pathlib import Path

import cv2

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "icebow" / "src"))
from pipeline.obs_contract import _catalog_names  # noqa: E402
from live_play import Layout, my_frame_xy  # noqa: E402

OUT_DIR = REPO / "icebow" / "data" / "overlayed_replays"
MINE, ENEMY = (230, 150, 60), (60, 60, 230)          # BGR, detect.draw_detections' team colours
FPS = 30.0
DET_EVERY = 3            # run the YOLO board detector on every 3rd output frame (10 Hz) and hold its boxes between


def load_board_detector():
    """play.py's YOLO board detector (clashrl.replay_mine.load_detector, weights from icebow/config/config.yaml).
    COSMETIC here: its boxes are drawn on the replay only; the model never sees them. None if unavailable."""
    try:
        from clashrl.config import Config
        from clashrl.replay_mine import load_detector
        det = load_detector(Config.load(REPO / "icebow" / "config" / "config.yaml"))
        return det if getattr(det, "_model", None) is not None else None
    except Exception as exc:                          # noqa: BLE001 -- the replay still renders without boxes
        print(f"[overlay] detector unavailable ({exc}); rendering without detector boxes")
        return None


def render(log_path: Path, offset: float = 0.0, overlay: str = "both") -> Path | None:
    """``overlay``: 'detector' (play.py-style YOLO boxes only), 'reader' (memory-reader entities + taps), 'both'."""
    ev = [json.loads(l) for l in open(log_path, encoding="utf-8") if l.strip()]
    frames = [e for e in ev if e["event"] == "frame"]
    plays = [e for e in ev if e["event"] in ("play", "ability") and "t_dev" in e]
    segs = next((e["segments"] for e in ev if e["event"] == "recording"), [])
    if not frames or not segs:
        print(f"[overlay] nothing to render: {len(frames)} frames, {len(segs)} video segments")
        return None
    ft = [f["t_dev"] for f in frames]
    names = _catalog_names()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"live_{Path(log_path).stem.removeprefix('live_play_')}.mp4"
    det = load_board_detector() if overlay in ("detector", "both") else None
    if det is not None:
        from clashrl.detect import draw_detections
    dets: list = []
    writer, n = None, 0
    for local, t_start in segs:
        cap = cv2.VideoCapture(str(local))
        ok, img = cap.read()
        if not ok:
            print(f"[overlay] unreadable segment {local}")
            continue
        h, w = img.shape[:2]
        lay = Layout(w, h)
        if writer is None:
            writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (w, h))
        pts = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        t_out = pts
        while ok:
            # screenrecord is variable-frame-rate: hold each source frame until the next one's timestamp
            nxt_ok, nxt = cap.read()
            nxt_pts = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0 if nxt_ok else pts + 1.0 / FPS
            while t_out < nxt_pts:
                t = t_start + t_out + offset
                i = bisect.bisect_right(ft, t) - 1
                if det is not None:
                    if n % DET_EVERY == 0:
                        dets = det.detect(img, conf=0.3)
                    canvas = draw_detections(img, dets)
                else:
                    canvas = img.copy()
                if overlay != "detector" and i >= 0 and t - ft[i] < 0.5:
                    draw_frame(canvas, frames[i], plays, t, lay, names)
                writer.write(canvas)
                n += 1
                t_out += 1.0 / FPS
            ok, img, pts = nxt_ok, nxt, nxt_pts
        cap.release()
    if writer is None:
        return None
    writer.release()
    print(f"[overlay] saved {out_path} ({n} frames, {n / FPS:.0f} s)")
    merge_raw([local for local, _ in segs], out_path.with_name(out_path.stem + "_raw.mp4"))
    return out_path


def merge_raw(parts: list, out: Path) -> Path | None:
    """The match's raw screenrecord clips (one per 170 s segment) joined into ONE un-overlaid video, losslessly
    (ffmpeg concat demuxer, stream copy: native ~60 fps, no re-encode). Skipped with a message if ffmpeg is absent."""
    import shutil
    import subprocess
    import tempfile
    ff = shutil.which("ffmpeg") or next((str(p) for p in (Path.home() / "tools" / "bin" / "ffmpeg.exe",) if p.is_file()),
                                         None)
    parts = [Path(p).resolve() for p in parts if Path(p).is_file()]   # absolute: the concat list lives in %TEMP%
    if not ff or not parts:
        print(f"[overlay] raw merge skipped ({'no ffmpeg' if not ff else 'no readable clips'})")
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as lst:
        lst.write("".join(f"file '{p.as_posix()}'\n" for p in parts))
    r = subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst.name, "-c", "copy",
                        str(out)], capture_output=True, text=True)
    Path(lst.name).unlink(missing_ok=True)
    if r.returncode != 0 or not out.is_file():
        print(f"[overlay] raw merge failed: {r.stderr.strip()[-300:]}")
        return None
    print(f"[overlay] saved {out} ({len(parts)} clip(s) joined, no re-encode)")
    return out


def draw_frame(img, f: dict, plays: list, t: float, lay: Layout, names: dict) -> None:
    side = f["my_side"]
    for s, x, y, cid, hp, mhp, *_ in f["ents"]:
        c = MINE if s == side else ENEMY
        px, py = lay.board(my_frame_xy({"x": x, "y": y}, side), side)
        tower = cid < 0
        cv2.circle(img, (px, py), 30 if tower else 12, c, 2)
        label = ("tower" if tower else names.get(cid, str(cid))) + (f" {100 * hp // mhp}%" if mhp else "")
        cv2.putText(img, label, (px - 30, py - (34 if tower else 16)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 1,
                    cv2.LINE_AA)
    for p in plays:
        if p["event"] == "ability":
            if 0 <= t - p["t_dev"] < 1.5:
                cv2.circle(img, tuple(p["tap"]), 45, (255, 0, 255), 3)
                cv2.putText(img, f"ABILITY {p['why']}", (12, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2,
                            cv2.LINE_AA)
            continue
        if 0 <= t - p["t_dev"] < 1.5:
            bx, by = p["tap_board"]
            cv2.circle(img, (bx, by), 22, (0, 255, 255), 3)
            cv2.circle(img, tuple(p["tap_hand"]), 40, (0, 255, 255), 3)
            cv2.putText(img, f"{p['name']} p={p['p_play']:.2f}{' FORCED' if p['forced'] else ''}", (bx - 60, by - 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(img, f"tick {f['tick']}  elixir {f['elixir']:.1f}", (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (255, 255, 255), 2, cv2.LINE_AA)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--overlay", choices=("both", "detector", "reader"), default="both",
                    help="detector = play.py-style YOLO boxes only (cosmetic), reader = memory-reader markers, both")
    a = ap.parse_args()
    return 0 if render(a.log, a.offset, a.overlay) else 1


if __name__ == "__main__":
    raise SystemExit(main())
