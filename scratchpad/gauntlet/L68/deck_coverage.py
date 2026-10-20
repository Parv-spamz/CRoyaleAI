"""L68: which ghost-pool decks can RoyaleSim load at all?

Run with the Royale stack venv (royalesim + royalegym installed):
    research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L68/deck_coverage.py [--split heldout]

A card "loads" if its base name is in the engine catalogue (``RustEngine().cards()``). Evolution / hero forms are
counted separately: RoyaleSim has no forms, so they can only ever run as the base card.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from pipeline.e1_pool import load_pool_v1, ours, select_split  # noqa: E402
from royalegym.rust_engine import RustEngine  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="heldout")
    a = ap.parse_args()
    loaded = {c.name for c in RustEngine().cards()}
    entries = select_split(load_pool_v1(), a.split)
    blockers, forms = Counter(), Counter()
    full = {"ours": 0, "ghost": 0, "both": 0, "both_but_tornado": 0}
    for e in entries:
        ok = {}
        for who, deck in (("ours", ours(e, "deck")), ("ghost", e["ghost_deck"])):
            missing = [it["name"] for it in deck if it["name"] not in loaded]
            blockers.update(f"{who}:{n}" for n in missing)
            forms.update(f"{who}:{it['name']}@{it['form']}" for it in deck if it["form"] != "base")
            ok[who] = missing
            full[who] += not missing
        full["both"] += not ok["ours"] and not ok["ghost"]
        full["both_but_tornado"] += all(n == "Tornado" for n in ok["ours"] + ok["ghost"])
    n = len(entries)
    print(json.dumps({"split": a.split, "entries": n, "engine_cards_loaded": len(loaded),
                      "decks_fully_loadable": {k: f"{v}/{n} ({100 * v / n:.1f}%)" for k, v in full.items()},
                      "top_blockers": blockers.most_common(25),
                      "forms_run_as_base": forms.most_common(15)}, indent=1))


if __name__ == "__main__":
    main()
