# Public hand inputs and subsequent response sequences

Owner-supervised successor, October 6. Freeze the existing 213995 training and
54723 development rows (1573/405 disjoint replays), original action labels and
public-only observation contract. No reserved confirmation or old validation.
This data preparation does not load a model or optimize parameters.

C1 constructs Mirror-aware hand tokens from regular public board frames. Reuse
the 160 previously saved public streams when their source bindings match; extract
the other streams through the same public projection. No player, log, deck or
command-timed frame enters the observation tracker. Save every stream and token.

Only a separate descriptive scorer reads accepted log events. At each query use
the first strictly later opponent play within 400 ticks, then first strictly
later own play within 100 ticks. Call this the subsequent response, not proof of
a counter, intention, profitability or causal effect. Record whether its card is
in our hand at the query and whether it is spent at/after the query but strictly
before the opponent event. Keep all missing, ambiguous and truncated windows.
Retaining can include playing other cards. All eight cards are eligible; no
counter mapping or holding targets/rewards are added. Future records are audit
only and are saved in separate arrays that training must not read as features.

V1 independently rebuilds FIFO bounds, public Mirror normalization, all feature
rows, event/row/source membership and the response windows from original logs.
Corruptions must fail. No model inference, optimization or live changes.

OWNS: this directory and icebow/data/bench/hand_retention_sequence_20261006.
