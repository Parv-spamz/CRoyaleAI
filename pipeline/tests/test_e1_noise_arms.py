"""Tests for the E1 attribution screen: e1_view.Noise's per-component switches over live_view, and
e1_eval's ``--noise-off`` CLI (HANDOFF "AW. L67aq" proposal 1: "split the 40-point gap by noise source").

    icebow/.venv/Scripts/python.exe -m unittest pipeline.tests.test_e1_noise_arms -v

No engine, no GPU, no training, no network. ``patch("pipeline.e1_view.DEGRADE_RECALL", ...)`` etc. below only
rebinds the NAME e1_view imported into its own module for the duration of one test -- obs_contract.py itself
is never touched.
"""
from __future__ import annotations

import dataclasses
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from pipeline import e1_eval                                  # noqa: E402
from pipeline import e1_view                                   # noqa: E402
from pipeline import obs_contract as oc                        # noqa: E402
from pipeline import vocab                                     # noqa: E402
from pipeline.e1_view import ALL_NOISE_OFF, KING_HP_LIVE, Noise, live_view    # noqa: E402
from pipeline.obs_contract import UNKNOWN_TEAM_RATE             # noqa: E402
from pipeline.tests.test_obs_contract import ENGINE_DECK, raw_obs   # noqa: E402

NOISE_FIELDS = ("recall", "false_pos", "position", "team", "unit_hp", "my_elixir", "opp_elixir", "king_hp",
                "deploying", "conf")


def _is_subsequence(sub, full) -> bool:
    """True iff every item of ``sub`` occurs in ``full``, in the same order (not necessarily contiguous)."""
    it = iter(full)
    return all(any(x == y for y in it) for x in sub)


def _extra_after_subsequence(sub, full) -> list:
    """Assuming ``sub`` is a subsequence of ``full`` (checked by the caller via ``_is_subsequence``), return
    the elements of ``full`` that are NOT part of that match -- e.g. the rescued (recall=False) units, given
    ``sub`` = the default (recall=True) path's kept units."""
    extra = []
    it = iter(sub)
    target = next(it, None)
    for item in full:
        if target is not None and item == target:
            target = next(it, None)
        else:
            extra.append(item)
    return extra


def _deck():
    return oc.load_deck("icebow")


def _bs(deck, *, extra_enemy: int = 6) -> oc.BoardState:
    """The obs_contract fixture board plus extra enemy bodies icebow cannot produce, through the SAME
    compact_raw -> from_engine path e1_eval uses (matches test_e1_baseline._engine_bs)."""
    from pipeline import engine_play as ep
    o = raw_obs(0)
    names = ["HogRider", "Musketeer", "Valkyrie", "Giant", "MiniPekka", "Wizard"]
    for i in range(extra_enemy):
        o["entities"].append({"side": 1, "x": 3000 + 2000 * i, "y": 18000 + 500 * i, "card_id": 26000100 + i,
                              "name": names[i % len(names)], "hp": 500, "max_hp": 1000, "kind": 15})
    return oc.from_engine(ep.compact_raw(o), 0, deck, engine_deck=ENGINE_DECK, unmapped=set())


def _reference_live_view(bs: oc.BoardState, rng: np.random.Generator, deck: oc.Deck) -> oc.BoardState:
    """The PRE-Noise live_view, written independently of e1_view.py, straight from its own module docstring:
    obs_contract.degrade() (untouched, all defaults) + the three live fill rules. Used to pin item 2 against
    the unmodified obs_contract.py rather than against e1_view's own (now Noise-aware) implementation."""
    d = oc.degrade(bs, rng)
    allowed = oc.mine_classes(deck)

    def fill(u):
        side = u.side
        if side < 0 and vocab.base_key(vocab.UNIT_VOCAB[int(u.cls)]) not in allowed:
            side = 1
        return replace(u, hp_frac=1.0, side=side)

    units = tuple(fill(u) for u in d.units)
    spells = tuple(fill(u) for u in d.spells)
    towers = tuple(replace(t, hp_frac=1.0) if (t.kind == "king" and t.alive) else t for t in d.towers)
    return replace(d, units=units, spells=spells, towers=towers)


# ------------------------------------------------------------------------------------------------------
# item 2: all switches at defaults == today's live_view / obs_contract.degrade, bit-identical
# ------------------------------------------------------------------------------------------------------
class TestAllOnBitIdentical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deck = _deck()
        cls.boards = [_bs(cls.deck), _bs(cls.deck, extra_enemy=0), raw_obs_board(cls.deck)]

    def test_degrade_switchable_matches_obs_contract_degrade(self):
        for bi, bs in enumerate(self.boards):
            for seed in range(12):
                d_ref = oc.degrade(bs, np.random.default_rng(seed))
                d_new = e1_view._degrade_switchable(bs, np.random.default_rng(seed), Noise())
                self.assertEqual(d_ref, d_new, (bi, seed))

    def test_live_view_matches_hand_written_reference(self):
        for bi, bs in enumerate(self.boards):
            for seed in range(12):
                ref = _reference_live_view(bs, np.random.default_rng(seed), self.deck)
                new = live_view(bs, np.random.default_rng(seed), self.deck)                  # default Noise
                new_explicit = live_view(bs, np.random.default_rng(seed), self.deck, Noise())
                self.assertEqual(ref, new, (bi, seed))
                self.assertEqual(ref, new_explicit, (bi, seed))
                tok_r, mask_r, sc_r = oc.to_tokens(ref, 64)
                tok_n, mask_n, sc_n = oc.to_tokens(new, 64)
                self.assertTrue(np.array_equal(tok_r, tok_n) and np.array_equal(mask_r, mask_n)
                                and np.array_equal(sc_r, sc_n))


