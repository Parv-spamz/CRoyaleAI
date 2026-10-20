# Preserve two training-harness failures; correct representation and reset accounting

Version 2 ran all thirteen fallback training cases and repeated them, then stopped
at its first unchanged control. A read-only comparison of the saved old/new control
records (03f212af364d40a1ba1a55a9e3e3cf63) found identical final, grade, log, opening
hand, final deck and frame count. The in-memory final dictionary uses integer side
keys; reading the old JSON makes those string keys. Comparing those representations
directly caused the false assertion. No physical tolerance or game criterion changes.

Version 3 compares the just-written JSON records with the old JSON, preserving
every original value. The independent verifier already reads serialized records.
Keep v2 sources, failed receipt, partial progress and all captures. None was
promoted as accepted recovery based on that incomplete run.

Review also found the resolver's 64-probe bound omitted the driver's original
two discovery resets and final reset. Version 3 restricts the resolver to 61,
so total per-attempt native resets are at most 64. Four v2 unresolved cases used
64 resolver resets; they exceeded the intended combined bound and remain failed.
This tightens accounting to the original plan; it does not extend search or
relax acceptance. Same selected cases, seed, source commands/forms, mechanics,
public fields, criteria and deterministic repeats. Rerun the fixed training
comparison once under distinct v3 artifacts; no confirmation retries yet.
