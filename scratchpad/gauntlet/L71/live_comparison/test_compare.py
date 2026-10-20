"""Adversarial tests for Q0. No game/model imports or filesystem fixtures."""
import copy
import io
import json
import unittest
from unittest.mock import patch

import compare as c

NAME = 'live_play_20261004_210000.jsonl'


def rows():
    return [{'event': 'start', 'ckpt': 'C:/data/rseries_r1e31_u0155.pt', 'dry_run': False},
            {'event': 'play', 'name': 'Rocket', 'tick': 10, 'xy': [.2, .2]},
            {'event': 'unconfirmed', 'name': 'Rocket', 'tick': 60},
            {'event': 'play', 'name': 'Xbow', 'tick': 80, 'xy': [.3, .6]},
            {'event': 'confirmed', 'name': 'Xbow', 'tick': 106},
            {'event': 'ability', 'tick': 150},
            {'event': 'ability_confirmed', 'tick': 152},
            {'event': 'end', 'played': 2, 'confirmed': 1, 'seconds': 180}]


class ComparisonTests(unittest.TestCase):
    def test_checkpoint_from_start_not_assumed_global(self):
        m, why = c.match_summary(NAME, rows())
        self.assertEqual(m['model'], 'r1e_u0155')
        self.assertIsNone(why)
        r = rows(); r[0]['ckpt'] = 'C:\\data\\rseries_r1_u0155.pt'
        self.assertEqual(c.match_summary(NAME, r)[0]['model'], 'old_r1_u0155')

    def test_reject_other_and_dry_runs(self):
        for value in (True, None):
            r = rows(); r[0]['dry_run'] = value
            self.assertIsNone(c.match_summary(NAME, r)[0])
        r = rows(); r[0]['ckpt'] = 'gen_s0.pt'
        self.assertIsNone(c.match_summary(NAME, r)[0])

    def test_receipts_and_missing_data(self):
        m, _ = c.match_summary(NAME, rows())
        g = c.aggregate([m])['r1e_u0155']
        self.assertEqual(g['card_attempts']['Rocket'], 1)
        self.assertEqual(g['card_confirmed'].get('Rocket', 0), 0)
        self.assertEqual(g['confirmed'], 1)
        self.assertEqual(g['xbow_confirmed_intended_xy'], {'0.3000,0.6000': 1})
        self.assertIsNone(g['preemptive_log_rate'])
        self.assertIsNone(g['trophies_over_time'])
        self.assertEqual(g['unknown_outcomes'], 1)
        self.assertEqual(g['losses'], 0)

    def test_mismatched_and_duplicate_receipts_fail(self):
        r = rows(); r[2]['name'] = 'Log'
        with self.assertRaises(ValueError): c.match_summary(NAME, r)
        r = rows(); r.insert(3, copy.deepcopy(r[2]))
        with self.assertRaises(ValueError): c.match_summary(NAME, r)

    def test_bad_end_totals_fail(self):
        r = rows(); r[-1]['confirmed'] = 2
        with self.assertRaises(ValueError): c.match_summary(NAME, r)

    def test_unfinished_excluded_from_behavior(self):
        m, _ = c.match_summary(NAME, rows()[:-1])
        g = c.aggregate([m])['r1e_u0155']
        self.assertEqual(g['incomplete_logs'], 1)
        self.assertEqual(g['attempts'], 0)
        self.assertEqual(g['resolved_matches'], 0)

    def test_wilson_known_values_and_extremes(self):
        lo, hi = c.wilson(50, 100)
        self.assertAlmostEqual(lo, .4038315304)
        self.assertAlmostEqual(hi, .5961684696)
        self.assertIsNone(c.wilson(0, 0))
        self.assertAlmostEqual(c.wilson(0, 10)[0], 0)
        self.assertAlmostEqual(c.wilson(10, 10)[1], 1)
        with self.assertRaises(ValueError): c.wilson(11, 10)

    def test_pair_outcome_and_unread(self):
        for won, expected in ((True, 'win'), (False, 'loss'), (None, 'unread_or_draw')):
            m, _ = c.match_summary(NAME, rows())
            n = {'file': 'nav', 't': m['estimated_end_unix'] + 3, 'dry_run': False,
                 'outcomes': [{'won': won}]}
            c.join_outcomes([m], [n], [m['started_unix']])
            self.assertEqual(m['outcome'], expected)

    def test_ambiguous_late_or_next_match_navigation_not_joined(self):
        for kind in ('duplicate', 'late', 'next_match', 'two_outcomes', 'dry'):
            m, _ = c.match_summary(NAME, rows())
            t = m['estimated_end_unix']
            n = {'file': 'nav', 't': t + (31 if kind == 'late' else 3),
                 'dry_run': kind == 'dry', 'outcomes': [{'won': True}]}
            navs = [n, dict(n, file='nav2')] if kind == 'duplicate' else [n]
            if kind == 'two_outcomes': n['outcomes'].append({'won': False})
            starts = [m['started_unix']] + ([t + 2] if kind == 'next_match' else [])
            c.join_outcomes([m], navs, starts)
            self.assertEqual(m['outcome'], 'unknown', kind)

    def test_incomplete_tail_ignored_internal_corruption_rejected(self):
        p = c.ROOT / 'fake.jsonl'
        raw = (json.dumps({'event': 'start'}) + '\n').encode() + b'{"event":'
        with patch('pathlib.Path.open', return_value=io.BytesIO(raw)):
            parsed, source = c.source_prefix(p, len(raw))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(source['incomplete_tail_bytes'], 9)
        raw = b'broken\n'
        with patch('pathlib.Path.open', return_value=io.BytesIO(raw)):
            with self.assertRaises(ValueError): c.source_prefix(p, len(raw))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ComparisonTests))
    if not result.wasSuccessful(): raise SystemExit(1)
    print('LIVE_COMPARISON_TESTS_PASSED')
