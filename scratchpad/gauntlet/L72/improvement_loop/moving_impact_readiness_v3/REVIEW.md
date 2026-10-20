# Third moving-impact collection failed during setup

October 5, 2026, 21:55 EDT. Receipt l72-moving-impact-v3-collection:
exit1, token false, 1.075143 seconds. One root completed six branches; the next
two-body root failed the accepted-setup-command assertion before a root was saved.
No complete report, independent verifier, model inference or optimization exists.
Original sources, PLAN/METRICS, started.json, first-root metadata and raw branches
remain intact. This is not a successful qualification or a model failure.

Source inspection identifies a setup mistake: py.rs apply_commands explicitly
rejects the second valid command from one team in the same batch as DUPLICATE_TEAM.
The collector batched Knight and Giant. The actual failing result was not saved,
so this is a source-based diagnosis, not a recovered status receipt. A successor
will issue separate commands at ticks180/181 and persist each result before its
assertion. No repeated full collection or retroactive passing gate is allowed.

The completed first-root producer checks include body/crown accounting and no
ordinary attack phase/projectile. They are partial producer evidence only.