def raw_obs_board(deck):
    from pipeline import engine_play as ep
    return oc.from_engine(ep.compact_raw(raw_obs(1)), 1, deck, engine_deck=ENGINE_DECK, unmapped=set())


# ------------------------------------------------------------------------------------------------------
# O5: golden for the split -- live_view(..., Noise(my_elixir=False, opp_elixir=False, king_hp=False)) must
# stay bit-identical to what the PRE-split single-field live_view(..., Noise(scalars=False)) produced at
# HEAD 4bca159. Captured BEFORE the O5 edit landed, by running (against the unedited e1_view.py, which still
# had the single `scalars` field) the exact fixtures/pattern this file already uses:
#     deck = _deck()
#     boards_seeds = [(_bs(deck), 0), (_bs(deck, extra_enemy=0), 1), (raw_obs_board(deck), 2)]
#     golden = [dataclasses.asdict(live_view(bs, np.random.default_rng(seed), deck, Noise(scalars=False)))
#               for bs, seed in boards_seeds]
# (ad hoc capture script, run once against the unedited tree; full script + exact output logged in
# scratchpad/gauntlet/L67/split/O5_split_switch.md). Pasted verbatim (pprint.pformat) below.
# ------------------------------------------------------------------------------------------------------
_O5_GOLDEN_SCALARS_OFF = [{'deck': (0, 164, 2, 3, 4, 149, 6, 7),
  'double_elixir': False,
  'my_elixir': 6.37,
  'my_elixir_exact': True,
  'my_hand': (164, 149, 3, 2),
  'my_next': 7,
  'opp_elixir': 3.0,
  'overtime': False,
  'source': 'degraded',
  'spells': (),
  't_sec': 60.0,
  't_source': 'clock',
  'towers': ({'alive': True, 'hp_frac': 1.0, 'kind': 'king', 'lane': None, 'side': 0},
             {'alive': True, 'hp_frac': 0.6553079947575361, 'kind': 'princess', 'lane': 'L', 'side': 0},
             {'alive': True, 'hp_frac': 1.0, 'kind': 'princess', 'lane': 'R', 'side': 0},
             {'alive': True, 'hp_frac': 1.0, 'kind': 'king', 'lane': None, 'side': 1},
             {'alive': True, 'hp_frac': 0.16382699868938402, 'kind': 'princess', 'lane': 'L', 'side': 1},
             {'alive': True, 'hp_frac': 1.0, 'kind': 'princess', 'lane': 'R', 'side': 1}),
  'units': ({'age_sec': None,
             'cls': 5,
             'conf': 0.8762717774709268,
             'deploying': None,
             'hp_frac': 1.0,
             'side': -1,
             'x': 0.21891960063993965,
             'y': 0.7277559435218587},
            {'age_sec': None,
             'cls': 3,
             'conf': 0.7186838389326549,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 0,
             'x': 0.4268510635492696,
             'y': 0.6540800105634149},
            {'age_sec': None,
             'cls': 144,
             'conf': 0.5317555051149931,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 0,
             'x': 0.4037629247386971,
             'y': 0.654866906785709},
            {'age_sec': None,
             'cls': 7,
             'conf': 0.8642305533992394,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 0,
             'x': 0.31193936454151994,
             'y': 0.5843956999040945},
            {'age_sec': None,
             'cls': 11,
             'conf': 0.6602399862834551,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 0,
             'x': 0.7277271003089735,
             'y': 0.29830224429398655},
            {'age_sec': None,
             'cls': 68,
             'conf': 0.8033420510553145,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 1,
             'x': 0.15032095143120816,
             'y': 0.43567730827619544},
            {'age_sec': None,
             'cls': 92,
             'conf': 0.6179704722149982,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 1,
             'x': 0.2973105627952885,
             'y': 0.4255939073015058},
            {'age_sec': None,
             'cls': 159,
             'conf': 0.8895413720784351,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 1,
             'x': 0.3508390980407983,
             'y': 0.4330431378330924},
            {'age_sec': None,
             'cls': 120,
             'conf': 0.3723691594576961,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 1,
             'x': 0.3987669403934391,
             'y': 0.4122949582084376},
            {'age_sec': None,
             'cls': 48,
             'conf': 0.9312562795460955,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 0,
             'x': 0.5434841969282533,
             'y': 0.38365125538128225},
            {'age_sec': None,
             'cls': 84,
             'conf': 0.832194182988158,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 1,
             'x': 0.5560233640949449,
             'y': 0.37573165745052967},
            {'age_sec': None,
             'cls': 125,
             'conf': 0.862207457622139,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 1,
             'x': 0.7677725063054303,
             'y': 0.34080643948418804})},
 {'deck': (0, 164, 2, 3, 4, 149, 6, 7),
  'double_elixir': False,
  'my_elixir': 6.37,
  'my_elixir_exact': True,
  'my_hand': (164, 149, 3, 2),
  'my_next': 7,
  'opp_elixir': 3.0,
  'overtime': False,
  'source': 'degraded',
  'spells': (),
  't_sec': 60.0,
  't_source': 'clock',
  'towers': ({'alive': True, 'hp_frac': 1.0, 'kind': 'king', 'lane': None, 'side': 0},
             {'alive': True, 'hp_frac': 0.6553079947575361, 'kind': 'princess', 'lane': 'L', 'side': 0},
             {'alive': True, 'hp_frac': 1.0, 'kind': 'princess', 'lane': 'R', 'side': 0},
             {'alive': True, 'hp_frac': 1.0, 'kind': 'king', 'lane': None, 'side': 1},
             {'alive': True, 'hp_frac': 0.16382699868938402, 'kind': 'princess', 'lane': 'L', 'side': 1},
             {'alive': True, 'hp_frac': 1.0, 'kind': 'princess', 'lane': 'R', 'side': 1}),
  'units': ({'age_sec': None,
             'cls': 5,
             'conf': 0.8800868557563805,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 0,
             'x': 0.24276267580975117,
             'y': 0.7233967713838289},
            {'age_sec': None,
             'cls': 3,
             'conf': 0.826859566084925,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 0,
             'x': 0.4535587543490963,
             'y': 0.6760112382342184},
            {'age_sec': None,
             'cls': 7,
             'conf': 0.4627947363899953,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 0,
             'x': 0.29274893309364347,
             'y': 0.5943085921364608},
            {'age_sec': None,
             'cls': 68,
             'conf': 0.8521352558575177,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 1,
             'x': 0.8101293731377329,
             'y': 0.38915706068398775},
            {'age_sec': None,
             'cls': 11,
             'conf': 0.9519247223371549,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 1,
             'x': 0.7276552704977863,
             'y': 0.3422821074929054})},
 {'deck': (0, 164, 2, 3, 4, 149, 6, 7),
  'double_elixir': False,
  'my_elixir': 6.37,
  'my_elixir_exact': True,
  'my_hand': (164, 149, 3, 2),
  'my_next': 7,
  'opp_elixir': 3.0,
  'overtime': False,
  'source': 'degraded',
  'spells': (),
  't_sec': 60.0,
  't_source': 'clock',
  'towers': ({'alive': True, 'hp_frac': 1.0, 'kind': 'king', 'lane': None, 'side': 0},
             {'alive': True, 'hp_frac': 0.6553079947575361, 'kind': 'princess', 'lane': 'L', 'side': 0},
             {'alive': True, 'hp_frac': 1.0, 'kind': 'princess', 'lane': 'R', 'side': 0},
             {'alive': True, 'hp_frac': 1.0, 'kind': 'king', 'lane': None, 'side': 1},
             {'alive': True, 'hp_frac': 0.16382699868938402, 'kind': 'princess', 'lane': 'L', 'side': 1},
             {'alive': True, 'hp_frac': 1.0, 'kind': 'princess', 'lane': 'R', 'side': 1}),
  'units': ({'age_sec': None,
             'cls': 5,
             'conf': 0.9114874642416753,
             'deploying': None,
             'hp_frac': 1.0,
             'side': -1,
             'x': 0.20915351118520353,
             'y': 0.7129412939210515},
            {'age_sec': None,
             'cls': 3,
             'conf': 0.5360312400460585,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 0,
             'x': 0.45147471118938565,
             'y': 0.6640868663627868},
            {'age_sec': None,
             'cls': 7,
             'conf': 0.8198476680456595,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 0,
             'x': 0.2752978264848431,
             'y': 0.6014181225401284},
            {'age_sec': None,
             'cls': 68,
             'conf': 0.9525516268254066,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 0,
             'x': 0.7860420529811609,
             'y': 0.3807727112761443},
            {'age_sec': None,
             'cls': 11,
             'conf': 0.8925093892538375,
             'deploying': None,
             'hp_frac': 1.0,
             'side': 1,
             'x': 0.6846014368756143,
             'y': 0.32433301568919687})}]


