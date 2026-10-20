"""No sockets or engine: deterministic observation/command fixture for driver tests."""
from copy import deepcopy
from unittest.mock import patch

from research.sandbox_tools import replay_drive as rd


class MockEnv:
    def __init__(self, entities=None, codes=(), terminal_tick=None):
        self.entities = entities or (lambda tick: [])
        self.codes = iter(codes)
        self.terminal_tick = terminal_tick
        self.calls = []
        self.observed = []
        self.tick = 0
        self.last_episode = {}

    def reset(self, replay, warmup_steps=0):
        self.tick = 0
        self.last_episode = {"terminated": False, "crowns": [0, 0], "winner": None,
                             "crown_towers": [{"side": s, "x": 9000, "y": y, "hp": 100, "max_hp": 100}
                                              for s, y in ((0, 1000), (1, 31000))]}
        return self.observe()

    def observe(self):
        self.observed.append(self.tick)
        return {"tick": self.tick, "episode": deepcopy(self.last_episode), "state_hash": "mock",
                "entities": deepcopy(self.entities(self.tick)),
                "players": [{"side": s, "hand_deck_indices": [0, 1, 2, 3],
                             "cycle_deck_indices": [4, 5, 6, 7], "next_deck_index": 4,
                             "hand": [{"name": "Knight"}], "elixir": 10, "elixir_exact": 10}
                            for s in (0, 1)]}

    observe_compact = observe

    def step(self, n):
        self.tick += n
        if self.terminal_tick is not None and self.tick >= self.terminal_tick:
            self.last_episode["terminated"] = True
        return {"tick_after": self.tick, "stepped": n, "episode": deepcopy(self.last_episode)}

    def act(self, **kwargs):
        self.calls.append((self.tick, "play", kwargs))
        return {"accepted": True, "result_code": 0, "tick": self.tick,
                "hand_index": 0, "placement_valid": True, "placement_reason": None}

    def use_ability(self, **kwargs):
        self.calls.append((self.tick, "ability", kwargs))
        code = next(self.codes, 0)
        return {"accepted": code == 0, "result_code": code, "tick": self.tick}

    def close(self):
        pass


def run_mock(battle, events, env=None, **kwargs):
    env = env or MockEnv()
    with patch.object(rd, "NativeRoyaleEnv", return_value=env), \
         patch.object(rd, "load_battle", return_value=(deepcopy(battle), deepcopy(events))), \
         patch.object(rd, "infer_deals", side_effect=lambda seq, ids: [(tuple(ids[:4]), tuple(ids[4:]))]):
        result = rd.drive("mock", port=0, seed=424242, level=11, elixir_slack=2,
                          tail_cap=max(e["tick"] for e in events), run_label="test", verbose=False, **kwargs)
    return result, env
