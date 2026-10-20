# Routing eval report: 20261019T094647Z

- **Model:** anthropic/claude-haiku-5.5
- **Commit:** 5a72891
- **Sizes:** 25, 50, 100, 200, 400, 800, 1600
- **Cases:** 31
- **Fixtures:** evals/routing/fixtures
- **Total cost:** $2.3551
- **Started:** 2026-10-19T09:46:47+00:00  **Finished:** 2026-10-19T10:06:25+00:00

## Per size

| size | accuracy | correct | wrong_reuse | false_create | false_reuse | missed | error | extra | calls | mean prompt tok | mean cached tok | mean completion tok | mean reasoning tok | cost $ | mean latency s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | 98% (313/320) | 313 | 0 | 0 | 0 | 7 | 0 | 0 | 577 | 19,616.3 | 17,471.9 | 329.4 | 102.5 | 0.3505 | 4.3 |
| 50 | 97% (311/320) | 311 | 0 | 0 | 0 | 9 | 0 | 0 | 571 | 19,533.5 | 17,488.2 | 328.0 | 101.1 | 0.3394 | 4.2 |
| 100 | 97% (310/320) | 310 | 0 | 0 | 0 | 10 | 0 | 0 | 576 | 19,507.6 | 17,497.7 | 324.3 | 100.1 | 0.3388 | 4.2 |
| 200 | 97% (311/320) | 311 | 0 | 0 | 0 | 9 | 0 | 0 | 577 | 19,477.2 | 17,503.2 | 329.3 | 102.5 | 0.3383 | 4.2 |
| 400 | 97% (310/320) | 310 | 0 | 0 | 0 | 10 | 0 | 0 | 581 | 19,401.4 | 17,531.0 | 324.1 | 100.0 | 0.3318 | 4.2 |
| 800 | 97% (310/320) | 310 | 0 | 0 | 0 | 10 | 0 | 0 | 575 | 19,361.3 | 17,507.3 | 327.3 | 100.0 | 0.3280 | 4.3 |
| 1600 | 97% (310/320) | 310 | 0 | 0 | 0 | 10 | 0 | 0 | 574 | 19,374.2 | 17,507.6 | 327.3 | 102.3 | 0.3283 | 4.3 |

Accuracy pools every repeat. Token columns are means per LLM call; latency is per case run.

## Agent search

| size | runs that searched | searches per run | gold in search results | creates without a search | rejected sends | search fallbacks |
|---|---|---|---|---|---|---|
| 25 | 84% | 0.850 | 100% | 1 | 2 | 0 |
| 50 | 82% | 0.820 | 100% | 1 | 1 | 0 |
| 100 | 83% | 0.840 | 100% | 1 | 1 | 0 |
| 200 | 84% | 0.850 | 100% | 2 | 3 | 0 |
| 400 | 84% | 0.850 | 100% | 0 | 1 | 0 |
| 800 | 82% | 0.830 | 100% | 0 | 2 | 0 |
| 1600 | 83% | 0.850 | 100% | 1 | 0 | 0 |

*Gold in search results*: of the existing-agent golds in runs where the query ranked agents (rosters above the search cutoff), how many the search returned. A false create with the gold returned is the IA's choice; without it, retrieval's.

## Before / after (baseline run `20261018T165232Z`)

| | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| **accuracy** | 95% → **98%** | 98% → **97%** | 91% → **97%** | 89% → **97%** | 83% → **97%** | 86% → **97%** | 78% → **97%** |
| overload target (dormant, inference) | 98% → **100%** | 98% → **100%** | 93% → **100%** | 87% → **100%** | 77% → **100%** | 67% → **100%** | 62% → **100%** |
| dormant control (name match) | 100% → **100%** | 100% → **100%** | 100% → **100%** | 100% → **100%** | 92% → **100%** | 100% → **100%** | 88% → **100%** |
| easy recent | 97% → **100%** | 100% → **100%** | 100% → **100%** | 100% → **100%** | 98% → **100%** | 100% → **100%** | 98% → **100%** |
| policy-ambiguous | 60% → **100%** | 80% → **100%** | 30% → **100%** | 40% → **100%** | 40% → **100%** | 60% → **100%** | 60% → **100%** |
| multi-task | 100% → **100%** | 100% → **100%** | 100% → **100%** | 60% → **100%** | 50% → **100%** | 90% → **100%** | 20% → **100%** |
| stress: paraphrase (dormant, no name) | - → **100%** | - → **100%** | - → **100%** | - → **100%** | - → **100%** | - → **100%** | - → **100%** |
| stress: new counterpart, familiar topic | - → **77%** | - → **70%** | - → **67%** | - → **70%** | - → **67%** | - → **67%** | - → **67%** |
| stress: typo (dormant name) | - → **100%** | - → **100%** | - → **100%** | - → **100%** | - → **100%** | - → **100%** | - → **100%** |

