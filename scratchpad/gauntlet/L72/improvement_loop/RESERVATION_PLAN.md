# Outcome-blind replay reservation, October 5

Reserve the unused raw command groups now, before any new model predictions or
successor training. This prevents later collection from consuming potential
confirmation examples. It does not certify their reconstruction or component
denominators and does not close N2.

All183 exact Icebow candidates are reserved for confirmation; none may enter
successor training or development. Every other unused command group is assigned
by SHA256 of `clashbot-l72-replay-reservation-20261005-v1:` followed by its existing
conservative command signature: first8 digest bytes, big endian, modulo100;
0–69 training,70–84 development,85–99 confirmation. All sides of a replay share
one assignment. Duplicate or historically exposed IDs/signatures are rejected.
Keep anonymous-player and conservative-prefix-deduplication limits explicit.

Native reconstruction success can determine availability, but cannot change a
group's assignment. Unsupported forms stay unavailable; do not strip forms or
silently replace observations with simulator states. Future public collections
must be deduplicated against this reservation and all historical exposure.
Final model selection uses development only. Before successor training, freeze
the usable reconstructed membership, feature/label hashes and the full statistical
analysis/sample-size plan required by PLAN.md. Reservation alone is insufficient.
