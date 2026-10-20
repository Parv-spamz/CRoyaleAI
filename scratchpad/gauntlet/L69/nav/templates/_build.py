"""Crop the nav templates from the L69 captures and write templates/manifest.json (run once; the manifest records
source + box so the crops are reproducible)."""
import json, sys, cv2
from pathlib import Path
REPO = Path(r"C:\Users\benpe\ClashBot")
RAW, OUT = REPO / "scratchpad/gauntlet/L69/nav/raw", REPO / "scratchpad/gauntlet/L69/nav/templates"
OUT.mkdir(parents=True, exist_ok=True)
TH = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
# name: source, crop box (x0,y0,x1,y1), search region, anchor (template whose match this one must sit next to), tap?
T = {
 "results_ok":   ("results_131619", (345, 1410, 555, 1492), (250, 1300, 650, 1580), None, True),
 "results_name": ("results_131619", (305, 428, 590, 480), (100, 300, 800, 620), None, False),
 "main_tab":     ("after_ok_131638", (380, 1435, 520, 1598), (300, 1400, 600, 1600), None, False),
 "social_hdr":   ("friends_list_130251", (80, 500, 218, 546), (40, 470, 300, 580), None, False),
 "row_name":     ("friends_list_130915", (200, 1112, 385, 1146), (80, 575, 830, 1250), None, True),
 "popup_hdr":    ("friend_entry_130350", (118, 1006, 270, 1038), (0, 300, 420, 1560), None, False),
 "popup_fb":     ("friend_entry_130350", (95, 1272, 292, 1352), (0, 300, 420, 1600), "popup_hdr", True),
 "bt_name":      ("battle_type_130729", (530, 252, 715, 290), (0, 150, 900, 420), None, False),
 "bt_1v1":       ("battle_type_130729", (355, 418, 545, 466), (40, 370, 860, 520), None, True),
 "pend_name":    ("invite_sent_130520", (372, 144, 540, 180), (0, 0, 900, 420), None, False),
 "pend_cancel":  ("invite_sent_130520", (650, 112, 850, 186), (400, 0, 900, 420), "pend_name", True),
 "inc_name":     ("invite_incoming_131227", (368, 604, 536, 637), (0, 0, 900, 1300), None, False),
 "inc_1v1":      ("invite_incoming_131227", (246, 634, 660, 670), (0, 0, 900, 1300), "inc_name", False),
 "inc_accept":   ("invite_incoming_131227", (472, 700, 678, 778), (0, 0, 900, 1300), "inc_name", True),
}
c = lambda b: ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
man = {"friend": "JinxTheCat", "frame": [900, 1600], "templates": {}}
for n, (src, box, reg, anc, tap) in T.items():
    box = tuple(v - v % 2 for v in box)              # even-aligned: the half-scale match grid lines up
    img = cv2.imread(str(RAW / f"{src}.png"))
    cv2.imwrite(str(OUT / f"{n}.png"), img[box[1]:box[3], box[0]:box[2]])
    e = {"file": f"{n}.png", "source": f"raw/{src}.png", "box": list(box), "region": list(reg),
         "threshold": TH.get(n, 0.85), "tap": tap}
    if anc:
        a = tuple(v - v % 2 for v in T[anc][1])
        e["anchor"] = {"of": anc, "dxdy": [round(c(box)[0] - c(a)[0], 1), round(c(box)[1] - c(a)[1], 1)], "tol": 25}
    man["templates"][n] = e
(OUT / "manifest.json").write_text(json.dumps(man, indent=1))
print("wrote", len(T), "templates")
