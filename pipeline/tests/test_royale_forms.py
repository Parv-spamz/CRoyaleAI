"""RoyaleSim card forms (pipeline/royale_env.py ``forms_mode``, L69): default "base" byte-identical to the pre-forms code
(commit fbca898, read with ``git show``), "deck" plays decked evolutions / heroes the engine loads, the policy's form
inputs follow what was loaded, and the config / flag plumbing.

    OMP_NUM_THREADS=2 research/ext/Royale/.venv/Scripts/python.exe -m pytest -q pipeline/tests/test_royale_forms.py

Needs royalegym/royalesim (the Royale stack venv); skipped elsewhere.
"""
from __future__ import annotations

import importlib.util
import json
import queue
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

try:
    from royalegym.protocol import STATUS_EVOLVED, status_of
    from pipeline import royale_env as RE
    from pipeline.royale_env import RoyalePoolEnv, RoyaleSelfPlayEnv
    from pipeline import e1_eval as E
except ImportError:                                   # no royalegym in this venv
    RoyaleSelfPlayEnv = None

PRE_FORMS = "fbca898"                                 # the last commit before forms_mode
ICEBOW = ["Tornado", "Tesla@evolution", "IceWizard", "Xbow", "Rocket", "Knight@evolution", "Log", "Skeletons"]
ICEBOW_HERO = ["Tornado", "Tesla@evolution", "IceWizard@hero", "Xbow", "Rocket", "Knight@evolution", "Log", "Skeletons"]
HOGEQ = ["HogRider", "Earthquake", "Log", "Cannon", "Musketeer", "IceSpirits", "Skeletons", "Valkyrie"]
CELL = {0: (9000, 10000), 1: (9000, 22000)}


