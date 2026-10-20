"""Offline row regression: accepted abilities must not alter play/wait/history semantics."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
from pipeline import dataset as ds, dataset_gen as dg
from pipeline.obs_contract import load_deck

RECORD = Path(__file__).parent / "fixtures/dataset_record.json"


class DatasetAbilities(unittest.TestCase):
    def test_accepted_abilities_leave_all_rows_byte_identical(self):
        rec = json.loads(RECORD.read_text(encoding="utf-8"))
        augmented = deepcopy(rec)
        play = next(e for e in rec["log"] if e.get("accepted"))
        ability = dict(play, play_index=100000, tick=play["tick"] + 1, kind="ability", ability=True,
                       entity_id=5000010, x=None, y=None)
        augmented["log"].append(ability)
        pf = deepcopy(next(p for p in rec["play_frames"] if p["play_index"] == play["play_index"]))
        pf.update(play_index=ability["play_index"], tick=ability["tick"], ability=True, x=None, y=None)
        augmented["play_frames"].append(pf)
        for shift in (0, 26):
            with self.subTest(shift=shift):
                outputs, stats = [], []
                for recording in (rec, augmented):
                    rows, st = ds._Rows(), {}
                    ds.build_replay(recording, load_deck("icebow"), rows, 0, stats=st, shift_ticks=shift)
                    outputs.append(rows.arrays())
                    stats.append(st)
                self.assertGreater(stats[0]["play_rows"], 0)  # positive card-play control
                self.assertGreater(sum(outputs[0]["y_gate"] == 0), 0)
                self.assertEqual(stats[0], stats[1])
                for key in outputs[0]:
                    np.testing.assert_array_equal(outputs[0][key], outputs[1][key], err_msg=key)

    def test_generalist_public_play_history_filters_abilities(self):
        card = dict(side=0, tick=10, play_index=0, card="knight", accepted=True, x=1000, y=1000)
        ability = dict(card, play_index=1, ability=True, kind="ability", x=None, y=None)
        rec = dict(final_decks={"0": ["Knight@hero"]}, log=[card, ability])
        with patch.object(dg, "evolution_cycles", return_value={}):
            plays = dg.played_forms(rec)
        self.assertEqual(len(plays), 1)
        self.assertEqual(plays[0]["play_index"], 0)


if __name__ == "__main__":
    unittest.main()