## Case groups (pass rate)

| group | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| overload target (dormant, inference) | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| dormant control (name match) | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| easy recent | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| policy-ambiguous | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| multi-task | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| stress: paraphrase (dormant, no name) | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| stress: new counterpart, familiar topic | 77% | 70% | 67% | 70% | 67% | 67% | 67% |
| stress: typo (dormant name) | 100% | 100% | 100% | 100% | 100% | 100% | 100% |

## Case x size

| case | category | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | pattern |
|---|---|---|---|---|---|---|---|---|---|
| c01_followup_named_counterpart | followup_counterpart_in_name | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c02_new_task_known_counterpart | new_task_known_counterpart | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c03_counterpart_not_in_owner_name | new_task_owner_name_unrelated | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c04_reply_to_email_found_by_unrelated_agent | reply_to_found_email | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c05_confirm_pending_draft | confirm_pending_draft | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c06_modify_existing_trigger | modify_reminder | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c07_revive_dormant_counterpart | dormant_counterpart_summary_only | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c08_same_first_name_other_person | same_first_name_other_person | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c09_new_counterpart_overlapping_name | new_counterpart_overlapping_name | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c10_parallel_known_and_new | parallel_known_and_new | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c11_dormant_name_match_noor | dormant_name_match | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c12_dormant_inference_noor | dormant_inference | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c13_dormant_name_match_tidewater | dormant_name_match | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c14_dormant_inference_tidewater | dormant_inference | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c15_dormant_name_match_ironwood | dormant_name_match | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c16_dormant_inference_ironwood | dormant_inference | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c17_dormant_name_match_harold | dormant_name_match | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c18_dormant_inference_harold | dormant_inference | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c19_dormant_name_match_marcus | dormant_name_match | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c20_dormant_inference_marcus | dormant_inference | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c21_dormant_paraphrase_wendell | dormant_paraphrase | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c22_dormant_paraphrase_ironwood | dormant_paraphrase | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c23_dormant_paraphrase_harold | dormant_paraphrase | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c24_dormant_paraphrase_tidewater | dormant_paraphrase | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c25_new_familiar_topic_dentist | new_counterpart_familiar_topic | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c26_new_familiar_topic_mechanic | new_counterpart_familiar_topic | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c27_new_familiar_topic_restaurant | new_counterpart_familiar_topic | 3/10 (missed×7) | 1/10 (missed×9) | 0/10 (missed×10) | 1/10 (missed×9) | 0/10 (missed×10) | 0/10 (missed×10) | 0/10 (missed×10) | fails at every size (starvation?) |
| c28_dormant_typo_wendell | dormant_typo | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c29_dormant_typo_tidewater | dormant_typo | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c30_dormant_typo_ironwood | dormant_typo | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c31_dormant_typo_harold | dormant_typo | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |

## Misses

### c27_new_familiar_topic_restaurant @ 25 #0: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 25 #1: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 25 #2: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 25 #3: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 25 #6: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 25 #7: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 25 #8: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 50 #0: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 50 #1: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 50 #2: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 50 #3: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 50 #4: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 50 #5: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 50 #7: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 50 #8: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 50 #9: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 100 #0: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 100 #1: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 100 #2: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 100 #3: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 100 #4: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 100 #5: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 100 #6: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 100 #7: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 100 #8: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 100 #9: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 200 #0: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 200 #1: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 200 #2: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 200 #4: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 200 #5: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 200 #6: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 200 #7: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 200 #8: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 200 #9: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 400 #0: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 400 #1: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 400 #2: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)
- **Search** (search): `Theo Marchetti Northfold Studio office lunch reservation quiet restaurant near office client`

### c27_new_familiar_topic_restaurant @ 400 #3: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 400 #4: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 400 #5: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 400 #6: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 400 #7: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 400 #8: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 400 #9: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 800 #0: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 800 #1: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 800 #2: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 800 #3: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 800 #4: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 800 #5: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 800 #6: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 800 #7: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 800 #8: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 800 #9: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 1600 #0: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 1600 #1: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 1600 #2: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 1600 #3: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 1600 #4: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 1600 #5: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 1600 #6: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 1600 #7: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 1600 #8: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)

### c27_new_familiar_topic_restaurant @ 1600 #9: `missed`

- **Task:** book a quiet lunch near the office on Thursday for Theo and a new client
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** (none)