def _damaged_kings(bs: oc.BoardState) -> oc.BoardState:
    """``bs`` with BOTH king towers' true hp_frac damaged (0.42 mine, 0.77 opp) -- see attempt-2 note below."""
    t = list(bs.towers)
    t[0] = replace(t[0], hp_frac=0.42)   # my king (BoardState.towers order: my K,L,R, opp K,L,R -- index 0)
    t[3] = replace(t[3], hp_frac=0.77)   # opp king (index 3)
    assert t[0].kind == "king" and t[3].kind == "king"
    return replace(bs, towers=tuple(t))


# Attempt-2 finding 1 (blind verifier): every board in ``_O5_GOLDEN_SCALARS_OFF`` above has BOTH kings at
# hp_frac 1.0 == KING_HP_LIVE, so that golden alone cannot detect a broken king_hp switch -- a live_view that
# left kings filled to 1.0 even with king_hp=False would still match it. This second golden closes that gap:
# ``_bs(deck)`` (my_elixir=6.37 fractional + exact=True, opp_elixir=3.0 -- both already non-trivial) with
# ``_damaged_kings`` applied (kings 0.42 / 0.77, i.e. != 1.0 == KING_HP_LIVE) and seed 3. Captured the SAME
# way as the first golden, but against the HEAD-4bca159 copy of e1_view.py (single `scalars` field) rather
# than a hand-edited live one: `scratchpad/gauntlet/L67/split/v5_scratch/e1_view_head.py`, first verified
# byte-identical to `git show 4bca159:pipeline/e1_view.py` (``diff`` -> no output) before this was run --
#     bs = _damaged_kings(_bs(deck))
#     v = head.live_view(bs, np.random.default_rng(3), deck, head.Noise(scalars=False))
#     golden = dataclasses.asdict(v)
# where ``head`` is that HEAD file loaded via importlib (not the real, edited pipeline/e1_view.py -- read-only
# on it). Full capture script + raw output logged in O5_split_switch.md Attempt 2. Pasted verbatim below.
_O5_GOLDEN_SCALARS_OFF_DAMAGED_KINGS = {'deck': (0, 164, 2, 3, 4, 149, 6, 7),
 'double_elixir': False,
 'my_elixir': 6.37,
 'my_elixir_exact': True,
 'my_hand': (164, 149, 3, 2),
 'my_next': 7,
 'opp_elixir': 3.0,
 'overtime': False,
 'source': 'degraded',
 'spells': (),
 't_sec': 60.0,
 't_source': 'clock',
 'towers': ({'alive': True, 'hp_frac': 0.42, 'kind': 'king', 'lane': None, 'side': 0},
            {'alive': True, 'hp_frac': 0.6553079947575361, 'kind': 'princess', 'lane': 'L', 'side': 0},
            {'alive': True, 'hp_frac': 1.0, 'kind': 'princess', 'lane': 'R', 'side': 0},
            {'alive': True, 'hp_frac': 0.77, 'kind': 'king', 'lane': None, 'side': 1},
            {'alive': True, 'hp_frac': 0.16382699868938402, 'kind': 'princess', 'lane': 'L', 'side': 1},
            {'alive': True, 'hp_frac': 1.0, 'kind': 'princess', 'lane': 'R', 'side': 1}),
 'units': ({'age_sec': None,
            'cls': 5,
            'conf': 0.5362445843016838,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 0,
            'x': 0.15833059643936767,
            'y': 0.7246295150320813},
           {'age_sec': None,
            'cls': 3,
            'conf': 0.8473420661831892,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 1,
            'x': 0.42281411753757087,
            'y': 0.7186046807028187},
           {'age_sec': None,
            'cls': 7,
            'conf': 0.8510089041920039,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 0,
            'x': 0.2680077533469114,
            'y': 0.6005273570258767},
           {'age_sec': None,
            'cls': 20,
            'conf': 0.9470789615344484,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 0,
            'x': 0.30806141792709135,
            'y': 0.5779616020120619},
           {'age_sec': None,
            'cls': 68,
            'conf': 0.6340150289939948,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 0,
            'x': 0.7716888108008002,
            'y': 0.3890950350179394},
           {'age_sec': None,
            'cls': 11,
            'conf': 0.8168159858086336,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 1,
            'x': 0.724510139804281,
            'y': 0.3219233424897755},
           {'age_sec': None,
            'cls': 68,
            'conf': 0.8576263711290704,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 1,
            'x': 0.1841802888004014,
            'y': 0.4312454576544609},
           {'age_sec': None,
            'cls': 204,
            'conf': 0.6503233283272503,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 1,
            'x': 0.2081893326377417,
            'y': 0.44355673894576936},
           {'age_sec': None,
            'cls': 92,
            'conf': 0.7477747574693904,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 1,
            'x': 0.29234123824417,
            'y': 0.41885396843727857},
           {'age_sec': None,
            'cls': 120,
            'conf': 0.7684624726950458,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 1,
            'x': 0.3479174602916267,
            'y': 0.4071127837320993},
           {'age_sec': None,
            'cls': 48,
            'conf': 0.8325852737922558,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 1,
            'x': 0.528910026210804,
            'y': 0.3602780493419752},
           {'age_sec': None,
            'cls': 84,
            'conf': 0.47760584040746323,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 1,
            'x': 0.6199744097682843,
            'y': 0.3602567973954678},
           {'age_sec': None,
            'cls': 125,
            'conf': 0.831233902524061,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 1,
            'x': 0.7410416870396569,
            'y': 0.3699719914649754},
           {'age_sec': None,
            'cls': 70,
            'conf': 0.8701078561407092,
            'deploying': None,
            'hp_frac': 1.0,
            'side': 1,
            'x': 0.7983373522963173,
            'y': 0.31373808746264337})}


