"""Latency-shifted play rows (``dataset.build_replay(shift_ticks=...)``): shift 0 == the pre-shift builder
(commit 87a7ff5) on real corpus replays, minus its wait rows on the side's own play tick (L69 label fix);
shifted semantics on a synthetic replay; no wait row on an own play tick (old builders emitted them)."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from pipeline import dataset as ds
from pipeline import dataset_gen as dg

REPO = Path(__file__).resolve().parents[2]
CORPORA = [REPO / "scratchpad" / "gauntlet" / "ext" / c for c in
           ("corpus_v6/icebow", "corpus_v6/hogeq", "corpus_gen_pilot/s1")]
REF_COMMIT = "87a7ff5"          # dataset.py before shift_ticks existed
PRE_FIX_COMMIT = "da9311d"      # dataset.py with shift_ticks, before the own-play-tick wait-row fix

N0 = ["Knight", "Archer", "Fireball", "Zap", "Giant", "Musketeer", "Valkyrie", "HogRider"]
N1 = ["Log", "IceSpirits", "MightyMiner", "Firecracker", "Tesla", "Skeletons", "Earthquake", "Cannon"]
# side-0 plays: (tick, card, hand_before). 300 -> 310 is a kept combo (fireball still in hand at 290, at a new
# hand position); 320 is a dropped one (musketeer not in hand at 290); 406 ties 390/370 -> the later frame.
PLAYS = [(200, "Knight", ["Knight", "Archer", "Fireball", "Zap"]),
         (300, "Archer", ["Giant", "Archer", "Fireball", "Zap"]),
         (310, "Fireball", ["Fireball", "Musketeer", "Giant", "Zap"]),
         (320, "Musketeer", ["Musketeer", "Valkyrie", "Giant", "Zap"]),
         (406, "Giant", ["Giant", "Valkyrie", "Knight", "Zap"])]


# like the real corpora: a frame ON every play tick, snapshotted BEFORE that tick's plays act. 276 and 280 both
# get t0 = 250, my own Archer play's tick: the hand there is the PRE-play one (Archer still in it).
PLAYS_ON_TICK = [(200, "Knight", ["Knight", "Archer", "Fireball", "Zap"]),
                 (250, "Archer", ["Giant", "Archer", "Fireball", "Zap"]),
                 (276, "Fireball", ["Fireball", "Musketeer", "Giant", "Zap"]),
                 (280, "Musketeer", ["Musketeer", "Valkyrie", "Giant", "Zap"])]


def synth(plays=PLAYS, frames_on_plays=False) -> dict:
    log, pfs = [], []
    for i, (t, card, hand) in enumerate(plays):
        key = dg.side_deck(N0).cards[N0.index(card)]
        log.append({"play_index": i, "tick": t, "side": 0, "card": key, "x": 9000, "y": 5000 + 100 * i,
                    "accepted": True, "hand_before": hand})
        pfs.append({"tick": t, "elixir": [5.0, 5.0], "entities": [], "towers": [], "projectiles": [],
                    "effects": [], "play_index": i, "side": 0, "card": card,
                    "players": [{"side": 0, "hand": hand, "next": 7}, {"side": 1, "hand": N1[:4], "next": 4}]})
    ticks = sorted(set(range(10, 600, 20)) | ({t for t, _, _ in plays} if frames_on_plays else set()))
    frames = [{"tick": t, "elixir": [t / 100.0, 1.0], "entities": [], "towers": []} for t in ticks]
    return {"tag": "synth", "record_every": 20, "final_decks": {"0": N0, "1": N1}, "log": log,
            "play_frames": pfs, "frames": frames, "expected": {"crowns_by_side": {"0": 1, "1": 0}}}


def build(rec, shift):
    rows, st = ds._Rows(), {}
    ds.build_replay(rec, dg.side_deck(N0), rows, 0, val_pct=0, stats=st, shift_ticks=shift)
    return rows.arrays(), st


def own_play_waits(rec: dict, a: dict) -> np.ndarray:
    """Mask of gate-0 rows whose tick is an accepted play tick of the same side."""
    acc = {s: {int(e["tick"]) for e in rec["log"] if e.get("accepted") and int(e.get("side", -1)) == s and "tick" in e}
           for s in (0, 1)}
    return (a["y_gate"] == 0) & np.asarray([int(t) in acc[int(s)] for t, s in zip(a["tick"], a["side"])], bool)


def take(a: dict, keep: np.ndarray) -> dict:
    """Row subset of ``_Rows.arrays()`` output (variable-length ``tok`` re-cut via ``off``)."""
    off, idx = a["off"], np.where(keep)[0]
    out = {k: v[keep] for k, v in a.items() if k not in ("tok", "off")}
    out["tok"] = np.concatenate([a["tok"][off[i]:off[i + 1]] for i in idx]) if len(idx) else a["tok"][:0]
    out["off"] = np.concatenate([[0], np.cumsum(np.diff(off)[idx])]).astype(np.int64)
    return out


def git_ref(commit: str, test: unittest.TestCase):
    try:
        src = subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:pipeline/dataset.py"],
                             capture_output=True, text=True, check=True, encoding="utf-8").stdout
    except (OSError, subprocess.CalledProcessError) as ex:   # no git / commit on this box
        test.skipTest(f"reference builder unavailable: {ex}")
    return ref_module(src)


def corpus_files(per: int = 2):
    return [f for c in CORPORA if c.exists() for f in sorted(c.glob("replay_*.json"))[:per]]


def ref_module(src: str):
    spec = importlib.util.spec_from_loader("pipeline._dataset_ref", loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__, mod.__file__ = "pipeline", str(REPO / "pipeline" / "dataset.py")
    sys.modules[spec.name] = mod
    exec(compile(src, "dataset_ref.py", "exec"), mod.__dict__)
    return mod


class TestShiftZeroIdentity(unittest.TestCase):
    def test_shift0_equals_pre_shift_builder(self):
        ref = git_ref(REF_COMMIT, self)
        files = corpus_files()
        if not files:
            self.skipTest("corpora not on this box")
        for f in files:
            rec = json.loads(f.read_text(encoding="utf-8"))
            for s in (0, 1):
                deck = dg.side_deck(rec["final_decks"][str(s)])
                if deck is None:
                    continue
                a, b = ds._Rows(), ref._Rows()
                ds.build_replay(rec, deck, a, 0, stats={})
                ref.build_replay(rec, deck, b, 0, stats={})
                a, b = a.arrays(), b.arrays()
                b = take(b, ~own_play_waits(rec, b))           # the only intended difference (L69 label fix)
                self.assertEqual(a.keys(), b.keys())
                for k in a:
                    np.testing.assert_array_equal(a[k], b[k], err_msg=f"{f.name} side {s} {k}")


class TestShiftSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a0, cls.s0 = build(synth(), 0)
        cls.a, cls.s = build(synth(), 26)

    def plays(self, a):
        p = a["y_gate"] == 1
        return a["tick"][p].tolist(), a["y_slot"][p].tolist(), a["past"][p], a["sc"][p]

    def test_state_tick_is_the_chosen_frame(self):
        ticks, slots, _, _ = self.plays(self.a)
        self.assertEqual(self.plays(self.a0)[0], [200, 300, 310, 320, 406])
        # 200 -> 170 (off 30), 300 -> 270 (off 30), 310 -> 290 (off 20), 320 dropped, 406 -> 390 (tie 16/36 -> later)
        self.assertEqual(ticks, [170, 270, 290, 390])
        self.assertEqual(slots, [0, 1, 2, 4])
        self.assertEqual({k: v for k, v in self.s.items() if k.startswith("shift_off:")},
                         {"shift_off:30": 2, "shift_off:20": 1, "shift_off:16": 1})

    def test_dropped_combo(self):
        self.assertEqual(self.s.get("shift_drop_combo"), 1)
        self.assertEqual(self.s.get("play_rows"), 4)
        self.assertNotIn("shift_drop_combo", self.s0)

    def test_hand_position_recomputed(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "replay_synth.json"
            p.write_text(json.dumps(synth()), encoding="utf-8")
            r0, r = dg.replay_rows(str(p), shift_ticks=0), dg.replay_rows(str(p), shift_ticks=26)
        pos0 = r0["y_hand_pos"][(r0["y_gate"] == 1) & (r0["side"] == 0)].tolist()
        pos = r["y_hand_pos"][(r["y_gate"] == 1) & (r["side"] == 0)].tolist()
        self.assertEqual(pos0, [0, 1, 0, 0, 0])
        self.assertEqual(pos, [0, 1, 2, 0])                # fireball sits at position 2 of the hand at tick 290

    def test_past_at_shifted_tick(self):
        _, _, past, _ = self.plays(self.a)
        # row for the 310 play (state 290): the 300 play is after 290 -> only the 200 play, 4.5 s ago
        self.assertEqual(past[2, 0].tolist()[0], 0)
        self.assertAlmostEqual(float(past[2, 0, 3]), (290 - 200) * 0.05, places=5)
        self.assertEqual(past[2, 1, 0], -1)
        # row for the 406 play (state 390): all four earlier plays happened (the dropped one included)
        self.assertEqual(past[3, :, 0].tolist(), [5, 2, 1])

    def test_wait_row_exclusion_window(self):
        w0 = self.a0["tick"][self.a0["y_gate"] == 0].tolist()
        w = self.a["tick"][self.a["y_gate"] == 0].tolist()
        self.assertIn(370, w0)                             # 406 is outside (370, 390]
        self.assertNotIn(370, w)                           # ... but inside (370, 416]
        acc = [t for t, _, _ in PLAYS]
        for t in w:
            self.assertFalse(any(t < p <= t + 26 + 20 for p in acc), t)


class TestPrePlayFrames(unittest.TestCase):
    """A frame on my own play tick q is the state BEFORE q acts: hand_before(q), q not yet in past."""

    def test_hand_is_pre_play_and_combo_dropped(self):
        rec = synth(PLAYS_ON_TICK, frames_on_plays=True)
        a, st = build(rec, 26)
        p = a["y_gate"] == 1
        # 200 -> 170 (off 30); 250 -> 230 (off 20; the 210 frame is off 40); 276 -> 250 (off 26, ON the Archer
        # play); 280 -> 250 (off 30): Musketeer is not in the pre-Archer hand -> dropped
        self.assertEqual(a["tick"][p].tolist(), [170, 230, 250])
        self.assertEqual(st.get("shift_drop_combo"), 1)
        hand = a["sc"][p, 7:43].reshape(-1, 4, 9).argmax(-1)
        self.assertEqual(hand[2].tolist(), [4, 1, 2, 3])                 # Giant Archer Fireball Zap (pre-Archer)
        self.assertEqual(a["past"][p][2, :, 0].tolist(), [0, -1, -1])   # the Archer play at 250 is not past yet
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "replay_synth.json"
            f.write_text(json.dumps(rec), encoding="utf-8")
            r = dg.replay_rows(str(f), shift_ticks=26)
        self.assertEqual(r["y_hand_pos"][(r["y_gate"] == 1) & (r["side"] == 0)].tolist(), [0, 1, 2])


class TestNoWaitOnOwnPlayTick(unittest.TestCase):
    """A frame on my own play tick is a PLAY row's pre-act state; the pre-fix builders also emitted it as a wait
    row with the POST-play hand (15.07% of gen_dataset_v1's wait rows)."""

    def test_synthetic(self):
        rec = synth(PLAYS_ON_TICK, frames_on_plays=True)     # the 200 frame (index 10) is on the stride grid
        for shift in (0, 26):
            a, st = build(rec, shift)
            w = a["y_gate"] == 0
            self.assertFalse(own_play_waits(rec, a).any(), shift)
            self.assertGreaterEqual(st.get("wait_on_play_tick", 0), 1, shift)
            # every wait row carries the pre-act hand: hand_before of my first play at tick >= t
            hand = a["sc"][w, 7:43].reshape(-1, 4, 9).argmax(-1)
            for t, h in zip(a["tick"][w], hand):
                want = next(hb for pt, _, hb in PLAYS_ON_TICK if pt >= t)
                self.assertEqual(h.tolist(), [N0.index(c) for c in want], (shift, int(t)))

    def test_old_builder_emitted_them(self):
        ref = git_ref(PRE_FIX_COMMIT, self)
        rec = synth(PLAYS_ON_TICK, frames_on_plays=True)
        b = ref._Rows()
        ref.build_replay(rec, dg.side_deck(N0), b, 0, val_pct=0, stats={})
        self.assertGreaterEqual(int(own_play_waits(rec, b.arrays()).sum()), 1)

    def test_real_replays_vs_pre_fix_builder(self):
        """Fixed corpus sample, shift 0 and 26: play rows identical to the pre-fix builder, wait rows = its wait
        rows minus the own-play-tick ones, none left; the generalist path (replay_rows) has none either."""
        ref = git_ref(PRE_FIX_COMMIT, self)
        files = corpus_files(3)
        if not files:
            self.skipTest("corpora not on this box")
        dropped = 0
        for f in files:
            rec = json.loads(f.read_text(encoding="utf-8"))
            for shift in (0, 26):
                for s in (0, 1):
                    deck = dg.side_deck(rec["final_decks"][str(s)])
                    if deck is None:
                        continue
                    a, b = ds._Rows(), ref._Rows()
                    ds.build_replay(rec, deck, a, 0, stats={}, shift_ticks=shift)
                    ref.build_replay(rec, deck, b, 0, stats={}, shift_ticks=shift)
                    a, b = a.arrays(), b.arrays()
                    self.assertFalse(own_play_waits(rec, a).any(), f"{f.name} shift {shift} side {s}")
                    bad = own_play_waits(rec, b)
                    dropped += int(bad.sum())
                    pa, pb = take(a, a["y_gate"] == 1), take(b, b["y_gate"] == 1)
                    wa, wb = take(a, a["y_gate"] == 0), take(b, (b["y_gate"] == 0) & ~bad)
                    for k in a:
                        np.testing.assert_array_equal(pa[k], pb[k], err_msg=f"{f.name} {shift} {s} play {k}")
                        np.testing.assert_array_equal(wa[k], wb[k], err_msg=f"{f.name} {shift} {s} wait {k}")
            r = dg.replay_rows(str(f))
            self.assertFalse(own_play_waits(rec, r).any(), f.name)
        self.assertGreater(dropped, 0, "the sample never hit the bug: the test would not bite")


if __name__ == "__main__":
    unittest.main()
