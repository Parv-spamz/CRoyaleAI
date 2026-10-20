# Public-input placement-effect learnability

Registered October 5, 2026, 22:14 EDT, before collection or optimization.
The qualified moving_impact_readiness_v4 instrument motivates an isolated test:
can a small learned scorer predict actual per-entity spell effects across new
placements and scene geometries? Compare current public state with the same state
plus measured recent movement. This does not claim the current policy lacks
velocity, that more movement inputs will repair it, or that damaging more objects
is good strategy. No policy action is selected, no reward/frequency rule is added.

New192 synthetic roots, not the16 exposed qualification roots. Geometry family
is (backfield x3.5/4.5/5.5/6.5tiles, backfield y2.5/3.5/4.5tiles, body count1/2),
24families. Each includes firing sides0/1, lanes0/1, levels11/14:8variants. All
mirrors/levels/actions of one family stay together. y3.5 families are development
(8families/64roots); y2.5 and4.5 are training(16families/128roots). This is explicit
interpolation development, not untouched policy confirmation or random seed
generalization. Seeds2026101100..1291 in x,y,count,side,lane,level product order.
Bind membership before simulation; fail if a complete public-state feature vector
is duplicated across the split. Never move/exclude a failing member or resample.

Same pinned updated MAIN runtime and base fixture deck as v4. Enemy Knight at
tick180, optional Giant one tile inward at181, natural resources, individually
saved accepted results/costs. Mirror x about18 for lane1 and y about32 for enemy1.
Save public-frame history at230 and240, full root bytes at240. No direct state
edits.16fixed candidate points: world x2.5/6.5/11.5/15.5 by enemy-backfield
y3.5/7.5/11.5/15.5. Rocket cast266 after26delay; observe each tick240..396.
Also exact-root WAIT/repeatedWAIT.18branches/root,3456branches,542592frames.
All unit/crown effects retained. Same alive/identity/idle-attack/no-projectile/
unchanged-WAIT/no-friendly-damage/final10plateau qualifications as v4. Save full
compressed raw records/root/finalbytes. Any qualification failure stops the chain.

Public projection is constructed BEFORE branches from only visible body/crown
positions, radius/footprint, identity/type/team, HP/maxHP/level at230/240, own
side/card level, and candidate resolved tile-center coordinates. No opponent
resources/hand/queue, target_uid/attack internals, engine bytes, seed/family/split,
future positions or outcomes enter features. UIDs only join records to labels.
Target queries cover every enemy standing crown/body. Outcome label is positive
matched WAIT-minus-cast HP at396, with all curves independently qualified. These
are simulator effect labels, not expert tactical actions. Public geometry is
native-simulator availability; real-client parity/availability remains unproved.

Two from-scratch auxiliary predictors: static_public and motion_public, identical
28->64->64->1 ReLU MLP. Only factor is zeroing versus retaining6 measured velocity
features (target and two body slots; difference240-230 in tiles). Both already see
candidate point and current visible geometry. No R1e/IL/RL parameters are changed.
Three paired seeds2026101200..1202, identical initial tensors and training draws.
Exactly1000Adam updates each, lr.001, batch256, clip1, CPU1thread, no dropout,
class-balanced BCE using TRAINING positive weight Nnegative/Npositive. Finalonly,
no early selection or tuning. Save all finite losses/final checkpoints and every
development probability. Data verifier must pass BEFORE any optimizer is built.

Independent data verifier reconstructs membership/public features/labels/curves
from raw records, proves public-input isolation with private-state corruptions,
and rejects corrupted joins/splits/costs/effects. Result verifier independently
recomputes original metrics and fixed filters from saved probabilities/labels;
no inference/optimization repeated. Shared source hashes frozen at first launch;
failed sources/receipts remain immutable. Single serial CPU chain, no GPU usage
or native replay client. Stop before next root/update/job at Tuesday04Z.

These auxiliary checkpoints cannot play a match and are NOT R1e replacements.
Report their measured comparison and explicitly state no comparable R1e outcome
score/new gameplay evidence, no acceptance/deployment. Keep original R1e policy
statistics contextual and unchanged; never relabel prototype results as policy
gains. No reserved/expert/old validation/owner bot data accessed. No live restart,
production source edits, repeated prior reports or changed final acceptance floor.