class TestGoldenSplitMatchesPreO5Scalars(unittest.TestCase):
    """b: the split (my_elixir/opp_elixir/king_hp all False) must be bit-identical to the pre-split
    scalars=False golden above, on the same boards/seeds it was captured with."""

    def test_three_switches_off_matches_scalars_off_golden(self):
        deck = _deck()
        boards_seeds = [(_bs(deck), 0), (_bs(deck, extra_enemy=0), 1), (raw_obs_board(deck), 2)]
        noise = Noise(my_elixir=False, opp_elixir=False, king_hp=False)
        for (bs, seed), golden in zip(boards_seeds, _O5_GOLDEN_SCALARS_OFF):
            v = live_view(bs, np.random.default_rng(seed), deck, noise)
            self.assertEqual(dataclasses.asdict(v), golden, seed)

    def test_damaged_kings_matches_scalars_off_golden(self):
        """The discriminating case attempt-2 asked for: kings != 1.0, so this golden WOULD fail if king_hp
        silently kept filling 1.0 (or any other king_hp regression) -- unlike the three boards above."""
        deck = _deck()
        bs = _damaged_kings(_bs(deck))
        noise = Noise(my_elixir=False, opp_elixir=False, king_hp=False)
        v = live_view(bs, np.random.default_rng(3), deck, noise)
        self.assertEqual(dataclasses.asdict(v), _O5_GOLDEN_SCALARS_OFF_DAMAGED_KINGS)


