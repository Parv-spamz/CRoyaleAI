# V5 blind verification of ticket O5 (split `scalars` into my_elixir/opp_elixir/king_hp)
Baseline 4bca159; work uncommitted. Verifier scratch: scratchpad/gauntlet/L67/split/v5_scratch/ (e1_view_head.py = `git show 4bca159:pipeline/e1_view.py`, v5_check.py = independent checks).

## Tree
- `git diff --stat 4bca159 -- pipeline/`: exactly e1_eval.py (+18/-?), e1_view.py (23), tests/test_e1_noise_arms.py (352). `git status --porcelain -- pipeline/`: only those 3, no untracked.
- `git diff 4bca159 -- pipeline/obs_contract.py | wc -c` = 0  -> (g) PASS.
- Source diff of e1_view.py: docstring, 3 fields replacing `scalars`, ALL_NOISE_OFF, and the 4 consumer sites (`noise.scalars` -> king_hp/my_elixir/my_elixir/opp_elixir/king_hp). No renames, no RNG reordering, no constant changes. e1_eval.py: NOISE_ALIASES + alias expansion in parse_noise_off + help string. `grep -rn "noise.scalars|\.scalars\b" pipeline/` outside the test file: none left.

## Per criterion
| crit | verdict | evidence |
| a | PASS | pytest: `30 passed in 1.85s`; unittest -v: `Ran 30 tests ... OK`. Baseline 23 `def test_`, now 30 (+7: 1 golden, 3 isolation, 3 alias). Old assertion on scalars split into per-switch assertions (diff L486-497), none deleted. |
| b | PASS | Independent golden: HEAD module loaded as `pipeline.e1_view_head`; 5 boards (bs6, bs0, raw1, bs6_dmg, raw1_dmg) x 8 seeds: `head.live_view(..., head.Noise(scalars=False))` == `new.live_view(..., Noise(my_elixir=False, opp_elixir=False, king_hp=False))` asdict-equal in 40/40; `Noise()` vs `Noise()` 40/40; `ALL_NOISE_OFF` outputs 40/40. (Field-dict of ALL_NOISE_OFF differs by construction: scalars vs three names.) |
| c | PASS | bs6_dmg/raw1_dmg (my_elixir=6.37 exact=True, opp_elixir=3.0, kings hp 0.42/0.77), 8 seeds x 3 switches: `rng.bit_generator.state` byte-identical to all-on run; units/spells equal; each switch changes only its own field(s) (my_elixir 6.0->6.37 & exact False->True; opp None->3.0; kings [1.0,1.0]->[0.42,0.77]); princess towers untouched. |
| d | PASS | `parse_noise_off("scalars") == Noise(my_elixir=False, opp_elixir=False, king_hp=False)` True; `"scalars,recall"` -> recall=False plus the three; `noise_off_names(...)` == ['king_hp','my_elixir','opp_elixir']; "bogus" and "scalars,bogus" -> SystemExit; "" -> Noise(). |
| e | PASS | existing TestAllOnBitIdentical unchanged in diff; plus my 40/40 all-on head-vs-new equality. |
| f | PASS | `python -m pipeline.e1_eval --help` exit 0; line: `--noise-off ... recall,false_pos,position,team,unit_hp,my_elixir,opp_elixir,king_hp,deploying,conf (plus alias 'scalars' = my_elixir,opp_elixir,king_hp)`. |
| g | PASS | obs_contract.py diff empty. |
| constraints | PASS | `Noise.__dataclass_params__.frozen` True; `Noise(scalars=False)` -> TypeError (alias lives only in parser); `dataclasses.fields` order == recall,false_pos,position,team,unit_hp,my_elixir,opp_elixir,king_hp,deploying,conf; no new imports. |

## Findings
1. (note, no FAIL) Worker's golden test `TestGoldenSplitMatchesPreO5Scalars` uses the three stock fixtures, all with king hp_frac == 1.0 == KING_HP_LIVE (printed: bs6/bs0/raw1 kings [1.0, 1.0]). The golden therefore cannot distinguish king_hp True/False -- it is vacuous for the king_hp third of (b). The king_hp behaviour is covered instead by `TestThreeSwitchesIsolated.test_king_hp_off_changes_only_king_towers` (damaged kings 0.42/0.77, asserts NotEqual) and by my independent damaged-king golden (40/40). Suggest a follow-up ticket adding a damaged-king board to the golden; not blocking.
2. (note) Worker's isolation tests compare outputs but not `rng.bit_generator.state`; RNG-order preservation is proven here (see c) and implied by units/spells equality.

## Not checked
- Full pipeline test suite beyond test_e1_noise_arms.py (not in ticket).
- A real `e1_eval` run with `--noise-off scalars` end-to-end (needs engine); parser path verified only.

VERDICT: PASS_WITH_NOTES
STATUS: complete
