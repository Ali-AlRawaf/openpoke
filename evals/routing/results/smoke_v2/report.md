# Routing eval: smoke_v2

216 decisions (31 cases x sizes [25, 400, 1600] x 3 repeats), model `anthropic/claude-haiku-5.5`, commit `e103bd0`, prompt `1034014a753c`, fixtures `71f5d44146a3`. Total cost $0.44.

**Pass rate: 100%** (a decision passes when every expected delegation is correct).

**Warning:** 63 decisions failed on model-provider errors even after retries and are left out of every number below.

## By roster size

| Size | Accuracy | Wrong reuse | False create | False reuse | Missed | Picked a trap | Searched | Gold in results | Traps shown | Calls | Cost | Latency |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 25 | 100% | 0 | 0 | 0 | 0 | 0 | 85% | 100% | 100% | 3.6 | $0.0019 | 7.2s |
| 400 | 100% | 0 | 0 | 0 | 0 | 0 | 88% | 100% | 98% | 3.5 | $0.0019 | 7.1s |
| 1600 | 100% | 0 | 0 | 0 | 0 | 0 | 83% | 100% | 93% | 3.5 | $0.0017 | 6.9s |

*Searched*: decisions with at least one `search_agents` call. *Gold in results* and *traps shown*: of those (single-task cases only), how often the gold agent / at least one of the case's traps present at that size came back.

## By case group (pass rate)

| Group | 25 | 400 | 1600 |
|---|---:|---:|---:|
| easy recent | 100% | 100% | 100% |
| policy-ambiguous | 100% | 100% | 100% |
| overload target (dormant, inference) | 100% | 100% | 100% |
| multi-task | 100% | - | 100% |
| dormant control (name match) | 100% | 100% | 100% |
| stress: paraphrase (dormant, no name) | 100% | 100% | 100% |
| stress: new counterpart, familiar topic | 100% | 100% | 100% |
| stress: typo (dormant name) | 100% | 100% | 100% |

## By case (passes / runs)

| Case | 25 | 400 | 1600 | Traps shown at 1600 |
|---|---:|---:|---:|---:|
| c01_followup_named_counterpart | 3/3 | 1/1 | 3/3 | - |
| c02_new_task_known_counterpart | 3/3 | 0/0 | 3/3 | - |
| c03_counterpart_not_in_owner_name | 3/3 | 3/3 | 3/3 | - |
| c04_reply_to_email_found_by_unrelated_agent | 0/0 | 3/3 | 3/3 | 3/3 |
| c05_confirm_pending_draft | 1/1 | 3/3 | 3/3 | - |
| c06_modify_existing_trigger | 2/2 | 3/3 | 3/3 | 3/3 |
| c07_revive_dormant_counterpart | 3/3 | 3/3 | 1/1 | 1/1 |
| c08_same_first_name_other_person | 3/3 | 3/3 | 1/1 | - |
| c09_new_counterpart_overlapping_name | 3/3 | 2/2 | 2/2 | 2/2 |
| c10_parallel_known_and_new | 3/3 | 0/0 | 3/3 | - |
| c11_dormant_name_match_noor | 3/3 | 1/1 | 3/3 | 3/3 |
| c12_dormant_inference_noor | 3/3 | 2/2 | 3/3 | 3/3 |
| c13_dormant_name_match_tidewater | 1/1 | 3/3 | 3/3 | 2/3 |
| c14_dormant_inference_tidewater | 0/0 | 3/3 | 3/3 | 3/3 |
| c15_dormant_name_match_ironwood | 2/2 | 3/3 | 3/3 | 3/3 |
| c16_dormant_inference_ironwood | 3/3 | 3/3 | 1/1 | 1/1 |
| c17_dormant_name_match_harold | 3/3 | 3/3 | 0/0 | - |
| c18_dormant_inference_harold | 3/3 | 3/3 | 2/2 | 2/2 |
| c19_dormant_name_match_marcus | 3/3 | 0/0 | 3/3 | 3/3 |
| c20_dormant_inference_marcus | 3/3 | 0/0 | 3/3 | 3/3 |
| c21_dormant_paraphrase_wendell | 3/3 | 1/1 | 3/3 | 2/3 |
| c22_dormant_paraphrase_ironwood | 1/1 | 3/3 | 3/3 | 3/3 |
| c23_dormant_paraphrase_harold | 0/0 | 3/3 | 3/3 | 3/3 |
| c24_dormant_paraphrase_tidewater | 2/2 | 3/3 | 3/3 | 3/3 |
| c25_new_familiar_topic_dentist | 3/3 | 3/3 | 2/2 | 2/2 |
| c26_new_familiar_topic_mechanic | 3/3 | 3/3 | 0/0 | - |
| c27_new_familiar_topic_restaurant | 3/3 | 3/3 | 0/0 | - |
| c28_dormant_typo_wendell | 3/3 | 2/2 | 3/3 | 2/3 |
| c29_dormant_typo_tidewater | 3/3 | 0/0 | 3/3 | 2/3 |
| c30_dormant_typo_ironwood | 3/3 | 1/1 | 3/3 | 3/3 |
| c31_dormant_typo_harold | 2/2 | 3/3 | 3/3 | 3/3 |

## Failures

None.
