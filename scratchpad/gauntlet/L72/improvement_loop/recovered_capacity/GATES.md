# Gates: recovered source capacity

OWNS: scratchpad/gauntlet/L72/improvement_loop/recovered_capacity/

- [x] I1: All independently qualified distinct source groups are included once with unchanged splits/forms and verified recording hashes.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/recovered_capacity/inventory.py
  EXPECT: RECOVERED_CAPACITY_INVENTORY_COMPLETE
  EVIDENCE: inventory.json and l72-recovered-capacity-inventory receipt exit0/matched;437 distinct qualified records from807 original selections, all hashes verified. Original failures retained;39 additions separately qualified.
- [x] I2: An independent original-command recount matches membership and cast totals and rejects deliberate corruption.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/recovered_capacity/verify.py
  EXPECT: RECOVERED_CAPACITY_INDEPENDENT_PASS
  EVIDENCE: verified.json and l72-recovered-capacity-independent receipt exit0/matched; independent raw CSV recount, one positive/eight rejected corruptions, exact108 confirmation replays.
- [x] I3: Review records remaining component scarcity and leaves all replacement gates and training restrictions intact.
  MANUAL: Inspect both receipts and counts; update review and HANDOFF with source casts versus opportunities distinguished.
  EVIDENCE: REVIEW.md/newest HANDOFF retain zero Barrel casts, scarce Witch/Night Witch/Furnace evidence, unqualified opportunity counts and unmet N2-N7. No training activation or model acceptance.
