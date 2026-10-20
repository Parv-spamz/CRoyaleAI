import copy
import json
from pathlib import Path
import unittest
from pipeline.native_recording import tag_native_recording
from pipeline import dataset_gen as D, obs_contract as O

ROOT = Path(__file__).resolve().parents[2]


class NativeRecordingTests(unittest.TestCase):
    def fixture(self):
        catalog = json.loads((ROOT/'research/ext/cr-native-sandbox/native_core/data/live_card_catalog.json').read_text())['cards']
        knight = next(c for c in catalog if c['display_name'] == 'Knight')
        ids = [knight['card_id'], knight['evolution_form_id'], knight['hero_form_id']]
        rows = [[1, 5000+i*1000, 20000, 'Knight', 100, 100, 3, cid, 100+i] for i, cid in enumerate(ids)]
        return dict(record_native=True, final_decks={'0': [], '1': []},
                    frames=[dict(tick=20, elixir=[5, 5], towers=[], entities=rows)], play_frames=[])

    def test_exact_forms_ignore_hidden_deck_and_play_history(self):
        rec = self.fixture()
        before = copy.deepcopy(rec)
        expected = tag_native_recording(rec, {})
        rec['final_decks']['1'] = ['Knight@hero']
        actual = tag_native_recording(rec, {})
        self.assertEqual(actual['frames'], expected['frames'])
        self.assertEqual(expected['frames'][0]['unit_forms'], [0, 1, 2])
        self.assertEqual(expected['frames'][0]['entity_ids'], [100, 101, 102])
        self.assertEqual(before['frames'][0]['entities'], rec['frames'][0]['entities'])
        self.assertEqual([len(e) for e in expected['frames'][0]['entities']], [7, 7, 7])

    def test_compact_native_forms_match_reader_style_raw_entities(self):
        rec = self.fixture()
        compact = tag_native_recording(rec, {})['frames'][0]
        raw = dict(tick=20, players=[], episode=dict(crown_towers=[]), entities=[
            dict(side=e[0], x=e[1], y=e[2], name=e[3], hp=e[4], max_hp=e[5],
                 kind=e[6], card_id=e[7], entity_id=e[8]) for e in rec['frames'][0]['entities']])
        deck = O.load_deck('icebow')
        for side in (0, 1):
            a = O.from_engine(compact, side, deck, feature_version=3)
            b = O.from_engine(raw, side, deck, feature_version=3)
            self.assertEqual(a.units, b.units)

    def test_non_full_native_rows_do_not_turn_card_id_into_kind(self):
        rec = self.fixture()
        for e in rec['frames'][0]['entities']:
            del e[6]
        frame = tag_native_recording(rec, {})['frames'][0]
        self.assertTrue(all(len(e) == 6 for e in frame['entities']))
        self.assertEqual(frame['unit_forms'], [0, 1, 2])

    def test_bad_shapes_missing_marker_or_ids_fail(self):
        for issue in ('marker', 'shape', 'duplicate', 'missing_id'):
            rec = self.fixture()
            if issue == 'marker':
                rec['record_native'] = False
            elif issue == 'shape':
                rec['frames'][0]['entities'][0].append(99)
            elif issue == 'duplicate':
                rec['frames'][0]['entities'][1][-1] = rec['frames'][0]['entities'][0][-1]
            else:
                rec['frames'][0]['entities'][0][-1] = -1
            with self.subTest(issue=issue), self.assertRaises(ValueError):
                tag_native_recording(rec, {})


if __name__ == '__main__':
    unittest.main()
