# Preserve and correct the first producer failure

The first audit failed its strict increasing-tick assertion on the fourth
selected record, tag50562e02a723466693061b91cd0b99bd: two compact entries at tick5860
are exactly equal Python JSON objects, including every nested observation field.
Its source, started.json, partial ignored rows.jsonl and nonzero receipt remain.

v2 collapses ONLY consecutive exactly-equal same-tick compact snapshots in the
timeline used for lifetimes/windows. Conflicting snapshots or decreasing ticks
still fail. PLAY keeps its exact original play_index frame. WAIT accepts equal
duplicates and records the first ORIGINAL compact index. No command, row, source,
label, tick, geometry, resource value or outcome is dropped/changed; duplicate
counts are reported. Original archives and the frozen METRICS remain unchanged.
This correction is bound separately before v2 runs. It does not relax missing
coverage, source qualification, final evidence or acceptance.
