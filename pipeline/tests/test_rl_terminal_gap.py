"""CPU-only terminal-gap, critic diagnostic and default-byte-compatibility checks; no live engine or GPU."""
import json
import unittest
from unittest.mock import patch

import numpy as np
import torch

from pipeline import rl_royale as RL
from pipeline.tests.test_rl_gae import SPEC, _learner, _strip, _Tmp
from pipeline.tests.test_rl_royale import _monitor_fields, _results, _tiny_model
from pipeline.tests.test_rl_shaping import SHP, _module_at, _with_phi


MONITORS = ("value_target_outside_share", "value_saturation_share", "value_mae")
BEFORE = "e7fed951a173069a132f90775555693a1c589efc"          # before terminal-gap / critic diagnostics


def _result(outcome="win"):
    # Four contributing rows plus a later dropped row: the gap starts at the last KEPT decision (tick 6).
    t = {k: np.zeros(5) for k in RL.TRAJ_KEYS + ("lp_gate", "lp_card", "lp_cell")}
    t.update(gate_sampled=np.array([True] * 4 + [False]), played=np.zeros(5, dtype=bool),
             tick=np.array([0, 2, 5, 6, 8]), phi_state=np.zeros((5, 8)))
    return {"entry_index": 0, "outcome": outcome, "end_tick": 10, "traj": t}


class TestTerminalGap(unittest.TestCase):
    def test_returns_and_flag_off_bytes(self):
        for outcome in ("win", "loss", "draw"):
            results = [_result(outcome)]
            old, _ = RL.collate(results, advantage="gae", gamma_tick=0.9)
            off, _ = RL.collate(results, advantage="gae", gamma_tick=0.9, gae_terminal_gap=False)
            on, _ = RL.collate(results, advantage="gae", gamma_tick=0.9, gae_terminal_gap=True)
            for k in old:
                self.assertEqual(old[k].tobytes(), off[k].tobytes(), k)
            for B, end in ((off, 6), (on, 10)):
                _, ret = RL.gae(B["r_step"], np.zeros(4), B["match"], B["gamma_row"], 1.0)
                np.testing.assert_allclose(ret, RL.reward(outcome) * 0.9 ** (end - np.array([0, 2, 5, 6])),
                                           rtol=0, atol=1e-15)
            self.assertEqual(on["gamma_row"].tobytes(), off["gamma_row"].tobytes())

    def test_shaping_unchanged(self):
        results = _with_phi([_result()])
        kw = dict(advantage="gae", gamma_tick=0.9, shaping=SHP)
        off, st_off = RL.collate(results, **kw)
        on, st_on = RL.collate(results, **kw, gae_terminal_gap=True)
        self.assertEqual(st_off, st_on)
        for k in off:
            if k != "r_step":
                self.assertEqual(off[k].tobytes(), on[k].tobytes(), k)

    def test_config(self):
        self.assertIs(RL.adv_cfg({})["gae_terminal_gap"], False)
        valid = {"advantage": "gae", "gae_gamma_unit": "tick", "gae_terminal_gap": True}
        self.assertIs(RL.adv_cfg(valid)["gae_terminal_gap"], True)
        for extra in ({"advantage": "match_loo"}, {"gae_gamma_unit": "row"},
                      {"advantage": "match_loo", "gae_gamma_unit": "row"},
                      *({"gae_terminal_gap": x} for x in (1, 0, "true", None))):
            with self.assertRaisesRegex(SystemExit, "gae_terminal_gap"):
                RL.adv_cfg({**valid, **extra})

    def test_missing_end_and_invalid_mode(self):
        r = _result()
        del r["end_tick"]
        # Even a match without contributing rows must have an end tick when enabled.
        for sampled in (True, False):
            r["traj"]["gate_sampled"][:] = sampled
            with self.assertRaisesRegex(ValueError, "end_tick for result 1"):
                RL.collate([_result(), r], advantage="gae", gamma_tick=0.9, gae_terminal_gap=True)
        for kw in ({}, {"advantage": "gae"}, {"gamma_tick": 0.9}):
            with self.assertRaisesRegex(ValueError, "gae_terminal_gap.*advantage gae.*gamma_tick"):
                RL.collate([_result()], gae_terminal_gap=True, **kw)

    def test_zero_and_invalid_gap(self):
        for end in (6, 5, float("nan")):
            r = _result()
            r["end_tick"] = end
            kw = dict(advantage="gae", gamma_tick=0.9, gae_terminal_gap=True)
            if end == 6:
                B, _ = RL.collate([r], **kw)
                self.assertEqual(B["r_step"][-1], 1.0)
            else:
                with self.assertRaisesRegex(ValueError, "end_tick must be finite and >= last kept tick"):
                    RL.collate([r], **kw)

    def test_end_tick_from_rollout_result(self):
        from pipeline import e1_eval as E
        from pipeline.tests import test_league as TL
        learner, opp = E.GenPolicy(TL._tiny_gen(1), TL.VOCAB), E.GenPolicy(TL._tiny_gen(2), TL.VOCAB)
        jobs = [(0, TL._spec(0, "snapA", 0), 0, {"rollout_index": 0, "update": 0})]
        results, envs = TL._run(jobs, learner, {"snapA": (opp, TL._cfg("sample", record=False))},
                               TL._cfg(record_tick=True), n=1)
        self.assertEqual(results[0]["end_tick"], envs[0].tick)
        self.assertGreater(results[0]["end_tick"], results[0]["traj"]["tick"][-1])
        RL.collate(results, advantage="gae", gamma_tick=0.9, gae_terminal_gap=True)


