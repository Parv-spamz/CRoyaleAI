# Frozen impact instrument definitions

Unit: a synthetic root and its seven counterfactual branches, not independent
matches. Root IDs enumerate phase90/4800, level11/14, firing side0/1, lane0/1.
Each branch starts at its root and records ticks root+26 through root+326,
inclusive. Preserve all roots/branches, including any failure; no substitution.

Tower key is (team,tower_slot), with uid/kind/card_id/position/max_hp/footprint
retained. All six native crown slots must exist every frame and have finite HP
between0 and max_hp. A missing entity is an error for these nonlethal fixtures,
never silently zero. Native crown/king kinds and EMPTY_CARD required.

Per tick and tower, incremental damage = paired WAIT.hp - branch.hp. Compare
the complete effect curve, target/non-target totals, first positive tick and
final effect. Report offset distance in tiles, not a predicted hit threshold.
Command cost equals paired-WAIT minus branch elixir immediately after deployment;
zero for WAIT and catalogue Rocket cost for accepted casts. Do not read long-run
elixir differences as spending because WAIT can cap. All spell effects must end
before the final ten-frame plateau. Full engine byte and trace equality for the
two WAIT branches. No statistics of policy strength or optimization selection.

Exact integers for ticks, entities, HP, mana, command/cost and counts; hashes
for binary/source artifacts. No float comparison required for fixture coordinates.
Independent verifier positive baseline plus corruptions must reject wrong team,
missing tower/frame, altered HP/damage/cost, wrong tick/command, duplicate branch.
