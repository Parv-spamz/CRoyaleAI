"""Shared machinery for the R2 pre-flight tools (reward_plan.md §3): play icebow (gen_v1_s0, search_s0's plain live
condition: noise off, opp-elixir counter, delay 26, extrapolate 26, tau 0.35) under a scripted POLICY vs the frozen
gen_v1 opponent (tau 0.27) on seeded census decks (search_s0's deck rule and redraw), recording at every one of OUR
decisions the crown-tower state + the engine's crowns, so the potentials can be recomputed for any weights / gamma.

Policies (our side only; the opponent is always the plain frozen gen_v1):
    il                 search_s0's plain arm (live rule, tau 0.35)
    never              never plays (stall rule included)
    spend_immediately  cheapest affordable card (lowest slot on ties) at the moment it is affordable, at --fixed-cell
    hold_to_9          plays only at >= 9 elixir: then the policy's top affordable card at its top cell, gate ignored
    spam_one_card      only --spam-card, whenever affordable, at the policy's top cell for it
    never_buildings    the IL rule with BUILDING cards masked out of the afford mask (RoyaleSim card_kind)
    never_spells       the IL rule with SPELL cards masked out
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
for _p in (REPO, REPO / "icebow" / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from pipeline import e1_eval as E                 # noqa: E402
from pipeline import reward_shaping as RS         # noqa: E402
from pipeline import search_s0 as S               # noqa: E402

POLICIES = ("il", "never", "spend_immediately", "hold_to_9", "spam_one_card", "never_buildings", "never_spells")
FIXED_CELL = 50 * 36 + 17        # board (0.486, 0.789): centre, between our princess towers, in front of the king
SPAM_CARD = "knight"


def wait(why: str) -> dict:
    return {"play": False, "slot": -1, "cell": -1, "why": why}


def snap(env) -> dict:
    """The part of raw() the potentials read, plus the engine's own crowns (raw() has none)."""
    raw, st = env.raw(), env.core.state()
    return {"tick": int(raw["tick"]), "episode": {"crown_towers": raw["episode"]["crown_towers"]},
            "crowns": [int(st.players[0].crowns), int(st.players[1].crowns)]}


