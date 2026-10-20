import contextlib
import io
import json
from pathlib import Path
import sys
import uuid
import unittest
from unittest.mock import patch

from mock_replay import MockEnv, rd, run_mock
from research.sandbox_tools import replay_batch as batch

FIXTURE = json.loads((Path(__file__).parent / "fixtures/legacy_replay.json").read_text(encoding="utf-8"))
BATTLE = dict(FIXTURE["battle"],
              opponent_deck="archer-queen,monk,knight,skeletons,tesla,rocket,the-log,ice-spirit",
              team_deck="archer-queen,monk,knight,skeletons,tesla,rocket,the-log,ice-spirit")


@contextlib.contextmanager
def temporary_output():
    # Inherit workspace ACLs; tempfile's private ACL is inaccessible in this sandbox.
    path = Path(__file__).resolve().parent / ("tmp_" + uuid.uuid4().hex)
    path.mkdir()
    try:
        yield str(path)
    finally:
        for child in path.iterdir():
            child.unlink()
        path.rmdir()


def press(tick=17, side=1, candidates=None, **extra):
    return dict(play_index=0, tick=tick, side=side, attr_card="_invalid", ability=1, x=None, y=None,
                ability_source_candidates=["archer-queen"] if candidates is None else candidates, **extra)


def unit(id=5000010, side=1, card="archer-queen", ready=True, hp=100):
    return dict(entity_id=id, side=side, base_card_id=rd.card_for_slug(card),
                ability_available=ready, hp=hp, max_hp=100, x=1000, y=2000, name=card)


