"""L70: census decks with evolution / hero forms -> loadable_decks.json.

    icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L70/pool_forms/loadable_decks.py [--top 1000]

Derived from L69/pool/loadable_decks.py. Stage 1 (icebow venv, polars): rank exact
form-carrying census card sets by deck-sides in the local IL_Replay parts. Stage 2
(this file re-run in the Royale venv): RoyaleSelfPlayEnv(forms_mode="deck").reset
for each top-N deck plus the unchanged icebow / live-account starter extras.
Loadable = no UnsupportedDeck, even when a requested form falls back to base.

RoyalAPI -evN maps to @evolution (all N, counted separately in form_variants),
and -hero to @hero, after resolving the base slug to its engine spelling. Unknown
base slugs still pass through for reset to refuse. Raw form-carrying slugs remain
the ranking key, so different census variants never silently merge. The legacy
census_distinct_base_decks key is retained for schema compatibility, but now
counts form-carrying decks, also explicitly named census_distinct_form_decks.
Form frequency statistics cover ALL census sides; fallback counts cover only
the tested top-N and extras, with their census weight reported separately.
"""
import glob
import json
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ROYALE_PY = REPO / "research/ext/Royale/.venv/Scripts/python.exe"
FORM = re.compile(r"-(ev\d+|hero)$")
slug = (lambda s: re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-"))
ICEBOW = ["Tornado", "Tesla", "IceWizard", "Xbow", "Rocket", "Knight", "Log", "Skeletons"]
STARTER = ["Knight", "GoblinHut", "Goblins", "Arrows", "Fireball", "Giant", "Musketeer", "MiniPekka"]


def slug_to_engine() -> dict:
    m = {}
    for c in json.load(open(REPO / "scratchpad/gauntlet/L69/generalist/royalesim_cards.json")):
        m[slug(c["name"])] = c["name"]
        m[slug(c.get("display_name") or c["name"])] = c["name"]
    for line in open(REPO / "icebow/data/ghost_pool/pool_env_v1.jsonl"):
        e = json.loads(line)
        for it in e["icebow_deck"] + e["ghost_deck"]:
            m.setdefault(it["slug"], it["name"])
    return m


def engine_name(card: str, mapping: dict) -> str:
    match = FORM.search(card)
    base = card[:match.start()] if match else card
    name = mapping.get(base, base)
    return name + ("@hero" if match[1] == "hero" else "@evolution") if match else name


def census():
    import polars as pl
    sides = Counter()
    for f in sorted(glob.glob(str(REPO / "scratchpad/gauntlet/L67/hf/replays/*.parquet"))):
        for pj in pl.read_parquet(f, columns=["payload_json"])["payload_json"]:
            b = json.loads(pj)["battle"]
            for who in ("team", "opponent"):
                for p in b[who]["players"]:
                    sides[tuple(sorted(c["card_key"] for c in p["deck"]))] += 1
    return sides


def form_stats(sides: Counter, mapping: dict) -> dict:
    total = sum(sides.values())
    counts, variants = Counter(), Counter()
    any_form = evo = hero = 0
    for cards, n in sides.items():
        forms = [(c, FORM.search(c)) for c in cards if FORM.search(c)]
        any_form += n * bool(forms)
        evo += n * any(m[1].startswith("ev") for _, m in forms)
        hero += n * any(m[1] == "hero" for _, m in forms)
        for name in {engine_name(c, mapping) for c, _ in forms}:
            counts[name] += n
        for _, match in forms:
            variants[match[1]] += n
    return {
        "census_sides_with_forms": any_form,
        "census_sides_with_evolution": evo,
        "census_sides_with_hero": hero,
        "census_forms_share": any_form / total,
        "census_evolution_share": evo / total,
        "census_hero_share": hero / total,
        "form_variants": dict(variants.most_common()),
        "top_form_cards": [{"card": c, "sides": n, "share_of_census": n / total}
                           for c, n in counts.most_common(15)],
    }


def reset_all(job: Path) -> None:
    """Stage 2: add loadable / blocker / form_fallbacks to every attempted deck."""
    sys.path.insert(0, str(REPO))
    from pipeline.royale_env import RoyaleSelfPlayEnv, UnsupportedDeck
    d = json.load(open(job))
    env = RoyaleSelfPlayEnv(forms_mode="deck")
    t0 = time.perf_counter()
    for x in d["decks"]:
        # An unsupported base card can fail before the env clears the last reset's fallbacks.
        env.form_fallbacks = []
        try:
            env.reset(x["engine"], ICEBOW, seed=0)
            x["loadable"], x["blocker"] = True, None
        except UnsupportedDeck as u:
            x["loadable"], x["blocker"] = False, str(u)
        x["form_fallbacks"] = list(env.form_fallbacks)
    d["reset_seconds"] = round(time.perf_counter() - t0, 2)
    d["resets_per_s"] = round(len(d["decks"]) / max(d["reset_seconds"], 1e-9), 1)
    json.dump(d, open(job, "w"))


def fallback_stats(decks: list) -> list:
    counts, sides = Counter(), Counter()
    for x in decks:
        for card in {name + {1: "@evolution", 2: "@hero"}[form]
                     for _, name, form in x["form_fallbacks"]}:
            counts[card] += 1
            sides[card] += x["sides"] or 0
    return [{"card": card, "decks": n, "census_deck_sides": sides[card]}
            for card, n in counts.most_common()]


def main(top: int) -> None:
    t0 = time.perf_counter()
    sides = census()
    total = sum(sides.values())
    m = slug_to_engine()
    decks = [{"rank": r, "sides": n, "slugs": list(k), "engine": [engine_name(s, m) for s in k]}
             for r, (k, n) in enumerate(sides.most_common(top), 1)]
    decks += [{"rank": None, "sides": None, "name": "icebow", "engine": ICEBOW},
              {"rank": None, "sides": None, "name": "starter", "engine": STARTER}]
    job = HERE / "_reset_job.json"
    json.dump({"decks": decks}, open(job, "w"))
    subprocess.run([str(ROYALE_PY), __file__, "--reset", str(job)], check=True)
    d = json.load(open(job))
    job.unlink()
    ranked = [x for x in d["decks"] if x["rank"]]
    ok = [x for x in ranked if x["loadable"]]
    blockers = Counter(x["blocker"] for x in ranked if not x["loadable"])
    out = {
        "top_n": top, "census_deck_sides": total, "census_distinct_base_decks": len(sides),
        "loadable_in_top_n": len(ok),
        "loadable_sides_share_of_census": round(sum(x["sides"] for x in ok) / total, 4),
        "top_n_sides_share_of_census": round(sum(x["sides"] for x in ranked) / total, 4),
        "top_blockers": blockers.most_common(15),
        "resets_per_s": d["resets_per_s"], "wall_s": round(time.perf_counter() - t0, 1),
        "extra": [{k: x[k] for k in ("name", "engine", "loadable", "blocker", "form_fallbacks")}
                  for x in d["decks"] if not x["rank"]],
        "decks": [{k: x[k] for k in ("rank", "sides", "engine", "slugs", "form_fallbacks")} for x in ok],
        "census_distinct_form_decks": len(sides),
        **form_stats(sides, m),
        "form_fallbacks_by_card": fallback_stats(d["decks"]),
        "unloadable_decks": [x for x in ranked if not x["loadable"]],
    }
    json.dump(out, open(HERE / "loadable_decks.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("decks", "unloadable_decks")}, indent=1))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--reset"]:
        reset_all(Path(sys.argv[2]))
    else:
        main(int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 1000)
