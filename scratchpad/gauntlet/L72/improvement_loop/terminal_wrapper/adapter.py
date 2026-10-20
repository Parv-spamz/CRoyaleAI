"""Opt-in experiment adapter for the pinned native tiebreak contract."""
from pipeline.e1_eval import SelfPlayMatch
from pipeline.royale_runtime import activate

def frozen(st):
    return (not st.game_over and st.overtime
            and st.tick >= st.regular_ticks + st.overtime_ticks)

class TerminalAwareMatch(SelfPlayMatch):
    def __init__(self, *args, stop_decisions_at_fulltime=False, **kwargs):
        if type(stop_decisions_at_fulltime) is not bool:
            raise TypeError('stop_decisions_at_fulltime must be bool')
        if stop_decisions_at_fulltime:
            activate()  # Pins the reviewed ClientHpDrain source/runtime contract.
        self.stop_decisions_at_fulltime = stop_decisions_at_fulltime
        self.terminal_decision_suppression_tick = None
        super().__init__(*args, **kwargs)

    def due(self):
        if not self.stop_decisions_at_fulltime:
            return super().due()
        while True:
            sides = super().due()
            if not sides or not frozen(self.env.core.state()):
                return sides
            self.terminal_decision_suppression_tick = int(self.env.tick)
            # Existing due() still lands already committed plays and drains the
            # engine. This changes future decision requests, never game outcome.
            for side in self.sides:
                side.next_tick = self.env.tail_cap + 1
