"""gen_v2 checkpoint selection (reward_plan.md 7b): joint gate+card+cell metric on ONE fixed eval set for gen_v1 AND
every gen_v2 epoch, then complete reactive play (search_s0 plain arm) for the top-N epochs and for gen_v1 itself.

    research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L69/gen_v2/select_gen_v2.py \
        --ckpts "icebow/data/pipeline/gen_v2_s0/gen_s0_ep*.pt" --out scratchpad/gauntlet/L69/gen_v2/select
    (select.sh = the GPU wait + this; the file is not named select.py because that shadows the stdlib select module)

EVAL SET = gen_dataset_v2's val rows (split 1, all 330,237 by default) and its v3val rows (11,972). Measured
(L69 gen_v2 prep): v2's val / v3val row keys (tag, tick, side, gate, card) are a strict SUBSET of v1's, the 92,189 /
3,796 play rows are the same rows, and the train/val split agrees on all 14,661 replays -> gen_v1 never trained on
any of them. The rows v1 has and v2 lacks are the 15% wait rows on a side's own play tick that carry the post-play
hand (the 3153fa4 bug): scoring there would reward having learned the bug. gen_v1's own 30k val sample cannot be
reused (val_rows samples from v1's longer val list).

METRICS (eval_gen.evaluate unchanged, plus the gate it already computes, tapped per row):
  joint_top1   (existing, = rl_royale proagree / train_gen) play rows: card argmax right AND tile right. The cell head
               is fed the pro's card, but when the card argmax is right that IS the model's own card, so this is
               the free-running card+cell joint.
  joint_gct    play rows: gate fires (logit > 0, evaluate's threshold) AND card right AND tile right.
  gate_tnr     wait rows: gate does not fire.
  joint_bal    0.5 * (joint_gct + gate_tnr)  -- default rank key (balanced like gate_bal_acc, so "always play"
               cannot win). --rank-key picks any other key.
  joint_gct_p035 / gate_tnr_p035 / joint_bal_p035: the same metrics at P(play) > --gate-p (default 0.35, deployed).
               Names stay *_p035 even when overridden; joint.json records gate_p. Only reporting uses --gate-p;
               the default rank key and reactive plain arm's play rule are unchanged.
REACTIVE = search_s0 --arms plain --opps gen,s1 --seeds 0:24 --forms-mode deck --opp-gen gen_v1 (the
rebase_1001_evo / league1c acceptance protocol); gen_v1 is re-run in the same session as the paired baseline
(per (opp, seed): tower-HP diff delta mean / t, win delta, via search_s0.summarise), and gen_v1's fresh run is paired
against the stored rebase_1001_evo/reactive_genv1 as an engine-drift check.
"""
import argparse
import glob
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from pipeline.dataset import load as load_ds  # noqa: E402
from pipeline.eval_gen import GenRows, evaluate, load_model, val_rows  # noqa: E402

GEN_V1 = "icebow/data/pipeline/gen_v1_s0/gen_s0.pt"
STORED_BASE = "scratchpad/gauntlet/L69/rebase_1001_evo/reactive_genv1"
KEYS = ("joint_bal", "joint_gct", "gate_tnr", "joint_top1", "card_top1", "cell_tile_top1", "cell_half_top1",
        "gate_bal_acc", "wait_top1", "joint_gct_p035", "gate_tnr_p035", "joint_bal_p035", "n_play", "n")


class GateTap:
    """The model, recording both gate thresholds for every row evaluate() feeds it, in evaluate's row order."""

    def __init__(self, m, gate_p=0.35):
        if not 0.0 < gate_p < 1.0:
            raise ValueError("gate_p must be in (0, 1)")
        self.m, self.g = m, []
        self.g_deployed, self.gate_logit = [], math.log(gate_p / (1.0 - gate_p))

    def eval(self):
        self.m.eval()
        return self

    def __call__(self, b, **kw):
        out = self.m(b, **kw)
        self.g.append((out["gate"] > 0).cpu().numpy())
        self.g_deployed.append((out["gate"] > self.gate_logit).cpu().numpy())
        return out


def score(model, arrs, rows, grid, gate_p=0.35) -> dict:
    tap, log = GateTap(model, gate_p), []
    r = evaluate(tap, rows, grid=grid, rowlog=log)
    gate, play = np.concatenate(tap.g), arrs["y_gate"][rows.idx] == 1
    ids = np.concatenate([x[0] for x in log])
    assert np.array_equal(ids, rows.idx[play]), "rowlog / gate tap misaligned"
    tile, card = np.concatenate([x[2] for x in log]), np.concatenate([x[3] for x in log])
    r["joint_gct"] = float((gate[play] & tile & card).mean())
    r["gate_tnr"] = float((~gate[~play]).mean())
    r["joint_bal"] = 0.5 * (r["joint_gct"] + r["gate_tnr"])
    deployed = np.concatenate(tap.g_deployed)
    r["joint_gct_p035"] = float((deployed[play] & tile & card).mean())
    r["gate_tnr_p035"] = float((~deployed[~play]).mean())
    r["joint_bal_p035"] = 0.5 * (r["joint_gct_p035"] + r["gate_tnr_p035"])
    return {k: r[k] for k in KEYS}


