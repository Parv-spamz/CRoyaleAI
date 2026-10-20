# Preserve the failed probe's final raw-pointer comparison

The native capture completed all three requested arms: DarkMagic, Arrows and
DarkMagic repeat. Accepted resolved IDs were 28000023/28000001/28000023 and
same-tick elixir deductions were 5/3/5. The final comparison then failed because
the new probe retained full entity dictionaries, including allocator-address
`id` and `target` fields. The older public-object normalizer only renames spell
objects. All 110 observed differences were these entity addresses, not geometry,
health, timing or actual target identity.

Preserve probe.py/probe.json and its nonzero receipt unchanged. Do not rerun the
native experiment merely to relabel a successful capture. The independent reader
will map entity addresses to their recorded stable native entity_id and resolve
target references through the same frame's entity map, rejecting unknown targets
or duplicate body IDs. It retains all other entity fields and uses the existing
spell-object lifetime normalization. Deliberate target/position/health/timing
corruptions must still fail. Final guest/source attestation is read-only because
the original final comparison prevented its last attestation from running.

A successful independent proof can establish the measured identity/cost/repeat
claim while the original producer receipt remains a failure. This is not new
mechanical behavior, policy inference, full-game parity or replay qualification.
