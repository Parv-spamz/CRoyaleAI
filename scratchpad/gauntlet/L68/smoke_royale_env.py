"""L68 smoke check for pipeline/royale_env.py. Asserts the facts the adapter assumes, then plays ghost-only matches.

    research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L68/smoke_royale_env.py
"""
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from royalegym.protocol import DeployCommand, DeployStatus, EntityKind, MatchSetup, ShuffleMode  # noqa: E402
from royalegym.rust_engine import RustEngine  # noqa: E402

from pipeline.e1_pool import load_pool_v1, select_split  # noqa: E402
from pipeline.obs_contract import from_engine, load_deck  # noqa: E402
from pipeline.royale_env import RoyalePoolEnv, UnsupportedDeck  # noqa: E402

core = RustEngine()
ids = {c.name: c.card_id for c in core.cards()}
deck = [ids[n] for n in ("Knight", "Skeletons", "Log", "IceWizard", "Xbow", "Rocket", "Tesla", "Arrows")]
core.reset(0, MatchSetup(decks=[deck, deck], shuffle=ShuffleMode.NONE))
st = core.state()
facts = {}
# 1. Blue (team 0) king sits at LOW y, like the pool's side 0
kings = {e.team: e.y for e in st.entities if e.kind == EntityKind.KING_TOWER}
facts["blue_king_y"], facts["red_king_y"] = kings[0], kings[1]
assert kings[0] < kings[1], kings
# 2. ShuffleMode.NONE: hand is the deck's first four, next is the fifth
facts["hand_is_first4"] = st.players[0].hand == deck[:4] and st.players[0].next_card == deck[4]
facts["start_tick"], facts["start_elixir"] = st.tick, st.players[0].elixir_milli / 1000
# 3. the start countdown: the real engine refuses every deploy before tick 90. Skeletons (slot 1) at tile (9, 10).
for t in (89, 90):
    core.reset(0, MatchSetup(decks=[deck, deck], shuffle=ShuffleMode.NONE))
    core.step([], t)
    try:   # RoyaleSim f046df9 refuses with TOO_EARLY, which RoyaleGym 60529df's status map lacks -> RuntimeError
        (r,) = core.step([DeployCommand(0, 1, 9 * 18000, 10 * 18000)], 0)
        facts[f"deploy_at_tick_{t}"] = DeployStatus(r.status).name
    except RuntimeError as exc:
        facts[f"deploy_at_tick_{t}"] = f"raised: {exc}"
facts["tick_after_zero_step"] = core.state().tick
facts["overtime_ticks"] = core.state().overtime_ticks
print(json.dumps(facts))

# 4. ghost-only matches on held-out entries (policy never plays): coverage + wall time per match
env = RoyalePoolEnv(subs={"Tornado": "Arrows"})
dk = load_deck("icebow")
n_ok = n_skip = 0
t0 = time.perf_counter()
for e in select_split(load_pool_v1(), "heldout")[:20]:
    try:
        state = env.reset(e)
    except UnsupportedDeck as u:
        n_skip += 1
        continue
    from_engine(state, env.side, dk, unmapped=set())          # the adapter's dict must parse
    while not env.terminated and env.tick < env.tail_cap:
        env._advance_to(min(env.tick + 10, env.tail_cap))
    n_ok += 1
    print(e["tag"], "end", env.tick, env.episode, "ghost ok/ref", env.ghost_ok, env.ghost_rejected,
          env.ghost_reject_reasons)
dt = time.perf_counter() - t0
print(json.dumps({"played": n_ok, "skipped_unsupported": n_skip, "s_per_match": round(dt / max(n_ok, 1), 3)}))
