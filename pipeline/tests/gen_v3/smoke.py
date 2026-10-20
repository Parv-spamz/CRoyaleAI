"""The authorized 50-replay smoke; never a full build. CPU only."""
import json
from pathlib import Path
import numpy as np
from pipeline.dataset_gen import build


def main():
    root=Path(__file__).resolve().parents[3]
    directory=Path(__file__).parent
    original=json.loads((root/"icebow/data/pipeline/gen_dataset_v2.json").read_text())
    out=directory/"gen_dataset_v3.npz"
    result=build([root/Path(c) for c in original["corpora"]],out,feature_version=3,limit=50,workers=1)
    assert result["files"]==50 and result["failed"]==0
    meta=json.loads(out.with_suffix(".json").read_text());st=meta["stats"]
    with np.load(out) as z:
        shapes={k:list(z[k].shape) for k in z.files if k not in ("meta",)}
        assert z["unit_form"].shape==(len(z["tok"]),)
        assert z["opp_past"].shape==(len(z["sc"]),3,5)
        assert set(np.unique(z["unit_form"]))=={0,1,2}
    names=sorted({k.split(":")[1] for k in st if k.startswith(("evo_deck_sides:","tag_observations:"))})
    cards={n:{"evo_observations":st.get(f"tag_observations:{n}:1",0),
              "hero_observations":st.get(f"tag_observations:{n}:2",0),
              "ambiguous_base_observations":sum(v for k,v in st.items() if k.startswith(f"tag_ambiguous:{n}:")),
              "tagged_max_hp":{k.split(":",2)[2]:v for k,v in st.items() if k.startswith(f"tag_max_hp:{n}:")}}
           for n in names}
    report={"summary":{k:v for k,v in result.items() if k not in ("stats","top20_decks")},
            "shapes":shapes,"features":meta["new_features"],"cards":cards,
            "evo_without_tagged_units":[n for n in names if st.get(f"evo_deck_sides:{n}") and not cards[n]["evo_observations"]],
            "counting":"Per-card counts are entity observations across frames/play_frames, not unique bodies (no stable ids in these 50 recordings). Token shares count the emitted dataset tokens.",
            "limitations":["No-id evolution attribution uses isolated cohorts; overlapping plays or missing birth evidence fall back to base.",
                           "Live opponent history inherits PlayDetector omissions for bodyless spells and estimates placement from spawn centroids.",
                           "Smoke takes first 50 ordered corpus replays, so coverage is not representative of all six corpora."]}
    (directory/"smoke_result.json").write_text(json.dumps(report,indent=2))
    print(json.dumps({"summary":report["summary"],"features":report["features"],"evo_without_tagged_units":report["evo_without_tagged_units"]}))


if __name__=="__main__":
    main()
