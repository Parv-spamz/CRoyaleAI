"""L67ac X1 (HANDOFF 5cs.99 AH): the live X-Bow assists no longer push a pro-depth X-Bow to the bridge.

run15: the model put X-Bows at board y 0.604 -- the pro row (pro median 0.609) -- and play.py's xbow_offense_depth_cell
moved 16 of 17 forward to board y 0.521, because it called a bow defensive only at FRAME y >= env.xbow_defense_front
0.52 and the pro row sits at frame 0.503. The live assists now use play.xbow_forward_board_y (0.58, the depth past which
pros place 6.5% of X-Bows) converted to frame y through the board warp.
"""
from __future__ import annotations

import ast
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from clashrl.actions import ActionSpace                                   # noqa: E402
from clashrl.config import Config                                         # noqa: E402
from clashrl.reward import xbow_lock_cell, xbow_offense_depth_cell         # noqa: E402

PLAY = os.path.join(os.path.dirname(__file__), "..", "src", "clashrl", "play.py")

# O22 attempt 2: this test used to assertIn() the three assist calls' exact source TEXT. O22
# legitimately added a 6th argument (enemy_alive=...) to the xbow_lock_cell call to fix the
# dead-lane defect, and that literal pin broke even though the live cut was still passed --
# the test was asserting the frozen spelling of a call, not the behaviour it exists to protect.
# Walk the AST instead and check, by argument NAME, that each assist still receives the live
# cut: this survives a reorder, an added kwarg, or any other cosmetic signature change, and
# only fails if the live cut is actually dropped or the stale global default reappears.
def _assist_calls(src, names):
    """{function name -> [ast.Call, ...]} for every call to one of `names` in play.py."""
    tree = ast.parse(src, filename=PLAY)
    found = {n: [] for n in names}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in names:
            found[node.func.id].append(node)
    return found


def _arg_names(call):
    """The bare-Name arguments (positional + keyword) of a Call -- these assist calls only ever
    pass local variables, never literals or expressions, so this is a complete enough view."""
    names = [a.id for a in call.args if isinstance(a, ast.Name)]
    names += [kw.value.id for kw in call.keywords if isinstance(kw.value, ast.Name)]
    return names


class XbowLiveDepth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = Config.load()
        cls.acts = ActionSpace(cls.cfg)
        cls.W = int(cls.cfg.get("action", "grid")[0])
        cls.deploy_top = float(cls.cfg.get("action", "deploy_top", default=0.44))
        cls.old = float(cls.cfg.get("env", "xbow_defense_front", default=0.52))
        cls.new = float(cls.acts.warp.board_to_frame(0.5, float(cls.cfg.get("play", "xbow_forward_board_y", default=0.58)))[1])

    def _frame_of(self, bx, by):
        c = self.acts.cell_at(*self.acts.warp.board_to_frame(bx, by))
        return self.acts.cell_center(c % self.W, c // self.W)

    def test_the_new_cut_sits_between_the_pro_row_and_the_row_ahead_of_it(self):
        _, pro_y = self._frame_of(0.861, 0.604)
        _, fwd_y = self._frame_of(0.861, 0.521)
        self.assertGreaterEqual(pro_y, self.new, "the pro X-Bow row must count as defensive")
        self.assertLess(fwd_y, self.new, "the bridge row must still count as forward")

    def test_old_cut_pushed_the_pro_row_forward_and_the_new_cut_leaves_it(self):
        for bx in (0.861, 0.139):                                         # both edge placements of run15
            cx, cy = self._frame_of(bx, 0.604)
            self.assertIsNotNone(xbow_offense_depth_cell(cx, cy, self.old, self.deploy_top, self.acts),
                                 "precondition: the old 0.52 cut moved the pro-depth X-Bow")
            self.assertIsNone(xbow_offense_depth_cell(cx, cy, self.new, self.deploy_top, self.acts))
            self.assertIsNone(xbow_lock_cell(cx, cy, [[0.25, 0.2], [0.75, 0.2]], 0.36, self.new, self.acts))

    def test_play_passes_the_live_cut_to_all_three_assists(self):
        """Intent: play.py's three X-Bow assists (lane, lock, depth) all key off the LIVE
        defence cut (xbow_live_defense_y), never the stale global default
        (env.xbow_defense_front) -- see AST-walking helpers above for why this is no longer a
        literal-text match."""
        with open(PLAY, encoding="utf-8") as fh:
            src = fh.read()
        names = ("xbow_target_lane_cell", "xbow_lock_cell", "xbow_offense_depth_cell")
        calls = _assist_calls(src, names)
        for name in names:
            self.assertTrue(calls[name], f"no call to {name}(...) found in play.py")
            for call in calls[name]:
                args = _arg_names(call)
                self.assertIn("xbow_live_defense_y", args,
                             f"play.py:{call.lineno} {name}(...) does not pass the live defence cut")
                self.assertNotIn("xbow_defense_front", args,
                                 f"play.py:{call.lineno} {name}(...) uses the stale global cut")


if __name__ == "__main__":
    unittest.main()
