# Sequence preparation review — October 6

C1/V1 and outside evidence review complete. Collection592.773279s,
independent322.451654s, review1.210942s, all exit0 and success token.
268718 original rows, 213995training/54723development, 1573/405 disjoint replays.
All original labels match both original and corrected raw datasets. All public
feature arrays, response-window descriptors and every replay count reconcile.
55 positive prefixes, three positive windows and18 corrupted result controls.
160 cached public event streams reused; remaining1818 extracted from regular
public frames only. No model inference/backward/optimizer/native replay/live calls.

Training statuses:8489 no future opponent play,49721 no own response in the
registered window,13 ambiguous timestamps,41428 response card not in query hand,
114310 available and retained,34 available and spent before the opponent play.
Development:2018/12255/3/10996/29437/14 respectively. Truncated windows14074/3429
retained separately. These overlapping row windows are not independent tactical
opportunities. Conditioning on a card actually being used soon afterward strongly
selects for cards retained or cycled back: the imbalance does NOT establish expert
intent, counter quality, profitability or a universal hold preference.

Public full-hand estimates67045training and17838development rows; detected issue
flags26529/6023; Mirror inference present2500/476 rows. These describe coverage,
not accuracy. Explicit tokens retain unknowns and untrusted-event flags. Raw
accepted logs are used only by the separate descriptor scorer, never as model
opponent observations. No future field is in features.npz. Subsequent preparation
splits feature archives by train/development before any optimization.

All existing model failures, final statistical/component/physical/gameplay/public
and Q4/Q5 requirements remain. No new-model report is due for this preparation.
Do not rerun this completed chain or modify its bound Python/PLAN/METRICS sources.