# ------------------------------------------------------------------------------------------------------
# item 4: all switches off == the clean path (--obs clean), tokens/scalars
# ------------------------------------------------------------------------------------------------------
class TestAllOffMatchesClean(unittest.TestCase):
    def test_tokens_and_scalars_match_clean(self):
        deck = _deck()
        bs = _bs(deck)
        for seed in range(10):
            v = live_view(bs, np.random.default_rng(seed), deck, ALL_NOISE_OFF)
            tok_v, mask_v, sc_v = oc.to_tokens(v, 64)
            tok_c, mask_c, sc_c = oc.to_tokens(bs, 64)
            self.assertTrue(np.array_equal(tok_v, tok_c), seed)
            self.assertTrue(np.array_equal(mask_v, mask_c), seed)
            self.assertTrue(np.array_equal(sc_v, sc_c), seed)
        # documented, intentional difference: metadata not read by to_tokens (module docstring / Noise docstring)
        v = live_view(bs, np.random.default_rng(0), deck, ALL_NOISE_OFF)
        self.assertEqual(v.source, "degraded")
        self.assertEqual(bs.source, "engine")
        self.assertEqual(v.t_source, "clock")
        self.assertEqual(bs.t_source, "tick")

    def test_deploying_off_keeps_true_value_even_though_compact_rows_are_none(self):
        deck = _deck()
        base = _bs(deck)
        bs = replace(base, units=(replace(base.units[0], deploying=True),) + base.units[1:])
        v = live_view(bs, np.random.default_rng(0), deck, ALL_NOISE_OFF)
        self.assertTrue(v.units[0].deploying)          # kept true, not dropped to None
        v_on = live_view(bs, np.random.default_rng(0), deck)     # default: deploying dropped
        self.assertIsNone(v_on.units[0].deploying)


