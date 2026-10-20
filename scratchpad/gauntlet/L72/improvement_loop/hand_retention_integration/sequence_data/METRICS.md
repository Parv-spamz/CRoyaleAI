# Frozen sequence semantics

- Exactly 268718 original rows and their original ids/rep/side/tick/part/labels.
- Features: opponent_hand_v2 TOKEN_COLUMNS (8x6) and QUALITY_COLUMNS (5).
  Strict event.tick < row.tick. Own and rejected/ability events excluded. No
  opponent deck/hand/elixir, accepted command truth, future states or labels.
- Standard eight-card/four-hand rules only; event uncertainty always declared.
  Mirror is conditional on consecutive genuine public plays; conservative event
  grouping may miss rapid Mirror copies. No hidden repair.
- Future window status: 0 no opponent within 400 ticks, 1 no own response within
  100 ticks of that opponent, 2 ambiguous timestamp (multiple candidate plays),
  3 response card absent from query hand, 4 response card available and retained,
  5 response card available and spent before opponent. Statuses are exhaustive.
  Separate truncated flag if final recorded tick < query+500; never silently drop.
- Save opponent/response card ids, ticks, response availability, number of own
  plays and response-card spends in [query, opponent), and public reveal status.
  These are audit fields only, not inputs or replacements for expert labels.
- Report per split and every replay: rows, six statuses, truncated windows,
  full-hand/issue/Mirror estimates and all available retained/spent card pairs.
  Rows overlap in time; no independent-opportunity or benefit claim.
- V1 exact integer/array equality. Float features contain integer or quarter
  fractions so exact equality required. Independently assert all raw labels match
  both original and corrected datasets. Positive fixture and >=8 corruption
  controls; no tolerance/threshold change to model acceptance.
