# Overnight continuation and conditional live deployment

Direct owner instruction, October 5, 2026, approximately 22:40 EDT:

> i'm going to bed now, keep working on the model overnight. Remember: if you don't see visible progress after trying something a bunch of times, it's a good idea to rethink your approach and try something new. if you produce a candidate that beats out R1e on our target metrics, you may deploy it live with start_live.sh, to see how it performs.

This extends the previous Tuesday 04:00Z experiment cutoff. The existing worker
heartbeat is extended through October 6 at 09:00 America/New_York (13:00Z), a
bounded overnight work window chosen for this instruction. Stop sooner if the
owner cancels or Claude actually takes over. Claude's old reset time alone is
not a takeover. The separate daily newsletter schedule is unchanged.

Continue measured model work without asking the sleeping owner about routine
reversible choices. After repeated failures or negligible gains, state which
hypothesis the evidence weakens, what a different approach would test, and how
the next experiment could distinguish it. Avoid blind grids, repeats of completed
jobs, or combining rejected recipes without evidence. Engineering fixture checks
must precede expensive training; a passing fixture is not model improvement.

The owner explicitly authorizes live evaluation through start_live.sh after a
NEW candidate satisfies the agreed R1e target-metric replacement criteria.
Keep the existing statistical, component, physical, gameplay, data-isolation,
public-input, Q4/Q5 and deployment verification requirements. No additional
approval is needed for that qualifying deployment. Preserve STOP and the idle
live state until then; this does not authorize an R1e fallback restart. At a
qualifying launch, use explicit Git Bash, inspect start_live.sh, verify the exact
checkpoint/options and one worker, then record normal confirmed plays, latency,
public audits and measured live performance. Stop the candidate on observed
operational failure or regression. Do not claim live success from startup alone.

Existing frozen experiment sources keep their original cutoff and hashes.
Any successor needing the extended window must be separately registered; never
edit a running or failed bound source to rewrite its evidence.