# ------------------------------------------------------------------------------------------------------
# item 3: RNG stability -- one component off changes only its own effect
# ------------------------------------------------------------------------------------------------------
class TestRngStability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deck = _deck()
        cls.bs = _bs(cls.deck)          # 3 mine + 3 real enemy + 6 extra unmapped-class enemy = enough units
        # a unit with true deploying=True and non-trivial hp, to make unit_hp/deploying assertions non-trivial
        cls.bs = replace(cls.bs, units=(replace(cls.bs.units[0], deploying=True),) + cls.bs.units[1:])

    def test_field_only_components_do_not_change_which_units_or_fps_appear(self):
        """position / team / conf / unit_hp / my_elixir / opp_elixir / king_hp / deploying never gate
        degrade()'s control flow: with one of them off, the SAME units (by class, in the SAME order) are
        kept and the SAME false positives are added, for every seed -- only that switch's own field(s) may
        differ."""
        field_only = ("position", "team", "conf", "unit_hp", "my_elixir", "opp_elixir", "king_hp", "deploying")
        counts_seen = set()
        for seed in range(60):
            d0 = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise())
            counts_seen.add(len(d0.units))
            for name in field_only:
                d1 = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise(**{name: False}))
                self.assertEqual([u.cls for u in d0.units], [u.cls for u in d1.units], (name, seed))
                self.assertEqual(len(d0.units), len(d1.units), (name, seed))
        self.assertGreater(len(counts_seen), 1, "recall/false_pos never varied the unit count over 60 seeds")

    def test_position_off_only_changes_xy(self):
        for seed in range(30):
            d0 = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise())
            d1 = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise(position=False))
            for u0, u1 in zip(d0.units, d1.units):
                self.assertEqual((u0.cls, u0.side, u0.hp_frac, u0.deploying, u0.conf),
                                 (u1.cls, u1.side, u1.hp_frac, u1.deploying, u1.conf), seed)

    def test_team_off_keeps_true_side_and_no_other_field_changes(self):
        for seed in range(30):
            d0 = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise())
            d1 = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise(team=False))
            for u0, u1 in zip(d0.units, d1.units):
                self.assertEqual((u0.cls, u0.x, u0.y, u0.hp_frac, u0.deploying, u0.conf),
                                 (u1.cls, u1.x, u1.y, u1.hp_frac, u1.deploying, u1.conf), seed)
                self.assertIn(u1.side, (0, 1))          # never -1: no unknown-team roll applied

    def test_conf_off_keeps_true_conf(self):
        for seed in range(30):
            d0 = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise())
            d1 = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise(conf=False))
            for u0, u1 in zip(d0.units, d1.units):
                self.assertEqual((u0.cls, u0.x, u0.y, u0.side, u0.hp_frac, u0.deploying),
                                 (u1.cls, u1.x, u1.y, u1.side, u1.hp_frac, u1.deploying), seed)
                self.assertEqual(u1.conf, 1.0)          # engine truth conf, never redrawn

    @patch("pipeline.e1_view.DEGRADE_RECALL", 1.0)
    @patch("pipeline.e1_view.DEGRADE_PRECISION", 1.0)
    def test_field_components_reduce_to_true_engine_values(self):
        """With drop/false-positive both forced off (patched, obs_contract.py untouched), each field-only
        switch off reproduces the exact engine truth for that field, unit for unit."""
        d = e1_view._degrade_switchable(self.bs, np.random.default_rng(0), Noise(position=False))
        for u, src in zip(d.units, self.bs.units):
            self.assertEqual((u.x, u.y), (src.x, src.y))
        d = e1_view._degrade_switchable(self.bs, np.random.default_rng(0), Noise(team=False))
        for u, src in zip(d.units, self.bs.units):
            self.assertEqual(u.side, src.side)
        d = e1_view._degrade_switchable(self.bs, np.random.default_rng(0), Noise(conf=False))
        for u, src in zip(d.units, self.bs.units):
            self.assertEqual(u.conf, src.conf)
        d = e1_view._degrade_switchable(self.bs, np.random.default_rng(0), Noise(unit_hp=False))
        for u, src in zip(d.units, self.bs.units):
            self.assertEqual(u.hp_frac, src.hp_frac)
        d = e1_view._degrade_switchable(self.bs, np.random.default_rng(0), Noise(deploying=False))
        for u, src in zip(d.units, self.bs.units):
            self.assertEqual(u.deploying, src.deploying)
        d = e1_view._degrade_switchable(self.bs, np.random.default_rng(0), Noise(my_elixir=False))
        self.assertEqual(d.my_elixir, self.bs.my_elixir)
        self.assertTrue(d.my_elixir_exact)
        d = e1_view._degrade_switchable(self.bs, np.random.default_rng(0), Noise(opp_elixir=False))
        self.assertEqual(d.opp_elixir, self.bs.opp_elixir)
        d = e1_view._degrade_switchable(self.bs, np.random.default_rng(0), Noise(king_hp=False))
        for t, src in zip(d.towers, self.bs.towers):
            if t.kind == "king" and t.alive:
                self.assertEqual(t.hp_frac, src.hp_frac)

    @patch("pipeline.e1_view.DEGRADE_PRECISION", 1.0)
    def test_recall_off_drops_nothing_and_keeps_the_kept_units_untouched(self):
        """precision patched to 1.0 (fp_rate 0, obs_contract.py untouched) isolates recall: OFF must equal
        the full board every time, and every unit degrade() itself would have kept is bit-identical to the
        default run (no extra draws are spent noising the rescued ones)."""
        n_units = len(self.bs.units)
        drops_seen = kept_seen = 0
        for seed in range(80):
            d_on = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise())
            d_off = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise(recall=False))
            self.assertEqual(len(d_off.units), n_units, seed)          # nothing ever dropped
            if len(d_on.units) < n_units:
                drops_seen += 1
            else:
                kept_seen += 1
                self.assertEqual(d_on.units, d_off.units, seed)        # nothing was rescued -> identical
        self.assertGreater(drops_seen, 0, "DEGRADE_RECALL=0.855 never dropped a unit over 80 seeds")
        self.assertGreater(kept_seen, 0)

    @patch("pipeline.e1_view.DEGRADE_RECALL", 1.0)
    def test_false_pos_off_adds_nothing_and_keeps_the_real_units_untouched(self):
        """recall patched to 1.0 (nothing dropped, obs_contract.py untouched) isolates false_pos: OFF must
        equal exactly the real units every time, and match the default run's real units field for field."""
        n_units = len(self.bs.units)
        fp_seen = clean_seen = 0
        for seed in range(80):
            d_on = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise())
            d_off = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise(false_pos=False))
            self.assertEqual(len(d_off.units), n_units, seed)          # never a false positive
            self.assertTrue(_is_subsequence(d_off.units, d_on.units), seed)  # the real units, untouched,
            # in order -- NOT a fixed prefix, since an earlier false positive shifts later ones' index
            if len(d_on.units) > n_units:
                fp_seen += 1
            else:
                clean_seen += 1
        self.assertGreater(fp_seen, 0, "DEGRADE_PRECISION=0.886 never added a false positive over 80 seeds")
        self.assertGreater(clean_seen, 0)


