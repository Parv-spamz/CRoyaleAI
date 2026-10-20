"""CPU-only selector metric checks, with a fixed evaluate rowlog; no checkpoints, data files or reactive play."""
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from scratchpad.gauntlet.L69.gen_v2 import select_gen_v2 as S


class TestGateMetrics(unittest.TestCase):
    def test_thresholds_and_old_keys(self):
        idx = np.array([5, 2, 7, 1, 0, 6, 4, 3])   # nontrivial eval order; first four play, last four wait
        y = np.zeros(8)
        y[idx[:4]] = 1
        z35 = math.log(0.35 / 0.65)
        logits = torch.tensor([0.2, -0.3, z35, -0.8, 0.2, -0.3, z35, -0.8], dtype=torch.float64)
        base = {k: i / 10 for i, k in enumerate(S.KEYS) if not k.endswith("_p035")}
        model = lambda b: {"gate": logits[b]}

        def evaluate(tap, rows, grid, rowlog):
            tap(slice(0, 3))
            tap(slice(3, 8))
            rowlog.extend([(idx[:2], None, np.ones(2, dtype=bool), np.ones(2, dtype=bool)),
                           (idx[2:4], None, np.ones(2, dtype=bool), np.ones(2, dtype=bool))])
            return dict(base)

        with patch.object(S, "evaluate", side_effect=evaluate):
            default = S.score(model, {"y_gate": y}, SimpleNamespace(idx=idx), "lattice")
            custom = S.score(model, {"y_gate": y}, SimpleNamespace(idx=idx), "lattice", gate_p=0.5)
        self.assertEqual(default["joint_gct_p035"], 0.5)      # -0.3 fires; exact threshold does not
        self.assertEqual(default["gate_tnr_p035"], 0.5)
        self.assertEqual(default["joint_bal_p035"], 0.5)
        want = {**base, "joint_gct": 0.25, "gate_tnr": 0.75, "joint_bal": 0.5}
        for k, v in want.items():
            self.assertEqual(default[k], v, k)
            self.assertEqual(custom[k], v, k)
        for k in ("joint_gct", "gate_tnr", "joint_bal"):
            self.assertEqual(custom[k + "_p035"], want[k])

    def test_invalid_probability(self):
        for p in (0.0, 1.0, -0.1, 1.1, float("nan")):
            with self.assertRaisesRegex(ValueError, "gate_p must be in"):
                S.GateTap(None, p)


if __name__ == "__main__":
    unittest.main()
