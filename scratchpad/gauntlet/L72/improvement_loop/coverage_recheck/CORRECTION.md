# Crown identity correction before reporting

The first producer completed, but review of its source-derived identities showed
more than two alleged enemy princess towers per match. Live `kind == 13` denotes
buildings as well as crown towers. For example, live_play_20261004_212221 listed
positions (2500,18500),(8500,21500),(9500,20500), not princess crown positions.
The required princess identity is kind13 AND card_id==-1. Native explicit tower
rows already use this identity. Ordinary buildings must not enter the requested
low-HP princess cohort. This corrects the parser, not the HP criterion.

Preserve run.py, verify.py, started.json, details.json, report.json and the original
producer receipt unchanged. The v2 independent verifier first checks the original
results and must reject this error, then checks separately produced v2 artifacts.
Add a hostile kind13/non-crown building to the positive fixture and enforce at
most two enemy princess identities per match. Sources and 1400/1500 thresholds
are unchanged. Only v2 counts may be used in the final report.
