"""Verify the persisted census, form edge cases, syntax and protected file bytes."""
import ast
import hashlib
import json
import py_compile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import loadable_decks as L

HERE, REPO = L.HERE, L.REPO
mapping = L.slug_to_engine()
assert L.engine_name("knight", mapping) == "Knight"
assert L.engine_name("knight-ev1", mapping) == "Knight@evolution"
assert L.engine_name("knight-ev2", mapping) == "Knight@evolution"
assert L.engine_name("knight-ev37", mapping) == "Knight@evolution"
assert L.engine_name("knight-hero", mapping) == "Knight@hero"
assert L.engine_name("missing-card-ev2", mapping) == "missing-card@evolution"
fixture = Counter({("knight",): 4, ("knight-ev1",): 3, ("knight-ev2", "musketeer-hero"): 2})
stats = L.form_stats(fixture, mapping)
assert (stats["census_sides_with_forms"], stats["census_sides_with_evolution"],
        stats["census_sides_with_hero"]) == (5, 5, 2)
assert stats["form_variants"] == {"ev1": 3, "ev2": 2, "hero": 2}
assert stats["top_form_cards"][0]["card"] == "Knight@evolution"
assert stats["top_form_cards"][0]["sides"] == 5

# Exercise census ranking inputs: base, ev1, ev2 and hero must remain distinct.
players = [{"deck": [{"card_key": c} for c in cards]} for cards in fixture]
payload = json.dumps({"battle": {"team": {"players": players}, "opponent": {"players": players}}})
with patch.object(L.glob, "glob", return_value=["fixture.parquet"]), \
        patch("polars.read_parquet", return_value={"payload_json": [payload]}):
    assert L.census() == Counter({cards: 2 for cards in fixture})

out = json.loads((HERE / "loadable_decks.json").read_text())
old = json.loads((REPO / "scratchpad/gauntlet/L69/pool/loadable_decks.json").read_text())
assert set(old) <= set(out)
assert out["census_deck_sides"] == old["census_deck_sides"]
assert out["top_n"] == 1000
assert len(out["decks"]) == out["loadable_in_top_n"]
ranked = sorted(out["decks"] + out["unloadable_decks"], key=lambda x: x["rank"])
assert [x["rank"] for x in ranked] == list(range(1, 1001))
assert [x["sides"] for x in ranked] == sorted((x["sides"] for x in ranked), reverse=True)
assert len({tuple(x["slugs"]) for x in ranked}) == 1000
for x in ranked:
    assert len(x["engine"]) == len(x["slugs"]) == 8
    assert x["engine"] == [L.engine_name(c, mapping) for c in x["slugs"]]
    assert set(old["decks"][0]) <= set(x)
    for side, name, form in x["form_fallbacks"]:
        assert side == 0 and form in (1, 2)
        assert name + {1: "@evolution", 2: "@hero"}[form] in x["engine"]
assert out["extra"][0]["engine"] == L.ICEBOW
assert out["extra"][1]["engine"] == L.STARTER
assert all(x["loadable"] and not x["form_fallbacks"] for x in out["extra"])
fallback_inputs = ranked + [dict(x, sides=None) for x in out["extra"]]
assert {x["card"]: x for x in out["form_fallbacks_by_card"]} == \
       {x["card"]: x for x in L.fallback_stats(fallback_inputs)}

# Independently count raw replay rows, form-bearing sides and card appearances.
# This also verifies the exact top-1000 ranking rather than trusting the output.
import polars as pl
raw, forms, variants = Counter(), Counter(), Counter()
tot = evo = hero = either = 0
for path in sorted((REPO / "scratchpad/gauntlet/L67/hf/replays").glob("*.parquet")):
    for payload in pl.read_parquet(path, columns=["payload_json"])["payload_json"]:
        battle = json.loads(payload)["battle"]
        for who in ("team", "opponent"):
            for player in battle[who]["players"]:
                cards = sorted(c["card_key"] for c in player["deck"])
                raw[tuple(cards)] += 1
                named = {L.engine_name(c, mapping) for c in cards}
                has_evo = any(c.endswith("@evolution") for c in named)
                has_hero = any(c.endswith("@hero") for c in named)
                tot += 1
                evo += has_evo
                hero += has_hero
                either += has_evo or has_hero
                forms.update(c for c in named if "@" in c)
                variants.update(c.rsplit("-", 1)[1] for c in cards if "@" in L.engine_name(c, mapping))
assert (tot, evo, hero, either) == (out["census_deck_sides"], out["census_sides_with_evolution"],
                                  out["census_sides_with_hero"], out["census_sides_with_forms"])
assert [(tuple(x["slugs"]), x["sides"]) for x in ranked] == raw.most_common(1000)
assert len(raw) == out["census_distinct_form_decks"] == out["census_distinct_base_decks"]
for key, value in (("census_forms_share", either), ("census_evolution_share", evo), ("census_hero_share", hero)):
    assert out[key] == value / tot
assert variants == out["form_variants"]
assert [(x["card"], x["sides"]) for x in out["top_form_cards"]] == forms.most_common(15)
assert out["loadable_sides_share_of_census"] == round(sum(x["sides"] for x in out["decks"]) / tot, 4)
assert out["top_n_sides_share_of_census"] == round(sum(x["sides"] for x in ranked) / tot, 4)

for source in (REPO / "pipeline/search_s0.py", HERE / "loadable_decks.py"):
    py_compile.compile(str(source), cfile=str(HERE / (source.stem + ".pyc")), doraise=True)
protected = json.loads((HERE / "protected_sha256.json").read_text())
for path, expected in protected.items():
    assert hashlib.sha256((REPO / path).read_bytes()).hexdigest() == expected, path
print(f"FORMS_CENSUS_VERIFIED: {len(ranked)} ranked decks, {tot} independently counted sides; "
      f"py_compile passed; {len(protected)} protected files unchanged")