class TestCriticDiagnostics(_Tmp):
    def test_known_targets_and_saturation(self):
        # Independent terminal rows: plain targets [1.2, -0.5], residual targets [1.2, -0.5]. The second
        # residual uses an unshaped return of 1, proving the monitor reads v_net's target, not that return.
        for shaping in (False, True):
            B = {"A": torch.zeros(2), "match": torch.tensor([0, 1]),
                 "r_step": torch.tensor([1.2, -0.5] if not shaping else [0.3, 1.0], dtype=torch.float64)}
            cfg = {"advantage": "gae", "gae_lambda": 1.0}
            if shaping:
                B["phi"] = torch.tensor([-1.5, 1.75], dtype=torch.float64)
                cfg.update(shaping="tower_crown", critic_warmup_updates=1, shaping_critic_scale=1.5)
            with patch.object(RL, "value_rows", return_value=torch.tensor([0.96, -0.2], dtype=torch.float64)):
                st = RL.gae_batch(None, B, cfg)
            np.testing.assert_allclose(B["ret"].numpy(), [1.2, -0.5], atol=1e-15)
            self.assertEqual(st["value_target_outside_share"], 0.5)
            self.assertEqual(st["value_saturation_share"], 0.5)
            self.assertAlmostEqual(st["value_mae"], 0.27, places=14)

    def test_boundaries_and_empty(self):
        for n in (0, 2):
            B = {"A": torch.zeros(n), "match": torch.arange(n),
                 "r_step": torch.tensor([1.0, -1.0][:n], dtype=torch.float64)}
            with patch.object(RL, "value_rows", return_value=torch.tensor([0.95, -0.95][:n], dtype=torch.float64)):
                st = RL.gae_batch(None, B, {"advantage": "gae"})
            for k in MONITORS[:2]:
                self.assertEqual(st[k], 0.0 if n else None)
            if not n:
                self.assertIsNone(st["value_mae"])

    def test_default_training_bytes_and_logged_monitors(self):
        """Compare the pre-change code, ignoring ONLY the three explicitly added diagnostic fields in logs."""
        old = _module_at(BEFORE)
        old.CKPT_ROOT = self.tmp
        model = _tiny_model(6)
        results = _with_phi(_monitor_fields(_results(model, SPEC, seed=13)))
        for r in results:
            r["traj"]["tick"] = np.arange(len(r["traj"]["played"])) * 10
            r["end_tick"] = int(r["traj"]["tick"][-1]) + 20
        for mode in ({}, {"advantage": "gae"}, {"advantage": "gae", "gae_gamma_unit": "tick"},
                     {"advantage": "gae", "gae_gamma_unit": "tick", "shaping": "tower_crown",
                      "critic_warmup_updates": 1}):
            runs = []
            for name, mod, extra in (("old", old, {}), ("absent", RL, {}),
                                     ("off", RL, {"gae_terminal_gap": False})):
                L = _learner(mod, model, results, self.tmp / name, **mode, **extra)
                L.log = RL.Log(L.run_dir)                         # verify the persisted train_log, too
                recs = [L.one_update(u)[0] for u in range(2)]
                if mod is RL and mode.get("advantage") == "gae":
                    logged = [json.loads(x) for x in (L.run_dir / "train_log.jsonl").read_text().splitlines()]
                    for rec in recs:
                        for k in MONITORS:
                            self.assertTrue(np.isfinite(rec["gae"][k]))
                            self.assertIn(k, logged[-1]["gae"])
                            rec["gae"].pop(k)
                runs.append(([_strip(r) for r in recs], L))
            for recs, L in runs[1:]:
                self.assertEqual(recs, runs[0][0])
                self.assertEqual(L.beta, runs[0][1].beta)
                self.assertEqual(L.rng.bit_generator.state, runs[0][1].rng.bit_generator.state)
                for k, v in L.model.state_dict().items():
                    self.assertEqual(v.numpy().tobytes(), runs[0][1].model.state_dict()[k].numpy().tobytes(), k)

    def test_one_update_terminal_gap_wiring(self):
        model = _tiny_model(6)
        results = _monitor_fields(_results(model, SPEC, seed=13))
        for r in results:
            r["traj"]["tick"] = np.arange(len(r["traj"]["played"]))
            r["end_tick"] = len(r["traj"]["played"]) + 4
        L = _learner(RL, model, results, self.tmp, advantage="gae", gae_gamma_unit="tick",
                     gae_gamma_tick=0.9, gae_terminal_gap=True)
        with patch.object(RL, "collate", wraps=RL.collate) as collate:
            rec, _, crash = L.one_update(0)
        self.assertFalse(crash)
        self.assertTrue(collate.call_args.kwargs["gae_terminal_gap"])
        self.assertTrue(all(k in rec["gae"] for k in MONITORS))


if __name__ == "__main__":
    unittest.main()