class AbilityTests(unittest.TestCase):
    def test_right_tick_side_and_newest_eligible_entity(self):
        env = MockEnv(lambda t: [unit(5000001), unit(5000009), unit(5000099, side=0),
                                 unit(5000100, ready=False), unit(5000101, hp=0)])
        out, env = run_mock(BATTLE, [press()], env, drive_abilities=True, record_every=5, record_plays=True)
        self.assertEqual(env.calls, [(17, "ability", {"side": 1, "entity_id": 5000009})])
        e = out["log"][0]
        self.assertEqual((e["kind"], e["ability"], e["card"], e["result_code"], e["accepted"]),
                         ("ability", True, "archer-queen", 0, True))
        self.assertEqual(out["play_frames"], [])
        self.assertIn(17, env.observed)

    def test_multiple_candidates_resolve_only_live_side(self):
        env = MockEnv(lambda t: [unit(card="monk"), unit(side=0), unit(hp=0)])
        out, env = run_mock(BATTLE, [press(candidates=["archer-queen", "monk"])], env, drive_abilities=True)
        self.assertEqual(out["log"][0]["card"], "monk")
        self.assertEqual(env.calls[0][2]["side"], 1)

    def test_multiple_live_candidates_skip_even_if_only_one_ready(self):
        out, env = run_mock(BATTLE, [press(candidates=["archer-queen", "monk"])],
                            MockEnv(lambda t: [unit(), unit(card="monk", ready=False)]), drive_abilities=True)
        self.assertEqual(env.calls, [])
        self.assertIn("multiple live candidates", out["log"][0]["skipped"])
        self.assertIsNone(out["log"][0]["card"])

    def test_no_eligible_entity_logged_skip(self):
        for entities in ([], [unit(ready=False)], [unit(side=0)], [unit(hp=0)]):
            with self.subTest(entities=entities):
                out, env = run_mock(BATTLE, [press()], MockEnv(lambda t: entities), drive_abilities=True)
                self.assertEqual(env.calls, [])
                e = out["log"][0]
                self.assertFalse(e["accepted"])
                self.assertIsNone(e["result_code"])
                self.assertIsNone(e["entity_id"])
                self.assertEqual(e["card"], "archer-queen")
                self.assertIn("no eligible", e["skipped"])
                self.assertEqual(out["grade"]["plays_driven"], 0)

    def test_no_candidate_and_no_live_candidate(self):
        for candidates, reason in (([], "no candidates"), (["archer-queen", "monk"], "no live candidate")):
            with self.subTest(candidates=candidates):
                out, env = run_mock(BATTLE, [press(candidates=candidates)], drive_abilities=True)
                self.assertEqual(env.calls, [])
                self.assertIn(reason, out["log"][0]["skipped"])

    def test_crawl_deck_fallback_and_explicit_form_attribution(self):
        deck = rd.deck_for_side(dict(BATTLE, team_deck=BATTLE["team_deck"].replace("knight,", "knight-hero,")), 1)
        self.assertEqual(rd.ability_candidates({"attr_card": "_invalid"}, deck), ["archer-queen", "monk", "knight"])
        self.assertEqual(rd.ability_candidates({"ability_source_candidates": '["knight-hero", "knight-hero"]'}, deck), ["knight"])
        row = press()
        del row["ability_source_candidates"]
        out, _ = run_mock(BATTLE, [row], MockEnv(lambda t: [unit(card="monk")]), drive_abilities=True)
        self.assertEqual(out["log"][0]["card"], "monk")

    def test_retry_refreshes_id_at_next_tick(self):
        env = MockEnv(lambda t: [unit(5000000 + t)], codes=[1050, 0])
        out, env = run_mock(BATTLE, [press()], env, drive_abilities=True)
        self.assertEqual(env.calls, [(17, "ability", {"side": 1, "entity_id": 5000017}),
                                     (18, "ability", {"side": 1, "entity_id": 5000018})])
        self.assertEqual(out["log"][0]["delay_ticks"], 1)

    def test_retry_entity_disappears(self):
        env = MockEnv(lambda t: [unit()] if t == 17 else [], codes=[1050])
        out, env = run_mock(BATTLE, [press()], env, drive_abilities=True)
        self.assertEqual(len(env.calls), 1)
        self.assertIn("no eligible", out["log"][0]["skipped"])
        self.assertEqual(out["log"][0]["result_code"], 1050)

    def test_retry_never_switches_attributed_card(self):
        env = MockEnv(lambda t: [unit(card="archer-queen" if t == 17 else "monk")], codes=[1050])
        out, env = run_mock(BATTLE, [press(candidates=["archer-queen", "monk"])], env, drive_abilities=True)
        self.assertEqual(len(env.calls), 1)
        self.assertEqual(out["log"][0]["card"], "archer-queen")
        self.assertIn("no eligible", out["log"][0]["skipped"])

    def test_hero_native_form_and_side_zero(self):
        knight = rd.card_for_slug("knight")
        entity = unit(side=0, card="knight")
        del entity["base_card_id"]
        entity["card_id"] = rd.catalog()[knight]["hero_form_id"]
        battle = dict(BATTLE, opponent_deck=BATTLE["opponent_deck"].replace("knight,", "knight-hero,"))
        out, env = run_mock(battle, [press(side=0, candidates=["knight-hero"])],
                            MockEnv(lambda t: [entity]), drive_abilities=True)
        self.assertTrue(out["log"][0]["accepted"])
        self.assertEqual(env.calls[0][2], {"side": 0, "entity_id": entity["entity_id"]})

    def test_raw_pointer_is_not_an_entity_handle(self):
        entity = unit()
        entity["id"] = entity.pop("entity_id")
        out, env = run_mock(BATTLE, [press()], MockEnv(lambda t: [entity]), drive_abilities=True)
        self.assertEqual(env.calls, [])
        self.assertIn("no eligible", out["log"][0]["skipped"])

    def test_explicit_attribution_does_not_fall_back_to_other_live_card(self):
        out, env = run_mock(BATTLE, [press()], MockEnv(lambda t: [unit(card="monk")]), drive_abilities=True)
        self.assertEqual(env.calls, [])
        self.assertEqual(out["log"][0]["card"], "archer-queen")

    def test_exhaustion_not_retried_and_slack_bounded(self):
        for codes, expected_calls in (([1014], 1), ([1050] * 4, 3)):
            with self.subTest(codes=codes):
                out, env = run_mock(BATTLE, [press()], MockEnv(lambda t: [unit()], codes), drive_abilities=True)
                self.assertEqual(len(env.calls), expected_calls)
                self.assertFalse(out["log"][0]["accepted"])
                self.assertEqual(out["log"][0]["result_code"], codes[0])

    def test_terminal_before_press_and_during_delay(self):
        for terminal, codes in ((17, []), (18, [1050])):
            with self.subTest(terminal=terminal):
                out, env = run_mock(BATTLE, [press()], MockEnv(lambda t: [unit()], codes, terminal), drive_abilities=True)
                self.assertEqual(len(env.calls), len(codes))
                self.assertIn("terminal", out["log"][0]["skipped"])
                self.assertTrue(out["log"][0]["ability"])

    def test_same_tick_order_and_following_card_after_delay(self):
        card = dict(play_index=1, tick=17, side=1, attr_card="knight", ability=0, x=1000, y=2000)
        out, env = run_mock(BATTLE, [press(), card], MockEnv(lambda t: [unit()], [1050, 0]), drive_abilities=True)
        self.assertEqual([(t, kind) for t, kind, _ in env.calls], [(17, "ability"), (18, "ability"), (18, "play")])
        self.assertEqual(out["log"][1]["tick"], 17)
        self.assertEqual(out["log"][1]["engine_tick"], 18)

    def test_off_matches_prechange_recorded_events_byte_for_byte(self):
        expected = json.dumps(FIXTURE["legacy_log"], separators=(",", ":"))
        for options in ({}, {"drive_abilities": False}):
            out, env = run_mock(FIXTURE["battle"], FIXTURE["events"], **options)
            self.assertEqual(json.dumps(out["log"], separators=(",", ":")), expected)
            self.assertNotIn("drive_abilities", out)
            self.assertFalse(any(kind == "ability" for _, kind, _ in env.calls))
        self.assertTrue(any("ability" in e.get("skipped", "") for e in FIXTURE["legacy_log"]))

    def test_batch_flag_passed_to_primary_and_determinism_runs(self):
        result, _ = run_mock(BATTLE, [press()], drive_abilities=True)
        for enabled in (False, True):
            with self.subTest(enabled=enabled), temporary_output() as tmp:
                tags = Path(tmp) / "tags.json"
                tags.write_text('["mock"]', encoding="utf-8")
                argv = ["replay_batch", "--tags", str(tags), "--out", tmp, "--determinism-every", "1"]
                if enabled:
                    argv.append("--drive-abilities")
                with patch.object(sys, "argv", argv), patch.object(batch.replay_drive, "drive", return_value=result) as drive, \
                     patch.object(batch, "OUT", Path(tmp)), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(batch.main(), 0)
                self.assertEqual(drive.call_count, 2)
                self.assertTrue(all(c.kwargs["drive_abilities"] == enabled for c in drive.call_args_list))

    def test_single_cli_flag_passed(self):
        result, _ = run_mock(BATTLE, [press()], drive_abilities=True)
        with temporary_output() as tmp, patch.object(rd, "OUT_DIR", Path(tmp)), \
             patch.object(sys, "argv", ["replay_drive", "--tag", "mock", "--drive-abilities", "--quiet"]), \
             patch.object(rd, "drive", return_value=result) as drive, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(rd.main(), 0)
            self.assertTrue(drive.call_args.kwargs["drive_abilities"])


if __name__ == "__main__":
    unittest.main()
