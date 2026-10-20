"""CPU reader -> real selected policy -> public audit -> local video check. No ADB."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
LIVE = ROOT / 'scratchpad/gauntlet/L68/live_reader'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
sys.path[:0] = [str(ROOT), str(LIVE)]


def main():
    import cv2
    import torch
    import live_play as live
    import overlay_replay as overlay
    from pipeline.live_checkpoint import resolve_checkpoint
    from pipeline.live_gen import GenPilot as OriginalPilot
    torch.set_num_threads(4)
    selected = resolve_checkpoint(None, ROOT / 'scratchpad/gauntlet/L70/live/CKPT_OVERRIDE', ROOT)
    pilot = live.GenPilot(str(selected.path), device='cpu', gate_tau=.35, use_counter=True,
                         extrapolate_ticks=26, public_audit=True)
    old = OriginalPilot(str(selected.path), device='cpu', gate_tau=.35, use_counter=True, extrapolate_ticks=26)
    recording = ROOT / 'scratchpad/gauntlet/L70/reader/sidebyside/re_v2xb.jsonl'
    decisions, last_tick = [], -1
    for line in recording.open():
        frame = json.loads(line)
        if not (frame.get('battle_active') and frame.get('coherent')):
            continue
        if sum(any(i >= 0 for i in p['hand_deck_indices']) for p in frame['players']) != 1:
            continue
        pilot.observe(frame)
        old.observe(frame)
        tick = frame['game_tick']
        if tick <= last_tick:
            continue
        d, control = pilot.decide(frame), old.decide(frame)
        keys = ('play', 'p_play', 'hand_pos', 'card', 'name', 'xy')
        assert {k: d.get(k) for k in keys} == {k: control.get(k) for k in keys}
        assert d['public_audit'] is not None
        json.dumps(d['public_audit'], allow_nan=False)
        decisions.append(dict(tick=tick, **{k:d.get(k) for k in keys}, public=d['public_audit']))
        last_tick = tick
        if len(decisions) >= 24:
            break
    assert len(decisions) == 24

    # Actual captured video, bounded to 30 frames. Exercise both overlays and
    # raw-file merge without overwriting an owner's recording.
    source_log = LIVE / 'live_play_20261005_052057.jsonl'
    events = [json.loads(line) for line in source_log.read_text().splitlines()]
    segments = next(e['segments'] for e in events if e['event'] == 'recording')
    source, t0 = segments[0]
    out = ROOT / 'icebow/data/bench/live_entry_check_20261005'
    out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(source)
    ok, im = cap.read()
    assert ok, source
    short = out / 'short_source.mp4'
    writer = cv2.VideoWriter(str(short), cv2.VideoWriter_fourcc(*'mp4v'), 30., (im.shape[1], im.shape[0]))
    assert writer.isOpened()
    for _ in range(30):
        if not ok: break
        writer.write(im)
        ok, im = cap.read()
    writer.release()
    cap.release()
    # The recording starts on a menu; also drive the actual reader marker
    # drawing with a captured in-battle frame so that branch is exercised.
    battle = next(e for e in events if e['event'] == 'frame')
    battle = dict(battle, t_dev=t0)
    log = out / 'offline_video.jsonl'
    log.write_text('\n'.join(json.dumps(e) for e in [battle, dict(event='recording', segments=[[str(short),t0]])]))
    overlay.OUT_DIR = out
    video = overlay.render(log, overlay='both')
    assert video and video.is_file()
    cap = cv2.VideoCapture(str(video))
    decoded = 0
    while cap.read()[0]: decoded += 1
    cap.release()
    assert decoded >= 29
    assert video.with_name(video.stem + '_raw.mp4').is_file()
    report = dict(checkpoint=str(selected.path), checkpoint_sha256=selected.sha256,
        feature_version=pilot.feature_version, device='cpu', anti_leak=False,
        recording=str(recording), recording_sha256=hashlib.sha256(recording.read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(live.__file__).read_bytes()).hexdigest(), source_video=source,
        decisions=decisions, decision_parity_with_original=True, video=str(video), decoded_frames=decoded,
        no_live_inputs=True, limitation='Archived-reader and video integration; not a new live-match acceptance.')
    (HERE/'offline_probe.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k:v for k,v in report.items() if k != 'decisions'}))
    print('LIVE_OFFLINE_INTEGRATION_PASS')


if __name__ == '__main__':
    main()
