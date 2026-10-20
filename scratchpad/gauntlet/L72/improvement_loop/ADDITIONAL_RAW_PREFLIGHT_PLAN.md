# Raw source form and coordinate preflight

The cleaned1592-match metadata contains five exact-Icebow base-deck matches,
but zero evolution/hero suffixes across every deck. It therefore cannot establish
original forms and is not eligible for conversion as-is.

At the pinned Cochon123 revision, fetch the raw file for each of those five IDs
(000Y2G2Y2R0C,08VP0LLGJC80,0999VPRVUQQL,09G9LL0U0LY9,09G9LL22QVVV), plus the
lexicographically first other cleaned match as an ordinary schema control. Only
use exact paths returned by the public dataset API; never infer remote paths.
Maximum six requests,4MiB each, anonymous. Save original bytes and hashes.

Inspect source schema/HTML for complete decks with original forms, both-side
timed/positioned actions, explicit orientation and ability attribution. Preserve
missing fields as missing and challenge/error captures as excluded. Compare
source commands with cleaned events only as a parser check. Do not reconstruct,
predict, optimize or choose examples using outcomes. Raw fidelity and deduplication
are mandatory before a separate bounded acquisition/reconstruction plan.
