# Frozen effect-predictor metrics and continuation

Rows query16candidate points against every enemy entity:13824rows,9216train and
4608development if complete. Denominators:192roots in24geometry families; multiple
targets/actions/mirrors/levels are dependent. Body versus crown results separate.
Label1 iff final matched HP difference>0; label0 otherwise. No coordinate-distance
substitution. All matched curves monotone/nonnegative, final10frames plateau,
every UID present/alive, six crowns fixed, no ordinary attacks/projectiles.

Features28, in order: target x/18,y/32; aim x/18,y/32; aim-minus-target x/18,y/32;
radius in tiles; footprint width/height in tiles (0for bodies); HP/10000;
target level/14; troop/king/princess flags; Knight/Giant flags; own Rocketlevel/14;
target displacement x/y in tiles over last10ticks; first body x/18,y/32,dx,dy;
second-body-present flag and second body x/18,y/32,dx,dy. Body slots are sorted by
public card ID, not hidden target/UID; absent slot zeros. Coordinates rotate180
for firing side0 so own side is bottom, including movement sign. Velocity indices
17,18,21,22,26,27 are zeroed in static control. No future features. Full projected
input arrays and whitelist required; exact float64 derivation checked independently.

For each arm/seed/split, report original row count, positive/negative counts,
Brier score, balanced Brier (half mean squared error on positives plus half on
negatives), recall and false-positive rate at fixed probability.5; separately
all/body/crown. Report all final losses, per-root/group mean squared error, all
three seeds and paired differences. Do not infer strength from accuracy dominated
by misses or from the larger number of WAIT/zero labels.

Motion-component continuation requires ALL: mean development BODY balanced Brier
<=.10; >=20% relative reduction from static; at least2of3paired seeds improve
BODY balanced Brier; mean CROWN balanced Brier <=static+.01; finite1000updates
perarm/seed and exact membership/provenance. These are new mechanism-development
filters, not revisions to any policy/aim/gameplay deployment floor. If static is
already accurate or motion loses, preserve that result; no alternate arm or best
seed substitution. No significance claim from only8development geometry families.
A pass supports separately registered integration/design only, not policy launch.

Prospective arithmetic comparison tolerance1e-12 for independently reduced float64
summary values; labels/counts/membership/hashes exact. This does not waive older
exact-logit/probability failures. No partial model eligible after failure/cutoff.
