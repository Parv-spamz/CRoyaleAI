# Independent frame oracle correction

A read-only partial check of the first v3 training capture caught an incorrect
new verifier assumption: grade.plays_driven includes abilities, while the
unchanged driver's play_frames contains ordinary card commands only. That capture
had sixteen accepted/driven commands and fifteen pre-card frames; index 12 was
an accepted Goblinstein ability. Original driver lines 530-566 handle abilities
before the card-frame snapshot. Nothing was missing from the command log.

Preserve verify.py, verify_v2.py and verify_v3.py. The standalone verify_v4.py
matches pre-card frames to exactly the driven non-ability command entries.
All abilities remain subject to the independent original CSV/log/grade recount;
no command is omitted from qualification. Capture sources/artifacts, thresholds,
source timeline and the active v3 trial chain are unchanged. This is a verifier
schema correction, not new ability-frame coverage or relaxed reconstruction.