def old_module(path: str, name: str):
    """``path`` as it was at PRE_FORMS, imported as module ``name`` (None if git cannot give it)."""
    try:
        src = subprocess.run(["git", "show", f"{PRE_FORMS}:{path}"], cwd=REPO, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    if name in sys.modules:
        return sys.modules[name]
    f = Path(tempfile.mkdtemp()) / f"{name}.py"
    f.write_bytes(src)
    spec = importlib.util.spec_from_file_location(name, f)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def scripted_trace(env, deck0, deck1, seed, every=20):
    """Both sides play their cheapest affordable card every ``every`` ticks; -> every raw() + the outcomes."""
    cost = {c.name: c.elixir for c in env.core.cards()}
    obs = env.reset(deck0, deck1, seed)
    trace = [obs]
    while not env.done:
        for s in (0, 1):
            me = next(p for p in obs["players"] if p["side"] == s)
            names = [env.names[c] for c in env.deck_ids[s]]
            hand = sorted((cost[h["name"]], names.index(h["name"])) for h in me["hand"])
            if hand and hand[0][0] <= me["elixir_exact"]:
                trace.append(env.act(s, hand[0][1], *CELL[s]))
        obs = env.advance_to(env.tick + every)
        trace.append(obs)
    return trace, env.outcome(0), env.outcome(1)


def pool_trace(env, entry, step=50):
    out = [env.reset(entry)]
    while not env.terminated and env.tick < env.tail_cap:
        env._advance_to(env.tick + step)
        out.append(env.raw())
    return out, env.ghost_ok, env.ghost_rejected, dict(env.ghost_reject_reasons), env.episode


def pool_entries(n):
    """The first ``n`` RoyaleSim-loadable pool entries, the last one with a non-base ghost form."""
    from pipeline.e1_pool import load_pool_v1
    out, env = [], RoyalePoolEnv()
    for e in load_pool_v1(REPO / "icebow/data/ghost_pool/pool_env_v1.jsonl"):
        if len(out) == n:
            break
        if len(out) == n - 1 and not {it["form"] for it in e["ghost_deck"]} - {"base"}:
            continue
        try:
            env.reset(e)
        except RE.UnsupportedDeck:
            continue
        out.append(e)
    return out


def digest(x):
    if isinstance(x, np.ndarray):
        return ("nd", str(x.dtype), x.shape, x.tobytes())
    if isinstance(x, dict):
        return tuple(sorted((str(k), digest(v)) for k, v in x.items() if k != "wall_s"))
    if isinstance(x, (list, tuple)):
        return tuple(digest(v) for v in x)
    return x


def tiny(decks):
    import torch
    from pipeline.dataset_gen import card_key
    from pipeline.model_gen import GenModel
    vocab = ["<pad>"] + sorted({card_key(n) for d in decks for n in d})
    torch.manual_seed(0)
    a = GenModel(d=16, layers=1, heads=2, d_c=8, n_cards=len(vocab)).eval()
    b = GenModel(d=16, layers=1, heads=2, d_c=8, n_cards=len(vocab)).eval()
    return vocab, a, b


def selfplay_rows(Emod, make_env, decks, tail_cap=1500):
    """run_selfplay_batch of 2 matches (tiny GenModels, recorded) under module ``Emod``; -> (results, every gen row)."""
    from pipeline.e1_view import Noise
    vocab, a, b = tiny(decks)
    learner, snap = Emod.GenPolicy(a, vocab), Emod.GenPolicy(b, vocab)
    rows = []
    real = learner.row

    def rec(*args):
        r = real(*args)
        rows.append(r)
        return r
    learner.row = rec
    cfg = {"policy": "sample", "tau": 0.27, "afford_mask": True, "stall_elixir": 9.0, "stall_seconds": 12.0,
           "obs": "live", "noise": Noise(**{n: False for n in Emod.NOISE_NAMES}), "p_random": 0.0,
           "random_hand_only": False, "grid": "lattice", "device": "cpu", "decide_every": 10, "slot": 0, "port": 0,
           "T": 0.5, "record": True, "opp_elixir": "counter"}
    spec = lambda i, side, ld, od: {"tag": f"sp_{i}", "opp": {"id": "snap", "type": "snapshot"}, "learner_deck": ld,  # noqa: E731
                                    "opp_deck": od, "learner_side": side, "seed": i}
    jobs = [(0, spec(0, 0, decks[0], decks[1]), 0, {"rollout_index": 0, "update": 0}),
            (1, spec(1, 1, decks[0], decks[1]), 0, {"rollout_index": 0, "update": 0})]
    out = []
    Emod.run_selfplay_batch(make_env, learner, {"snap": (snap, {**cfg, "record": False})}, jobs, cfg, 2,
                            on_result=out.append)
    return sorted(out, key=lambda r: r["tag"]), rows


@unittest.skipIf(RoyaleSelfPlayEnv is None, "royalegym not importable (run in research/ext/Royale/.venv)")
class TestDefaultIdentity(unittest.TestCase):
    """forms_mode default == "base" == the pre-forms code, raw state by raw state."""

    @classmethod
    def setUpClass(cls):
        cls.old = old_module("pipeline/royale_env.py", "royale_env_pre_forms")
        if cls.old is None:
            raise unittest.SkipTest(f"git show {PRE_FORMS} unavailable")

    def test_selfplay_env_identical(self):
        for d0, d1, seed in ((ICEBOW, HOGEQ, 0), (HOGEQ, ICEBOW, 3), (ICEBOW_HERO, ICEBOW, 7)):
            ref = scripted_trace(self.old.RoyaleSelfPlayEnv(), d0, d1, seed)
            self.assertGreater(len(ref[0]), 300)
            for env in (RoyaleSelfPlayEnv(), RoyaleSelfPlayEnv(forms_mode="base")):
                self.assertEqual(scripted_trace(env, d0, d1, seed), ref, (d0, seed))
                self.assertEqual([p.evo for p in env.core.state().players], [[], []])   # nothing evolves
        # negative control: the comparison sees forms -- deck mode (Tesla / Knight evolve) diverges from it
        self.assertNotEqual(scripted_trace(RoyaleSelfPlayEnv(forms_mode="deck"), ICEBOW, HOGEQ, 0),
                            scripted_trace(self.old.RoyaleSelfPlayEnv(), ICEBOW, HOGEQ, 0))

    def test_pool_env_identical(self):
        es = pool_entries(3)
        self.assertGreaterEqual(len(es), 3)
        for e in es:
            ref = pool_trace(self.old.RoyalePoolEnv(), e)
            self.assertEqual(pool_trace(RoyalePoolEnv(), e), ref, e["tag"])

    def test_policy_rows_identical_to_pre_forms_e1_eval(self):
        """The whole self-play rollout -- every GenModel input row (hand/next/deck/past forms included), every record
        and trajectory array -- under today's e1_eval + env (default) == the pre-forms e1_eval + env."""
        oldE = old_module("pipeline/e1_eval.py", "e1_eval_pre_forms")
        decks = (ICEBOW_HERO, HOGEQ)
        ref, ref_rows = selfplay_rows(oldE, lambda: self.old.RoyaleSelfPlayEnv(tail_cap=1500), decks)
        got, rows = selfplay_rows(E, lambda: RoyaleSelfPlayEnv(tail_cap=1500), decks)
        self.assertGreater(len(rows), 50)
        self.assertEqual(len(rows), len(ref_rows))
        self.assertEqual(digest(rows), digest(ref_rows))
        self.assertEqual(digest(got), digest(ref))
        self.assertNotIn("forms_mode", got[0])

    def test_loaded_deck_names_is_identity_off(self):
        for env in (types.SimpleNamespace(), RoyaleSelfPlayEnv()):
            self.assertIs(E.loaded_deck_names(env, 0, ICEBOW), ICEBOW)

    def test_bad_mode_refused(self):
        with self.assertRaises(ValueError):
            RoyaleSelfPlayEnv(forms_mode="evo")


@unittest.skipIf(RoyaleSelfPlayEnv is None, "royalegym not importable (run in research/ext/Royale/.venv)")
class TestDeckMode(unittest.TestCase):
    def test_icebow_evolutions_load_hero_falls_back(self):
        env = RoyaleSelfPlayEnv(forms_mode="deck")
        env.reset(ICEBOW_HERO, ["Knight@hero"] + HOGEQ[1:], 3)
        self.assertEqual(env.loaded_forms[0], [0, 1, 0, 0, 0, 1, 0, 0])      # Tesla, Knight evolve; IceWizard hero -> 0
        self.assertEqual(env.loaded_forms[1], [2, 0, 0, 0, 0, 0, 0, 0])      # Knight hero loads
        self.assertEqual(env.form_fallbacks, [(0, "IceWizard", 2)])
        self.assertEqual(env.decks[0], [n.split("@")[0] for n in ICEBOW_HERO])  # deck / deal unchanged by forms
        st = env.core.state()
        self.assertEqual(sorted(r[0] for r in st.players[0].evo), sorted([env.ids["Tesla"], env.ids["Knight"]]))
        self.assertEqual(len(st.players[1].abilities), 1)                    # the hero's button
        env.reset(ICEBOW, HOGEQ, 3)                                          # counted per reset
        self.assertEqual(env.form_fallbacks, [])
        base = RoyaleSelfPlayEnv()
        base.reset(ICEBOW, HOGEQ, 3)
        self.assertEqual(base.deal, env.deal)                                # same deal either mode

    def test_unknown_suffix_refused_before_state(self):
        env = RoyaleSelfPlayEnv(forms_mode="deck")
        with self.assertRaises(RE.UnsupportedDeck):
            env.reset(["Tesla@elite"] + ICEBOW[2:] + ["Knight"], HOGEQ, 0)
        self.assertFalse(hasattr(env, "decks"))

    def test_evolved_tesla_on_every_third_play(self):
        """Tesla@evolution plays its evolution on its 3rd and 6th play (STATUS_EVOLVED on the unit, the engine's
        ``evo`` row says so beforehand); base mode never evolves it."""
        for mode, want in (("deck", [False, False, True, False, False, True]), ("base", [False] * 6)):
            env = RoyaleSelfPlayEnv(forms_mode=mode)
            env.reset(ICEBOW, HOGEQ, 0)
            cost = {c.name: c.elixir for c in env.core.cards()}
            tesla = env.ids["Tesla"]
            ti = env.deck_ids[0].index(tesla)
            got, flagged = [], []
            while len(got) < 6 and not env.done:
                st = env.core.state()
                me = st.players[0]
                el = me.elixir_milli / 1000.0
                if tesla in me.hand and el >= cost["Tesla"]:
                    before = {e.uid for e in st.entities if e.card_id == tesla}
                    evo = [r for r in me.evo if r[0] == tesla]
                    flagged.append(bool(evo and evo[0][2]))
                    self.assertTrue(env.act(0, ti, 5000, 12000)["accepted"])
                    env.advance_to(env.tick + 20)
                    new = [e for e in env.core.state().entities if e.card_id == tesla and e.uid not in before]
                    self.assertEqual(len(new), 1)
                    got.append(bool(status_of(new[0]) & STATUS_EVOLVED))
                    continue
                other = sorted((cost[env.names[c]], env.deck_ids[0].index(c)) for c in me.hand if c != tesla)
                if tesla not in me.hand and other and other[0][0] <= el:      # cycle to the Tesla
                    env.act(0, other[0][1], *CELL[0])
                env.advance_to(env.tick + 20)
            self.assertEqual(got, want, mode)
            self.assertEqual(flagged, want, mode)

    def test_policy_form_inputs_follow_loaded_forms(self):
        """SelfPlaySide's engine deck -> GenPolicy.slot_ident forms: deck mode = what the engine loaded (Tesla 1,
        Knight 1, the refused IceWizard hero 0); base mode = the decked suffix, as before (IceWizard 2)."""
        from pipeline.dataset_gen import card_form
        vocab, a, _ = tiny((ICEBOW_HERO, HOGEQ))
        pol = E.GenPolicy(a, vocab)
        cfg = {"policy": "live", "tau": 0.27, "afford_mask": True, "stall_elixir": 9.0, "stall_seconds": 12.0,
               "obs": "live", "noise": None, "p_random": 0.0, "random_hand_only": False, "grid": "lattice",
               "device": "cpu", "decide_every": 10, "slot": 0, "port": 0, "T": 0.5, "record": False}
        from pipeline.e1_view import Noise
        cfg["noise"] = Noise(**{n: False for n in E.NOISE_NAMES})
        for mode, want in (("deck", {"Tesla": 1, "Knight": 1, "IceWizard": 0}),
                           ("base", {"Tesla": 1, "Knight": 1, "IceWizard": 2})):
            env = RoyaleSelfPlayEnv(forms_mode=mode)
            spec = {"tag": "f", "learner_deck": ICEBOW_HERO, "opp_deck": HOGEQ, "learner_side": 0, "seed": 1}
            m = E.SelfPlayMatch(env, spec, 0, cfg, cfg, pol, pol)
            side = m.learner
            _, form = pol.slot_ident(side.engine_deck, side.deck_index_of_slot)
            by_name = {side.engine_deck[side.deck_index_of_slot[s]].split("@")[0]: int(form[s]) for s in range(8)}
            self.assertEqual({k: by_name[k] for k in want}, want, mode)
            if mode == "deck":                                   # == the engine's loaded form, card by card
                self.assertEqual([card_form(n) for n in side.engine_deck], env.loaded_forms[0])
            self.assertIn(m.learner, m.due())
            m.learner.prepare()
            row = m.learner.gen_row(pol)
            hs = row["hand_slot"]
            self.assertEqual(list(row["hand_form"]), [int(form[s]) for s in hs])

    def test_fork_carries_forms(self):
        from pipeline import search_s0 as S
        env = RoyaleSelfPlayEnv(forms_mode="deck")
        cfg = {"policy": "live", "tau": 0.27, "afford_mask": True, "stall_elixir": 9.0, "stall_seconds": 12.0,
               "obs": "live", "p_random": 0.0, "random_hand_only": False, "grid": "lattice", "device": "cpu",
               "decide_every": 10, "slot": 0, "port": 0, "T": 0.5, "record": False}
        from pipeline.e1_view import Noise
        cfg["noise"] = Noise(**{n: False for n in E.NOISE_NAMES})
        vocab, a, _ = tiny((ICEBOW, HOGEQ))
        pol = E.GenPolicy(a, vocab)
        m = E.SelfPlayMatch(env, {"tag": "f", "learner_deck": ICEBOW, "opp_deck": HOGEQ, "learner_side": 0,
                                  "seed": 2}, 0, cfg, cfg, pol, pol)
        f = S.fork_into(m, RoyaleSelfPlayEnv(forms_mode="deck"), env.core.save_state())
        self.assertEqual(f.env.loaded_forms, env.loaded_forms)
        self.assertEqual([p.evo for p in f.env.core.state().players], [p.evo for p in env.core.state().players])
        self.assertTrue(env.core.state().players[0].evo)

    def test_pool_env_deck_mode(self):
        e = pool_entries(1)[0]
        self.assertTrue({it["form"] for it in e["ghost_deck"]} - {"base"})
        env = RoyalePoolEnv(forms_mode="deck")
        env.reset(e)
        g = env.opp
        want = [RE.FORM_OF[it["form"]] for it in env.final_decks[g]]
        got = env.loaded_forms[g]
        fb = [(s, n, f) for s, n, f in env.form_fallbacks if s == g]
        self.assertEqual(sum(1 for w, x in zip(want, got) if w != x), len(fb))
        self.assertTrue(all(x in (w, 0) for w, x in zip(want, got)))
        ours = env.final_decks[env.side]
        names = [f"{it['name']}@{it['form']}" if it["form"] != "base" else it["name"] for it in ours]
        self.assertEqual(E.loaded_deck_names(env, env.side, names),
                         [n.split("@")[0] + ("", "@evolution", "@hero")[f] for n, f in zip(names, env.loaded_forms[env.side])])


@unittest.skipIf(RoyaleSelfPlayEnv is None, "royalegym not importable (run in research/ext/Royale/.venv)")
class TestPlumbing(unittest.TestCase):
    def test_rl_config_key_and_actor(self):
        """rl_royale.yaml forms_mode (default base, overridable) -> actor_base -> the actor's env: a screen job on a
        pool entry under deck mode returns a record with forms_mode / form_fallbacks."""
        import io
        import torch
        from pipeline import rl_royale as RL
        from pipeline.model_v3 import S1Model
        cfg = RL.load_config(REPO / "pipeline/rl_royale.yaml", [], smoke=False)
        self.assertEqual(cfg["forms_mode"], "base")
        cfg = RL.load_config(REPO / "pipeline/rl_royale.yaml", ["forms_mode=deck"], smoke=False)
        L = object.__new__(RL.Learner)
        L.cfg, L.init_meta, L.grid = cfg, {"args": {"d": 16, "layers": 1}}, "floor"
        from pipeline.royale_runtime import activate
        L.runtime = activate()
        base = L.actor_base()
        self.assertEqual(base["forms_mode"], "deck")
        base["actor_device"], base["actor_threads"], base["in_flight"] = "cpu", 2, 1
        L.cfg = dict(cfg, forms_mode="evo")
        with self.assertRaises(SystemExit):
            L.actor_base()
        torch.manual_seed(0)
        buf = io.BytesIO()
        torch.save(S1Model(d=16, layers=1).state_dict(), buf)
        e = pool_entries(1)[0]

        class Out(list):
            def cancel_join_thread(self):
                pass

            def put(self, m):
                self.append(m)
        in_q, out = queue.Queue(), Out()
        in_q.put(("screen", 0, buf.getvalue(), [(0, e, 0)]))
        in_q.put(None)
        RL.actor_main(0, 0, in_q, out, base)
        done = [m for m in out if m[0] == "done"]
        self.assertEqual(len(done), 1, [m for m in out if m[0] == "error"])
        rec = done[0][3][0]
        self.assertEqual(rec["forms_mode"], "deck")
        self.assertIsInstance(rec["form_fallbacks"], list)

    def test_search_s0_flag(self):
        from pipeline import search_s0 as S
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "run"
            S.main(["--out", str(out), "--seeds", "0,", "--opps", "gen", "--arms", "plain", "--forms-mode", "deck",
                    "--tail-cap", "200"])
            run = json.loads((out / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(run["forms_mode"], "deck")
            self.assertEqual(S._W["runner"].make_env().forms_mode, "deck")
            rec = json.loads((out / "matches.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(rec.get("forms_mode"), "deck", rec)

    def test_run_screen_flag(self):
        sys.path.insert(0, str(REPO / "scratchpad/gauntlet/L68/generalist/screen_gen"))
        import run_screen
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "s.jsonl"
            run_screen.main(["--ckpt", str(REPO / "icebow/data/pipeline/gen_v1_s0/gen_s0.pt"), "--out", str(out), "--max-matches",
                             "1", "--batch", "1", "--seeds", "0", "--forms-mode", "deck"])
            meta = json.loads(out.with_suffix(".run.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["forms_mode"], "deck")
            rec = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(rec["forms_mode"], "deck")


if __name__ == "__main__":
    unittest.main()