# ------------------------------------------------------------------------------------------------------
# O5 split: my_elixir / opp_elixir / king_hp are three independent switches (formerly one `scalars` field).
# c: each switch alone must change ONLY its own field(s) -- the other two scalar targets, and units/spells
# (the RNG-consuming path), stay byte-identical to Noise() (default, all on).
# ------------------------------------------------------------------------------------------------------
class TestThreeSwitchesIsolated(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deck = _deck()
        base = _bs(cls.deck)          # my_elixir=6.37 (fractional) and opp_elixir=3.0 are already non-trivial
        towers = list(base.towers)    # for the my_elixir/opp_elixir checks below; kings start at hp_frac 1.0,
        towers[0] = replace(towers[0], hp_frac=0.42)   # so damage them (my K, index 0) so king_hp=False is a
        towers[3] = replace(towers[3], hp_frac=0.77)   # real, non-trivial difference too (opp K, index 3)
        cls.bs = replace(base, towers=tuple(towers))

    def test_my_elixir_off_changes_only_my_elixir(self):
        for seed in range(10):
            r0 = np.random.default_rng(seed)
            v0 = live_view(self.bs, r0, self.deck, Noise())
            s0 = r0.bit_generator.state                                  # reference: the all-on draw sequence
            r1 = np.random.default_rng(seed)
            v1 = live_view(self.bs, r1, self.deck, Noise(my_elixir=False))
            self.assertEqual(r1.bit_generator.state, s0, seed)           # my_elixir=False draws nothing extra
            self.assertEqual(v0.my_elixir, 6.0, seed)                    # default: floored
            self.assertEqual(v1.my_elixir, self.bs.my_elixir, seed)      # off: exact, unfloored
            self.assertFalse(v0.my_elixir_exact, seed)
            self.assertTrue(v1.my_elixir_exact, seed)
            self.assertEqual(v0.opp_elixir, v1.opp_elixir, seed)         # unchanged
            self.assertEqual(v0.towers, v1.towers, seed)                 # unchanged, king_hp included
            self.assertEqual(v0.units, v1.units, seed)                   # RNG path untouched
            self.assertEqual(v0.spells, v1.spells, seed)

    def test_opp_elixir_off_changes_only_opp_elixir(self):
        for seed in range(10):
            r0 = np.random.default_rng(seed)
            v0 = live_view(self.bs, r0, self.deck, Noise())
            s0 = r0.bit_generator.state                                  # reference: the all-on draw sequence
            r1 = np.random.default_rng(seed)
            v1 = live_view(self.bs, r1, self.deck, Noise(opp_elixir=False))
            self.assertEqual(r1.bit_generator.state, s0, seed)           # opp_elixir=False draws nothing extra
            self.assertIsNone(v0.opp_elixir, seed)                       # default: dropped
            self.assertEqual(v1.opp_elixir, self.bs.opp_elixir, seed)    # off: true value kept
            self.assertEqual(v0.my_elixir, v1.my_elixir, seed)           # unchanged
            self.assertEqual(v0.my_elixir_exact, v1.my_elixir_exact, seed)
            self.assertEqual(v0.towers, v1.towers, seed)                 # unchanged, king_hp included
            self.assertEqual(v0.units, v1.units, seed)                   # RNG path untouched
            self.assertEqual(v0.spells, v1.spells, seed)

    def test_king_hp_off_changes_only_king_towers(self):
        for seed in range(10):
            r0 = np.random.default_rng(seed)
            v0 = live_view(self.bs, r0, self.deck, Noise())
            s0 = r0.bit_generator.state                                  # reference: the all-on draw sequence
            r1 = np.random.default_rng(seed)
            v1 = live_view(self.bs, r1, self.deck, Noise(king_hp=False))
            self.assertEqual(r1.bit_generator.state, s0, seed)           # king_hp=False draws nothing extra
            self.assertEqual(v0.my_elixir, v1.my_elixir, seed)           # unchanged
            self.assertEqual(v0.my_elixir_exact, v1.my_elixir_exact, seed)
            self.assertEqual(v0.opp_elixir, v1.opp_elixir, seed)         # unchanged
            for t0, t1, src in zip(v0.towers, v1.towers, self.bs.towers):
                if t1.kind == "king" and t1.alive:
                    self.assertEqual(t0.hp_frac, KING_HP_LIVE, seed)     # default: filled to 1.0
                    self.assertEqual(t1.hp_frac, src.hp_frac, seed)      # off: true (damaged) hp kept
                    self.assertNotEqual(t0.hp_frac, t1.hp_frac, seed)    # a real, non-trivial difference
                else:
                    self.assertEqual(t0, t1, seed)                       # princess towers: untouched either way
            self.assertEqual(v0.units, v1.units, seed)                   # RNG path untouched
            self.assertEqual(v0.spells, v1.spells, seed)


# ------------------------------------------------------------------------------------------------------
# O1 repair: recall=False must NOISE the rescued units (position/team/hp/deploying/conf), not append them
# clean -- an independent "side" RNG stream carries that noise so the main stream is untouched either way.
# ------------------------------------------------------------------------------------------------------
class TestRecallRescueNoise(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deck = _deck()
        cls.bs = _bs(cls.deck, extra_enemy=0)      # 5 units, each a UNIQUE class -> unambiguous cls lookup

    def test_side_rng_creation_does_not_advance_main_rng(self):
        """``Generator(rng.bit_generator.jumped()).random()`` must not change what ``rng`` draws next."""
        rng = np.random.default_rng(123)
        before = [rng.random() for _ in range(4)]
        _side = np.random.Generator(rng.bit_generator.jumped())
        _ = _side.random(3)                                     # drawing from the side stream too: still inert
        after = [rng.random() for _ in range(4)]
        ref = np.random.default_rng(123)
        expected = [ref.random() for _ in range(8)]
        self.assertEqual(before + after, expected)

    @patch("pipeline.e1_view.DEGRADE_PRECISION", 1.0)   # isolate recall: no FPs, so d_on is a clean subsequence
    def test_kept_units_identical_to_default_rescued_units_are_extra(self):
        """recall=False's KEPT units (i.e. everything degrade() itself would also have kept) are bit-identical
        to the default path's, in the same order -- rescued units are additional entries, never replacements."""
        for seed in range(60):
            d_on = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise())
            d_off = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise(recall=False))
            self.assertEqual(len(d_off.units), len(self.bs.units), seed)     # recall off drops nothing
            self.assertTrue(_is_subsequence(d_on.units, d_off.units), seed)

    @patch("pipeline.e1_view.DEGRADE_PRECISION", 1.0)
    def test_rescued_units_are_noised_like_kept_ones(self):
        by_cls = {u.cls: u for u in self.bs.units}
        dxdy: list[float] = []
        unknown_side = total = 0
        for seed in range(300):
            d_on = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise())
            d_off = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise(recall=False))
            rescued = _extra_after_subsequence(d_on.units, d_off.units)
            for u in rescued:
                total += 1
                self.assertIsNone(u.hp_frac, seed)          # dropped like a kept unit (unit_hp default ON)
                src = by_cls[u.cls]
                dxdy.append(abs(u.x - src.x) + abs(u.y - src.y))
                unknown_side += int(u.side == -1)
        self.assertGreater(total, 20, "DEGRADE_RECALL=0.855 never dropped a unit worth rescuing over 300 seeds")
        self.assertGreater(float(np.mean(dxdy)), 0.01, "rescued units carry no position noise")
        self.assertAlmostEqual(unknown_side / total, UNKNOWN_TEAM_RATE, delta=0.15)   # loose: small-n binomial

    @patch("pipeline.e1_view.DEGRADE_PRECISION", 1.0)
    def test_hp_none_before_fill_1_0_after_live_view(self):
        for seed in range(60):
            d_on = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise())
            d_off = e1_view._degrade_switchable(self.bs, np.random.default_rng(seed), Noise(recall=False))
            if not _extra_after_subsequence(d_on.units, d_off.units):
                continue
            v = live_view(self.bs, np.random.default_rng(seed), self.deck, Noise(recall=False))
            self.assertTrue(all(u.hp_frac == 1.0 for u in v.units), seed)   # live fill still applies
            break
        else:
            self.fail("no seed in range(60) rescued a unit -- test is vacuous")

    def test_deterministic_for_a_fixed_seed(self):
        d1 = e1_view._degrade_switchable(self.bs, np.random.default_rng(7), Noise(recall=False))
        d2 = e1_view._degrade_switchable(self.bs, np.random.default_rng(7), Noise(recall=False))
        self.assertEqual(d1, d2)
        v1 = live_view(self.bs, np.random.default_rng(7), self.deck, Noise(recall=False))
        v2 = live_view(self.bs, np.random.default_rng(7), self.deck, Noise(recall=False))
        self.assertEqual(v1, v2)