class ShapeRunner(S.Runner):
    """search_s0.Runner (setup, models, live cfg) with our side's decision replaced per scripted policy and every
    decision's state recorded."""

    fixed_cell, spam_card = FIXED_CELL, SPAM_CARD

    def slot_kinds(self, s) -> list[str]:
        """RoyaleSim card_kind name (TROOP / BUILDING / SPELL) of each deck slot of side ``s``."""
        cat = {c.card_id: str(getattr(c.card_kind, "name", c.card_kind)) for c in s.env.core.cards()}
        return [cat[s.env.deck_ids[s.side][s.deck_index_of_slot[k]]] for k in range(E.N_SLOTS)]

    def decide(self, policy: str, s, p, enc, heads, hand) -> dict:
        from pipeline.e1_eval import live_decide_batch
        el, allowed, stalled = s.pre(hand)
        if policy in ("never_buildings", "never_spells"):
            kind = "BUILDING" if policy == "never_buildings" else "SPELL"
            allowed = allowed & np.array([k != kind for k in self.slot_kinds(s)])
        live = live_decide_batch(s.model, enc, heads, [p], allowed[None], np.array([stalled]), tau=s.cfg["tau"],
                                 device=s.cfg["device"])[0]
        if policy in ("il", "never_buildings", "never_spells"):
            return live
        if policy == "never":
            return wait("never")
        if not allowed.any():
            return wait("no_affordable")
        if policy == "spend_immediately":
            slot = min(np.flatnonzero(allowed), key=lambda k: (s.costs[k], k))
            return {"play": True, "slot": int(slot), "cell": int(self.fixed_cell), "why": "spend_immediately"}
        if policy == "hold_to_9":
            if el < 9:
                return wait("hold")
            return {**S.shortlist(s.model, enc, heads, allowed, 1, 1)[0], "why": "hold_to_9"}
        if policy == "spam_one_card":
            slot = [k for k, c in enumerate(s.deck.cards) if c.startswith(self.spam_card)]
            if len(slot) != 1:
                raise ValueError(f"spam card {self.spam_card!r} matches deck slots {slot} of {s.deck.cards}")
            only = np.zeros_like(allowed)
            only[slot[0]] = allowed[slot[0]]
            if not only.any():
                return wait("spam_not_affordable")
            return {**S.shortlist(s.model, enc, heads, only, 1, 1)[0], "why": "spam_one_card"}
        raise ValueError(f"policy {policy!r} not in {POLICIES}")

    def play_policy(self, policy: str, m) -> dict:
        t0, states, keep = time.perf_counter(), [], []
        while True:
            ds = m.due()
            if not ds:
                break
            if m.learner in ds:
                states.append(snap(m.env))
            for s in ds:
                s.prepare()
            todo = []
            for s in ds:
                p, enc, heads, hand = S.forward(s)
                if s is m.learner:
                    d = self.decide(policy, s, p, enc, heads, hand)
                    _, allowed, stalled = s.pre(hand)        # training's keep rule (e1_eval sample_decide_batch +
                    keep.append(bool((allowed.any() and not stalled) or d["play"]))   # rl_royale.collate)
                else:
                    _, allowed, stalled = s.pre(hand)
                    d = E.live_decide_batch(s.model, enc, heads, [p], allowed[None], np.array([stalled]),
                                            tau=s.cfg["tau"], device=s.cfg["device"])[0]
                todo.append((s, p, d))
            for s, p, d in todo:
                s.apply(p, d)
        final = snap(m.env)
        r, L = m.result(), m.learner.side
        mism = sum(tuple(x["crowns"]) != RS.crowns({**x, "crowns": None}) for x in states + [final])
        return {"policy": policy, "seed": int(m.spec["seed"]), "tag": m.spec["tag"], "learner_side": L,
                "opp_deck": m.spec["opp_deck"], "outcome": r["outcome"],
                "z": {"win": 1.0, "loss": -1.0}.get(r["outcome"], 0.0),
                "crowns_for": r["crowns_for"], "crowns_against": r["crowns_against"], "end_tick": r["end_tick"],
                "decisions": len(states), "plays_attempted": r["plays_attempted"],
                "plays_accepted": r["plays_accepted"], "opp_plays_accepted": r["opp_side"]["plays_accepted"],
                "crowns_derivation_mismatch": int(mism),
                # KEPT rows = training's rows (gate_sampled | played); keep[i] for decision i
                "kept_rows": int(sum(keep)), "keep": keep,
                # reward_shaping.phi_record per decision (what e1_eval records under record_phi); final for reference
                "phi_rows": [RS.phi_record(x, L) for x in states], "final_phi_row": RS.phi_record(final, L),
                "wall_s": round(time.perf_counter() - t0, 1), "_states": states}


# ------------------------------------------------------------------------------------------------------
# workers
# ------------------------------------------------------------------------------------------------------
_W: dict = {}


def init_worker(args: dict) -> None:
    import torch
    torch.set_num_threads(max(1, int(args["threads"])))
    from pipeline.rl_royale import league_decks
    from pipeline.royale_env import RoyaleSelfPlayEnv
    dev, cap = args["device"], int(args["tail_cap"])
    gen, gi = E.load_policy(REPO / S.GEN_CKPT, dev)
    og, oi = E.load_policy(REPO / S.GEN_CKPT, dev)          # its own object, as search_s0
    run = ShapeRunner(gen, {"gen": (og, S.live_cfg(S.TAU_OPP, oi["grid"], dev))}, S.live_cfg(S.TAU_PLAIN, gi["grid"], dev),
                      lambda: RoyaleSelfPlayEnv(decision_ticks=10, tail_cap=cap))
    run.fixed_cell, run.spam_card = int(args["fixed_cell"]), str(args["spam_card"])
    _W["runner"] = run
    _W["census"] = league_decks(REPO / "scratchpad/gauntlet/L68/selfplay/loadable_decks.json")


def run_job(job: tuple) -> dict:
    """search_s0._run_job's gen-opponent deck draw (same seed -> same deck and side), then ``play_policy``."""
    policy, seed = job
    from pipeline.dataset_gen import card_key
    from pipeline.royale_env import UnsupportedDeck
    run, census = _W["runner"], _W["census"]
    for j in range(50):
        d = S.opp_deck_for(seed * 1000 + j, census)
        if any(card_key(n) not in run.opps["gen"][0].gid for n in d["engine"]):
            continue
        try:
            m = run.setup("gen", seed, d["engine"])
            break
        except (UnsupportedDeck, KeyError):
            continue
    else:
        return {"policy": policy, "seed": seed, "skipped": "no loadable deck"}
    rec = run.play_policy(policy, m)
    rec["opp_deck_name"] = d["name"]
    return rec


