# Gates: gen_v3 observation contract

OWNS: pipeline/obs_contract.py pipeline/dataset.py pipeline/dataset_gen.py pipeline/model_gen.py pipeline/train_gen.py pipeline/live_gen.py pipeline/e1_eval.py pipeline/opp_elixir_count.py pipeline/tests/**

Scope: version-gated actual unit forms and public opponent history; the approved SIM continuation closes production wiring (SIM_GATES.md).

- [x] G1: Recording cycles, conservative attribution, heroes including Goblins flag, and opponent history verified.
  EVIDENCE: test_contract.py passes; real recordings and explicit-id/no-id fixtures; exact commands in TESTS.md.
- [x] G2: V3 CPU forward/round-trip and actual RoyaleSim replay versus recording features pass for both sides.
  EVIDENCE: test_contract.py and test_sim_contract.py pass. Production SIM/RL is separately unmet in G5.
- [x] G3: Pre-edit legacy generalist sources and current sources emit byte-identical arrays and checkpoint outputs.
  EVIDENCE: test_legacy.py passes with rseries_r1_u0155, default/v2 rows, seeded initialization, live rows and e1 heads.
- [x] G4: Only 50-replay smoke builds were run; shapes, counts and ambiguity are measured and saved.
  EVIDENCE: smoke_result.json and gen_dataset_v3.json; 50 replays, 0 failed, 12448 rows, 50440 tokens.
- [x] G5: All production SIM screens, plain reactive search and RL consumers route v3 inputs from checkpoint args.
  EVIDENCE: approved continuation, SIM_REPORT.md; production SIM replay parity, one ghost and one reactive smoke, tiny RL collate/GAE, mixed-version/S1 checks and versioned actor loading pass. 274 tests pass; one environment skip and five no-git exclusions recorded.

Result: 5 met, 0 unmet. DONE_WITH_CONCERNS for the documented environment/test limitations. No abandoned implementation requirements.