# ------------------------------------------------------------------------------------------------------
# CLI: --noise-off
# ------------------------------------------------------------------------------------------------------
class TestNoiseOffCli(unittest.TestCase):
    def test_names_match_the_dataclass(self):
        self.assertEqual(set(e1_eval.NOISE_NAMES), set(NOISE_FIELDS))

    def test_default_is_all_on(self):
        n = e1_eval.parse_noise_off("")
        self.assertEqual(n, Noise())
        self.assertEqual(e1_eval.noise_off_names(n), [])

    def test_single_and_multiple_names(self):
        n = e1_eval.parse_noise_off("unit_hp")
        self.assertEqual(n, Noise(unit_hp=False))
        n = e1_eval.parse_noise_off("recall, team , conf")
        self.assertEqual(n, Noise(recall=False, team=False, conf=False))
        self.assertEqual(e1_eval.noise_off_names(n), ["conf", "recall", "team"])

    def test_all_names_off_equals_all_noise_off_constant(self):
        n = e1_eval.parse_noise_off(",".join(NOISE_FIELDS))
        self.assertEqual(n, ALL_NOISE_OFF)

    def test_unknown_name_rejected(self):
        with self.assertRaises(SystemExit):
            e1_eval.parse_noise_off("bogus")
        with self.assertRaises(SystemExit):
            e1_eval.parse_noise_off("recall,not_a_component")

    # -- O5: 'scalars' is kept as an alias for the three fields it split into -----------------------------
    def test_scalars_alias_expands_to_the_three_split_fields(self):
        n = e1_eval.parse_noise_off("scalars")
        self.assertEqual(n, Noise(my_elixir=False, opp_elixir=False, king_hp=False))
        self.assertEqual(e1_eval.noise_off_names(n), ["king_hp", "my_elixir", "opp_elixir"])

    def test_scalars_alias_combines_with_a_plain_name(self):
        n = e1_eval.parse_noise_off("scalars,recall")
        self.assertEqual(n, Noise(my_elixir=False, opp_elixir=False, king_hp=False, recall=False))
        self.assertEqual(e1_eval.noise_off_names(n), ["king_hp", "my_elixir", "opp_elixir", "recall"])

    def test_scalars_alias_still_rejects_an_unknown_name_alongside_it(self):
        with self.assertRaises(SystemExit):
            e1_eval.parse_noise_off("scalars,bogus")

    def test_argparse_wires_the_flag(self):
        a = e1_eval.build_parser().parse_args(["--port", "1", "--out", "x"])
        self.assertEqual(a.noise_off, "")
        a = e1_eval.build_parser().parse_args(["--port", "1", "--out", "x", "--noise-off", "recall,position"])
        self.assertEqual(a.noise_off, "recall,position")
        self.assertEqual(e1_eval.parse_noise_off(a.noise_off), Noise(recall=False, position=False))

    def test_obs_clean_path_never_calls_live_view(self):
        """--obs clean's branch is `bs` unmodified regardless of --noise-off (module docstring of e1_eval /
        EXPECTED OUTCOME item 5): verified structurally, since clean never reaches live_view. The branch lives in
        Match.prepare since L68 (run_match became a Match loop)."""
        import inspect
        src = inspect.getsource(e1_eval.Match.prepare)
        self.assertIn('live_view(bs, self.rng_obs, self.deck, cfg["noise"]) if cfg["obs"] == "live" else bs', src)


if __name__ == "__main__":
    unittest.main()