def cli(doc: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=doc.split("\n")[0])
    ap.add_argument("--out", type=Path, required=True, help="output dir (must be empty or absent)")
    ap.add_argument("--matches", type=int, default=100, help="seeds 0..N-1 (learner_side = seed %% 2)")
    ap.add_argument("--smoke", action="store_true", help="2 matches")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--threads", type=int, default=2, help="torch threads per process")
    ap.add_argument("--device", default="cpu", choices=("cpu",))
    ap.add_argument("--tail-cap", type=int, default=7200)
    ap.add_argument("--fixed-cell", type=int, default=FIXED_CELL)
    ap.add_argument("--spam-card", default=SPAM_CARD, help="obs-contract card name prefix (knight -> knight_evo)")
    return ap


def play_all(a, policies, reduce) -> list[dict]:
    """Every (policy, seed) job; lines to <out>/matches.jsonl (without the states) as each ends. -> [reduce(rec)] for
    the played matches; ``reduce`` sees the record WITH its ``_states`` (dropped afterwards, to bound memory)."""
    if a.smoke:
        a.matches = 2
    if a.out.exists() and any(a.out.iterdir()):
        raise SystemExit(f"REFUSING: {a.out} exists and is not empty")
    a.out.mkdir(parents=True, exist_ok=True)
    wargs = {"threads": a.threads, "device": a.device, "tail_cap": a.tail_cap, "fixed_cell": a.fixed_cell,
             "spam_card": a.spam_card}
    (a.out / "run.json").write_text(json.dumps({**{k: str(v) if isinstance(v, Path) else v for k, v in vars(a).items()},
                                                "gen_sha256": S.sha256(REPO / S.GEN_CKPT),
                                                "started": time.strftime("%Y-%m-%d %H:%M:%S")}, indent=1),
                                    encoding="utf-8")
    jobs = [(pol, s) for s in range(a.matches) for pol in policies]
    rows = []
    with (a.out / "matches.jsonl").open("a", encoding="utf-8") as fh:
        def emit(rec):
            if not rec.get("skipped"):
                rows.append(reduce(rec))
            fh.write(json.dumps({k: v for k, v in rec.items() if k != "_states"}) + "\n")
            fh.flush()
            print(f"[rshape] {rec['policy']:17s} seed {rec['seed']} " + (rec.get("skipped") or
                  f"{rec['outcome']:4s} {rec['crowns_for']}-{rec['crowns_against']} dec {rec['decisions']} "
                  f"kept {rec['kept_rows']} "
                  f"plays {rec['plays_accepted']}/{rec['plays_attempted']} wall {rec['wall_s']}s"), flush=True)
        if a.workers <= 1:
            init_worker(wargs)
            for j in jobs:
                emit(run_job(j))
        else:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(a.workers, initializer=init_worker, initargs=(wargs,)) as pool:
                for rec in pool.imap_unordered(run_job, jobs):
                    emit(rec)
    return rows


def kept_shaping(rec: dict, gamma: float, w_tower: float, w_crown: float) -> dict:
    """Training's R2 rewards for one match record: rl_royale.terminal_rewards (z on the LAST kept row) + rl_royale.
    shaping_rewards over the KEPT rows' phi_record rows (gamma per kept row, Phi = 0 after the last kept row). ->
    shaping_rewards' dict + ``r`` (terminal + F per kept row) + ``rows`` (phi_record rows of the kept decisions)."""
    from pipeline import rl_royale as RL
    rows = np.asarray(rec["phi_rows"], dtype=np.float64)[np.asarray(rec["keep"], dtype=bool)]
    if not len(rows):
        z = np.zeros(0)
        return {"F": z, "tower": z, "crown": z, "phi": z, "phi_tower": z, "phi_crown": z, "r": z, "rows": rows}
    sh = RL.shaping_rewards(rows, {"gamma": gamma, "w_tower": w_tower, "w_crown": w_crown})
    sh["r"] = RL.terminal_rewards([len(rows)], [rec["outcome"]])[0] + sh["F"]
    sh["rows"] = rows
    return sh


def write(out: Path, name: str, obj: dict) -> None:
    (out / name).write_text(json.dumps(obj, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in obj.items() if k != "per_match"}, indent=1), flush=True)


def mean(xs) -> float:
    xs = list(xs)
    return float(np.mean(xs)) if xs else math.nan