def reactive(ckpt: str, out: Path, a) -> list:
    if not (out / "summary.json").exists():
        cmd = [sys.executable, "-m", "pipeline.search_s0", "--out", str(out), "--seeds", a.seeds, "--opps", a.opps,
               "--arms", "plain", "--gen", ckpt, "--opp-gen", GEN_V1, "--forms-mode", "deck", "--device", a.device,
               "--workers", str(a.workers), "--threads", str(a.threads), "--tail-cap", "7200"]
        print("[select] " + " ".join(cmd), flush=True)
        with open(str(out) + ".log", "w") as fh:
            rc = subprocess.call(cmd, cwd=REPO, stdout=fh, stderr=subprocess.STDOUT)
        if rc:
            raise SystemExit(f"search_s0 exit {rc}, see {out}.log")
    return [json.loads(x) for x in (out / "matches.jsonl").read_text(encoding="utf-8").splitlines() if x]


def paired(cand: list, base: list) -> dict:
    """search_s0.summarise's per-(opp, seed) pairing, with the candidate relabelled as an arm vs 'plain'."""
    from pipeline.search_s0 import summarise
    s = summarise([dict(r, arm="plain") for r in base] + [dict(r, arm="search") for r in cand])
    return {"cand": {k.split("|")[1]: v for k, v in s["per_arm_opp"].items() if k.startswith("search|")},
            "base": {k.split("|")[1]: v for k, v in s["per_arm_opp"].items() if k.startswith("plain|")},
            "cand_minus_base": {k.split("|")[1]: v for k, v in s["paired_vs_plain"].items()}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpts", required=True, help="glob of gen_v2 epoch checkpoints")
    ap.add_argument("--base", default=GEN_V1)
    ap.add_argument("--data", default="icebow/data/pipeline/gen_dataset_v2.npz")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--val-sample", type=int, default=0, help="0 = every v2 val row; N = a fixed seed-0 sample")
    ap.add_argument("--rank-key", default="joint_bal", choices=KEYS[:-2])
    ap.add_argument("--gate-p", type=float, default=0.35, help="second reporting threshold; keys stay *_p035")
    ap.add_argument("--rank-on", default="val", choices=("val", "v3val"))
    ap.add_argument("--top", type=int, default=2)
    ap.add_argument("--device", default="cuda", choices=("cpu", "cuda"))
    ap.add_argument("--seeds", default="0:24")
    ap.add_argument("--opps", default="gen,s1")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--skip-reactive", action="store_true")
    a = ap.parse_args()
    if not 0.0 < a.gate_p < 1.0:
        ap.error("--gate-p must be in (0, 1)")
    a.out.mkdir(parents=True, exist_ok=True)
    cands = sorted(glob.glob(str(REPO / a.ckpts) if not Path(a.ckpts).is_absolute() else a.ckpts))
    if not cands:
        raise SystemExit(f"no checkpoints match {a.ckpts}")
    dev = torch.device(a.device)
    arrs, meta = load_ds(REPO / a.data)
    va, v3 = val_rows(arrs, a.val_sample), np.where(arrs["v3val"] == 1)[0]
    rows = GenRows(arrs, va, dev)
    res = {"data": a.data, "val_sample": a.val_sample, "rank_key": a.rank_key, "rank_on": a.rank_on,
           "gate_p": a.gate_p, "ckpts": {}}
    for ck in [a.base] + cands:
        model, st = load_model(REPO / ck, dev)
        if st["card_vocab"] != meta["card_vocab"]:
            raise SystemExit(f"{ck}: card_vocab differs from {a.data}")
        grid = st["args"]["grid"]
        res["ckpts"][str(ck)] = {"epoch": st.get("epoch"), "val": score(model, arrs, rows, grid, a.gate_p),
                                 "v3val": score(model, arrs, rows.view(v3), grid, a.gate_p)}
        print(json.dumps({"ckpt": str(ck), **{p: {k: round(v, 4) if isinstance(v, float) else v
                                                  for k, v in res["ckpts"][str(ck)][p].items()}
                                              for p in ("val", "v3val")}}), flush=True)
        del model
    rank = sorted(cands, key=lambda c: -res["ckpts"][c][a.rank_on][a.rank_key])
    res["ranking"] = [(c, res["ckpts"][c][a.rank_on][a.rank_key]) for c in rank]
    res["top"] = rank[:a.top]
    (a.out / "joint.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({"ranking": res["ranking"], "top": res["top"]}), flush=True)
    if a.skip_reactive:
        return 0
    del rows, arrs
    if dev.type == "cuda":
        torch.cuda.empty_cache()
    base_m = reactive(a.base, a.out / "reactive_base", a)
    rx = {"base_vs_stored": paired(base_m, [json.loads(x) for x in (REPO / STORED_BASE / "matches.jsonl")
                                            .read_text(encoding="utf-8").splitlines() if x])}
    for c in res["top"]:
        rx[c] = paired(reactive(c, a.out / f"reactive_{Path(c).stem}", a), base_m)
    (a.out / "reactive.json").write_text(json.dumps(rx, indent=1))
    print(json.dumps(rx, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
