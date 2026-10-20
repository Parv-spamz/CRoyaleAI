# Diagnose exact saved-root restore without advancing simulation

Original corrected collection failed before any trajectory at combined exact-byte
and in-memory-frame assertion. Preserve its source and nonzero receipt. Load each
of the192 already prepared roots once, with no reset, step, action or optimizer.
Check native bytes EXACTLY unchanged and compare every frame to its saved JSON
representation. Inventory type-only differences; accept no numeric tolerance,
missing fields or UID change. Corruption controls must reject altered coordinates,
HP, missing entity and native bytes. This is a serialization diagnosis, not a
retroactive pass of the original in-memory comparison. Reuse qualified preparation
only after diagnosis, with a separately registered recovery collector.
